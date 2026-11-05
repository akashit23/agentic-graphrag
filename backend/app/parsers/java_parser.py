import re

from .base import RegexParser

_MODS = r"(?:(?:public|private|protected|static|final|abstract|synchronized|native|default)\s+)*"


class JavaParser(RegexParser):
    language = "java"
    extensions = (".java",)
    class_re = re.compile(
        r"^\s*(?:@\w+\s+)*(?:(?:public|private|protected|static|final|abstract)\s+)*(?:class|interface|enum)\s+(\w+)"
        r"(?:<[^>]*>)?(?:\s+extends\s+([\w.<>]+))?(?:\s+implements\s+([\w.,<> ]+?))?\s*\{?\s*$")
    func_res = [(re.compile(r"^\s*(?:@\w+\s+)*" + _MODS +
                            r"(?:<[^>]+>\s+)?[\w<>\[\],.?]+\s+(\w+)\s*\(.*\)\s*(?:throws\s+[\w., ]+)?\s*\{?\s*$"), True)]
    import_res = [re.compile(r"^\s*import\s+(?:static\s+)?([\w.]+)", re.M)]
