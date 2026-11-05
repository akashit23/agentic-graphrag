import re

from .base import RegexParser

_CLASS = re.compile(r"^\s*(?:class|struct)\s+(\w+)(?:\s*:\s*(?:public|private|protected)?\s*(\w+))?\s*\{?\s*$")
_FUNCS = [
    (re.compile(r"^\s*(?:[\w:<>*&~]+\s+)+[*&]*\s*([\w:~]+)\s*\(.*\)\s*(?:const)?\s*(?:noexcept)?\s*(?:override)?\s*\{?\s*$"), True),
    (re.compile(r"^\s*([A-Za-z_]\w*::~?\w+)\s*\(.*\)\s*(?:const)?\s*\{?\s*$"), True),
]
_INCLUDE = [re.compile(r'^\s*#\s*include\s*["<]([^">]+)[">]', re.M)]


class CppParser(RegexParser):
    language = "cpp"
    extensions = (".cpp", ".cc", ".cxx", ".hpp", ".hh", ".h")
    class_re = _CLASS
    func_res = _FUNCS
    import_res = _INCLUDE


class CParser(RegexParser):
    language = "c"
    extensions = (".c",)
    class_re = None
    func_res = _FUNCS[:1]
    import_res = _INCLUDE
