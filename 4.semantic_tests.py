from dataclasses import dataclass, field
from pathlib import Path
from typing import List
import importlib.util
import sys


def load_stage_module(module_name: str, filename: str):
    if module_name in sys.modules:
        return sys.modules[module_name]
    module_path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


make_token = load_stage_module("make_token", "1.lexer.py")
syntax = load_stage_module("syntax", "2.recursive_descent_parser.py")
semantic_analysis = load_stage_module("semantic_analysis", "3.semantic_analyzer.py")
Tokenizer = make_token.Tokenizer


@dataclass
class SemanticCase:
    name: str
    source: str
    expected_errors: List[str] = field(default_factory=list)


def parse_source(source: str) -> syntax.ProgramNode:
    tokens = Tokenizer(source).tokenize()
    syntax_tree, syntax_error = syntax.syntax_analysis(tokens)
    if syntax_error:
        raise AssertionError(f"Syntax error: {syntax_error}")
    return syntax_tree


def analyze_source(source: str) -> List[str]:
    syntax_tree = parse_source(source)
    _, errors = semantic_analysis.semantic_analysis(syntax_tree)
    return errors


def assert_expected_errors(case: SemanticCase, errors: List[str]) -> None:
    for expected in case.expected_errors:
        if not any(expected in error for error in errors):
            raise AssertionError(
                f"{case.name}: expected error containing {expected!r}, got {errors}"
            )

    if not case.expected_errors and errors:
        raise AssertionError(f"{case.name}: expected no semantic errors, got {errors}")


def run_semantic_case(case: SemanticCase) -> None:
    print(f"=== {case.name} ===")
    errors = analyze_source(case.source)

    for error in errors:
        print(error)

    assert_expected_errors(case, errors)
    print("PASS")


def run_all_cases(cases: List[SemanticCase]) -> None:
    for case in cases:
        run_semantic_case(case)


CASES = [
    SemanticCase(
        name="duplicate variable definition",
        source="""
program DuplicateExample
type t = integer;
var integer value;
    char value;
begin
    read(value)
end.
""",
        expected_errors=["duplicate definition 'value'"],
    ),
]


if __name__ == "__main__":
    run_all_cases(CASES)
