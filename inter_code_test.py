from lexer import Tokenizer
import recursive_descent_parser as parser
import semantic_analyzer as semantic
import inter_code
import inter_code_optimizer


SOURCE = """
program InterCodeDemo
var integer a;
    integer b;
    integer x;
    integer y;
    integer i;
begin
    read(a);
    read(b);
    y := 2 * 3;
    x := a + b;
    y := a + b;
    while i < 10 do
        x := a + b;
        i := i + 1
    endwh;
    write(x)
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
    optimized_quads = inter_code_optimizer.optimize_quadruples(quads)

    print("Quadruples before optimization:")
    inter_code.print_quadruples(quads)

    print("\nQuadruples after optimization:")
    inter_code.print_quadruples(optimized_quads)

    print("\nSymbol table after intermediate code generation:")
    updated_symtab.print_table()


if __name__ == "__main__":
    main()
