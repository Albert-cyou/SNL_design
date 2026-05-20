from lexer import Tokenizer
import recursive_descent_parser as parser
import semantic_analyzer as semantic


SOURCE = """
program SymbolTableDemo
type t = integer;
var t x;
    char y;
procedure add(integer a; var integer b);
var integer temp;
begin
    temp := a;
    b := temp
end
begin
    read(x);
    x := x
end.
"""


def main():
    tokens = Tokenizer(SOURCE).tokenize()
    syntax_tree, syntax_error = parser.syntax_analysis(tokens)
    if syntax_error:
        print("Syntax error:", syntax_error)
        return

    symtab, semantic_errors = semantic.semantic_analysis(syntax_tree)
    if semantic_errors:
        print("Semantic errors:")
        for error in semantic_errors:
            print(error)
        return

    symtab.print_table()


if __name__ == "__main__":
    main()
