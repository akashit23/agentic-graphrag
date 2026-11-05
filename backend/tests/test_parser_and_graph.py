from app.graph.graph_builder import GraphData, build_graph
from app.parsers import parse_file

JAVA = """package a;
import b.Student;
public class Svc extends Base {
    public void save(Student s) {
        db.insert(s);
        validate(s);
    }
}
"""


def test_java_parser_extracts_class_method_calls_imports():
    pf = parse_file("Svc.java", JAVA)
    assert [c.name for c in pf.classes] == ["Svc"] and pf.classes[0].bases == ["Base"]
    save = pf.functions[0]
    assert save.name == "save" and save.class_name == "Svc" and {"insert", "validate"} <= set(save.calls)
    assert "b.Student" in pf.imports


def test_python_parser():
    pf = parse_file("m.py", "import os\nclass A(B):\n    def f(self):\n        return g()\ndef g():\n    pass\n")
    assert pf.classes[0].bases == ["B"] and {f.name for f in pf.functions} == {"f", "g"}
    assert pf.functions[0].calls == ["g"]


def test_js_and_cpp_parsers():
    js = parse_file("a.js", "export class A {\n  run(x) {\n    foo(x);\n  }\n}\nfunction foo(x) {\n  return 1;\n}\n")
    assert {f.name for f in js.functions} == {"run", "foo"}
    cpp = parse_file("a.cpp", "#include \"b.h\"\nint Foo::get(int x) const {\n  return h(x);\n}\n")
    assert cpp.functions[0].class_name == "Foo" and cpp.imports == ["b.h"]


def test_unsupported_language_returns_none():
    assert parse_file("x.rb", "puts 1") is None


def test_graph_creation_and_dependencies(sample_dir):
    parsed, contents = [], {}
    for f in sample_dir.rglob("*.java"):
        rel = f.relative_to(sample_dir / "src").as_posix()
        contents[rel] = f.read_text()
        parsed.append(parse_file(rel, contents[rel]))
    g = build_graph("t", "Sample", parsed, contents)
    assert g["stats"]["files"] == 8 and g["stats"]["relationships"] > 20
    types = {e["type"] for e in g["edges"]}
    assert {"CONTAINS", "IMPORTS", "CALLS", "DEPENDS_ON", "USES"} <= types
    data = GraphData(g)
    assert "db/Database.java" in data.file_deps("services/StudentService.java")
    assert "services/StudentService.java" in data.impacted("db/Database.java")
