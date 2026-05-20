# 中间代码生成
# 输入：语法树，符号表
# 输出：四元式列表，更新后的符号表

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Tuple

import recursive_descent_parser as syntax
import semantic_analyzer


class Operation(Enum):
    ADD = auto()        # Arg3 = Arg1 + Arg2
    SUB = auto()        # Arg3 = Arg1 - Arg2
    MULT = auto()       # Arg3 = Arg1 * Arg2
    DIV = auto()        # Arg3 = Arg1 / Arg2
    EQC = auto()        # Arg3 = Arg1 == Arg2
    LTC = auto()        # Arg3 = Arg1 < Arg2
    READC = auto()      # read Arg1
    WRITEC = auto()     # write Arg1
    RETURNC = auto()    # return Arg1
    ASSIG = auto()      # Arg1 = Arg2
    AADD = auto()       # Arg3 = address(Arg1) + Arg2
    LABEL = auto()      # label Arg1
    JUMP = auto()       # goto Arg1
    JUMP0 = auto()      # if Arg1 == 0 goto Arg2
    CALL = auto()       # call Arg1
    VARACT = auto()     # var argument
    VALACT = auto()     # value argument
    PENTRY = auto()     # procedure entry
    ENDPENTRY = auto()  # procedure exit
    MENTRY = auto()     # main entry


class FormKind(Enum):
    ValueForm = auto()
    LabelForm = auto()
    AddrForm = auto()
    TextForm = auto()


@dataclass
class ARG:
    form: FormKind


@dataclass
class ValueARG(ARG):
    value: int

    def __init__(self, value: int):
        super().__init__(FormKind.ValueForm)
        self.value = value


@dataclass
class LabelARG(ARG):
    value: str

    def __init__(self, value: str):
        super().__init__(FormKind.LabelForm)
        self.value = value


@dataclass
class AddrARG(ARG):
    idx: int
    name: str
    level: int
    off: int
    access: bool

    def __init__(self, idx: int, name: str, level: int, off: int, access: bool):
        super().__init__(FormKind.AddrForm)
        self.idx = idx
        self.name = name
        self.level = level
        self.off = off
        self.access = access


@dataclass
class TextARG(ARG):
    text: str

    def __init__(self, text: str):
        super().__init__(FormKind.TextForm)
        self.text = text


@dataclass
class Quadruple:
    codekind: Operation
    Arg1: Optional[ARG] = None
    Arg2: Optional[ARG] = None
    Arg3: Optional[ARG] = None

    def __str__(self) -> str:
        return f"({self.codekind.name}, {format_arg(self.Arg1)}, {format_arg(self.Arg2)}, {format_arg(self.Arg3)})"


def format_arg(arg: Optional[ARG]) -> str:
    if arg is None:
        return "_"
    if isinstance(arg, ValueARG):
        return str(arg.value)
    if isinstance(arg, LabelARG):
        return arg.value
    if isinstance(arg, AddrARG):
        return f"{arg.name}#{arg.idx}"
    if isinstance(arg, TextARG):
        return arg.text
    return str(arg)


class IntermediateCodeGenerator:
    def __init__(self, symtab: semantic_analyzer.symbol_table):
        self.symtab = symtab
        self.quads: List[Quadruple] = []
        self.temp_count = 0
        self.label_count = 0
        self.current_level = 0

    def generate(self, program: syntax.ProgramNode) -> Tuple[List[Quadruple], semantic_analyzer.symbol_table]:
        self.emit(Operation.MENTRY, None, ValueARG(0), ValueARG(0))
        if program.Declare and program.Declare.proc_dec_head:
            for proc_decl in program.Declare.proc_dec_head.nodes:
                self.gen_procedure(proc_decl)
        if program.StmL:
            self.gen_body(program.StmL)
        return self.quads, self.symtab

    def emit(self, op: Operation, arg1: Optional[ARG] = None, arg2: Optional[ARG] = None, arg3: Optional[ARG] = None) -> int:
        self.quads.append(Quadruple(op, arg1, arg2, arg3))
        return len(self.quads) - 1

    def new_label(self) -> LabelARG:
        self.label_count += 1
        return LabelARG(f"L{self.label_count}")

    def new_temp(self, type_ptr: Optional[semantic_analyzer.Ptr] = None) -> AddrARG:
        self.temp_count += 1
        name = f"_t{self.temp_count}"
        if type_ptr is None:
            type_ptr = semantic_analyzer.Ptr(kind=semantic_analyzer.Typekind.intTy, size=1)
        temp_sym = semantic_analyzer.VarSym(
            TypePtr=type_ptr,
            kind=semantic_analyzer.SymKind.varKind,
            name=name,
            Access=True,
            Level=self.current_level,
            Off=0,
        )
        idx = self.symtab.add_var(temp_sym)
        return AddrARG(idx=idx, name=name, level=temp_sym.Level, off=temp_sym.Off, access=temp_sym.Access)

    def lookup_var_arg(self, name: str) -> AddrARG:
        candidates = []
        for idx in self.symtab.get_all_idx(name):
            entry = self.symtab.get_var(idx)
            if entry is not None and entry.Level <= self.current_level:
                candidates.append(entry)
        if not candidates:
            idx = self.symtab.get_var_idx(name)
            entry = self.symtab.get_var(idx) if idx is not None else None
        else:
            entry = max(candidates, key=lambda item: item.Level)
        if entry is None or entry.idx is None:
            raise ValueError(f"variable '{name}' is not in symbol table")
        return AddrARG(idx=entry.idx, name=entry.name, level=entry.Level, off=entry.Off, access=entry.Access)

    def gen_procedure(self, proc_decl: syntax.ProcDecNode) -> None:
        old_level = self.current_level
        self.current_level = old_level + 1
        proc_name = proc_decl.name.name if proc_decl.name else "<anonymous>"
        entry_label = self.new_label()
        self.emit(Operation.PENTRY, entry_label, TextARG(proc_name), ValueARG(self.current_level))
        if proc_decl.body:
            self.gen_body(proc_decl.body)
        self.emit(Operation.ENDPENTRY, TextARG(proc_name))
        self.current_level = old_level

    def gen_body(self, body: syntax.ProgramBodyNode) -> None:
        for stmt in body.children_list:
            self.gen_statement(stmt)

    def gen_statement(self, stmt: syntax.StmtNode) -> None:
        if isinstance(stmt, syntax.ReadNode):
            self.emit(Operation.READC, self.gen_variable_addr(stmt.var))
            return
        if isinstance(stmt, syntax.WriteNode):
            self.emit(Operation.WRITEC, self.gen_expression(stmt.exp))
            return
        if isinstance(stmt, syntax.AssignNode):
            target = self.gen_variable_addr(stmt.var)
            value = self.gen_expression(stmt.exp)
            self.emit(Operation.ASSIG, target, value)
            return
        if isinstance(stmt, syntax.IfNode):
            self.gen_if(stmt)
            return
        if isinstance(stmt, syntax.WhileNode):
            self.gen_while(stmt)
            return
        if isinstance(stmt, syntax.CallNode):
            self.gen_call(stmt)
            return
        if isinstance(stmt, syntax.ReturnNode):
            value = self.gen_expression(stmt.exp) if stmt.exp else None
            self.emit(Operation.RETURNC, value)
            return
        self.emit(Operation.RETURNC, TextARG(f"unsupported statement: {type(stmt).__name__}"))

    def gen_if(self, stmt: syntax.IfNode) -> None:
        else_label = self.new_label()
        end_label = self.new_label()
        cond = self.gen_expression(stmt.condition)
        self.emit(Operation.JUMP0, cond, else_label)
        for child in stmt.then_stm:
            self.gen_statement(child)
        self.emit(Operation.JUMP, end_label)
        self.emit(Operation.LABEL, else_label)
        for child in stmt.else_stm:
            self.gen_statement(child)
        self.emit(Operation.LABEL, end_label)

    def gen_while(self, stmt: syntax.WhileNode) -> None:
        start_label = self.new_label()
        end_label = self.new_label()
        self.emit(Operation.LABEL, start_label)
        cond = self.gen_expression(stmt.condition)
        self.emit(Operation.JUMP0, cond, end_label)
        for child in stmt.body:
            self.gen_statement(child)
        self.emit(Operation.JUMP, start_label)
        self.emit(Operation.LABEL, end_label)

    def gen_call(self, stmt: syntax.CallNode) -> None:
        for arg in stmt.args:
            if isinstance(arg, (syntax.IDNode, syntax.ArrayElemNode, syntax.RecordFieldNode)):
                self.emit(Operation.VARACT, self.gen_variable_addr(arg))
            else:
                self.emit(Operation.VALACT, self.gen_expression(arg))
        self.emit(Operation.CALL, TextARG(stmt.name.name))

    def gen_expression(self, node) -> ARG:
        if isinstance(node, syntax.RelExpNode):
            left = self.gen_expression(node.left)
            if node.right is None:
                return left
            right = self.gen_expression(node.right)
            result = self.new_temp()
            op = Operation.LTC if node.CompOp == syntax.CompOpType.LT else Operation.EQC
            self.emit(op, left, right, result)
            return result

        if isinstance(node, syntax.ExpNode):
            result = self.gen_expression(node.term)
            for op_kind, term in node.otherterm:
                right = self.gen_expression(term)
                temp = self.new_temp()
                op = Operation.ADD if op_kind == syntax.AddOpType.PLUS else Operation.SUB
                self.emit(op, result, right, temp)
                result = temp
            return result

        if isinstance(node, syntax.TermNode):
            result = self.gen_expression(node.factor)
            for op_kind, factor in node.otherfactor:
                right = self.gen_expression(factor)
                temp = self.new_temp()
                op = Operation.MULT if op_kind == syntax.MultOpType.TIMES else Operation.DIV
                self.emit(op, result, right, temp)
                result = temp
            return result

        if isinstance(node, syntax.ParenExpNode):
            return self.gen_expression(node.exp)
        if isinstance(node, syntax.IntConstNode):
            return ValueARG(node.value)
        if isinstance(node, syntax.CharConstNode):
            return TextARG(repr(node.value))
        if isinstance(node, (syntax.IDNode, syntax.ArrayElemNode, syntax.RecordFieldNode)):
            return self.gen_variable_addr(node)

        raise ValueError(f"unsupported expression node: {type(node).__name__}")

    def gen_variable_addr(self, node) -> ARG:
        if isinstance(node, syntax.IDNode):
            return self.lookup_var_arg(node.name)

        if isinstance(node, syntax.ArrayElemNode):
            base = self.lookup_var_arg(node.array.name)
            index = self.gen_expression(node.index)
            result = self.new_temp()
            self.emit(Operation.AADD, base, index, result)
            return result

        if isinstance(node, syntax.RecordFieldNode):
            record = self.lookup_var_arg(node.record.name)
            field_text = self._field_to_text(node.field)
            return TextARG(f"{format_arg(record)}.{field_text}")

        raise ValueError(f"unsupported variable node: {type(node).__name__}")

    def _field_to_text(self, field) -> str:
        if isinstance(field, syntax.IDNode):
            return field.name
        if isinstance(field, syntax.ArrayElemNode):
            index = self.gen_expression(field.index)
            return f"{field.array.name}[{format_arg(index)}]"
        return str(field)


def generate_intermediate_code(
    program: syntax.ProgramNode,
    symtab: semantic_analyzer.symbol_table,
) -> Tuple[List[Quadruple], semantic_analyzer.symbol_table]:
    generator = IntermediateCodeGenerator(symtab)
    return generator.generate(program)


def print_quadruples(quads: List[Quadruple]) -> None:
    for index, quad in enumerate(quads):
        print(f"{index:03}: {quad}")
