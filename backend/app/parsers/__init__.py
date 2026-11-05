"""Parser registry. To add a language: create a parser class and add it to PARSERS."""
import os

from .base import BaseParser, ParsedFile
from .cpp_parser import CParser, CppParser
from .java_parser import JavaParser
from .javascript_parser import JavaScriptParser, TypeScriptParser
from .python_parser import PythonParser

PARSERS: list[BaseParser] = [PythonParser(), JavaParser(), JavaScriptParser(), TypeScriptParser(), CppParser(), CParser()]
LANG_BY_EXT: dict[str, str] = {ext: p.language for p in PARSERS for ext in p.extensions}
_BY_EXT: dict[str, BaseParser] = {ext: p for p in PARSERS for ext in p.extensions}


def parse_file(path: str, source: str) -> ParsedFile | None:
    parser = _BY_EXT.get(os.path.splitext(path)[1].lower())
    return parser.parse(path, source) if parser else None


__all__ = ["parse_file", "LANG_BY_EXT", "ParsedFile"]
