"""Python parser based on the standard library `ast` module (exact, no regex)."""
import ast

from .base import BaseParser, ParsedFile, Symbol


class PythonParser(BaseParser):
    language = "python"
    extensions = (".py",)

    def parse(self, path: str, source: str) -> ParsedFile:
        lines = source.splitlines()
        pf = ParsedFile(path=path, language=self.language, line_count=len(lines))
        try:
            tree = ast.parse(source)
        except (SyntaxError, ValueError) as exc:
            pf.error = f"SyntaxError: {exc}"
            return pf
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                pf.imports += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                pf.imports.append(node.module)
                pf.imports += [f"{node.module}.{a.name}" for a in node.names]
        pf.imports = list(dict.fromkeys(pf.imports))

        def add_function(fn, cls: str) -> None:
            calls: dict[str, None] = {}
            for sub in ast.walk(fn):
                if isinstance(sub, ast.Call):
                    f = sub.func
                    name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
                    if name and name != fn.name:
                        calls[name] = None
            pf.functions.append(Symbol(fn.name, "function", fn.lineno, fn.end_lineno or fn.lineno,
                                       class_name=cls, calls=list(calls)))

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                add_function(node, "")
            elif isinstance(node, ast.ClassDef):
                bases = [b.id if isinstance(b, ast.Name) else b.attr for b in node.bases
                         if isinstance(b, (ast.Name, ast.Attribute))]
                pf.classes.append(Symbol(node.name, "class", node.lineno, node.end_lineno or node.lineno, bases=bases))
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        add_function(item, node.name)
        return pf
