from dataclasses import dataclass, field
from typing import List
import importlib


make_token = importlib.import_module("1_lexer")
syntax = importlib.import_module("2_recursive_descent_parser")
semantic_analysis = importlib.import_module("3_semantic_analyzer")
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
