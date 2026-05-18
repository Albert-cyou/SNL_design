from make_token import Tokenizer
import LL1_syntax

s = '''{注释}
program Example
var t v1;
begin
 read(v1);
 v1:=v1*10;
 write(v1)
end.
'''

tokenizer = Tokenizer(s)
tokens = tokenizer.tokenize()
root, err = LL1_syntax.Program(tokens)
if err:
    print('Error:', err)
else:
    print('AST from LL1:')
    root.print()
