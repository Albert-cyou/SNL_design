# 输入：Token序列
# 输出：语法错误检查信息和语法树
# 方法：递归下降法

from dataclasses import dataclass, field
from typing import List, Optional, Union
from enum import Enum, auto
from make_token import TokenType, Token, Tokenizer


class ExpType(Enum):
    Void = auto()      # 无类型
    Integer = auto()   # 整数类型
    Boolean = auto()   # 布尔类型 

class TypeKind(Enum):
    CHAR = auto()      # 基本类型
    INTEGER = auto()   # 基本类型
    Array = auto()     # 数组类型
    Record = auto()    # 记录类型

class StmType(Enum):
    IfK      =   auto()  # if语句
    ThenK    =   auto()  # then语句
    ElseK    =   auto()  # else语句
    WhileK   =   auto()  # while语句
    AssignK  =   auto()  # 赋值语句
    ReturnK  =   auto()  # return语句
    ReadK    =   auto()  # read语句
    WriteK   =   auto()  # write语句
    CallK    =   auto()  # 过程调用语句

class CompOpType(Enum):
    LT = auto()   # <
    EQ = auto()   # =   

class AddOpType(Enum):
    PLUS = auto()  # +
    MINUS = auto() # -

class MultOpType(Enum):
    TIMES = auto() # *
    DIV = auto()   # /


@dataclass
class ASTNode:
    lineno: int = field(default=0, init=False)

    def children(self):
        return []

    def _pretty_label(self):
        class_name = self.__class__.__name__
        if class_name == "ProgramNode":
            return "Program"
        if class_name == "AssignNode":
            return "Assign"
        if class_name == "IDNode":
            return f"ID({self.name})"
        if class_name == "IntConstNode":
            return f"IntConst({self.value})"
        if class_name == "CharConstNode":
            return f"CharConst({self.value})"
        if class_name == "ArrayElemNode":
            return "ArrayElem"
        if class_name == "RecordFieldNode":
            return "RecordField"
        return class_name

    def _pretty_children(self):
        from dataclasses import fields
        children = []
        for field_info in fields(self):
            value = getattr(self, field_info.name)
            if value is None:
                continue
            if isinstance(value, ASTNode):
                children.append(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, ASTNode):
                        children.append(item)
        return children

    def pretty_print(self, prefix: str = "", is_last: bool = True):
        label = self._pretty_label()
        branch = "└── " if prefix == "" or is_last else "├── "
        print(f"{prefix}{branch}{label}")
        children = self._pretty_children()
        for index, child in enumerate(children):
            next_prefix = prefix + ("    " if prefix == "" or is_last else "│   ")
            child.pretty_print(next_prefix, index == len(children) - 1)

    def print(self, indent: int = 0):
        self.pretty_print()


@dataclass
class TypeNode(ASTNode):
    pass


@dataclass
class ProgramNode(ASTNode):
    ProgramHead: 'ProgramHeadNode'
    Declare: Optional['DeclareNode'] = None
    StmL: Optional['ProgramBodyNode'] = None


@dataclass
class ProgramHeadNode(ASTNode):
    name: 'IDNode'


@dataclass
class DeclareNode(ASTNode):
    type_dec_head: Optional['TypeDecNode'] = None
    var_dec_head: Optional['VarDecHeadNode'] = None
    proc_dec_head: Optional['ProcDecHeadNode'] = None


@dataclass
class TypeDecNode(ASTNode):
    name: 'IDNode'
    type_def: TypeNode


@dataclass
class BaseTypeNode(TypeNode):
    kind: TypeKind


@dataclass
class NamedTypeNode(TypeNode):
    name: 'IDNode'


@dataclass
class ArrayTypeNode(TypeNode):
    low: 'IntConstNode'
    up: 'IntConstNode'
    base_type: TypeNode


@dataclass
class RecordTypeNode(TypeNode):
    fields: List['VarDecNode'] = field(default_factory=list)


@dataclass
class VarDecNode(ASTNode):
    type: TypeNode
    name: Optional['IDNode'] = None


@dataclass
class VarDecHeadNode(ASTNode):
    children: List[VarDecNode] = field(default_factory=list)


@dataclass
class ProcDecHeadNode(ASTNode):
    children: List['ProcDecNode'] = field(default_factory=list)


@dataclass
class ProcDecNode(ASTNode):
    name: Optional['IDNode'] = None
    params: List['ParamNode'] = field(default_factory=list)
    declare: Optional['DeclareNode'] = None
    body: Optional['ProgramBodyNode'] = None


@dataclass
class ParamNode(ASTNode):
    type: TypeNode
    names: List['IDNode'] = field(default_factory=list)
    is_var: bool = False


@dataclass
class StmtNode(ASTNode):
    kind: StmType


@dataclass
class IfNode(StmtNode):
    condition: 'RelExpNode'
    then_stm: List['StmtNode'] = field(default_factory=list)
    else_stm: List['StmtNode'] = field(default_factory=list)
    kind: StmType = field(default=StmType.IfK, init=False)


@dataclass
class WhileNode(StmtNode):
    condition: 'RelExpNode'
    body: List['StmtNode'] = field(default_factory=list)
    kind: StmType = field(default=StmType.WhileK, init=False)


@dataclass
class ReadNode(StmtNode):
    var: 'IDNode'
    kind: StmType = field(default=StmType.ReadK, init=False)


@dataclass
class WriteNode(StmtNode):
    exp: 'ExpNode'
    kind: StmType = field(default=StmType.WriteK, init=False)


@dataclass
class ReturnNode(StmtNode):
    exp: Optional['ExpNode'] = None
    kind: StmType = field(default=StmType.ReturnK, init=False)


@dataclass
class AssignNode(StmtNode):
    var: Union['IDNode', 'ArrayElemNode', 'RecordFieldNode']
    exp: 'ExpNode'
    kind: StmType = field(default=StmType.AssignK, init=False)


@dataclass
class CallNode(StmtNode):
    name: 'IDNode'
    args: List['ExpNode'] = field(default_factory=list)
    kind: StmType = field(default=StmType.CallK, init=False)


@dataclass
class IDNode(ASTNode):
    name: str = ""


@dataclass
class ArrayElemNode(ASTNode):
    array: IDNode
    index: 'ExpNode'


@dataclass
class RecordFieldNode(ASTNode):
    record: IDNode
    field: Union[IDNode, ArrayElemNode]


@dataclass
class RelExpNode(ASTNode):
    CompOp: Optional[CompOpType]
    left: 'ExpNode'
    right: Optional['ExpNode'] = None


@dataclass
class ExpNode(ASTNode):
    term: 'TermNode'
    otherterm: List[tuple[AddOpType, 'TermNode']] = field(default_factory=list)


@dataclass
class TermNode(ASTNode):
    factor: 'FactorNode'
    otherfactor: List[tuple[MultOpType, 'FactorNode']] = field(default_factory=list)


@dataclass
class FactorNode(ASTNode):
    pass


@dataclass
class ParenExpNode(FactorNode):
    exp: 'ExpNode'


@dataclass
class IntConstNode(FactorNode):
    value: int = 0


@dataclass
class CharConstNode(FactorNode):
    value: str = ""


@dataclass
class ProgramBodyNode(ASTNode):
    children: List[StmtNode] = field(default_factory=list)


##########################################################################
# 下面都是递归下降法语法分析函数

def current_line(tokens, current_token):
    if current_token < len(tokens):
        return tokens[current_token].Lineshow
    if tokens:
        return tokens[-1].Lineshow
    return 0


def Match(expected_token, tokens, current_token):
    if current_token < len(tokens) and tokens[current_token].Sem == expected_token:
        return True, current_token + 1
    return False, current_token


def Program(tokens):
    current_token = 0
    PheadK, error, current_token = ProgramHead(tokens, current_token)
    if error:
        return None, error
    DeclareK, error, current_token = DeclarePart(tokens, current_token)
    if error:
        return None, error
    StmLK, error, current_token = ProgramBody(tokens, current_token)
    if error:
        return None, error
    if current_token < len(tokens) and tokens[current_token].Sem == TokenType.DOT:
        current_token += 1
    return ProgramNode(ProgramHead=PheadK, Declare=DeclareK, StmL=StmLK), None, current_token


def ProgramHead(tokens, current_token):
    matched, current_token = Match(TokenType.PROGRAM, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'program' keyword", current_token
    name, error, current_token = ProgramName(tokens, current_token)
    if error:
        return None, error, current_token
    return ProgramHeadNode(name=name), None, current_token


def ProgramName(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected identifier after 'program' keyword", current_token
    return IDNode(name=tokens[current_token - 1].Lex), None, current_token


def DeclarePart(tokens, current_token):
    type_dec_head, error, current_token = TypeDecpart(tokens, current_token)
    if error:
        return None, error, current_token
    var_dec_head, error, current_token = VarDecpart(tokens, current_token)
    if error:
        return None, error, current_token
    proc_dec_head, error, current_token = ProcDecpart(tokens, current_token)
    if error:
        return None, error, current_token
    return DeclareNode(type_dec_head=type_dec_head, var_dec_head=var_dec_head, proc_dec_head=proc_dec_head), None, current_token


def TypeDecpart(tokens, current_token):
    if tokens[current_token].Sem in [TokenType.BEGIN, TokenType.PROCEDURE, TokenType.VAR]:
        return None, None, current_token
    if tokens[current_token].Sem == TokenType.TYPE:
        return TypeDec(tokens, current_token)
    return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected type declaration or begin/procedure/var", current_token


def TypeDec(tokens, current_token):
    matched, current_token = Match(TokenType.TYPE, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'type' keyword", current_token
    type_decls, error, current_token = TypeDecList(tokens, current_token)
    if error:
        return None, error, current_token
    return type_decls, None, current_token


def TypeDecList(tokens, current_token):
    declarations: List[TypeDecNode] = []
    while True:
        type_id, error, current_token = TypeId(tokens, current_token)
        if error:
            return None, error, current_token
        matched, current_token = Match(TokenType.EQ, tokens, current_token)
        if not matched:
            return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected '='", current_token
        type_def, error, current_token = TypeDef(tokens, current_token)
        if error:
            return None, error, current_token
        matched, current_token = Match(TokenType.SEMICOLON, tokens, current_token)
        if not matched:
            return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ';'", current_token
        declarations.append(TypeDecNode(name=type_id, type_def=type_def))
        if tokens[current_token].Sem != TokenType.ID:
            break
    return declarations, None, current_token


def TypeId(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected identifier", current_token
    return IDNode(name=tokens[current_token - 1].Lex), None, current_token


def TypeDef(tokens, current_token):
    if tokens[current_token].Sem in [TokenType.CHAR, TokenType.INTEGER]:
        return BaseType(tokens, current_token)
    if tokens[current_token].Sem == TokenType.ARRAY:
        return ArrayType(tokens, current_token)
    if tokens[current_token].Sem == TokenType.RECORD:
        return RecType(tokens, current_token)
    if tokens[current_token].Sem == TokenType.ID:
        return NamedType(tokens, current_token)
    return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected type definition", current_token


def NamedType(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected type identifier", current_token
    return NamedTypeNode(name=IDNode(name=tokens[current_token - 1].Lex)), None, current_token


def BaseType(tokens, current_token):
    if tokens[current_token].Sem == TokenType.INTEGER:
        matched, current_token = Match(TokenType.INTEGER, tokens, current_token)
        return BaseTypeNode(kind=TypeKind.INTEGER), None, current_token
    if tokens[current_token].Sem == TokenType.CHAR:
        matched, current_token = Match(TokenType.CHAR, tokens, current_token)
        return BaseTypeNode(kind=TypeKind.CHAR), None, current_token
    return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected base type", current_token


def ArrayType(tokens, current_token):
    matched, current_token = Match(TokenType.ARRAY, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'array'", current_token
    matched, current_token = Match(TokenType.LEFT_SQUARE, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected '['", current_token
    low, error, current_token = Low(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.ARRAY_LOWER, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected '..'", current_token
    up, error, current_token = Top(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.RIGHT_SQUARE, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ']'", current_token
    matched, current_token = Match(TokenType.OF, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'of'", current_token
    base_type, error, current_token = BaseType(tokens, current_token)
    if error:
        return None, error, current_token
    return ArrayTypeNode(low=low, up=up, base_type=base_type), None, current_token


def Low(tokens, current_token):
    matched, current_token = Match(TokenType.INTC, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected integer constant", current_token
    return IntConstNode(value=int(tokens[current_token - 1].Lex)), None, current_token


def Top(tokens, current_token):
    return Low(tokens, current_token)


def RecType(tokens, current_token):
    matched, current_token = Match(TokenType.RECORD, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'record'", current_token
    fields, error, current_token = FieldDecList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.END, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'end'", current_token
    return RecordTypeNode(fields=fields), None, current_token


def FieldDecList(tokens, current_token):
    fields: List[VarDecNode] = []
    while tokens[current_token].Sem in [TokenType.CHAR, TokenType.INTEGER, TokenType.ARRAY]:
        field_type, error, current_token = FieldType(tokens, current_token)
        if error:
            return None, error, current_token
        ids, error, current_token = IdList(tokens, current_token)
        if error:
            return None, error, current_token
        matched, current_token = Match(TokenType.SEMICOLON, tokens, current_token)
        if not matched:
            return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ';'", current_token
        fields.extend([VarDecNode(type=field_type, name=id_node) for id_node in ids])
    return fields, None, current_token


def FieldType(tokens, current_token):
    if tokens[current_token].Sem in [TokenType.CHAR, TokenType.INTEGER]:
        return BaseType(tokens, current_token)
    if tokens[current_token].Sem == TokenType.ARRAY:
        return ArrayType(tokens, current_token)
    return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected base type or array", current_token


def IdList(tokens, current_token):
    ids: List[IDNode] = []
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected identifier", current_token
    ids.append(IDNode(name=tokens[current_token - 1].Lex))
    while tokens[current_token].Sem == TokenType.COMMA:
        current_token += 1
        matched, current_token = Match(TokenType.ID, tokens, current_token)
        if not matched:
            return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected identifier after ','", current_token
        ids.append(IDNode(name=tokens[current_token - 1].Lex))
    return ids, None, current_token


def VarDecpart(tokens, current_token):
    if tokens[current_token].Sem in [TokenType.BEGIN, TokenType.PROCEDURE]:
        return None, None, current_token
    if tokens[current_token].Sem == TokenType.VAR:
        return VarDec(tokens, current_token)
    return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected var declaration or begin/procedure", current_token


def VarDec(tokens, current_token):
    matched, current_token = Match(TokenType.VAR, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'var'", current_token
    declarations, error, current_token = VarDecList(tokens, current_token)
    if error:
        return None, error, current_token
    return VarDecHeadNode(children=declarations), None, current_token


def VarDecList(tokens, current_token):
    declarations: List[VarDecNode] = []
    while tokens[current_token].Sem in [TokenType.ARRAY, TokenType.CHAR, TokenType.INTEGER, TokenType.ID, TokenType.RECORD]:
        var_type, error, current_token = TypeDef(tokens, current_token)
        if error:
            return None, error, current_token
        id_nodes, error, current_token = VarIdList(tokens, current_token)
        if error:
            return None, error, current_token
        matched, current_token = Match(TokenType.SEMICOLON, tokens, current_token)
        if not matched:
            return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ';'", current_token
        declarations.extend([VarDecNode(type=var_type, name=id_node) for id_node in id_nodes])
        if tokens[current_token].Sem not in [TokenType.ARRAY, TokenType.CHAR, TokenType.INTEGER, TokenType.ID, TokenType.RECORD]:
            break
    return declarations, None, current_token


def VarIdList(tokens, current_token):
    return IdList(tokens, current_token)


def ProcDecpart(tokens, current_token):
    if tokens[current_token].Sem == TokenType.BEGIN:
        return None, None, current_token
    if tokens[current_token].Sem != TokenType.PROCEDURE:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected procedure declaration or begin", current_token
    procedures, error, current_token = ProcDecs(tokens, current_token)
    if error:
        return None, error, current_token
    return ProcDecHeadNode(children=procedures), None, current_token


def ProcDecs(tokens, current_token):
    procedures: List[ProcDecNode] = []
    while tokens[current_token].Sem == TokenType.PROCEDURE:
        proc_node, error, current_token = ProcDec(tokens, current_token)
        if error:
            return None, error, current_token
        procedures.append(proc_node)
    return procedures, None, current_token


def ProcDec(tokens, current_token):
    matched, current_token = Match(TokenType.PROCEDURE, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'procedure'", current_token
    proc_name, error, current_token = ProcName(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.LEFT_PAREN, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected '('", current_token
    params, error, current_token = ParamList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.RIGHT_PAREN, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ')'", current_token
    matched, current_token = Match(TokenType.SEMICOLON, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ';'", current_token
    proc_declare, error, current_token = ProcDecPart(tokens, current_token)
    if error:
        return None, error, current_token
    proc_body, error, current_token = ProcBody(tokens, current_token)
    if error:
        return None, error, current_token
    return ProcDecNode(name=proc_name, params=params or [], declare=proc_declare, body=proc_body), None, current_token


def ProcName(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected identifier", current_token
    return IDNode(name=tokens[current_token - 1].Lex), None, current_token


def ParamList(tokens, current_token):
    if tokens[current_token].Sem == TokenType.RIGHT_PAREN:
        return [], None, current_token
    return ParamDecList(tokens, current_token)


def ParamDecList(tokens, current_token):
    params: List[ParamNode] = []
    param_node, error, current_token = Param(tokens, current_token)
    if error:
        return None, error, current_token
    params.append(param_node)
    while tokens[current_token].Sem == TokenType.SEMICOLON:
        current_token += 1
        param_node, error, current_token = Param(tokens, current_token)
        if error:
            return None, error, current_token
        params.append(param_node)
    return params, None, current_token


def Param(tokens, current_token):
    is_var = False
    if tokens[current_token].Sem == TokenType.VAR:
        matched, current_token = Match(TokenType.VAR, tokens, current_token)
        if not matched:
            return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'var'", current_token
        is_var = True
    type_def, error, current_token = TypeDef(tokens, current_token)
    if error:
        return None, error, current_token
    name_nodes, error, current_token = FormList(tokens, current_token)
    if error:
        return None, error, current_token
    return ParamNode(type=type_def, names=name_nodes, is_var=is_var), None, current_token


def FormList(tokens, current_token):
    ids, error, current_token = IdList(tokens, current_token)
    if error:
        return None, error, current_token
    return ids, None, current_token


def ProcDecPart(tokens, current_token):
    return DeclarePart(tokens, current_token)


def ProcBody(tokens, current_token):
    return ProgramBody(tokens, current_token)


def ProgramBody(tokens, current_token):
    matched, current_token = Match(TokenType.BEGIN, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'begin'", current_token
    statements, error, current_token = StmList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.END, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'end'", current_token
    return ProgramBodyNode(children=statements), None, current_token


def StmList(tokens, current_token):
    statements: List[StmtNode] = []
    statement, error, current_token = Stm(tokens, current_token)
    if error:
        return None, error, current_token
    statements.append(statement)
    while tokens[current_token].Sem == TokenType.SEMICOLON:
        current_token += 1
        if tokens[current_token].Sem in [TokenType.ELSE, TokenType.END, TokenType.ENDWH, TokenType.FI]:
            break
        statement, error, current_token = Stm(tokens, current_token)
        if error:
            return None, error, current_token
        statements.append(statement)
    return statements, None, current_token


def Stm(tokens, current_token):
    current = tokens[current_token].Sem
    if current == TokenType.IF:
        return ConditionalStm(tokens, current_token)
    if current == TokenType.WHILE:
        return LoopStm(tokens, current_token)
    if current == TokenType.READ:
        return InputStm(tokens, current_token)
    if current == TokenType.WRITE:
        return OutputStm(tokens, current_token)
    if current == TokenType.RETURN:
        return ReturnStm(tokens, current_token)
    if current == TokenType.ID:
        return AssCall(tokens, current_token)
    return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected statement", current_token


def ConditionalStm(tokens, current_token):
    matched, current_token = Match(TokenType.IF, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'if'", current_token
    condition, error, current_token = RelExp(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.THEN, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'then'", current_token
    then_stmts, error, current_token = StmList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.ELSE, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'else'", current_token
    else_stmts, error, current_token = StmList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.FI, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'fi'", current_token
    return IfNode(condition=condition, then_stm=then_stmts, else_stm=else_stmts), None, current_token


def LoopStm(tokens, current_token):
    matched, current_token = Match(TokenType.WHILE, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'while'", current_token
    condition, error, current_token = RelExp(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.DO, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'do'", current_token
    body, error, current_token = StmList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.ENDWH, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'endwh'", current_token
    return WhileNode(condition=condition, body=body), None, current_token


def InputStm(tokens, current_token):
    matched, current_token = Match(TokenType.READ, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'read'", current_token
    matched, current_token = Match(TokenType.LEFT_PAREN, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected '('", current_token
    var_node, error, current_token = Invar(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.RIGHT_PAREN, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ')'", current_token
    return ReadNode(var=var_node), None, current_token


def Invar(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected identifier", current_token
    return IDNode(name=tokens[current_token - 1].Lex), None, current_token


def OutputStm(tokens, current_token):
    matched, current_token = Match(TokenType.WRITE, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'write'", current_token
    matched, current_token = Match(TokenType.LEFT_PAREN, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected '('", current_token
    exp_node, error, current_token = Exp(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.RIGHT_PAREN, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ')'", current_token
    return WriteNode(exp=exp_node), None, current_token


def ReturnStm(tokens, current_token):
    matched, current_token = Match(TokenType.RETURN, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'return'", current_token
    exp_node = None
    if tokens[current_token].Sem not in [TokenType.SEMICOLON, TokenType.ELSE, TokenType.END, TokenType.ENDWH, TokenType.FI, TokenType.THEN, TokenType.RIGHT_PAREN]:
        exp_node, error, current_token = Exp(tokens, current_token)
        if error:
            return None, error, current_token
    return ReturnNode(exp=exp_node), None, current_token


def AssCall(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected identifier", current_token
    name_node = IDNode(name=tokens[current_token - 1].Lex)
    return AssCallRest(tokens, current_token, name_node)


def AssCallRest(tokens, current_token, name_node):
    if tokens[current_token].Sem in [TokenType.DOT, TokenType.ASSIGN, TokenType.LEFT_SQUARE]:
        return AssignmentRest(tokens, current_token, name_node)
    if tokens[current_token].Sem == TokenType.LEFT_PAREN:
        return CallStmRest(tokens, current_token, name_node)
    return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected assignment or call", current_token


def AssignmentRest(tokens, current_token, name_node):
    var_suffix, error, current_token = VariMore(tokens, current_token, name_node)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.ASSIGN, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ':='", current_token
    exp_node, error, current_token = Exp(tokens, current_token)
    if error:
        return None, error, current_token
    var_node = var_suffix if var_suffix is not None else name_node
    return AssignNode(var=var_node, exp=exp_node), None, current_token


def CallStmRest(tokens, current_token, name_node):
    matched, current_token = Match(TokenType.LEFT_PAREN, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected '('", current_token
    args, error, current_token = ActParamList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.RIGHT_PAREN, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ')'", current_token
    return CallNode(name=name_node, args=args or []), None, current_token


def ActParamList(tokens, current_token):
    args: List[ExpNode] = []
    if tokens[current_token].Sem == TokenType.RIGHT_PAREN:
        return args, None, current_token
    exp_node, error, current_token = Exp(tokens, current_token)
    if error:
        return None, error, current_token
    args.append(exp_node)
    while tokens[current_token].Sem == TokenType.COMMA:
        current_token += 1
        exp_node, error, current_token = Exp(tokens, current_token)
        if error:
            return None, error, current_token
        args.append(exp_node)
    return args, None, current_token


def RelExp(tokens, current_token):
    left, error, current_token = Exp(tokens, current_token)
    if error:
        return None, error, current_token
    if tokens[current_token].Sem in [TokenType.LESS, TokenType.EQ]:
        comp_op, error, current_token = CmpOp(tokens, current_token)
        if error:
            return None, error, current_token
        right, error, current_token = Exp(tokens, current_token)
        if error:
            return None, error, current_token
        return RelExpNode(CompOp=comp_op, left=left, right=right), None, current_token
    return RelExpNode(CompOp=None, left=left, right=None), None, current_token


def Exp(tokens, current_token):
    term_node, error, current_token = Term(tokens, current_token)
    if error:
        return None, error, current_token
    other_terms, error, current_token = OtherTerm(tokens, current_token)
    if error:
        return None, error, current_token
    return ExpNode(term=term_node, otherterm=other_terms or []), None, current_token


def OtherTerm(tokens, current_token):
    items: List[tuple[AddOpType, TermNode]] = []
    while tokens[current_token].Sem in [TokenType.PLUS, TokenType.MINUS]:
        op, error, current_token = AddOp(tokens, current_token)
        if error:
            return None, error, current_token
        term_node, error, current_token = Term(tokens, current_token)
        if error:
            return None, error, current_token
        items.append((op, term_node))
    return items, None, current_token


def Term(tokens, current_token):
    factor_node, error, current_token = Factor(tokens, current_token)
    if error:
        return None, error, current_token
    other_factors, error, current_token = OtherFactor(tokens, current_token)
    if error:
        return None, error, current_token
    return TermNode(factor=factor_node, otherfactor=other_factors or []), None, current_token


def OtherFactor(tokens, current_token):
    items: List[tuple[MultOpType, FactorNode]] = []
    while tokens[current_token].Sem in [TokenType.TIMES, TokenType.DIV]:
        op, error, current_token = MultOp(tokens, current_token)
        if error:
            return None, error, current_token
        factor_node, error, current_token = Factor(tokens, current_token)
        if error:
            return None, error, current_token
        items.append((op, factor_node))
    return items, None, current_token


def Factor(tokens, current_token):
    if tokens[current_token].Sem == TokenType.LEFT_PAREN:
        matched, current_token = Match(TokenType.LEFT_PAREN, tokens, current_token)
        exp_node, error, current_token = Exp(tokens, current_token)
        if error:
            return None, error, current_token
        matched, current_token = Match(TokenType.RIGHT_PAREN, tokens, current_token)
        if not matched:
            return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ')'", current_token
        return ParenExpNode(exp=exp_node), None, current_token
    if tokens[current_token].Sem == TokenType.INTC:
        matched, current_token = Match(TokenType.INTC, tokens, current_token)
        return IntConstNode(value=int(tokens[current_token - 1].Lex)), None, current_token
    if tokens[current_token].Sem == TokenType.ID:
        return Variable(tokens, current_token)
    return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected factor", current_token


def Variable(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected identifier", current_token
    base = IDNode(name=tokens[current_token - 1].Lex)
    suffix, error, current_token = VariMore(tokens, current_token, base)
    if error:
        return None, error, current_token
    return suffix if suffix is not None else base, None, current_token


def VariMore(tokens, current_token, base):
    if tokens[current_token].Sem == TokenType.LEFT_SQUARE:
        matched, current_token = Match(TokenType.LEFT_SQUARE, tokens, current_token)
        index, error, current_token = Exp(tokens, current_token)
        if error:
            return None, error, current_token
        matched, current_token = Match(TokenType.RIGHT_SQUARE, tokens, current_token)
        if not matched:
            return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ']'", current_token
        return ArrayElemNode(array=base, index=index), None, current_token
    if tokens[current_token].Sem == TokenType.DOT:
        matched, current_token = Match(TokenType.DOT, tokens, current_token)
        return FieldVar(tokens, current_token, base)
    if tokens[current_token].Sem in [TokenType.ASSIGN, TokenType.PLUS, TokenType.MINUS, TokenType.TIMES, TokenType.DIV, TokenType.SEMICOLON, TokenType.COMMA, TokenType.RIGHT_PAREN, TokenType.ELSE, TokenType.END, TokenType.ENDWH, TokenType.FI, TokenType.THEN]:
        return None, None, current_token
    return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected variable suffix", current_token


def FieldVar(tokens, current_token, record_base):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected identifier", current_token
    field_id = IDNode(name=tokens[current_token - 1].Lex)
    if tokens[current_token].Sem == TokenType.LEFT_SQUARE:
        matched, current_token = Match(TokenType.LEFT_SQUARE, tokens, current_token)
        index, error, current_token = Exp(tokens, current_token)
        if error:
            return None, error, current_token
        matched, current_token = Match(TokenType.RIGHT_SQUARE, tokens, current_token)
        if not matched:
            return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ']'", current_token
        field = ArrayElemNode(array=field_id, index=index)
    else:
        field = field_id
    return RecordFieldNode(record=record_base, field=field), None, current_token


def CmpOp(tokens, current_token):
    if tokens[current_token].Sem == TokenType.LESS:
        matched, current_token = Match(TokenType.LESS, tokens, current_token)
        return CompOpType.LT, None, current_token
    if tokens[current_token].Sem == TokenType.EQ:
        matched, current_token = Match(TokenType.EQ, tokens, current_token)
        return CompOpType.EQ, None, current_token
    return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected comparison operator", current_token


def AddOp(tokens, current_token):
    if tokens[current_token].Sem == TokenType.PLUS:
        matched, current_token = Match(TokenType.PLUS, tokens, current_token)
        return AddOpType.PLUS, None, current_token
    if tokens[current_token].Sem == TokenType.MINUS:
        matched, current_token = Match(TokenType.MINUS, tokens, current_token)
        return AddOpType.MINUS, None, current_token
    return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected add operator", current_token


def MultOp(tokens, current_token):
    if tokens[current_token].Sem == TokenType.TIMES:
        matched, current_token = Match(TokenType.TIMES, tokens, current_token)
        return MultOpType.TIMES, None, current_token
    if tokens[current_token].Sem == TokenType.DIV:
        matched, current_token = Match(TokenType.DIV, tokens, current_token)
        return MultOpType.DIV, None, current_token
    return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected mult operator", current_token


def syntax_analysis(tokens):
    root, error, _ = Program(tokens)
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
