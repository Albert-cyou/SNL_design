# 语义分析
# 输入：语法树
# 输出：语义错误信息
# 数据结构：语法树，符号表

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum, auto
import syntax


# kind，表示标识符的类别
class SymKind(Enum):
    typeKind = auto()
    varKind  = auto()
    procKind = auto()

# 类型
class Typekind(Enum):
    intTy    = auto()
    charTy   = auto()
    arrayTy  = auto()
    recordTy = auto()
    voidTy   = auto()
    boolTy   = auto()

# 内部表示基类
@dataclass
class Ptr:
    kind: Typekind
    size: int = 1

# 数组内部表示
@dataclass
class arrayPtr:
    kind: Typekind = Typekind.arrayTy
    indexTy: Ptr = None  # 下标类型的内部表示
    elemTy: Ptr = None   # 元素类型的内部表示
    size: int = 1

# 记录类型的内部表示
@dataclass
class recordPtr:
    kind: Typekind = Typekind.recordTy
    body: List['RecordField'] = field(default_factory=list)
    size: int = 1

# 记录域类型
@dataclass
class RecordField:
    idname: str = ""
    typePtr: Ptr = None
    offset: int = 0


# 符号表项基类
@dataclass
class Symbol():
    TypePtr: Ptr
    kind: SymKind
    name: str = field(default="", kw_only=True)

# 类型标识符
@dataclass
class TypeSym(Symbol):
    kind: SymKind.typeKind

# 变量标识符
@dataclass
class VarSym(Symbol):
    kind: SymKind.varKind
    Access: bool  # True 为直接变量， False为间接变量
    Level: int # 层数
    Off: int # 偏移

# 过程标识符
@dataclass
class ProcSym(Symbol):
    kind: SymKind.procKind
    Level: int
    Parm:  List[int] # 形参信息表，存储形参在符号表内的位置
    size: int
    code: int # 目标代码地址

# 符号表
@dataclass
class symbol_table():
    Type: List[TypeSym] = field(default_factory=list)
    Var : List[VarSym] = field(default_factory=list)
    proc: List[ProcSym] = field(default_factory=list)

    def get(self, pos):
        if pos <= len(self.Type):
            return self.Type[pos]
        elif pos > len(self.Type) and pos <= len(self.Type) + len(self.Var):
            return self.Var[pos - len(self.Type)]
        elif pos > len(self.Type) + len(self.Var) and pos <= len(self.Type) + len(self.Var) + len(self.proc):
            return self.proc[pos - len(self.Type) - len(self.Var)]
        else:
            return None

    def _ptr_to_str(self, ptr: Ptr) -> str:
        if ptr is None:
            return "None"
        if isinstance(ptr, arrayPtr):
            return f"array[{ptr.indexTy.kind.name}]{ptr.size} of {self._ptr_to_str(ptr.elemTy)}"
        if isinstance(ptr, recordPtr):
            fields = ", ".join([f"{f.idname}:{f.typePtr.kind.name}@{f.offset}" for f in ptr.body])
            return f"record{{{fields}}}[{ptr.size}]"
        return ptr.kind.name

    def print_table(self) -> None:
        def render_rows(rows: List[List[str]]) -> None:
            widths = [max(len(cell) for cell in column) for column in zip(*rows)]
            sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
            print(sep)
            header = rows[0]
            print("| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(header)) + " |")
            print(sep)
            for row in rows[1:]:
                print("| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)) + " |")
            print(sep)

        if self.Type:
            rows = [["Idx", "Name", "Kind", "Type", "Size"]]
            for idx, entry in enumerate(self.Type):
                rows.append([
                    str(idx),
                    entry.name,
                    entry.kind.name,
                    self._ptr_to_str(entry.TypePtr),
                    str(entry.TypePtr.size)
                ])
            print("Type Symbols:")
            render_rows(rows)
            print()

        if self.Var:
            rows = [["Idx", "Name", "Kind", "Type", "Size", "Access", "Level", "Off"]]
            for idx, entry in enumerate(self.Var):
                rows.append([
                    str(idx),
                    entry.name,
                    entry.kind.name,
                    self._ptr_to_str(entry.TypePtr),
                    str(entry.TypePtr.size),
                    "direct" if entry.Access else "indirect",
                    str(entry.Level),
                    str(entry.Off)
                ])
            print("Variable Symbols:")
            render_rows(rows)
            print()

        if self.proc:
            rows = [["Idx", "Name", "Kind", "Type", "Parms", "Level", "Size", "Code"]]
            for idx, entry in enumerate(self.proc):
                parm_str = ",".join(str(p) for p in entry.Parm)
                rows.append([
                    str(idx),
                    entry.name,
                    entry.kind.name,
                    self._ptr_to_str(entry.TypePtr),
                    parm_str,
                    str(entry.Level),
                    str(entry.size),
                    str(entry.code)
                ])
            print("Procedure Symbols:")
            render_rows(rows)
            print()


def _type_node_to_ptr(type_node: syntax.TypeNode, type_map: Dict[str, Ptr]) -> Ptr:
    if isinstance(type_node, syntax.BaseTypeNode):
        if type_node.kind == syntax.TypeKind.INTEGER:
            return Ptr(size=1, kind=Typekind.intTy)
        if type_node.kind == syntax.TypeKind.CHAR:
            return Ptr(size=1, kind=Typekind.charTy)

    if isinstance(type_node, syntax.ArrayTypeNode):
        elem_ptr = _type_node_to_ptr(type_node.base_type, type_map)
        low = type_node.low.value
        up = type_node.up.value
        count = max(0, up - low + 1)
        return arrayPtr(size=elem_ptr.size * count, indexTy=Ptr(size=1, kind=Typekind.intTy), elemTy=elem_ptr)

    if isinstance(type_node, syntax.RecordTypeNode):
        fields: List[RecordField] = []
        offset = 0
        for field_decl in type_node.fields:
            field_type = _type_node_to_ptr(field_decl.type, type_map)
            names = field_decl.name if isinstance(field_decl.name, list) else [field_decl.name]
            for name_node in names:
                fields.append(RecordField(idname=name_node.name, typePtr=field_type, offset=offset))
                offset += field_type.size
        return recordPtr(size=offset, body=fields)

    if isinstance(type_node, syntax.NamedTypeNode):
        name = type_node.name.name
        if name in type_map:
            return type_map[name]
        placeholder = Ptr(size=1, kind=Typekind.intTy)
        type_map[name] = placeholder
        return placeholder

    raise ValueError(f"Unsupported type node: {type(type_node).__name__}")


def _add_var_declaration(var_decl: syntax.VarDecNode, symtab: symbol_table, type_map: Dict[str, Ptr], level: int, access: bool = True) -> None:
    var_type = _type_node_to_ptr(var_decl.type, type_map)
    names = []
    if isinstance(var_decl.name, list):
        names = var_decl.name
    elif var_decl.name is not None:
        names = [var_decl.name]

    for name_node in names:
        symtab.Var.append(VarSym(
            TypePtr=var_type,
            kind=SymKind.varKind,
            name=name_node.name,
            Access=access,
            Level=level,
            Off=0
        ))


def _add_procedure(proc_decl: syntax.ProcDecNode, symtab: symbol_table, type_map: Dict[str, Ptr], level: int) -> None:
    param_positions: List[int] = []
    for param in proc_decl.params:
        param_type = _type_node_to_ptr(param.type, type_map)
        for name_node in param.names:
            symtab.Var.append(VarSym(
                name=name_node.name,
                TypePtr=param_type,
                kind=SymKind.varKind,
                Access=not param.is_var,
                Level=level + 1,
                Off=0
            ))
            param_positions.append(len(symtab.Type) + len(symtab.Var) - 1)

    proc_sym = ProcSym(
        TypePtr=Ptr(size=0, kind=Typekind.voidTy),
        kind=SymKind.procKind,
        name=proc_decl.name.name if proc_decl.name else "",
        Level=level,
        Parm=param_positions,
        size=0,
        code=-1
    )
    symtab.proc.append(proc_sym)

    if proc_decl.declare:
        _populate_declare(proc_decl.declare, symtab, type_map, level + 1)


def _populate_declare(declare: syntax.DeclareNode, symtab: symbol_table, type_map: Dict[str, Ptr], level: int) -> None:
    if declare.type_dec_head:
        for type_decl in declare.type_dec_head.nodes:
            type_ptr = _type_node_to_ptr(type_decl.type_def, type_map)
            symtab.Type.append(TypeSym(TypePtr=type_ptr, kind=SymKind.typeKind, name=type_decl.name.name))
            type_map[type_decl.name.name] = type_ptr

    if declare.var_dec_head:
        for var_decl in declare.var_dec_head.nodes:
            _add_var_declaration(var_decl, symtab, type_map, level)

    if declare.proc_dec_head:
        for proc_decl in declare.proc_dec_head.nodes:
            _add_procedure(proc_decl, symtab, type_map, level)


def build_symbol_table(program: syntax.ProgramNode) -> symbol_table:
    symtab = symbol_table()
    type_map: Dict[str, Ptr] = {}
    if program.Declare:
        _populate_declare(program.Declare, symtab, type_map, level=0)
    return symtab


@dataclass
class SemanticScope:
    types: Dict[str, Ptr] = field(default_factory=dict)
    vars: Dict[str, VarSym] = field(default_factory=dict)
    procs: Dict[str, syntax.ProcDecNode] = field(default_factory=dict)
    parent: Optional['SemanticScope'] = None

    def lookup_type(self, name: str) -> Optional[Ptr]:
        scope = self
        while scope:
            if name in scope.types:
                return scope.types[name]
            scope = scope.parent
        return None

    def lookup_var(self, name: str) -> Optional[VarSym]:
        scope = self
        while scope:
            if name in scope.vars:
                return scope.vars[name]
            scope = scope.parent
        return None

    def lookup_proc(self, name: str) -> Optional[syntax.ProcDecNode]:
        scope = self
        while scope:
            if name in scope.procs:
                return scope.procs[name]
            scope = scope.parent
        return None

    def has_name(self, name: str) -> bool:
        return name in self.types or name in self.vars or name in self.procs


def _type_to_string(ptr: Ptr) -> str:
    if ptr is None:
        return "None"
    if isinstance(ptr, arrayPtr):
        return f"array[{ptr.indexTy.kind.name}]{ptr.size} of {_type_to_string(ptr.elemTy)}"
    if isinstance(ptr, recordPtr):
        fields = ", ".join([f"{f.idname}:{f.typePtr.kind.name}@{f.offset}" for f in ptr.body])
        return f"record{{{fields}}}[{ptr.size}]"
    return ptr.kind.name


def _same_type(left: Ptr, right: Ptr) -> bool:
    if left is None or right is None:
        return False
    if type(left) != type(right):
        return False
    if isinstance(left, arrayPtr) and isinstance(right, arrayPtr):
        return _same_type(left.elemTy, right.elemTy)
    if isinstance(left, recordPtr) and isinstance(right, recordPtr):
        if len(left.body) != len(right.body):
            return False
        for lf, rf in zip(left.body, right.body):
            if lf.idname != rf.idname or not _same_type(lf.typePtr, rf.typePtr):
                return False
        return True
    return left.kind == right.kind


def _report_error(errors: List[str], node: Any, message: str) -> None:
    lineno = getattr(node, "lineno", 0)
    errors.append(f"Line {lineno}: {message}")


def _resolve_type(type_node: syntax.TypeNode, scope: SemanticScope, errors: List[str]) -> Optional[Ptr]:
    if isinstance(type_node, syntax.BaseTypeNode):
        if type_node.kind == syntax.TypeKind.INTEGER:
            return Ptr(kind=Typekind.intTy, size=1)
        if type_node.kind == syntax.TypeKind.CHAR:
            return Ptr(kind=Typekind.charTy, size=1)

    if isinstance(type_node, syntax.ArrayTypeNode):
        low = type_node.low.value
        up = type_node.up.value
        if up <= low:
            _report_error(errors, type_node, f"array upper bound must be greater than lower bound: {low}..{up}")
        elem_type = _resolve_type(type_node.base_type, scope, errors)
        if elem_type is None:
            return None
        count = max(0, up - low + 1)
        return arrayPtr(indexTy=Ptr(kind=Typekind.intTy, size=1), elemTy=elem_type, size=elem_type.size * count)

    if isinstance(type_node, syntax.RecordTypeNode):
        fields: List[RecordField] = []
        offset = 0
        for field_decl in type_node.fields:
            field_type = _resolve_type(field_decl.type, scope, errors)
            if field_type is None:
                field_type = Ptr(kind=Typekind.intTy, size=1)
            names = field_decl.name if isinstance(field_decl.name, list) else [field_decl.name]
            for name_node in names:
                fields.append(RecordField(idname=name_node.name, typePtr=field_type, offset=offset))
                offset += field_type.size
        return recordPtr(body=fields, size=offset)

    if isinstance(type_node, syntax.NamedTypeNode):
        type_name = type_node.name.name
        target = scope.lookup_type(type_name)
        if target is None:
            _report_error(errors, type_node, f"undefined type '{type_name}'")
            return None
        return target

    _report_error(errors, type_node, f"unsupported type node '{type(type_node).__name__}'")
    return None


def _infer_variable_type(node: Any, scope: SemanticScope, errors: List[str]) -> Optional[Ptr]:
    if isinstance(node, syntax.IDNode):
        var = scope.lookup_var(node.name)
        if var is None:
            _report_error(errors, node, f"undeclared variable '{node.name}'")
            return None
        return var.TypePtr

    if isinstance(node, syntax.ArrayElemNode):
        array_type = _infer_variable_type(node.array, scope, errors)
        index_type = _infer_expression_type(node.index, scope, errors)
        if index_type and index_type.kind != Typekind.intTy:
            _report_error(errors, node.index, "array index must be of integer type")
        if not isinstance(array_type, arrayPtr):
            _report_error(errors, node.array, f"'{getattr(node.array, 'name', str(node.array))}' is not an array")
            return None
        return array_type.elemTy

    if isinstance(node, syntax.RecordFieldNode):
        record_type = _infer_variable_type(node.record, scope, errors)
        if not isinstance(record_type, recordPtr):
            _report_error(errors, node.record, f"'{getattr(node.record, 'name', str(node.record))}' is not a record")
            return None
        if isinstance(node.field, syntax.IDNode):
            field_name = node.field.name
            field_entry = next((f for f in record_type.body if f.idname == field_name), None)
            if field_entry is None:
                _report_error(errors, node.field, f"field '{field_name}' does not exist in record")
                return None
            return field_entry.typePtr
        if isinstance(node.field, syntax.ArrayElemNode):
            field_name = node.field.array.name
            field_entry = next((f for f in record_type.body if f.idname == field_name), None)
            if field_entry is None:
                _report_error(errors, node.field.array, f"field '{field_name}' does not exist in record")
                return None
            if not isinstance(field_entry.typePtr, arrayPtr):
                _report_error(errors, node.field.array, f"field '{field_name}' is not an array")
                return None
            index_type = _infer_expression_type(node.field.index, scope, errors)
            if index_type and index_type.kind != Typekind.intTy:
                _report_error(errors, node.field.index, "array index must be of integer type")
                return None
            return field_entry.typePtr.elemTy
        _report_error(errors, node.field, "unsupported record field access")
        return None

    _report_error(errors, node, f"unsupported variable node '{type(node).__name__}'")
    return None


def _infer_expression_type(node: Any, scope: SemanticScope, errors: List[str]) -> Optional[Ptr]:
    if isinstance(node, syntax.ExpNode):
        base_type = _infer_expression_type(node.term, scope, errors)
        if base_type is None:
            return None
        for _, term in node.otherterm:
            next_type = _infer_expression_type(term, scope, errors)
            if next_type is None:
                return None
            if base_type.kind != Typekind.intTy or next_type.kind != Typekind.intTy:
                _report_error(errors, node, "arithmetic expression requires integer operands")
                return None
            base_type = Ptr(kind=Typekind.intTy, size=1)
        return base_type

    if isinstance(node, syntax.TermNode):
        factor_type = _infer_expression_type(node.factor, scope, errors)
        if factor_type is None:
            return None
        for _, factor in node.otherfactor:
            next_type = _infer_expression_type(factor, scope, errors)
            if next_type is None:
                return None
            if factor_type.kind != Typekind.intTy or next_type.kind != Typekind.intTy:
                _report_error(errors, node, "multiplicative expression requires integer operands")
                return None
            factor_type = Ptr(kind=Typekind.intTy, size=1)
        return factor_type

    if isinstance(node, syntax.ParenExpNode):
        return _infer_expression_type(node.exp, scope, errors)
    if isinstance(node, syntax.IntConstNode):
        return Ptr(kind=Typekind.intTy, size=1)
    if isinstance(node, syntax.CharConstNode):
        return Ptr(kind=Typekind.charTy, size=1)
    if isinstance(node, syntax.RelExpNode):
        left_type = _infer_expression_type(node.left, scope, errors)
        if node.right is None:
            return left_type
        right_type = _infer_expression_type(node.right, scope, errors)
        if left_type is None or right_type is None:
            return None
        if not _same_type(left_type, right_type):
            _report_error(errors, node, "incompatible types in relational expression")
            return None
        if node.CompOp == syntax.CompOpType.LT and left_type.kind != Typekind.intTy:
            _report_error(errors, node, "'<'' comparison requires integer operands")
            return None
        return Ptr(kind=Typekind.boolTy, size=1)
    if isinstance(node, syntax.IDNode) or isinstance(node, syntax.ArrayElemNode) or isinstance(node, syntax.RecordFieldNode):
        return _infer_variable_type(node, scope, errors)

    _report_error(errors, node, f"unsupported expression node '{type(node).__name__}'")
    return None


def _check_statement(stmt: syntax.StmtNode, scope: SemanticScope, errors: List[str], symtab: symbol_table) -> None:
    if isinstance(stmt, syntax.IfNode):
        cond_type = _infer_expression_type(stmt.condition, scope, errors)
        if cond_type and cond_type.kind not in (Typekind.intTy, Typekind.boolTy):
            _report_error(errors, stmt.condition, "if condition must be boolean or integer")
        for child in stmt.then_stm:
            _check_statement(child, scope, errors, symtab)
        for child in stmt.else_stm:
            _check_statement(child, scope, errors, symtab)
        return
    if isinstance(stmt, syntax.WhileNode):
        cond_type = _infer_expression_type(stmt.condition, scope, errors)
        if cond_type and cond_type.kind not in (Typekind.intTy, Typekind.boolTy):
            _report_error(errors, stmt.condition, "while condition must be boolean or integer")
        for child in stmt.body:
            _check_statement(child, scope, errors, symtab)
        return
    if isinstance(stmt, syntax.ReadNode):
        _infer_variable_type(stmt.var, scope, errors)
        return
    if isinstance(stmt, syntax.WriteNode):
        _infer_expression_type(stmt.exp, scope, errors)
        return
    if isinstance(stmt, syntax.ReturnNode):
        if stmt.exp:
            _infer_expression_type(stmt.exp, scope, errors)
        return
    if isinstance(stmt, syntax.AssignNode):
        left_type = _infer_variable_type(stmt.var, scope, errors)
        right_type = _infer_expression_type(stmt.exp, scope, errors)
        if left_type and right_type and not _same_type(left_type, right_type):
            _report_error(errors, stmt, "assignment type mismatch")
        return
    if isinstance(stmt, syntax.CallNode):
        proc_decl = scope.lookup_proc(stmt.name.name)
        if proc_decl is None:
            _report_error(errors, stmt.name, f"undefined procedure '{stmt.name.name}'")
            return
        params = []
        for param in proc_decl.params:
            for name_node in param.names:
                params.append((param, name_node.name))
        if len(params) != len(stmt.args):
            _report_error(errors, stmt, f"procedure '{stmt.name.name}' expects {len(params)} arguments, got {len(stmt.args)}")
            return
        for arg_node, (param, _) in zip(stmt.args, params):
            arg_type = _infer_expression_type(arg_node, scope, errors)
            param_type = _resolve_type(param.type, scope, errors)
            if arg_type and param_type and not _same_type(arg_type, param_type):
                _report_error(errors, arg_node, f"argument type mismatch for procedure '{stmt.name.name}'")
            if param.is_var and not isinstance(arg_node, (syntax.IDNode, syntax.ArrayElemNode, syntax.RecordFieldNode)):
                _report_error(errors, arg_node, f"var parameter for '{stmt.name.name}' requires a variable argument")
        return
    _report_error(errors, stmt, f"unsupported statement '{type(stmt).__name__}'")


def _populate_declare_semantic(declare: syntax.DeclareNode, scope: SemanticScope, symtab: symbol_table, errors: List[str], level: int) -> None:
    if declare.type_dec_head:
        for type_decl in declare.type_dec_head.nodes:
            if scope.has_name(type_decl.name.name):
                _report_error(errors, type_decl.name, f"duplicate definition '{type_decl.name.name}'")
                continue
            type_ptr = _resolve_type(type_decl.type_def, scope, errors)
            if type_ptr is None:
                type_ptr = Ptr(kind=Typekind.intTy, size=1)
            scope.types[type_decl.name.name] = type_ptr
            symtab.Type.append(TypeSym(TypePtr=type_ptr, kind=SymKind.typeKind, name=type_decl.name.name))
    if declare.var_dec_head:
        for var_decl in declare.var_dec_head.nodes:
            var_type = _resolve_type(var_decl.type, scope, errors)
            if var_type is None:
                var_type = Ptr(kind=Typekind.intTy, size=1)
            names = var_decl.name if isinstance(var_decl.name, list) else [var_decl.name]
            for name_node in names:
                if scope.has_name(name_node.name):
                    _report_error(errors, name_node, f"duplicate definition '{name_node.name}'")
                    continue
                symtab.Var.append(VarSym(TypePtr=var_type, kind=SymKind.varKind, name=name_node.name, Access=True, Level=level, Off=0))
                scope.vars[name_node.name] = symtab.Var[-1]
    if declare.proc_dec_head:
        for proc_decl in declare.proc_dec_head.nodes:
            if proc_decl.name and scope.has_name(proc_decl.name.name):
                _report_error(errors, proc_decl.name, f"duplicate definition '{proc_decl.name.name}'")
                continue
            proc_sym = ProcSym(TypePtr=Ptr(kind=Typekind.voidTy, size=0), kind=SymKind.procKind, name=proc_decl.name.name if proc_decl.name else "", Level=level, Parm=[], size=0, code=-1)
            symtab.proc.append(proc_sym)
            scope.procs[proc_decl.name.name] = proc_decl
            child_scope = SemanticScope(parent=scope)
            for param in proc_decl.params:
                param_type = _resolve_type(param.type, scope, errors)
                if param_type is None:
                    param_type = Ptr(kind=Typekind.intTy, size=1)
                for name_node in param.names:
                    if child_scope.has_name(name_node.name):
                        _report_error(errors, name_node, f"duplicate definition '{name_node.name}' in procedure '{proc_decl.name.name}'")
                        continue
                    symtab.Var.append(VarSym(TypePtr=param_type, kind=SymKind.varKind, name=name_node.name, Access=not param.is_var, Level=level + 1, Off=0))
                    child_scope.vars[name_node.name] = symtab.Var[-1]
                    proc_sym.Parm.append(len(symtab.Type) + len(symtab.Var) - 1)
            if proc_decl.declare:
                _populate_declare_semantic(proc_decl.declare, child_scope, symtab, errors, level + 1)
            if proc_decl.body:
                _check_program_body(proc_decl.body, child_scope, errors, symtab)


def _check_program_body(body: syntax.ProgramBodyNode, scope: SemanticScope, errors: List[str], symtab: symbol_table) -> None:
    for stmt in body.children_list:
        _check_statement(stmt, scope, errors, symtab)


def semantic_analysis(program: syntax.ProgramNode) -> Tuple[Optional[symbol_table], List[str]]:
    errors: List[str] = []
    symtab = symbol_table()
    global_scope = SemanticScope()
    if program.Declare:
        _populate_declare_semantic(program.Declare, global_scope, symtab, errors, level=0)
    if program.StmL:
        _check_program_body(program.StmL, global_scope, errors, symtab)
    if errors:
        return None, errors
    return symtab, []


def analyze_program(program: syntax.ProgramNode) -> Tuple[Optional[symbol_table], List[str]]:
    symtab, errors = semantic_analysis(program)
    if errors:
        for msg in errors:
            print(msg)
    else:
        symtab.print_table()
    return symtab, errors

