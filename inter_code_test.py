from lexer import Tokenizer
import recursive_descent_parser as parser
import semantic_analyzer as semantic
import inter_code


SOURCE = """
program InterCodeDemo
var integer x;
    integer y;
begin
    read(x);
    y := x + 2 * 3;
    if y < 10 then
        y := y + 1
    else
        y := y - 1
    fi;
    while y < 20 do
        y := y + 2
    endwh;
    write(y)
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

    quads, updated_symtab = inter_code.generate_intermediate_code(syntax_tree, symtab)

    print("Quadruples:")
    inter_code.print_quadruples(quads)

    print("\nSymbol table after intermediate code generation:")
    updated_symtab.print_table()


if __name__ == "__main__":
    main()
