from lexer import Tokenizer
import ll1_parser

s = """
program p
type t = integer;
var t x;
    char y;
procedure add(integer a; var integer b);
var integer temp;
begin
    temp := a;
    b := temp
end
begin    read(x);
    x := x
end.

"""
tokens = Tokenizer(s).tokenize()
parser = ll1_parser.LL1Parser()
root, err = parser.parse(tokens)
print('err=', err)
print(root)
