import re

from .base import RegexParser

_CLASS = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+([\w.]+))?"
                    r"(?:\s+implements\s+([\w., ]+))?\s*\{?\s*$")
_FUNCS = [
    (re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\*?\s+(\w+)\s*\("), False),
    (re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*(?::[^=]+)?=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*(?::[^=]+)?=>"), False),
    (re.compile(r"^\s+(?:(?:static|async|public|private|protected|readonly|get|set)\s+)*(\w+)\s*\([^)]*\)\s*(?::\s*[\w<>\[\]| .]+)?\s*\{\s*$"), True),
]
_IMPORTS = [re.compile(r"""import\s+(?:[^'"]*?\sfrom\s+)?['"]([^'"]+)['"]"""),
            re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)""")]


class JavaScriptParser(RegexParser):
    language = "javascript"
    extensions = (".js", ".jsx", ".mjs", ".cjs")
    class_re = _CLASS
    func_res = _FUNCS
    import_res = _IMPORTS


class TypeScriptParser(RegexParser):
    language = "typescript"
    extensions = (".ts", ".tsx")
    class_re = _CLASS
    func_res = _FUNCS
    import_res = _IMPORTS
