# 输入：Token序列
# 输出：语法错误检查信息和语法树
# 方法：LL(1) table驱动语法分析

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import importlib.util
import sys


def _load_stage_module(module_name: str, filename: str):
    if module_name in sys.modules:
        return sys.modules[module_name]
    module_path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


syntax = _load_stage_module("syntax", "2.recursive_descent_parser.py")
make_token = _load_stage_module("make_token", "1.lexer.py")
Token = make_token.Token
TokenType = make_token.TokenType

@dataclass
class TokenValue:
    symbol: str
    lex: str
    lineno: int

class LL1Parser:
    def __init__(self, table_path: str = 'll1_table.json'):
        with open(table_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.table: Dict[str, Any] = {k: v for k, v in data.items() if k != 'build_actions'}
        self.build_actions: Dict[str, str] = data.get('build_actions', {})
        self.tokens: List[Token] = []
        self.pos: int = 0
        self.value_terminals = {
            'ID', 'INTC', 'INTEGER', 'CHAR', 'VAR',
            'LESS', 'EQ', 'PLUS', 'MINUS', 'TIMES', 'DIV'
        }

    def token_symbol(self, tok: Token) -> str:
        mapping = {
            TokenType.LEFT_PAREN: '(', TokenType.RIGHT_PAREN: ')',
            TokenType.LEFT_SQUARE: '[', TokenType.RIGHT_SQUARE: ']',
            TokenType.SEMICOLON: ';', TokenType.DOT: '.', TokenType.LESS: '<',
            TokenType.ASSIGN: ':=', TokenType.ARRAY_LOWER: '..', TokenType.COMMA: ',',
            TokenType.PLUS: '+', TokenType.MINUS: '-', TokenType.TIMES: '*', TokenType.DIV: '/',
            TokenType.EQ: '=',
        }
        return mapping.get(tok.Sem, tok.Sem.name)

    def is_nonterminal(self, symbol: str) -> bool:
        return symbol in self.table

    def is_value_terminal(self, symbol: str) -> bool:
        return symbol in self.value_terminals

    def make_token_value(self, tok: Token) -> Optional[Any]:
        name = tok.Sem.name
        if name == 'ID':
            return syntax.IDNode(name=tok.Lex, lineno=tok.Lineshow)
        if name == 'INTC':
            return syntax.IntConstNode(value=int(tok.Lex), lineno=tok.Lineshow)
        if name in {'INTEGER', 'CHAR', 'VAR', 'LESS', 'EQ', 'PLUS', 'MINUS', 'TIMES', 'DIV'}:
            return TokenValue(symbol=name, lex=tok.Lex, lineno=tok.Lineshow)
        return None

    def choose_production(self, nonterminal: str) -> Optional[List[str]]:
        if self.pos >= len(self.tokens):
            return None
        token = self.tokens[self.pos]
        symbol = self.token_symbol(token)
        entry = self.table.get(nonterminal, {})
        prod = entry.get(symbol)
        if prod is None:
            prod = entry.get(token.Sem.name)
        return prod

    def build_nonterminal(self, nonterminal: str, children: List[Any]) -> Any:
        action = None
        action_name = self.build_actions.get(nonterminal)
        if action_name:
            action = getattr(self, action_name, None)
        if action is None:
            action = getattr(self, f'act_{nonterminal}', None)
        filtered_children = [c for c in children if c is not None]
        if action is None:
            return filtered_children[0] if len(filtered_children) == 1 else filtered_children
        return action(filtered_children)

    def first(self, children: List[Any], typ: type) -> Optional[Any]:
        return next((c for c in children if isinstance(c, typ)), None)

    def flatten_ids(self, children: List[Any]) -> List[syntax.IDNode]:
        ids: List[syntax.IDNode] = []
        for c in children:
            if isinstance(c, syntax.IDNode):
                ids.append(c)
            elif isinstance(c, list):
                ids.extend([x for x in c if isinstance(x, syntax.IDNode)])
        return ids

    def parse(self, tokens: List[Token]) -> Tuple[Optional[Any], Optional[str]]:
        self.tokens = tokens
        self.pos = 0
        parse_stack: List[Any] = ['$', 'Program']
        node_stack: List[Any] = []

        while parse_stack:
            top = parse_stack.pop()
            if top == '$':
                if self.pos < len(self.tokens) and self.tokens[self.pos].Sem == TokenType.EOF:
                    break
                current = self.tokens[self.pos] if self.pos < len(self.tokens) else None
                return None, f"Line {current.Lineshow if current is not None else 'EOF'}: unexpected extra input"

            if isinstance(top, tuple) and top[0] == 'REDUCE':
                _, nonterminal, count = top
                children = [node_stack.pop() for _ in range(count)] if count > 0 else []
                children.reverse()
                node_stack.append(self.build_nonterminal(nonterminal, children))
                continue

            if self.is_nonterminal(top):
                production = self.choose_production(top)
                if production is None:
                    current = self.tokens[self.pos] if self.pos < len(self.tokens) else None
                    symbol = self.token_symbol(current) if current is not None else 'EOF'
                    return None, f"Line {current.Lineshow if current is not None else 'EOF'}: LL(1) parse error at {symbol} for {top}"
                parse_stack.append(('REDUCE', top, len(production)))
                for symbol in reversed(production):
                    parse_stack.append(symbol)
                continue

            if self.pos >= len(self.tokens):
                return None, 'Line EOF: unexpected end of input'

            current_token = self.tokens[self.pos]
            current_symbol = self.token_symbol(current_token)
            if top == current_symbol or top == current_token.Sem.name:
                value = self.make_token_value(current_token) if self.is_value_terminal(top) or self.is_value_terminal(current_token.Sem.name) else None
                node_stack.append(value)
                self.pos += 1
                continue

            return None, f"Line {current_token.Lineshow}: expected {top}, got {current_symbol}"

        if len(node_stack) != 1:
            return None, 'Internal parse error: AST stack has wrong size'
        return node_stack[0], None

    def act_Program(self, children: List[Any]):
        head = self.first(children, syntax.ProgramHeadNode)
        declare = self.first(children, syntax.DeclareNode)
        body = self.first(children, syntax.ProgramBodyNode)
        lineno = head.lineno if head else 0
        return syntax.ProgramNode(ProgramHead=head, Declare=declare, StmL=body, lineno=lineno)

    def act_ProgramHead(self, children: List[Any]):
        name = self.first(children, syntax.IDNode)
        return syntax.ProgramHeadNode(name=name, lineno=name.lineno if name else 0)

    def act_ProgramName(self, children: List[Any]):
        return self.first(children, syntax.IDNode)

    def act_DeclarePart(self, children: List[Any]):
        type_dec = self.first(children, syntax.TypeDecHeadNode)
        var_dec = self.first(children, syntax.VarDecHeadNode)
        proc_dec = self.first(children, syntax.ProcDecHeadNode)
        lineno = (type_dec.lineno if type_dec else
                  var_dec.lineno if var_dec else
                  proc_dec.lineno if proc_dec else 0)
        return syntax.DeclareNode(type_dec_head=type_dec, var_dec_head=var_dec, proc_dec_head=proc_dec, lineno=lineno)

    def act_TypeDecpart(self, children: List[Any]):
        return children[0] if children else None

    def act_VarDecpart(self, children: List[Any]):
        return children[0] if children else None

    def act_ProcDecpart(self, children: List[Any]):
        return children[0] if children else None

    def act_TypeDec(self, children: List[Any]):
        nodes = next((c for c in children if isinstance(c, list) and c and isinstance(c[0], syntax.TypeDecNode)), [])
        return syntax.TypeDecHeadNode(nodes=nodes, lineno=(nodes[0].lineno if nodes else 0))

    def act_TypeDecList(self, children: List[Any]):
        identifier = self.first(children, syntax.IDNode)
        type_def = self.first(children, syntax.TypeNode)
        rest = next((c for c in children if isinstance(c, list) and c and isinstance(c[0], syntax.TypeDecNode)), [])
        node = syntax.TypeDecNode(name=identifier, type_def=type_def, lineno=identifier.lineno if identifier else 0)
        return [node] + rest

    def act_TypeDecMore(self, children: List[Any]):
        return children[0] if children else []

    def act_TypeId(self, children: List[Any]):
        return self.first(children, syntax.IDNode)

    def act_TypeDef(self, children: List[Any]):
        child = children[0] if children else None
        if isinstance(child, syntax.IDNode):
            return syntax.NamedTypeNode(name=child, lineno=child.lineno)
        return child

    def act_BaseType(self, children: List[Any]):
        token = children[0] if children else None
        kind = syntax.TypeKind.INTEGER if getattr(token, 'symbol', None) == 'INTEGER' else syntax.TypeKind.CHAR
        return syntax.BaseTypeNode(kind=kind, lineno=token.lineno if token else 0)

    def act_StructureType(self, children: List[Any]):
        return children[0] if children else None

    def act_ArrayType(self, children: List[Any]):
        low = next((c for c in children if isinstance(c, syntax.IntConstNode)), None)
        ups = [c for c in children if isinstance(c, syntax.IntConstNode) and c is not low]
        up = ups[0] if ups else None
        base_type = self.first(children, syntax.TypeNode)
        return syntax.ArrayTypeNode(low=low, up=up, base_type=base_type, lineno=low.lineno if low else 0)

    def act_RecType(self, children: List[Any]):
        fields = next((c for c in children if isinstance(c, list)), [])
        return syntax.RecordTypeNode(fields=fields, lineno=(fields[0].lineno if fields else 0))

    def act_FieldDecList(self, children: List[Any]):
        type_node = self.first(children, syntax.TypeNode)
        ids = self.flatten_ids(children)
        rest = next((c for c in children if isinstance(c, list) and c and isinstance(c[0], syntax.VarDecNode)), [])
        nodes = [syntax.VarDecNode(type=type_node, name=id_node, lineno=id_node.lineno) for id_node in ids]
        return nodes + rest

    def act_FieldDecMore(self, children: List[Any]) -> Any:
        return children[0] if children else []

    def act_IdList(self, children: List[Any]) -> Any:
        return self.flatten_ids(children)

    def act_IdMore(self, children: List[Any]):
        return children[0] if children else []

    def act_VarDec(self, children: List[Any]):
        nodes = next((c for c in children if isinstance(c, list) and c and isinstance(c[0], syntax.VarDecNode)), [])
        return syntax.VarDecHeadNode(nodes=nodes, lineno=(nodes[0].lineno if nodes else 0))

    def act_VarDecList(self, children: List[Any]):
        type_node = self.first(children, syntax.TypeNode)
        ids = self.flatten_ids(children)
        rest = next((c for c in children if isinstance(c, list) and c and isinstance(c[0], syntax.VarDecNode)), [])
        nodes = [syntax.VarDecNode(type=type_node, name=id_node, lineno=id_node.lineno) for id_node in ids]
        return nodes + rest

    def act_VarDecMore(self, children: List[Any]) -> Any:
        return children[0] if children else []

    def act_VarIdList(self, children: List[Any]) -> Any:
        return self.flatten_ids(children)

    def act_VarIdMore(self, children: List[Any]):
        return children[0] if children else []

    def act_ProcDec(self, children: List[Any]):
        name = self.first(children, syntax.IDNode)
        params = next((c for c in children if isinstance(c, list) and c and isinstance(c[0], syntax.ParamNode)), [])
        declare = self.first(children, syntax.DeclareNode)
        body = self.first(children, syntax.ProgramBodyNode)
        return syntax.ProcDecNode(name=name, params=params, declare=declare, body=body, lineno=name.lineno if name else 0)

    def act_ProcDecMore(self, children: List[Any]):
        return children[0] if children else []

    def act_ProcName(self, children: List[Any]):
        return self.first(children, syntax.IDNode)

    def act_ParamList(self, children: List[Any]):
        return children[0] if children else []

    def act_Param(self, children: List[Any]):
        if not children:
            return None
        if getattr(children[0], 'symbol', None) == 'VAR':
            type_node = children[1]
            names = children[2] if len(children) > 2 else []
            return syntax.ParamNode(type=type_node, names=names, is_var=True, lineno=type_node.lineno if type_node else 0)
        type_node = children[0]
        names = children[1] if len(children) > 1 else []
        return syntax.ParamNode(type=type_node, names=names, is_var=False, lineno=type_node.lineno if type_node else 0)

    def act_ParamMore(self, children: List[Any]):
        return children[0] if children else []

    def act_FormList(self, children: List[Any]):
        if not children:
            return []
        if len(children) == 1:
            return [children[0]] if isinstance(children[0], syntax.IDNode) else children[0]
        return [children[0]] + (children[1] if isinstance(children[1], list) else [])

    def act_FidMore(self, children: List[Any]):
        return children[0] if children else []

    def act_ProcDecPart(self, children: List[Any]):
        return children[0] if children else None

    def act_ProcBody(self, children: List[Any]):
        return children[0] if children else None

    def act_ProgramBody(self, children: List[Any]):
        stmts = children[0] if children else []
        return syntax.ProgramBodyNode(children_list=stmts, lineno=(stmts[0].lineno if stmts else 0))

    def act_StmList(self, children: List[Any]):
        if not children:
            return []
        return [children[0]] + (children[1] if len(children) > 1 else [])

    def act_StmMore(self, children: List[Any]):
        return children[0] if children else []

    def act_Stm(self, children: List[Any]):
        return children[0] if children else None

    def act_ConditionalStm(self, children: List[Any]):
        condition = self.first(children, syntax.RelExpNode)
        then_stmt = children[1] if len(children) > 1 else []
        else_stmt = children[2] if len(children) > 2 else []
        return syntax.IfNode(condition=condition, then_stm=then_stmt or [], else_stm=else_stmt or [], lineno=(condition.lineno if condition else 0))

    def act_LoopStm(self, children: List[Any]):
        condition = self.first(children, syntax.RelExpNode)
        body = children[1] if len(children) > 1 else []
        return syntax.WhileNode(condition=condition, body=body or [], lineno=(condition.lineno if condition else 0))

    def act_InputStm(self, children: List[Any]):
        var = self.first(children, syntax.IDNode)
        return syntax.ReadNode(var=var, lineno=(var.lineno if var else 0))

    def act_OutputStm(self, children: List[Any]):
        exp = self.first(children, syntax.ExpNode)
        return syntax.WriteNode(exp=exp, lineno=(exp.lineno if exp else 0))

    def act_ReturnStm(self, children: List[Any]):
        return syntax.ReturnNode(exp=None, lineno=0)

    def act_IDAssCall(self, children: List[Any]):
        name = self.first(children, syntax.IDNode)
        action = children[1] if len(children) > 1 else None
        if isinstance(action, tuple) and action[0] == 'ASSIGN':
            suffix, exp = action[1], action[2]
            if suffix is None:
                target = name
            elif suffix[0] == 'ARRAY':
                target = syntax.ArrayElemNode(array=name, index=suffix[1], lineno=name.lineno)
            else:
                target = syntax.RecordFieldNode(record=name, field=suffix[1], lineno=name.lineno)
            return syntax.AssignNode(var=target, exp=exp, lineno=(exp.lineno if exp else name.lineno))
        if isinstance(action, tuple) and action[0] == 'CALL':
            return syntax.CallNode(name=name, args=action[1] or [], lineno=name.lineno if name else 0)
        return None

    def act_AssCall(self, children: List[Any]):
        return children[0] if children else None

    def act_AssignmentRest(self, children: List[Any]):
        if len(children) == 1 and isinstance(children[0], syntax.ExpNode):
            return ('ASSIGN', None, children[0])
        return ('ASSIGN', children[0] if children else None, children[1] if len(children) > 1 else None)

    def act_CallStmRest(self, children: List[Any]):
        return ('CALL', children[0] if children else [])

    def act_VariMore(self, children: List[Any]):
        if not children:
            return None
        if isinstance(children[0], syntax.ExpNode):
            return ('ARRAY', children[0])
        return ('FIELD', children[0])

    def act_FieldVar(self, children: List[Any]):
        if len(children) == 1:
            return children[0]
        suffix = children[1]
        if isinstance(suffix, syntax.ExpNode):
            return syntax.ArrayElemNode(array=children[0], index=suffix, lineno=children[0].lineno)
        return children[0]

    def act_FieldVarMore(self, children: List[Any]):
        return children[0] if children else None

    def act_CmpOp(self, children: List[Any]):
        token = children[0]
        if getattr(token, 'symbol', None) == 'LESS':
            return syntax.CompOpType.LT
        return syntax.CompOpType.EQ

    def act_AddOp(self, children: List[Any]):
        token = children[0]
        return syntax.AddOpType.PLUS if getattr(token, 'symbol', None) == 'PLUS' else syntax.AddOpType.MINUS

    def act_MultOp(self, children: List[Any]):
        token = children[0]
        return syntax.MultOpType.TIMES if getattr(token, 'symbol', None) == 'TIMES' else syntax.MultOpType.DIV

    def act_OtherRelE(self, children: List[Any]):
        if not children:
            return None
        return (children[0], children[1])

    def act_RelExp(self, children: List[Any]):
        if len(children) == 1:
            return syntax.RelExpNode(CompOp=None, left=children[0], right=None, lineno=children[0].lineno)
        op, right = children[1]
        return syntax.RelExpNode(CompOp=op, left=children[0], right=right, lineno=children[0].lineno)

    def act_OtherTerm(self, children: List[Any]):
        if not children:
            return []
        op = children[0]
        exp = children[1]
        return [(op, exp.term)] + exp.otherterm

    def act_Exp(self, children: List[Any]):
        return syntax.ExpNode(term=children[0], otherterm=children[1] if len(children) > 1 else [], lineno=children[0].lineno)

    def act_OtherFactor(self, children: List[Any]):
        if not children:
            return []
        op = children[0]
        term = children[1]
        return [(op, term.factor)] + term.otherfactor

    def act_Term(self, children: List[Any]):
        return syntax.TermNode(factor=children[0], otherfactor=children[1] if len(children) > 1 else [], lineno=children[0].lineno)

    def act_Factor(self, children: List[Any]):
        return children[0] if children else None

    def act_Variable(self, children: List[Any]):
        if len(children) == 1:
            return children[0]
        suffix = children[1]
        if suffix is None:
            return children[0]
        if suffix[0] == 'ARRAY':
            return syntax.ArrayElemNode(array=children[0], index=suffix[1], lineno=children[0].lineno)
        return syntax.RecordFieldNode(record=children[0], field=suffix[1], lineno=children[0].lineno)

    def act_ActParamList(self, children: List[Any]):
        if not children:
            return []
        return [children[0]] + (children[1] if len(children) > 1 else [])

    def act_ActParamMore(self, children: List[Any]):
        return children[0] if children else []

    def act_Invar(self, children: List[Any]):
        return children[0] if children else None

    def act_Stm(self, children: List[Any]):
        return children[0] if children else None


def Program(tokens: List[Token]) -> Tuple[Optional[Any], Optional[str]]:
    parser = LL1Parser('ll1_table.json')
    return parser.parse(tokens)
