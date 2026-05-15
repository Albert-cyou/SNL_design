# 输入：Token序列
# 输出：语法错误检查信息和语法树
# 方法：递归下降法

from enum import Enum,auto
from make_token import TokenType, Token, Tokenizer

class NodeKind(Enum):
    ProK      =   auto()  # 根节点
    PheadK    =   auto()  # 程序头节点
    TypeK     =   auto()  # 类型声明节点
    VarK      =   auto()  # 变量节点
    ProcDecK  =   auto()  # 过程声明节点
    StmLK     =   auto()  # 程序体节点
    DecK      =   auto()  # 声明节点
    StmtK     =   auto()  # 语句节点
    ExpK      =   auto()  # 表达式节点

class NodeType(Enum):
    # nodekind=DecK
    ArrayK   =   auto()  # 数组类型
    CharK    =   auto()  # 字符类型
    IntegerK =   auto()  # 整数类型
    RecordK  =   auto()  # 记录类型
    IdK      =   auto()  # 标识符
    # nodekind=StmtK
    IfK      =   auto()  # if语句
    ThenK    =   auto()  # then语句
    ElseK    =   auto()  # else语句
    WhileK   =   auto()  # while语句
    AssignK  =   auto()  # 赋值语句
    ReturnK  =   auto()  # return语句
    ReadK    =   auto()  # read语句
    WriteK   =   auto()  # write语句
    CallK    =   auto()  # 过程调用语句
    # nodekind=ExpK
    OpK      =   auto()  # 运算符
    ConstK   =   auto()  # 常量
    ExpIdK   =   auto()  # 标识符

class ValParamType(Enum):
    valparamtype = auto()   # 值参数
    varparamtype = auto()   # 变参数

class ExpAttropType(Enum):
    LT = auto()    # 整数类型
    EQ = auto()    # 等于运算符
    GT = auto()    # 大于运算符
    LE = auto()    # 小于等于运算符
    GE = auto()    # 大于等于运算符
    NE = auto()    # 不等于运算符
    PLUS = auto()  # 加法运算符
    MINUS = auto() # 减法运算符
    TIMES = auto() # 乘法运算符
    OVER = auto()  # 除法运算符

class ExpAttrvarkindType(Enum):
    IdV = auto()       # 标识符
    ArrayMemV = auto() # 数组元素
    FieldV = auto()    # 记录域

class ExpType(Enum):
    Void = auto()      # 无类型
    Integer = auto()   # 整数类型
    Boolean = auto()   # 布尔类型 

# 语法树节点类
class SyntaxTreeNode:
    def __init__(self, nodekind=None, kind=None):
        self.children = [] # 孩子节点列表
        self.sibling = []  # 兄弟节点列表
        self.lineno = 0    # 行号
        self.nodekind = nodekind # 节点类型，取值维NodeKind枚举类
        self.kind = kind     # 具体类型，取值维NodeType枚举类
        self.idnum = 0    # 标识符的个数
        self.name = ""     # 标识符的名字
        self.table = []    # 符号表指针
        self.type_name = ""  # 类型名字 当前节点是声明类型，且类型是类型标识符的时候有效
        self.attr = {
            "ArrayAttr":{
                "low":0,    # 数组下界
                "up":0,     # 数组上界
                "childType": None   # 数组元素类型,在TokenType枚举类中取值
            },
            "procAttr":{
                "paramt": None # 过程参数列表，元素类型为枚举类型valparamtype或者varparamtype表示值参还是变参
            },
            "ExpAttr":{
                "op": None,  # 运算符，TokenType枚举类中取值;
                             # 如果是关系运算，为LT,EQ;加减为PLUS,MINUS;乘除为TIMES,OVER
                "val": 0,  # 常量值，整数类型
                "varkind": None, # 变量类型，取值为枚举类型IdV,ArrayMemV,FieldV表示标识符、数组元素、记录域
                "type": None  # 表达式类型，取值Void,Integer,Boolean为类型检查ExpType类型。
            }
        }  

    def _get_node_label(self):
        """
        内部工具：生成当前节点应该显示的文本
        """
        # 这些类型只显示【声明节点】
        special_kinds = {NodeKind.ProK, NodeKind.PheadK, NodeKind.TypeK, NodeKind.VarK, NodeKind.ProcDecK, NodeKind.StmLK}
        
        if self.nodekind in special_kinds:
            return f"【{self.nodekind} 声明节点】"

        # 其他节点：优先显示 name / 值 / 类型
        if self.name:
            return self.name
        if self.attr["ExpAttr"]["val"] != 0:
            return str(self.attr["ExpAttr"]["val"])
        if self.kind:
            return str(self.kind)
        if self.nodekind:
            return str(self.nodekind)
        
        return "空节点"

    def _print_tree(self, node, level=0, prefix="", is_last_child=False):
        """
        递归打印排版：
        - 每一行一层
        - 父子用 | 连接
        - 兄弟用 --- 连接
        """
        if not node:
            return

        # 生成当前行的显示内容
        label = node._get_node_label()
        children = node.children

        # 构建前缀（缩进 + 连接线）
        line_prefix = prefix + ("└── " if is_last_child else "├── ")
        # 真正打印当前节点
        print(f"{line_prefix}{label}")

        # 递归打印孩子
        for i, child in enumerate(children):
            is_last = (i == len(children) - 1)
            # 给下一层准备缩进前缀
            new_prefix = prefix + ("    " if is_last_child else "│   ")
            self._print_tree(child, level + 1, new_prefix, is_last)

    def print(self):
        """对外打印接口"""
        print("=" * 50)
        print("语法树可视化结构")
        print("=" * 50)
        self._print_tree(self, level=0, prefix="", is_last_child=True)
        print("=" * 50)
    
# 下面都是递归下降法语法分析函数
def Match(expected_token, tokens, current_token):
    if current_token < len(tokens) and tokens[current_token].Sem == expected_token:
        return True, current_token + 1
    else:
        return False, current_token

def Program(tokens):
    current_token = 0
    PheadK, error, current_token = ProgramHead(tokens, current_token)
    if error:
        return None, error
    TypeK, error, current_token = DeclarePart(tokens, current_token)
    if error:
        return None, error
    stmLK, error, current_token = ProgramBody(tokens, current_token)
    if error:
        return None, error
    root = SyntaxTreeNode(nodekind=NodeKind.ProK) # 构造根节点
    root.children.append(PheadK) # 将程序头节点作为根节点的第一个孩子
    root.children.append(TypeK)  # 将类型声明节点作为根节点的第二个孩子
    root.children.append(stmLK)  # 将程序体节点作为根节点的第三个孩子
    return root, None # 返回根节点和语法错误检查信息

def ProgramHead(tokens, current_token):
    # 程序头就不生成节点了，直接检查语法正确性
    matched, current_token = Match(TokenType.PROGRAM, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'program' keyword", current_token
    name, error, current_token = ProgramName(tokens, current_token)
    if error:
        return None, error, current_token
    # 构造节点
    root = SyntaxTreeNode(nodekind=NodeKind.PheadK) # 构造程序头节点
    root.children.append(name) # 将程序名字节点作为程序头节点的第一个孩子
    return root, None, current_token # 返回程序头节点和语法错误检查信息

def ProgramName(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected identifier after 'program' keyword", current_token
    name = tokens[current_token-1].Sem # 获取标识符名字
    # 构造节点
    root = SyntaxTreeNode(nodekind=NodeKind.TypeK, kind=NodeType.IdK) # 构造程序名字节点
    root.lineno = tokens[current_token-1].Lineshow # 将行号保存在节点属性中
    root.name = name # 将标识符名字保存在节点属性中
    return root, None, current_token # 返回程序名字节点和语法错误检查信息

def DeclarePart(tokens, current_token):
    TypeK, error, current_token = TypeDecpart(tokens, current_token)
    if error:
        return None, error, current_token
    VarK, error, current_token = VarDecpart(tokens, current_token)
    if error:
        return None, error, current_token
    ProcK, error, current_token = ProcDecpart(tokens, current_token)
    if error:
        return None, error, current_token
    root = SyntaxTreeNode(nodekind=NodeKind.DecK)
    if TypeK:
        root.children.append(TypeK)
    if VarK:
        root.children.append(VarK)
    if ProcK:
        root.children.append(ProcK)
    return root, None, current_token

def TypeDecpart(tokens, current_token):
    if tokens[current_token].Sem in [TokenType.BEGIN, TokenType.PROCEDURE, TokenType.VAR]:
        return None, None, current_token  # ε
    elif tokens[current_token].Sem == TokenType.TYPE:
        return TypeDec(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected type declaration or begin/procedure/var", current_token

def TypeDec(tokens, current_token):
    matched, current_token = Match(TokenType.TYPE, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'type' keyword", current_token
    TypeDecListK, error, current_token = TypeDecList(tokens, current_token)
    if error:
        return None, error, current_token
    root = SyntaxTreeNode(nodekind=NodeKind.TypeK)
    root.children.append(TypeDecListK)
    return root, None, current_token

def TypeDecList(tokens, current_token):
    TypeIdK, error, current_token = TypeId(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.EQ, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected '='", current_token
    TypeDefK, error, current_token = TypeDef(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.SEMICOLON, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ';'", current_token
    TypeDecMoreK, error, current_token = TypeDecMore(tokens, current_token)
    if error:
        return None, error, current_token
    root = SyntaxTreeNode(nodekind=NodeKind.TypeK)
    root.children.append(TypeIdK)
    root.children.append(TypeDefK)
    if TypeDecMoreK:
        root.children.append(TypeDecMoreK)
    return root, None, current_token

def TypeDecMore(tokens, current_token):
    if tokens[current_token].Sem in [TokenType.BEGIN, TokenType.PROCEDURE, TokenType.VAR]:
        return None, None, current_token  # ε
    elif tokens[current_token].Sem == TokenType.ID:
        return TypeDecList(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected type declaration more", current_token

def TypeId(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected identifier", current_token
    root = SyntaxTreeNode(nodekind=NodeKind.DecK, kind=NodeType.IdK)
    root.name = tokens[current_token-1].Lex
    root.lineno = tokens[current_token-1].Lineshow
    return root, None, current_token

def TypeDef(tokens, current_token):
    if tokens[current_token].Sem in [TokenType.CHAR, TokenType.INTEGER]:
        return BaseType(tokens, current_token)
    elif tokens[current_token].Sem in [TokenType.ARRAY, TokenType.RECORD]:
        return StructureType(tokens, current_token)
    elif tokens[current_token].Sem == TokenType.ID:
        return TypeId(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected type definition", current_token

def BaseType(tokens, current_token):
    if tokens[current_token].Sem == TokenType.INTEGER:
        matched, current_token = Match(TokenType.INTEGER, tokens, current_token)
        root = SyntaxTreeNode(nodekind=NodeKind.DecK, kind=NodeType.IntegerK)
        return root, None, current_token
    elif tokens[current_token].Sem == TokenType.CHAR:
        matched, current_token = Match(TokenType.CHAR, tokens, current_token)
        root = SyntaxTreeNode(nodekind=NodeKind.DecK, kind=NodeType.CharK)
        return root, None, current_token
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected base type", current_token

def StructureType(tokens, current_token):
    if tokens[current_token].Sem == TokenType.ARRAY:
        return ArrayType(tokens, current_token)
    elif tokens[current_token].Sem == TokenType.RECORD:
        return RecType(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected structure type", current_token

def ArrayType(tokens, current_token):
    matched, current_token = Match(TokenType.ARRAY, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'array'", current_token
    matched, current_token = Match(TokenType.LEFT_SQUARE, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected '['", current_token
    LowK, error, current_token = Low(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.ARRAY_LOWER, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected '..'", current_token
    TopK, error, current_token = Top(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.RIGHT_SQUARE, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ']'", current_token
    matched, current_token = Match(TokenType.OF, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'of'", current_token
    BaseTypeK, error, current_token = BaseType(tokens, current_token)
    if error:
        return None, error, current_token
    root = SyntaxTreeNode(nodekind=NodeKind.DecK, kind=NodeType.ArrayK)
    root.attr["ArrayAttr"]["low"] = LowK.attr["ExpAttr"]["val"]
    root.attr["ArrayAttr"]["up"] = TopK.attr["ExpAttr"]["val"]
    root.attr["ArrayAttr"]["childType"] = BaseTypeK.kind
    return root, None, current_token

def Low(tokens, current_token):
    matched, current_token = Match(TokenType.INTC, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected integer constant", current_token
    root = SyntaxTreeNode(nodekind=NodeKind.ExpK, kind=NodeType.ConstK)
    root.attr["ExpAttr"]["val"] = int(tokens[current_token-1].Sem)
    return root, None, current_token

def Top(tokens, current_token):
    return Low(tokens, current_token)  # Same as Low

def RecType(tokens, current_token):
    matched, current_token = Match(TokenType.RECORD, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'record'", current_token
    FieldDecListK, error, current_token = FieldDecList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.END, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'end'", current_token
    root = SyntaxTreeNode(nodekind=NodeKind.DecK, kind=NodeType.RecordK)
    root.children.append(FieldDecListK)
    return root, None, current_token

def FieldDecList(tokens, current_token):
    if tokens[current_token].Sem in [TokenType.CHAR, TokenType.INTEGER]:
        TypeK, error, current_token = BaseType(tokens, current_token)
    elif tokens[current_token].Sem == TokenType.ARRAY:
        TypeK, error, current_token = ArrayType(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected base type or array", current_token
    if error:
        return None, error, current_token
    IdListK, error, current_token = IdList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.SEMICOLON, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ';'", current_token
    FieldDecMoreK, error, current_token = FieldDecMore(tokens, current_token)
    if error:
        return None, error, current_token
    root = SyntaxTreeNode(nodekind=NodeKind.DecK)
    root.children.append(TypeK)
    root.children.append(IdListK)
    if FieldDecMoreK:
        root.children.append(FieldDecMoreK)
    return root, None, current_token

def FieldDecMore(tokens, current_token):
    if tokens[current_token].Sem == TokenType.END:
        return None, None, current_token  # ε
    elif tokens[current_token].Sem in [TokenType.ARRAY, TokenType.CHAR, TokenType.INTEGER]:
        return FieldDecList(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected field declaration more", current_token

def IdList(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected identifier", current_token
    root = SyntaxTreeNode(nodekind=NodeKind.DecK, kind=NodeType.IdK)
    root.name = tokens[current_token-1].Sem
    root.lineno = tokens[current_token-1].Lineshow
    IdMoreK, error, current_token = IdMore(tokens, current_token)
    if error:
        return None, error, current_token
    if IdMoreK:
        root.children.append(IdMoreK)
    return root, None, current_token

def IdMore(tokens, current_token):
    if tokens[current_token].Sem == TokenType.SEMICOLON:
        return None, None, current_token  # ε
    # Note: Assuming COMMA is TokenType.COMMA, but it's not in token.py. Need to add it.
    # For now, assume it's added.
    elif tokens[current_token].Sem == TokenType.COMMA:
        matched, current_token = Match(TokenType.COMMA, tokens, current_token)
        return IdList(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ';' or ','", current_token

# Continuing with VarDecpart etc.

def VarDecpart(tokens, current_token):
    if tokens[current_token].Sem == TokenType.BEGIN or tokens[current_token].Sem == TokenType.PROCEDURE:
        return None, None, current_token  # ε
    elif tokens[current_token].Sem == TokenType.VAR:
        return VarDec(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected var declaration or begin/procedure", current_token

def VarDec(tokens, current_token):
    matched, current_token = Match(TokenType.VAR, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'var'", current_token
    VarDecListK, error, current_token = VarDecList(tokens, current_token)
    if error:
        return None, error, current_token
    root = SyntaxTreeNode(nodekind=NodeKind.VarK)
    root.children.append(VarDecListK)
    return root, None, current_token

def VarDecList(tokens, current_token):
    TypeDefK, error, current_token = TypeDef(tokens, current_token)
    if error:
        return None, error, current_token
    VarIdListK, error, current_token = VarIdList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.SEMICOLON, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ';'", current_token
    VarDecMoreK, error, current_token = VarDecMore(tokens, current_token)
    if error:
        return None, error, current_token
    root = SyntaxTreeNode(nodekind=NodeKind.VarK)
    root.children.append(TypeDefK)
    root.children.append(VarIdListK)
    if VarDecMoreK:
        root.children.append(VarDecMoreK)
    return root, None, current_token

def VarDecMore(tokens, current_token):
    if tokens[current_token].Sem == TokenType.BEGIN or tokens[current_token].Sem == TokenType.PROCEDURE:
        return None, None, current_token  # ε
    elif tokens[current_token].Sem in [TokenType.ARRAY, TokenType.CHAR, TokenType.ID, TokenType.INTEGER, TokenType.RECORD]:
        return VarDecList(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected var declaration more", current_token

def VarIdList(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected identifier", current_token
    root = SyntaxTreeNode(nodekind=NodeKind.DecK, kind=NodeType.IdK)
    root.name = tokens[current_token-1].Sem
    root.lineno = tokens[current_token-1].Lineshow
    VarIdMoreK, error, current_token = VarIdMore(tokens, current_token)
    if error:
        return None, error, current_token
    if VarIdMoreK:
        root.children.append(VarIdMoreK)
    return root, None, current_token

def VarIdMore(tokens, current_token):
    if tokens[current_token].Sem == TokenType.SEMICOLON:
        return None, None, current_token  # ε
    elif tokens[current_token].Sem == TokenType.COMMA:
        matched, current_token = Match(TokenType.COMMA, tokens, current_token)
        return VarIdList(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ';' or ','", current_token

def ProcDecpart(tokens, current_token):
    if tokens[current_token].Sem == TokenType.BEGIN:
        return None, None, current_token  # ε
    elif tokens[current_token].Sem == TokenType.PROCEDURE:
        return ProcDec(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected procedure declaration or begin", current_token

def ProcDec(tokens, current_token):
    matched, current_token = Match(TokenType.PROCEDURE, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'procedure'", current_token
    ProcNameK, error, current_token = ProcName(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.LEFT_PAREN, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected '('", current_token
    ParamListK, error, current_token = ParamList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.RIGHT_PAREN, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ')'", current_token
    matched, current_token = Match(TokenType.SEMICOLON, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ';'", current_token
    ProcDecPartK, error, current_token = ProcDecPart(tokens, current_token)
    if error:
        return None, error, current_token
    ProcBodyK, error, current_token = ProcBody(tokens, current_token)
    if error:
        return None, error, current_token
    ProcDecMoreK, error, current_token = ProcDecMore(tokens, current_token)
    if error:
        return None, error, current_token
    root = SyntaxTreeNode(nodekind=NodeKind.ProcDecK)
    root.children.append(ProcNameK)
    if ParamListK:
        root.children.append(ParamListK)
    root.children.append(ProcDecPartK)
    root.children.append(ProcBodyK)
    if ProcDecMoreK:
        root.children.append(ProcDecMoreK)
    return root, None, current_token

def ProcDecMore(tokens, current_token):
    if tokens[current_token].Sem == TokenType.BEGIN:
        return None, None, current_token  # ε
    elif tokens[current_token].Sem == TokenType.PROCEDURE:
        return ProcDec(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected procedure declaration more", current_token

def ProcName(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected identifier", current_token
    root = SyntaxTreeNode(nodekind=NodeKind.DecK, kind=NodeType.IdK)
    root.name = tokens[current_token-1].Sem
    root.lineno = tokens[current_token-1].Lineshow
    return root, None, current_token

def ParamList(tokens, current_token):
    if tokens[current_token].Sem == TokenType.RIGHT_PAREN:
        return None, None, current_token  # ε
    else:
        return ParamDecList(tokens, current_token)

def ParamDecList(tokens, current_token):
    ParamK, error, current_token = Param(tokens, current_token)
    if error:
        return None, error, current_token
    ParamMoreK, error, current_token = ParamMore(tokens, current_token)
    if error:
        return None, error, current_token
    root = SyntaxTreeNode(nodekind=NodeKind.DecK)
    root.children.append(ParamK)
    if ParamMoreK:
        root.children.append(ParamMoreK)
    return root, None, current_token

def ParamMore(tokens, current_token):
    if tokens[current_token].Sem == TokenType.RIGHT_PAREN:
        return None, None, current_token  # ε
    elif tokens[current_token].Sem == TokenType.SEMICOLON:
        matched, current_token = Match(TokenType.SEMICOLON, tokens, current_token)
        return ParamDecList(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ')' or ';'", current_token

def Param(tokens, current_token):
    if tokens[current_token].Sem == TokenType.VAR:
        matched, current_token = Match(TokenType.VAR, tokens, current_token)
        TypeDefK, error, current_token = TypeDef(tokens, current_token)
        if error:
            return None, error, current_token
        FormListK, error, current_token = FormList(tokens, current_token)
        if error:
            return None, error, current_token
        root = SyntaxTreeNode(nodekind=NodeKind.DecK)
        root.attr["procAttr"]["paramt"] = ValParamType.varparamtype
        root.children.append(TypeDefK)
        root.children.append(FormListK)
        return root, None, current_token
    else:
        TypeDefK, error, current_token = TypeDef(tokens, current_token)
        if error:
            return None, error, current_token
        FormListK, error, current_token = FormList(tokens, current_token)
        if error:
            return None, error, current_token
        root = SyntaxTreeNode(nodekind=NodeKind.DecK)
        root.attr["procAttr"]["paramt"] = ValParamType.valparamtype
        root.children.append(TypeDefK)
        root.children.append(FormListK)
        return root, None, current_token

def FormList(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected identifier", current_token
    root = SyntaxTreeNode(nodekind=NodeKind.DecK, kind=NodeType.IdK)
    root.name = tokens[current_token-1].Sem
    root.lineno = tokens[current_token-1].Lineshow
    FidMoreK, error, current_token = FidMore(tokens, current_token)
    if error:
        return None, error, current_token
    if FidMoreK:
        root.children.append(FidMoreK)
    return root, None, current_token

def FidMore(tokens, current_token):
    if tokens[current_token].Sem in [TokenType.RIGHT_PAREN, TokenType.SEMICOLON]:
        return None, None, current_token  # ε
    elif tokens[current_token].Sem == TokenType.COMMA:
        matched, current_token = Match(TokenType.COMMA, tokens, current_token)
        return FormList(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ')', ';', or ','", current_token

def ProcDecPart(tokens, current_token):
    return DeclarePart(tokens, current_token)

def ProcBody(tokens, current_token):
    return ProgramBody(tokens, current_token)

def ProgramBody(tokens, current_token):
    matched, current_token = Match(TokenType.BEGIN, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'begin'", current_token
    StmListK, error, current_token = StmList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.END, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'end'", current_token
    root = SyntaxTreeNode(nodekind=NodeKind.StmLK)
    root.children.append(StmListK)
    return root, None, current_token

def StmList(tokens, current_token):
    StmK, error, current_token = Stm(tokens, current_token)
    if error:
        return None, error, current_token
    StmMoreK, error, current_token = StmMore(tokens, current_token)
    if error:
        return None, error, current_token
    root = SyntaxTreeNode(nodekind=NodeKind.StmLK)
    root.children.append(StmK)
    if StmMoreK:
        root.children.append(StmMoreK)
    return root, None, current_token

def StmMore(tokens, current_token):
    if tokens[current_token].Sem in [TokenType.ELSE, TokenType.END, TokenType.ENDWH, TokenType.FI]:
        return None, None, current_token  # ε
    elif tokens[current_token].Sem == TokenType.SEMICOLON:
        matched, current_token = Match(TokenType.SEMICOLON, tokens, current_token)
        return StmList(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected statement more", current_token

def Stm(tokens, current_token):
    if tokens[current_token].Sem == TokenType.IF:
        return ConditionalStm(tokens, current_token)
    elif tokens[current_token].Sem == TokenType.WHILE:
        return LoopStm(tokens, current_token)
    elif tokens[current_token].Sem == TokenType.READ:
        return InputStm(tokens, current_token)
    elif tokens[current_token].Sem == TokenType.WRITE:
        return OutputStm(tokens, current_token)
    elif tokens[current_token].Sem == TokenType.RETURN:
        return ReturnStm(tokens, current_token)
    elif tokens[current_token].Sem == TokenType.ID:
        return AssCall(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected statement", current_token

def ConditionalStm(tokens, current_token):
    matched, current_token = Match(TokenType.IF, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'if'", current_token
    RelExpK, error, current_token = RelExp(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.THEN, tokens, current_token)  # Assuming THEN is TokenType.THEN, but not in token.py. Need to add.
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'then'", current_token
    StmListK, error, current_token = StmList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.ELSE, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'else'", current_token
    StmListK2, error, current_token = StmList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.FI, tokens, current_token)  # Assuming FI is TokenType.FI, not in token.py.
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'fi'", current_token
    root = SyntaxTreeNode(nodekind=NodeKind.StmtK, kind=NodeType.IfK)
    root.children.append(RelExpK)
    root.children.append(StmListK)
    root.children.append(StmListK2)
    return root, None, current_token

def LoopStm(tokens, current_token):
    matched, current_token = Match(TokenType.WHILE, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'while'", current_token
    RelExpK, error, current_token = RelExp(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.DO, tokens, current_token)  # Assuming DO is TokenType.DO, not in token.py.
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'do'", current_token
    StmListK, error, current_token = StmList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.ENDWH, tokens, current_token)  # Assuming ENDWH is TokenType.ENDWH, not in token.py.
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'endwh'", current_token
    root = SyntaxTreeNode(nodekind=NodeKind.StmtK, kind=NodeType.WhileK)
    root.children.append(RelExpK)
    root.children.append(StmListK)
    return root, None, current_token

def InputStm(tokens, current_token):
    matched, current_token = Match(TokenType.READ, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'read'", current_token
    matched, current_token = Match(TokenType.LEFT_PAREN, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected '('", current_token
    InvarK, error, current_token = Invar(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.RIGHT_PAREN, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ')'", current_token
    root = SyntaxTreeNode(nodekind=NodeKind.StmtK, kind=NodeType.ReadK)
    root.children.append(InvarK)
    return root, None, current_token

def Invar(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected identifier", current_token
    root = SyntaxTreeNode(nodekind=NodeKind.ExpK, kind=NodeType.ExpIdK)
    root.name = tokens[current_token-1].Sem
    root.lineno = tokens[current_token-1].Lineshow
    return root, None, current_token

def OutputStm(tokens, current_token):
    matched, current_token = Match(TokenType.WRITE, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'write'", current_token
    matched, current_token = Match(TokenType.LEFT_PAREN, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected '('", current_token
    ExpK, error, current_token = Exp(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.RIGHT_PAREN, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ')'", current_token
    root = SyntaxTreeNode(nodekind=NodeKind.StmtK, kind=NodeType.WriteK)
    root.children.append(ExpK)
    return root, None, current_token

def ReturnStm(tokens, current_token):
    matched, current_token = Match(TokenType.RETURN, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected 'return'", current_token
    root = SyntaxTreeNode(nodekind=NodeKind.StmtK, kind=NodeType.ReturnK)
    return root, None, current_token

def AssCall(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected identifier", current_token
    AssCallK, error, current_token = AssCallRest(tokens, current_token)
    if error:
        return None, error, current_token
    # Depending on AssCallRest, it could be assignment or call
    return AssCallK, None, current_token

def AssCallRest(tokens, current_token):
    if tokens[current_token].Sem in [TokenType.DOT, TokenType.ASSIGN, TokenType.LEFT_SQUARE]:
        return AssignmentRest(tokens, current_token)
    elif tokens[current_token].Sem == TokenType.LEFT_PAREN:
        return CallStmRest(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected assignment or call", current_token

def AssignmentRest(tokens, current_token):
    VariMoreK, error, current_token = VariMore(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.ASSIGN, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ':='", current_token
    ExpK, error, current_token = Exp(tokens, current_token)
    if error:
        return None, error, current_token
    root = SyntaxTreeNode(nodekind=NodeKind.StmtK, kind=NodeType.AssignK)
    root.children.append(VariMoreK)
    root.children.append(ExpK)
    return root, None, current_token

def CallStmRest(tokens, current_token):
    matched, current_token = Match(TokenType.LEFT_PAREN, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected '('", current_token
    ActParamListK, error, current_token = ActParamList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.RIGHT_PAREN, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ')'", current_token
    root = SyntaxTreeNode(nodekind=NodeKind.StmtK, kind=NodeType.CallK)
    if ActParamListK:
        root.children.append(ActParamListK)
    return root, None, current_token

def ActParamList(tokens, current_token):
    if tokens[current_token].Sem == TokenType.RIGHT_PAREN:
        return None, None, current_token  # ε
    else:
        ExpK, error, current_token = Exp(tokens, current_token)
        if error:
            return None, error, current_token
        ActParamMoreK, error, current_token = ActParamMore(tokens, current_token)
        if error:
            return None, error, current_token
        root = SyntaxTreeNode(nodekind=NodeKind.ExpK)
        root.children.append(ExpK)
        if ActParamMoreK:
            root.children.append(ActParamMoreK)
        return root, None, current_token

def ActParamMore(tokens, current_token):
    if tokens[current_token].Sem == TokenType.RIGHT_PAREN:
        return None, None, current_token  # ε
    elif tokens[current_token].Sem == TokenType.COMMA:
        matched, current_token = Match(TokenType.COMMA, tokens, current_token)
        return ActParamList(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ')' or ','", current_token

def RelExp(tokens, current_token):
    ExpK, error, current_token = Exp(tokens, current_token)
    if error:
        return None, error, current_token
    OtherRelEK, error, current_token = OtherRelE(tokens, current_token)
    if error:
        return None, error, current_token
    root = SyntaxTreeNode(nodekind=NodeKind.ExpK)
    root.children.append(ExpK)
    if OtherRelEK:
        root.children.append(OtherRelEK)
    return root, None, current_token

def OtherRelE(tokens, current_token):
    CmpOpK, error, current_token = CmpOp(tokens, current_token)
    if error:
        return None, error, current_token
    ExpK, error, current_token = Exp(tokens, current_token)
    if error:
        return None, error, current_token
    root = SyntaxTreeNode(nodekind=NodeKind.ExpK, kind=NodeType.OpK)
    root.attr["ExpAttr"]["op"] = CmpOpK
    root.children.append(ExpK)
    return root, None, current_token

def Exp(tokens, current_token):
    TermK, error, current_token = Term(tokens, current_token)
    if error:
        return None, error, current_token
    OtherTermK, error, current_token = OtherTerm(tokens, current_token)
    if error:
        return None, error, current_token
    root = SyntaxTreeNode(nodekind=NodeKind.ExpK)
    root.children.append(TermK)
    if OtherTermK:
        root.children.append(OtherTermK)
    return root, None, current_token

def OtherTerm(tokens, current_token):
    if tokens[current_token].Sem in [TokenType.RIGHT_PAREN, TokenType.COMMA, TokenType.SEMICOLON, TokenType.LESS, TokenType.EQ, TokenType.DO, TokenType.ELSE, TokenType.END, TokenType.ENDWH, TokenType.FI, TokenType.THEN, TokenType.RIGHT_SQUARE]:
        return None, None, current_token  # ε
    else:
        AddOpK, error, current_token = AddOp(tokens, current_token)
        if error:
            return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected operator", current_token
        ExpK, error, current_token = Exp(tokens, current_token)
        if error:
            return None, error, current_token
        root = SyntaxTreeNode(nodekind=NodeKind.ExpK, kind=NodeType.OpK)
        root.attr["ExpAttr"]["op"] = AddOpK
        root.children.append(ExpK)
        return root, None, current_token

def Term(tokens, current_token):
    FactorK, error, current_token = Factor(tokens, current_token)
    if error:
        return None, error, current_token
    OtherFactorK, error, current_token = OtherFactor(tokens, current_token)
    if error:
        return None, error, current_token
    root = SyntaxTreeNode(nodekind=NodeKind.ExpK)
    root.children.append(FactorK)
    if OtherFactorK:
        root.children.append(OtherFactorK)
    return root, None, current_token

def OtherFactor(tokens, current_token):
    if tokens[current_token].Sem in [TokenType.RIGHT_PAREN, TokenType.PLUS, TokenType.COMMA, TokenType.MINUS, TokenType.SEMICOLON, TokenType.LESS, TokenType.EQ, TokenType.DO, TokenType.ELSE, TokenType.END, TokenType.ENDWH, TokenType.FI, TokenType.THEN, TokenType.RIGHT_SQUARE]:
        return None, None, current_token  # ε
    else:
        MultOpK, error, current_token = MultOp(tokens, current_token)
        if error:
            return None, error, current_token
        TermK, error, current_token = Term(tokens, current_token)
        if error:
            return None, error, current_token
        root = SyntaxTreeNode(nodekind=NodeKind.ExpK, kind=NodeType.OpK)
        root.attr["ExpAttr"]["op"] = MultOpK
        root.children.append(TermK)
        return root, None, current_token

def Factor(tokens, current_token):
    if tokens[current_token].Sem == TokenType.LEFT_PAREN:
        matched, current_token = Match(TokenType.LEFT_PAREN, tokens, current_token)
        ExpK, error, current_token = Exp(tokens, current_token)
        if error:
            return None, error, current_token
        matched, current_token = Match(TokenType.RIGHT_PAREN, tokens, current_token)
        if not matched:
            return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ')'", current_token
        return ExpK, None, current_token
    elif tokens[current_token].Sem == TokenType.INTC:
        matched, current_token = Match(TokenType.INTC, tokens, current_token)
        root = SyntaxTreeNode(nodekind=NodeKind.ExpK, kind=NodeType.ConstK)
        root.attr["ExpAttr"]["val"] = int(tokens[current_token-1].Lex)
        return root, None, current_token
    elif tokens[current_token].Sem == TokenType.ID:
        return Variable(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected factor", current_token

def Variable(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected identifier", current_token
    root = SyntaxTreeNode(nodekind=NodeKind.ExpK, kind=NodeType.ExpIdK)
    root.name = tokens[current_token-1].Sem
    root.lineno = tokens[current_token-1].Lineshow
    VariMoreK, error, current_token = VariMore(tokens, current_token)
    if error:
        return None, error, current_token
    if VariMoreK:
        root.children.append(VariMoreK)
    return root, None, current_token

def VariMore(tokens, current_token):
    if tokens[current_token].Sem in [TokenType.RIGHT_PAREN, TokenType.TIMES, TokenType.PLUS, TokenType.COMMA, TokenType.MINUS, TokenType.ASSIGN, TokenType.SEMICOLON, TokenType.LESS, TokenType.EQ, TokenType.DO, TokenType.ELSE, TokenType.END, TokenType.ENDWH, TokenType.FI, TokenType.THEN, TokenType.RIGHT_SQUARE]:
        return None, None, current_token  # ε
    elif tokens[current_token].Sem == TokenType.LEFT_SQUARE:
        matched, current_token = Match(TokenType.LEFT_SQUARE, tokens, current_token)
        ExpK, error, current_token = Exp(tokens, current_token)
        if error:
            return None, error, current_token
        matched, current_token = Match(TokenType.RIGHT_SQUARE, tokens, current_token)
        if not matched:
            return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ']'", current_token
        root = SyntaxTreeNode(nodekind=NodeKind.ExpK)
        root.attr["ExpAttr"]["varkind"] = ExpAttrvarkindType.ArrayMemV
        root.children.append(ExpK)
        return root, None, current_token
    elif tokens[current_token].Sem == TokenType.DOT:
        matched, current_token = Match(TokenType.DOT, tokens, current_token)
        return FieldVar(tokens, current_token)
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected vari more", current_token

def FieldVar(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected identifier", current_token
    root = SyntaxTreeNode(nodekind=NodeKind.ExpK, kind=NodeType.ExpIdK)
    root.name = tokens[current_token-1].Sem
    root.lineno = tokens[current_token-1].Lineshow
    FieldVarMoreK, error, current_token = FieldVarMore(tokens, current_token)
    if error:
        return None, error, current_token
    if FieldVarMoreK:
        root.children.append(FieldVarMoreK)
    return root, None, current_token

def FieldVarMore(tokens, current_token):
    if tokens[current_token].Sem in [TokenType.RIGHT_PAREN, TokenType.TIMES, TokenType.PLUS, TokenType.COMMA, TokenType.MINUS, TokenType.ASSIGN, TokenType.SEMICOLON, TokenType.LESS, TokenType.EQ, TokenType.DO, TokenType.ELSE, TokenType.END, TokenType.ENDWH, TokenType.FI, TokenType.THEN, TokenType.RIGHT_SQUARE]:
        return None, None, current_token  # ε
    elif tokens[current_token].Sem == TokenType.LEFT_SQUARE:
        matched, current_token = Match(TokenType.LEFT_SQUARE, tokens, current_token)
        ExpK, error, current_token = Exp(tokens, current_token)
        if error:
            return None, error, current_token
        matched, current_token = Match(TokenType.RIGHT_SQUARE, tokens, current_token)
        if not matched:
            return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected ']'", current_token
        root = SyntaxTreeNode(nodekind=NodeKind.ExpK)
        root.attr["ExpAttr"]["varkind"] = ExpAttrvarkindType.ArrayMemV
        root.children.append(ExpK)
        return root, None, current_token
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected field var more", current_token

def CmpOp(tokens, current_token):
    if tokens[current_token].Sem == TokenType.LESS:
        matched, current_token = Match(TokenType.LESS, tokens, current_token)
        return ExpAttropType.LT, None, current_token
    elif tokens[current_token].Sem == TokenType.EQ:
        matched, current_token = Match(TokenType.EQ, tokens, current_token)
        return ExpAttropType.EQ, None, current_token
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected comparison operator", current_token

def AddOp(tokens, current_token):
    if tokens[current_token].Sem == TokenType.PLUS:
        matched, current_token = Match(TokenType.PLUS, tokens, current_token)
        return ExpAttropType.PLUS, None, current_token
    elif tokens[current_token].Sem == TokenType.MINUS:
        matched, current_token = Match(TokenType.MINUS, tokens, current_token)
        return ExpAttropType.MINUS, None, current_token
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected add operator", current_token

def MultOp(tokens, current_token):
    if tokens[current_token].Sem == TokenType.TIMES:
        matched, current_token = Match(TokenType.TIMES, tokens, current_token)
        return ExpAttropType.TIMES, None, current_token
    elif tokens[current_token].Sem == TokenType.DIV:
        matched, current_token = Match(TokenType.DIV, tokens, current_token)
        return ExpAttropType.OVER, None, current_token
    else:
        return None, f"Line {tokens[current_token].Lineshow}: Syntax error: expected mult operator", current_token

################################################# 

def syntax_analysis(tokens):
    # 语法分析函数，输入Token序列，输出语法树根节点和语法错误检查信息
    root, error = Program(tokens)
    return root, error

if __name__ == "__main__":
    source_code = """{我是一个注释}
    program Example
    type t=integer;
    var t v1;
        char v2;
    begin
        read(v1);
        v1:=v1*10;
        write(v1)
    end.
    """
    tokenizer = Tokenizer(source_code)
    tokens = tokenizer.tokenize()
    syntax_tree, syntax_error = syntax_analysis(tokens)
    if syntax_error:
        print("Syntax error:", syntax_error)
    else:
        print("Syntax tree:")
        syntax_tree.print()