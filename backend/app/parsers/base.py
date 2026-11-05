"""Parser base classes. Add a new language by subclassing RegexParser (or BaseParser)
and registering it in parsers/__init__.py."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

KEYWORDS = {
    "if", "for", "while", "switch", "catch", "return", "new", "sizeof", "else", "do", "try", "throw",
    "super", "this", "elif", "def", "class", "synchronized", "assert", "typeof", "function", "delete",
    "await", "async", "yield", "with", "lambda", "print", "len", "range", "str", "int", "float", "list",
    "dict", "set", "tuple", "isinstance", "enumerate", "open", "sorted", "min", "max", "sum", "any",
    "all", "map", "filter", "zip", "bool", "require", "import", "from", "case", "defined",
}
CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")


@dataclass
class Symbol:
    name: str
    kind: str  # "class" | "function"
    start_line: int  # 1-based
    end_line: int
    class_name: str = ""
    bases: list[str] = field(default_factory=list)
    interfaces: list[str] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)


@dataclass
class ParsedFile:
    path: str
    language: str
    line_count: int
    classes: list[Symbol] = field(default_factory=list)
    functions: list[Symbol] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    error: str = ""


def extract_calls(body_lines: list[str], own_name: str) -> list[str]:
    seen: dict[str, None] = {}
    for line in body_lines:
        line = line.split("//")[0]
        for name in CALL_RE.findall(line):
            if name not in KEYWORDS and name != own_name:
                seen[name] = None
    return list(seen)


def find_block_end(lines: list[str], start: int) -> int:
    """Return the 0-based index of the line closing the brace block opened at/after `start`."""
    depth, opened = 0, False
    for j in range(start, min(len(lines), start + 3000)):
        for ch in lines[j]:
            if ch == "{":
                depth, opened = depth + 1, True
            elif ch == "}":
                depth -= 1
        if opened and depth <= 0:
            return j
        if not opened and j >= start + 2:
            return start
    return min(len(lines) - 1, start)


class BaseParser(ABC):
    language: str = ""
    extensions: tuple[str, ...] = ()

    @abstractmethod
    def parse(self, path: str, source: str) -> ParsedFile: ...


class RegexParser(BaseParser):
    """Brace-language parser driven by regular expressions (fast, dependency free)."""

    class_re: re.Pattern | None = None  # groups: 1=name, 2=extends (opt), 3=implements (opt)
    func_res: list = []  # (regex, requires opening brace)
    import_res: list = []

    def parse(self, path: str, source: str) -> ParsedFile:
        lines = source.splitlines()
        pf = ParsedFile(path=path, language=self.language, line_count=len(lines))
        try:
            for rx in self.import_res:
                for m in rx.finditer(source):
                    pf.imports.append(m.group(1))
            pf.imports = list(dict.fromkeys(pf.imports))
            for i, line in enumerate(lines):
                s = line.strip()
                if not s or s.startswith(("//", "*", "/*", "#")):
                    continue
                cm = self.class_re.match(line) if self.class_re else None
                if cm:
                    end = find_block_end(lines, i)
                    sym = Symbol(cm.group(1), "class", i + 1, end + 1)
                    if cm.lastindex and cm.lastindex >= 2 and cm.group(2):
                        sym.bases = [cm.group(2).split(".")[-1]]
                    if cm.lastindex and cm.lastindex >= 3 and cm.group(3):
                        sym.interfaces = [x.strip() for x in cm.group(3).split(",") if x.strip()]
                    pf.classes.append(sym)
                    continue
                for rx, needs_brace in self.func_res:
                    m = rx.match(line)
                    if not m:
                        continue
                    name = m.group(1)
                    if name.split("::")[-1] in KEYWORDS:
                        continue
                    rs = line.rstrip()
                    nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    if needs_brace and not (rs.endswith("{") or (rs.endswith(")") and nxt == "{")):
                        continue
                    end = find_block_end(lines, i) if ("{" in line or nxt == "{") else i
                    cls = ""
                    if "::" in name:
                        cls, name = name.rsplit("::", 1)
                        cls = cls.split("::")[-1]
                    pf.functions.append(Symbol(name, "function", i + 1, end + 1, class_name=cls))
                    break
            self._finalize(pf, lines)
        except Exception as exc:  # parsing must never crash indexing
            pf.error = str(exc)
        return pf

    @staticmethod
    def _finalize(pf: ParsedFile, lines: list[str]) -> None:
        funcs = sorted(pf.functions, key=lambda f: (f.start_line, -f.end_line))
        kept: list[Symbol] = []
        for f in funcs:  # drop functions nested inside other functions (callbacks, anonymous classes)
            if any(o.start_line <= f.start_line and f.end_line <= o.end_line for o in kept):
                continue
            kept.append(f)
        for f in kept:
            if not f.class_name:
                owners = [c for c in pf.classes if c.start_line <= f.start_line and f.end_line <= c.end_line]
                if owners:
                    f.class_name = min(owners, key=lambda c: c.end_line - c.start_line).name
            f.calls = extract_calls(lines[f.start_line:f.end_line], f.name)
        pf.functions = kept
