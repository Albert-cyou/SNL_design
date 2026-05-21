from make_token import Tokenizer
import LL1_syntax

s = '{注释}\nprogram Example\ntype t = integer;\nvar v1 : t;\nbegin\n write(v1)\nend.\n'
tokens = Tokenizer(s).tokenize()
parser = LL1_syntax.LL1Parser()
root, err = parser.parse(tokens)
print('err=', err)
print(root)
