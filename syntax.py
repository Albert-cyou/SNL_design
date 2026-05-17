# 输入：Token序列
# 输出：语法错误检查信息和语法树
# 方法：递归下降法

from dataclasses import dataclass, field, fields
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
    lineno: int = field(default=0, kw_only=True)

    def children(self):
        return []
    
    def node_print(self):
        return self.__class__.__name__

    def pretty_print(self, prefix="", is_last=True):
        branch = "└── " if is_last else "├── "
        print(prefix + branch + self.node_print())

        children = self.children()
        # Filter out None values from children
        if children is None:
            children = []
        else:
            children = [c for c in children if c is not None]

        for i, child in enumerate(children):
            next_prefix = prefix + (
                "    " if is_last else "│   "
            )
            child.pretty_print(
                next_prefix,
                i == len(children)-1
            )

    def print(self, indent: int = 0):
        self.pretty_print()


# Helper class for branch labels in tree display
class BranchLabel(ASTNode):
    """用于在语法树中显示分支标签（如THEN、ELSE、DO等）"""
    def __init__(self, label: str, children: List = None):
        self.label = label
        self._children = children or []
    
    def node_print(self):
        return f"[{self.label}]"
    
    def children(self):
        return self._children


@dataclass
class TypeNode(ASTNode):
    pass


@dataclass
class ProgramNode(ASTNode):
    ProgramHead: 'ProgramHeadNode'
    Declare: Optional['DeclareNode'] = None
    StmL: Optional['ProgramBodyNode'] = None

    def node_print(self):
        return "Program"
    
    def children(self):
        return [self.ProgramHead, self.Declare, self.StmL]


@dataclass
class ProgramHeadNode(ASTNode):
    name: 'IDNode'

    def node_print(self):
        return f"Program \"{self.name.name}\""


@dataclass
class DeclareNode(ASTNode):
    type_dec_head: Optional['TypeDecHeadNode'] = None
    var_dec_head: Optional['VarDecHeadNode'] = None
    proc_dec_head: Optional['ProcDecHeadNode'] = None

    def children(self):
        return [self.type_dec_head,
                self.var_dec_head,
                self.proc_dec_head]
    
    def node_print(self):
        return "DeclarePart"

@dataclass
class TypeDecHeadNode(ASTNode):
    nodes: List['TypeDecNode'] = field(default_factory=list)

    def children(self):
        return self.nodes

    def node_print(self):
        return "TypeDeclarationHead"

@dataclass
class TypeDecNode(ASTNode):
    name: 'IDNode'
    type_def: TypeNode

    def children(self):
        return []
    
    def node_print(self):
        return f"TypeDec: {self.name.name} = {self.type_def.node_print()}"


@dataclass
class BaseTypeNode(TypeNode):
    kind: TypeKind
    
    def node_print(self):
        return self.kind.name


@dataclass
class NamedTypeNode(TypeNode):
    name: 'IDNode'

    def node_print(self):
        return f"Type({self.name.name})"


@dataclass
class ArrayTypeNode(TypeNode):
    low: 'IntConstNode'
    up: 'IntConstNode'
    base_type: TypeNode

    def node_print(self):
        return f"Array[{self.low.value}..{self.up.value}] of {self.base_type.node_print()}"


@dataclass
class RecordTypeNode(TypeNode):
    fields: List['VarDecNode'] = field(default_factory=list)

    def node_print(self):
        return "Record"
    
    def children(self):
        return self.fields


@dataclass
class VarDecNode(ASTNode):
    type: TypeNode
    name: Optional[Union['IDNode', List['IDNode']]] = None

    def node_print(self):
        if self.name is None:
            return f"Var: {self.type.node_print()}"
        if isinstance(self.name, list):
            names = ', '.join([n.name for n in self.name])
        else:
            names = self.name.name
        return f"Var: {names} : {self.type.node_print()}"
    
    def children(self):
        return []


@dataclass
class VarDecHeadNode(ASTNode):
    nodes: List[VarDecNode] = field(default_factory=list)

    def children(self):
        return self.nodes
    
    def node_print(self):
        return "VarDecHead"

@dataclass
class ProcDecHeadNode(ASTNode):
    nodes: List['ProcDecNode'] = field(default_factory=list)

    def children(self):
        return self.nodes
    
    def node_print(self):
        return "ProcDecHead"

@dataclass
class ProcDecNode(ASTNode):
    name: Optional['IDNode'] = None
    params: List['ParamNode'] = field(default_factory=list)
    declare: Optional['DeclareNode'] = None
    body: Optional['ProgramBodyNode'] = None

    def children(self):
        return [self.name] + self.params + [self.declare,self.body]

    def node_print(self):
        return "ProcDec"

@dataclass
class ParamNode(ASTNode):
    type: TypeNode
    names: List['IDNode'] = field(default_factory=list)
    is_var: bool = False
    
    def node_print(self):
        var_flag = "var" if self.is_var else ""
        name_str = ', '.join([n.name for n in self.names])
        return f"Param {var_flag}: {name_str} : {self.type.node_print()}"

@dataclass
class StmtNode(ASTNode):
    kind: StmType


@dataclass
class IfNode(StmtNode):
    condition: 'RelExpNode'
    then_stm: List['StmtNode'] = field(default_factory=list)
    else_stm: List['StmtNode'] = field(default_factory=list)
    kind: StmType = field(default=StmType.IfK, init=False)

    def node_print(self):
        return "IF"
    
    def children(self):
        result = [self.condition]
        if self.then_stm:
            result.append(BranchLabel("THEN", self.then_stm))
        if self.else_stm:
            result.append(BranchLabel("ELSE", self.else_stm))
        return result 


@dataclass
class WhileNode(StmtNode):
    condition: 'RelExpNode'
    body: List['StmtNode'] = field(default_factory=list)
    kind: StmType = field(default=StmType.WhileK, init=False)

    def children(self):
        result = [self.condition]
        if self.body:
            result.append(BranchLabel("DO", self.body))
        return result


@dataclass
class ReadNode(StmtNode):
    var: 'IDNode'
    kind: StmType = field(default=StmType.ReadK, init=False)

    def node_print(self):
        return "READ"
    
    def children(self):
        return [self.var]


@dataclass
class WriteNode(StmtNode):
    exp: 'ExpNode'
    kind: StmType = field(default=StmType.WriteK, init=False)

    def node_print(self):
        return "WRITE"
    
    def children(self):
        return [self.exp]


@dataclass
class ReturnNode(StmtNode):
    exp: Optional['ExpNode'] = None
    kind: StmType = field(default=StmType.ReturnK, init=False)

    def node_print(self):
        return "RETURN"
    
    def children(self):
        return [self.exp] if self.exp else []


@dataclass
class AssignNode(StmtNode):
    var: Union['IDNode', 'ArrayElemNode', 'RecordFieldNode']
    exp: 'ExpNode'
    kind: StmType = field(default=StmType.AssignK, init=False)

    def node_print(self):
        return "ASSIGN :="
    
    def children(self):
        return [self.var, self.exp]


@dataclass
class CallNode(StmtNode):
    name: 'IDNode'
    args: List['ExpNode'] = field(default_factory=list)
    kind: StmType = field(default=StmType.CallK, init=False)

    def node_print(self):
        return f"CALL {self.name.name}()"
    
    def children(self):
        return [self.name] + self.args


@dataclass
class IDNode(ASTNode):
    name: str = ""

    def node_print(self):
        return f"ID={self.name}"


@dataclass
class ArrayElemNode(ASTNode):
    array: IDNode
    index: 'ExpNode'

    def node_print(self):
        return f"ArrayElem[]"
    
    def children(self):
        return [self.array, self.index]


@dataclass
class RecordFieldNode(ASTNode):
    record: IDNode
    field: Union[IDNode, ArrayElemNode]

    def node_print(self):
        return "RecordField(.)"
    
    def children(self):
        return [self.record, self.field]


@dataclass
class RelExpNode(ASTNode):
    CompOp: Optional[CompOpType]
    left: 'ExpNode'
    right: Optional['ExpNode'] = None

    def node_print(self):
        if self.CompOp:
            op_str = "<" if self.CompOp == CompOpType.LT else "="
            return f"RelExp({op_str})"
        return "RelExp"
    
    def children(self):
        if self.right:
            return [self.left, self.right]
        return [self.left]


@dataclass
class ExpNode(ASTNode):
    term: 'TermNode'
    otherterm: List[tuple[AddOpType, 'TermNode']] = field(default_factory=list)

    def node_print(self):
        if self.otherterm:
            return "Exp(+/-)"
        return "Exp"
    
    def children(self):
        result = [self.term]
        for op, term in self.otherterm:
            op_label = BranchLabel(f"{op.name}", [term])
            result.append(op_label)
        return result


@dataclass
class TermNode(ASTNode):
    factor: 'FactorNode'
    otherfactor: List[tuple[MultOpType, 'FactorNode']] = field(default_factory=list)

    def node_print(self):
        if self.otherfactor:
            return "Term(*/)" 
        return "Term"
    
    def children(self):
        result = [self.factor]
        for op, factor in self.otherfactor:
            op_label = BranchLabel(f"{op.name}", [factor])
            result.append(op_label)
        return result


@dataclass
class FactorNode(ASTNode):
    pass


@dataclass
class ParenExpNode(FactorNode):
    exp: 'ExpNode'

    def node_print(self):
        return "("
    
    def children(self):
        return [self.exp]


@dataclass
class IntConstNode(FactorNode):
    value: int = 0

    def node_print(self):
        return f"IntConst({self.value})"


@dataclass
class CharConstNode(FactorNode):
    value: str = ""

    def node_print(self):
        return f"CharConst('{self.value}')"


@dataclass
class ProgramBodyNode(ASTNode):
    children_list: List[StmtNode] = field(default_factory=list)

    def node_print(self):
        return "Body"
    
    def children(self):
        return self.children_list


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
    lineno = 0
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
    return ProgramNode(ProgramHead=PheadK, Declare=DeclareK, StmL=StmLK, lineno=lineno), None, current_token


def ProgramHead(tokens, current_token):
    matched, current_token = Match(TokenType.PROGRAM, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'program' keyword", current_token
    lineno = tokens[current_token].Lineshow
    name, error, current_token = ProgramName(tokens, current_token)
    if error:
        return None, error, current_token
    return ProgramHeadNode(name=name, lineno=lineno), None, current_token


def ProgramName(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected identifier after 'program' keyword", current_token
    return IDNode(name=tokens[current_token - 1].Lex, lineno=tokens[current_token - 1].Lineshow), None, current_token


def DeclarePart(tokens, current_token):
    lineno = tokens[current_token].Lineshow
    type_dec_head, error, current_token = TypeDecpart(tokens, current_token)
    if error:
        return None, error, current_token
    var_dec_head, error, current_token = VarDecpart(tokens, current_token)
    if error:
        return None, error, current_token
    proc_dec_head, error, current_token = ProcDecpart(tokens, current_token)
    if error:
        return None, error, current_token
    return DeclareNode(type_dec_head=type_dec_head, var_dec_head=var_dec_head, proc_dec_head=proc_dec_head, lineno=lineno), None, current_token


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
    declarations: TypeDecHeadNode = TypeDecHeadNode(nodes=[])
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
        declarations.nodes.append(TypeDecNode(name=type_id, type_def=type_def))
        if tokens[current_token].Sem != TokenType.ID:
            break
    return declarations, None, current_token


def TypeId(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected identifier", current_token
    return IDNode(name=tokens[current_token - 1].Lex,lineno=tokens[current_token - 1].Lineshow), None, current_token


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
    return NamedTypeNode(name=IDNode(name=tokens[current_token - 1].Lex), lineno=tokens[current_token - 1].Lineshow), None, current_token


def BaseType(tokens, current_token):
    if tokens[current_token].Sem == TokenType.INTEGER:
        matched, current_token = Match(TokenType.INTEGER, tokens, current_token)
        return BaseTypeNode(kind=TypeKind.INTEGER, lineno=tokens[current_token - 1].Lineshow), None, current_token
    if tokens[current_token].Sem == TokenType.CHAR:
        matched, current_token = Match(TokenType.CHAR, tokens, current_token)
        return BaseTypeNode(kind=TypeKind.CHAR, lineno=tokens[current_token - 1].Lineshow), None, current_token
    return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected base type", current_token


def ArrayType(tokens, current_token):
    matched, current_token = Match(TokenType.ARRAY, tokens, current_token)
    lineno = tokens[current_token - 1].Lineshow
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
    return ArrayTypeNode(low=low, up=up, base_type=base_type,lineno=lineno), None, current_token


def Low(tokens, current_token):
    matched, current_token = Match(TokenType.INTC, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected integer constant", current_token
    return IntConstNode(value=int(tokens[current_token - 1].Lex),lineno=tokens[current_token - 1].Lineshow), None, current_token


def Top(tokens, current_token):
    return Low(tokens, current_token)


def RecType(tokens, current_token):
    matched, current_token = Match(TokenType.RECORD, tokens, current_token)
    lineno=tokens[current_token - 1].Lineshow
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'record'", current_token
    fields, error, current_token = FieldDecList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.END, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'end'", current_token
    return RecordTypeNode(fields=fields,lineno=lineno), None, current_token


def FieldDecList(tokens, current_token):
    fields: List[VarDecNode] = []
    while tokens[current_token].Sem in [TokenType.CHAR, TokenType.INTEGER, TokenType.ARRAY]:
        lineno = tokens[current_token].Lineshow
        field_type, error, current_token = FieldType(tokens, current_token)
        if error:
            return None, error, current_token
        ids, error, current_token = IdList(tokens, current_token)
        if error:
            return None, error, current_token
        matched, current_token = Match(TokenType.SEMICOLON, tokens, current_token)
        if not matched:
            return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ';'", current_token
        fields.extend([VarDecNode(type=field_type, name=id_node,lineno=lineno) for id_node in ids])
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
    ids.append(IDNode(name=tokens[current_token - 1].Lex,lineno=tokens[current_token - 1].Lineshow))
    while tokens[current_token].Sem == TokenType.COMMA:
        current_token += 1
        matched, current_token = Match(TokenType.ID, tokens, current_token)
        if not matched:
            return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected identifier after ','", current_token
        ids.append(IDNode(name=tokens[current_token - 1].Lex,lineno=tokens[current_token - 1].Lineshow))
    return ids, None, current_token


def VarDecpart(tokens, current_token):
    if tokens[current_token].Sem in [TokenType.BEGIN, TokenType.PROCEDURE]:
        return None, None, current_token
    if tokens[current_token].Sem == TokenType.VAR:
        return VarDec(tokens, current_token)
    return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected var declaration or begin/procedure", current_token


def VarDec(tokens, current_token):
    matched, current_token = Match(TokenType.VAR, tokens, current_token)
    lineno=tokens[current_token - 1].Lineshow
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'var'", current_token
    declarations, error, current_token = VarDecList(tokens, current_token)
    if error:
        return None, error, current_token
    return VarDecHeadNode(nodes=declarations,lineno=lineno), None, current_token


def VarDecList(tokens, current_token):
    declarations: List[VarDecNode] = []
    while tokens[current_token].Sem in [TokenType.ARRAY, TokenType.CHAR, TokenType.INTEGER, TokenType.ID, TokenType.RECORD]:
        lineno = tokens[current_token].Lineshow
        var_type, error, current_token = TypeDef(tokens, current_token)
        if error:
            return None, error, current_token
        id_nodes, error, current_token = VarIdList(tokens, current_token)
        if error:
            return None, error, current_token
        matched, current_token = Match(TokenType.SEMICOLON, tokens, current_token)
        if not matched:
            return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ';'", current_token
        declarations.extend([VarDecNode(type=var_type, name=id_node,lineno=lineno) for id_node in id_nodes])
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
    lineno = tokens[current_token].Lineshow
    procedures, error, current_token = ProcDecs(tokens, current_token)
    if error:
        return None, error, current_token
    return ProcDecHeadNode(nodes=procedures,lineno=lineno), None, current_token


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
    lineno = tokens[current_token-1].Lineshow
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
    return ProcDecNode(name=proc_name, params=params or [], declare=proc_declare, body=proc_body,lineno=lineno), None, current_token


def ProcName(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected identifier", current_token
    return IDNode(name=tokens[current_token - 1].Lex, lineno=tokens[current_token-1].Lineshow), None, current_token


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
    lineno = tokens[current_token - 1].Lineshow
    type_def, error, current_token = TypeDef(tokens, current_token)
    if error:
        return None, error, current_token
    name_nodes, error, current_token = FormList(tokens, current_token)
    if error:
        return None, error, current_token
    return ParamNode(type=type_def, names=name_nodes, is_var=is_var, lineno=lineno), None, current_token


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
    lineno = tokens[current_token-1].Lineshow
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'begin'", current_token
    statements, error, current_token = StmList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.END, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'end'", current_token
    return ProgramBodyNode(children_list=statements,lineno=lineno), None, current_token


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
    lineno = tokens[current_token-1].Lineshow
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
    return IfNode(condition=condition, then_stm=then_stmts, else_stm=else_stmts,lineno=lineno), None, current_token


def LoopStm(tokens, current_token):
    matched, current_token = Match(TokenType.WHILE, tokens, current_token)
    lineno = tokens[current_token-1].Lineshow
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
    return WhileNode(condition=condition, body=body, lineno=lineno), None, current_token


def InputStm(tokens, current_token):
    matched, current_token = Match(TokenType.READ, tokens, current_token)
    lineno = tokens[current_token-1].Lineshow
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
    return ReadNode(var=var_node, lineno=lineno), None, current_token


def Invar(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected identifier", current_token
    return IDNode(name=tokens[current_token - 1].Lex, lineno = tokens[current_token-1].Lineshow), None, current_token


def OutputStm(tokens, current_token):
    matched, current_token = Match(TokenType.WRITE, tokens, current_token)
    lineno = tokens[current_token-1].Lineshow
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
    return WriteNode(exp=exp_node, lineno=lineno), None, current_token


def ReturnStm(tokens, current_token):
    matched, current_token = Match(TokenType.RETURN, tokens, current_token)
    lineno = tokens[current_token-1].Lineshow
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected 'return'", current_token
    exp_node = None
    if tokens[current_token].Sem not in [TokenType.SEMICOLON, TokenType.ELSE, TokenType.END, TokenType.ENDWH, TokenType.FI, TokenType.THEN, TokenType.RIGHT_PAREN]:
        exp_node, error, current_token = Exp(tokens, current_token)
        if error:
            return None, error, current_token
    return ReturnNode(exp=exp_node, lineno=lineno), None, current_token


def AssCall(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected identifier", current_token
    name_node = IDNode(name=tokens[current_token - 1].Lex, lineno = tokens[current_token-1].Lineshow)
    return AssCallRest(tokens, current_token, name_node)


def AssCallRest(tokens, current_token, name_node):
    if tokens[current_token].Sem in [TokenType.DOT, TokenType.ASSIGN, TokenType.LEFT_SQUARE]:
        return AssignmentRest(tokens, current_token, name_node)
    if tokens[current_token].Sem == TokenType.LEFT_PAREN:
        return CallStmRest(tokens, current_token, name_node)
    return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected assignment or call", current_token


def AssignmentRest(tokens, current_token, name_node):
    lineno = tokens[current_token].Lineshow
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
    return AssignNode(var=var_node, exp=exp_node, lineno=lineno), None, current_token


def CallStmRest(tokens, current_token, name_node):
    matched, current_token = Match(TokenType.LEFT_PAREN, tokens, current_token)
    lineno = tokens[current_token-1].Lineshow
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected '('", current_token
    args, error, current_token = ActParamList(tokens, current_token)
    if error:
        return None, error, current_token
    matched, current_token = Match(TokenType.RIGHT_PAREN, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ')'", current_token
    return CallNode(name=name_node, args=args or [], lineno=lineno), None, current_token


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
        lineno = tokens[current_token].Lineshow
        comp_op, error, current_token = CmpOp(tokens, current_token)
        if error:
            return None, error, current_token
        right, error, current_token = Exp(tokens, current_token)
        if error:
            return None, error, current_token
        return RelExpNode(CompOp=comp_op, left=left, right=right, lineno=lineno), None, current_token
    return RelExpNode(CompOp=None, left=left, right=None, lineno = tokens[current_token-1].Lineshow), None, current_token


def Exp(tokens, current_token):
    lineno = tokens[current_token].Lineshow
    term_node, error, current_token = Term(tokens, current_token)
    if error:
        return None, error, current_token
    other_terms, error, current_token = OtherTerm(tokens, current_token)
    if error:
        return None, error, current_token
    return ExpNode(term=term_node, otherterm=other_terms or [], lineno=lineno), None, current_token


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
    lineno = tokens[current_token].Lineshow
    factor_node, error, current_token = Factor(tokens, current_token)
    if error:
        return None, error, current_token
    other_factors, error, current_token = OtherFactor(tokens, current_token)
    if error:
        return None, error, current_token
    return TermNode(factor=factor_node, otherfactor=other_factors or [], lineno=lineno), None, current_token


def OtherFactor(tokens, current_token):
    items: List[tuple[MultOpType, FactorNode]] = []
    while tokens[current_token].Sem in [TokenType.TIMES, TokenType.DIV]:
        op, error, current_token = MultOp(tokens, current_token)
        if error:
            return None, error, current_token
        factor_node, error, current_token = Term(tokens, current_token)
        if error:
            return None, error, current_token
        items.append((op, factor_node))
    return items, None, current_token


def Factor(tokens, current_token):
    if tokens[current_token].Sem == TokenType.LEFT_PAREN:
        matched, current_token = Match(TokenType.LEFT_PAREN, tokens, current_token)
        lineno = tokens[current_token-1].Lineshow
        exp_node, error, current_token = Exp(tokens, current_token)
        if error:
            return None, error, current_token
        matched, current_token = Match(TokenType.RIGHT_PAREN, tokens, current_token)
        if not matched:
            return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ')'", current_token
        return ParenExpNode(exp=exp_node, lineno=lineno), None, current_token
    if tokens[current_token].Sem == TokenType.INTC:
        matched, current_token = Match(TokenType.INTC, tokens, current_token)
        return IntConstNode(value=int(tokens[current_token - 1].Lex), lineno = tokens[current_token-1].Lineshow), None, current_token
    if tokens[current_token].Sem == TokenType.ID:
        return Variable(tokens, current_token)
    return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected factor", current_token


def Variable(tokens, current_token):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected identifier", current_token
    base = IDNode(name=tokens[current_token - 1].Lex, lineno = tokens[current_token-1].Lineshow)
    suffix, error, current_token = VariMore(tokens, current_token, base)
    if error:
        return None, error, current_token
    return suffix if suffix is not None else base, None, current_token


def VariMore(tokens, current_token, base):
    if tokens[current_token].Sem == TokenType.LEFT_SQUARE:
        matched, current_token = Match(TokenType.LEFT_SQUARE, tokens, current_token)
        lineno = tokens[current_token-1].Lineshow
        index, error, current_token = Exp(tokens, current_token)
        if error:
            return None, error, current_token
        matched, current_token = Match(TokenType.RIGHT_SQUARE, tokens, current_token)
        if not matched:
            return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ']'", current_token
        return ArrayElemNode(array=base, index=index, lineno=lineno), None, current_token
    if tokens[current_token].Sem == TokenType.DOT:
        matched, current_token = Match(TokenType.DOT, tokens, current_token)
        return FieldVar(tokens, current_token, base)
    if tokens[current_token].Sem in [TokenType.ASSIGN, TokenType.PLUS, TokenType.MINUS, TokenType.TIMES, TokenType.DIV, TokenType.SEMICOLON, TokenType.COMMA, TokenType.RIGHT_PAREN, TokenType.ELSE, TokenType.END, TokenType.ENDWH, TokenType.FI, TokenType.THEN]:
        return None, None, current_token
    return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected variable suffix", current_token


def FieldVar(tokens, current_token, record_base):
    matched, current_token = Match(TokenType.ID, tokens, current_token)
    lineno = tokens[current_token-1].Lineshow
    if not matched:
        return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected identifier", current_token
    field_id = IDNode(name=tokens[current_token - 1].Lex, lineno=lineno)
    if tokens[current_token].Sem == TokenType.LEFT_SQUARE:
        matched, current_token = Match(TokenType.LEFT_SQUARE, tokens, current_token)
        index, error, current_token = Exp(tokens, current_token)
        if error:
            return None, error, current_token
        matched, current_token = Match(TokenType.RIGHT_SQUARE, tokens, current_token)
        if not matched:
            return None, f"Line {current_line(tokens, current_token)}: Syntax error: expected ']'", current_token
        field = ArrayElemNode(array=field_id, index=index, lineno=lineno)
    else:
        field = field_id
    return RecordFieldNode(record=record_base, field=field, lineno=lineno), None, current_token


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
    type t=integer;k=char;
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