### 词法分析程序
# 输入： SNL源程序
# 输出：单词的内部表示序列--Token序列
# 程序设计步骤
# 1. 定义Token类，包含单词的类型、值、行号等信息
# 2. 定义Tokenizer类，包含词法分析的主要逻辑
# 3. 构造DFA；
# 4. 根据DFA生成单词识别函数

from enum import Enum, auto

class TokenType(Enum):
    ID               =    auto()     # 标识符
    IF               =    auto()     # 关键字 if
    ELSE             =    auto()     # 关键字 else    
    BEGIN            =    auto()     # 关键字 begin
    END              =    auto()     # 关键字 end
    RETURN           =    auto()     # 关键字 return
    REPEAT           =    auto()     # 关键字 repeat
    READ             =    auto()     # 关键字 read
    WRITE            =    auto()     # 关键字 write
    WHILE            =    auto()     # 关键字 while
    VAR              =    auto()     # 关键字 var
    ARRAY            =    auto()     # 关键字 array
    OF               =    auto()     # 关键字 of
    PROGRAM          =    auto()     # 关键字 program
    PROCEDURE        =    auto()     # 关键字 procedure
    INTEGER          =    auto()     # 关键字 integer
    CHAR             =    auto()     # 关键字 char
    INTC             =    auto()     # 无符号整数
    PLUS             =    auto()     # 单字符分节符 +
    MINUS            =    auto()     # 单字符分节符 -
    TIMES            =    auto()     # 单字符分节符 *
    DIV              =    auto()     # 单字符分节符 /
    EQ               =    auto()     # 单字符分节符 =
    LEFT_PAREN       =    auto()     # 单字符分节符 (
    RIGHT_PAREN      =    auto()     # 单字符分节符 )
    LEFT_SQUARE      =    auto()     # 单字符分节符 [
    RIGHT_SQUARE     =    auto()     # 单字符分节符 ]
    SEMICOLON        =    auto()     # 单字符分节符 ;
    DOT              =    auto()     # 单字符分节符 .
    LESS             =    auto()     # 单字符分节符 <
    EOF              =    auto()     # 单字符分节符 EOF
    BLANK            =    auto()     # 单字符分节符 空格
    ASSIGN           =    auto()     # 双字符分节符 :=
    COMMENT_BEGIN    =    auto()     # 注释开始符 {
    COMMENT_END      =    auto()     # 注释结束符 }
    IDENTIFYER       =    auto()     # 标识符 '
    ARRAY_LOWER      =    auto()     # 数组下界 ..
    COMMA            =    auto()     # 逗号 ,
    THEN             =    auto()     # 关键字 then
    FI               =    auto()     # 关键字 fi
    DO               =    auto()     # 关键字 do
    ENDWH            =    auto()     # 关键字 endwh
    TYPE             =    auto()     # 关键字 type
    ERROR            =    auto()     # 错误类型
    RECORD           =    auto()     # 关键字 record
    
class Token:
    def __init__(self, Lineshow, Lex, Sem):
        self.Lineshow = Lineshow  # 行号
        self.Lex = Lex  # 单词的词法信息
        self.Sem = Sem  # 单词的语义信息

# 定义DFA状态
class State(Enum):
    START = auto()         # 初始状态
    LETTER = auto()        # 字母（标识符/关键字）
    DIGIT = auto()         # 数字,只有无符号整数
    SINGLE = auto()        # 单分界符
    DOUBLE = auto()        # 双分界符
    ASSIGN = auto()        # 赋值符 :=
    COMMENT = auto()       # 注释开始状态
    COMMENT_END = auto()   # 注释结束状态
    DOT_OP = auto()        # 点号
    ARRAY_LOWER = auto()   # 数组下界 ..
    ARCH = auto()          # 字符串'
    ARCH_OVER = auto()     # 字符串结束'
    ERROR = auto()         # 错误状态
    END_STATE = auto()     # 结束状态

# 关键字表
KEYWORDS = {
    'if': TokenType.IF,
    'then': TokenType.THEN,
    'else':TokenType.ELSE,
    'fi':TokenType.FI,
    'begin': TokenType.BEGIN,
    'end': TokenType.END,
    'return': TokenType.RETURN,
    'repeat': TokenType.REPEAT,
    'read': TokenType.READ,
    'write': TokenType.WRITE,
    'while': TokenType.WHILE,
    'do':TokenType.DO,
    'endwh':TokenType.ENDWH,
    'var': TokenType.VAR,
    'array': TokenType.ARRAY,
    'of': TokenType.OF,
    'program': TokenType.PROGRAM,
    'procedure': TokenType.PROCEDURE,
    'integer': TokenType.INTEGER,
    'char': TokenType.CHAR,
    'type': TokenType.TYPE,
    'record': TokenType.RECORD
}

class Tokenizer:
    def __init__(self, source_code: str):
        self.source = source_code
        self.pos = 0
        self.line = 1
        
    # def skip_whitespace_and_comments(self):
    #     """跳过空格和注释"""
    #     while self.pos < len(self.source):
    #         char = self.source[self.pos]
            
    #         # 跳过空格和制表符
    #         if char in ' \t':
    #             self.pos += 1
    #             continue
            
    #         # 处理换行符
    #         if char == '\n':
    #             self.line += 1
    #             self.pos += 1
    #             continue
            
    #         # 处理注释
    #         if char == '{':
    #             self.pos += 1
    #             while self.pos < len(self.source) and self.source[self.pos] != '}':
    #                 if self.source[self.pos] == '\n':
    #                     self.line += 1
    #                 self.pos += 1
    #             if self.pos < len(self.source):
    #                 self.pos += 1  # 跳过 }
    #             continue
            
    #         break
  
    def tokenize(self):
        """主tokenize函数，使用DFA直接转向法"""
        tokens = []

        while self.pos < len(self.source):

            state = State.START
            lex_start = self.pos
            token = None

            while state != State.END_STATE :
                if self.pos >= len(self.source):
                    state = State.END_STATE
                    break

                current_char = self.source[self.pos]

                match state:
                    case State.START:
                        if current_char.isalpha():
                            state = State.LETTER
                            self.pos += 1
                        elif current_char.isdigit():
                            state = State.DIGIT
                            self.pos += 1
                        elif current_char == ':':
                            state = State.ASSIGN
                            self.pos += 1
                        elif current_char == '.':
                            state = State.DOT_OP
                            self.pos += 1
                        elif current_char == "'":
                            state = State.ARCH
                            self.pos += 1
                        elif current_char in '+-*/=();[]<':
                            state = State.SINGLE
                        elif current_char in ' \t\n':
                            state = State.START
                            self.line += 1 if current_char == '\n' else 0
                            self.pos += 1
                        elif current_char == '{':
                            state = State.COMMENT
                            self.pos += 1
                        else:
                            # 其他字符报错
                            state = State.ERROR

                    case State.LETTER:
                        lex_start = self.pos - 1
                        while self.pos < len(self.source) and self.source[self.pos].isalnum():
                            self.pos += 1
                        lex = self.source[lex_start:self.pos]
                        token_type = KEYWORDS.get(lex, TokenType.ID)
                        token = Token(self.line, lex, token_type)
                        state = State.END_STATE

                    case State.DIGIT:
                        while self.pos < len(self.source) and self.source[self.pos].isdigit():
                            self.pos += 1
                        lex = self.source[lex_start:self.pos]
                        token = Token(self.line, lex, TokenType.INTC)
                        state = State.END_STATE

                    case State.SINGLE:
                        ch = current_char
                        symbol_map = {
                            '+': TokenType.PLUS,
                            '-': TokenType.MINUS,
                            '*': TokenType.TIMES,
                            '/': TokenType.DIV,
                            '=': TokenType.EQ,
                            '(': TokenType.LEFT_PAREN,
                            ')': TokenType.RIGHT_PAREN,
                            '[': TokenType.LEFT_SQUARE,
                            ']': TokenType.RIGHT_SQUARE,
                            ';': TokenType.SEMICOLON,
                            '<': TokenType.LESS,
                        }
                        token_type = symbol_map.get(ch)
                        if token_type is not None:
                            token = Token(self.line, ch, token_type)
                        self.pos += 1
                        state = State.END_STATE

                    case State.ASSIGN:
                        if self.pos < len(self.source) and self.source[self.pos] == '=':
                            token = Token(self.line, ':=', TokenType.ASSIGN)
                            self.pos += 1
                        else:
                            # 单独的 ':' 未定义，直接忽略
                            token = None
                        state = State.END_STATE

                    case State.DOT_OP:
                        if self.pos < len(self.source) and self.source[self.pos] == '.':
                            self.pos += 1
                            token = Token(self.line, '..', TokenType.ARRAY_LOWER)
                        else:
                            token = Token(self.line, '.', TokenType.DOT)
                        state = State.END_STATE

                    case State.ARCH:
                        while self.pos < len(self.source) and self.source[self.pos] != "'":
                            if self.source[self.pos] == '\n':
                                self.line += 1
                            self.pos += 1
                        if self.pos < len(self.source) and self.source[self.pos] == "'":
                            self.pos += 1
                        lex = self.source[lex_start:self.pos]
                        token = Token(self.line, lex, TokenType.IDENTIFYER)
                        state = State.END_STATE

                    case State.COMMENT:
                        while self.pos < len(self.source) and self.source[self.pos] != '}':
                            if self.source[self.pos] == '\n':
                                self.line += 1
                            self.pos += 1
                        if self.pos < len(self.source) and self.source[self.pos] == '}':
                            self.pos += 1
                        state = State.END_STATE

                    case State.ERROR:
                        token = Token(self.line, current_char, TokenType.ERROR)
                        self.pos += 1
                        state = State.END_STATE

                    case State.END_STATE:
                        break

            if token is not None:
                tokens.append(token)

        tokens.append(Token(self.line, '', TokenType.EOF))
        return tokens
    
        
if __name__ == "__main__":
    source_code = """{我是一个注释}
    program _Example
    type t=integer;
    var t v1;
        char v2;
    begin
        read(v1);
        v1:=v1*10;
        v1="d";
        v2:='a';
        write(v1);
    end.
    """
    tokenizer = Tokenizer(source_code)
    tokens = tokenizer.tokenize()
    print("Tokens:")
    for token in tokens:
        print(f"Line {token.Lineshow}: {token.Lex} ({token.Sem})")