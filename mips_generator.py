from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

import inter_code
import semantic_analyzer


WORD_SIZE = 4


@dataclass
class MIPSGenerator:
    symtab: semantic_analyzer.symbol_table
    address_results: Set[int] = field(default_factory=set)
    proc_param_map: Dict[str, List[int]] = field(default_factory=dict)
    label_map: Dict[str, str] = field(default_factory=dict)
    pending_arg_bytes: int = 0
    runtime_labels: int = 0

    def generate(self, quads: List[inter_code.Quadruple]) -> str:
        self._collect_metadata(quads)
        lines: List[str] = []
        lines.extend(self._generate_data_section())
        lines.append("")
        lines.append(".text")
        lines.append(".globl main")
        lines.append("main:")
        lines.append("    j __snl_main_body")
        lines.extend(self._generate_text_section(quads))
        return "\n".join(lines) + "\n"

    def _collect_metadata(self, quads: List[inter_code.Quadruple]) -> None:
        for quad in quads:
            if quad.codekind == inter_code.Operation.AADD and isinstance(quad.Arg3, inter_code.AddrARG):
                self.address_results.add(quad.Arg3.idx)

        for proc in self.symtab.proc:
            self.proc_param_map[proc.name] = list(proc.Parm)

    def _generate_data_section(self) -> List[str]:
        lines = [".data", "__snl_newline: .asciiz \"\\n\""]
        for var in self.symtab.Var:
            label = self._var_label(var.idx)
            size = max(1, getattr(var.TypePtr, "size", 1))
            values = ", ".join(["0"] * size)
            lines.append(f"{label}: .word {values}")
        return lines

    def _generate_text_section(self, quads: List[inter_code.Quadruple]) -> List[str]:
        lines: List[str] = []
        main_body_emitted = False
        in_procedure = False

        for quad in quads:
            op = quad.codekind

            if op == inter_code.Operation.MENTRY:
                continue

            if op == inter_code.Operation.PENTRY:
                in_procedure = True
                lines.extend(self._emit_procedure_entry(quad))
                continue

            if op == inter_code.Operation.ENDPENTRY:
                lines.extend(self._emit_procedure_exit())
                in_procedure = False
                continue

            if not in_procedure and not main_body_emitted:
                lines.append("__snl_main_body:")
                main_body_emitted = True

            lines.extend(self._emit_quad(quad))

        if not main_body_emitted:
            lines.append("__snl_main_body:")
        lines.extend(self._emit_exit())
        return lines

    def _emit_quad(self, quad: inter_code.Quadruple) -> List[str]:
        op = quad.codekind

        if op in {inter_code.Operation.ADD, inter_code.Operation.SUB}:
            return self._emit_binary_arithmetic(quad, "add" if op == inter_code.Operation.ADD else "sub")
        if op == inter_code.Operation.MULT:
            return self._emit_mult_or_div(quad, "mult")
        if op == inter_code.Operation.DIV:
            return self._emit_mult_or_div(quad, "div")
        if op in {inter_code.Operation.LTC, inter_code.Operation.EQC}:
            return self._emit_compare(quad, "blt" if op == inter_code.Operation.LTC else "beq")
        if op == inter_code.Operation.ASSIG:
            return self._emit_assign(quad)
        if op == inter_code.Operation.AADD:
            return self._emit_address_add(quad)
        if op == inter_code.Operation.READC:
            return self._emit_read(quad.Arg1)
        if op == inter_code.Operation.WRITEC:
            return self._emit_write(quad.Arg1)
        if op == inter_code.Operation.LABEL:
            return [f"{self._quad_label(quad.Arg1)}:"]
        if op == inter_code.Operation.JUMP:
            return [f"    j {self._quad_label(quad.Arg1)}"]
        if op == inter_code.Operation.JUMP0:
            return self._emit_jump0(quad)
        if op in {inter_code.Operation.VARACT, inter_code.Operation.VALACT}:
            return self._emit_argument(quad)
        if op == inter_code.Operation.CALL:
            return self._emit_call(quad)
        if op == inter_code.Operation.RETURNC:
            return self._emit_return(quad)

        return [f"    # unsupported quadruple: {quad}"]

    def _emit_binary_arithmetic(self, quad: inter_code.Quadruple, instr: str) -> List[str]:
        lines = []
        lines.extend(self._load_value(quad.Arg1, "$t0"))
        lines.extend(self._load_value(quad.Arg2, "$t1"))
        lines.append(f"    {instr} $t2, $t0, $t1")
        lines.extend(self._store_value(quad.Arg3, "$t2"))
        return lines

    def _emit_mult_or_div(self, quad: inter_code.Quadruple, instr: str) -> List[str]:
        lines = []
        lines.extend(self._load_value(quad.Arg1, "$t0"))
        lines.extend(self._load_value(quad.Arg2, "$t1"))
        lines.append(f"    {instr} $t0, $t1")
        lines.append("    mflo $t2")
        lines.extend(self._store_value(quad.Arg3, "$t2"))
        return lines

    def _emit_compare(self, quad: inter_code.Quadruple, branch_instr: str) -> List[str]:
        true_label = self._new_runtime_label("cmp_true")
        end_label = self._new_runtime_label("cmp_end")
        lines = []
        lines.extend(self._load_value(quad.Arg1, "$t0"))
        lines.extend(self._load_value(quad.Arg2, "$t1"))
        lines.append("    li $t2, 0")
        lines.append(f"    {branch_instr} $t0, $t1, {true_label}")
        lines.append(f"    j {end_label}")
        lines.append(f"{true_label}:")
        lines.append("    li $t2, 1")
        lines.append(f"{end_label}:")
        lines.extend(self._store_value(quad.Arg3, "$t2"))
        return lines

    def _emit_assign(self, quad: inter_code.Quadruple) -> List[str]:
        lines = self._load_value(quad.Arg2, "$t0")
        lines.extend(self._store_value(quad.Arg1, "$t0"))
        return lines

    def _emit_address_add(self, quad: inter_code.Quadruple) -> List[str]:
        lines = []
        lines.extend(self._load_address(quad.Arg1, "$t0"))
        lines.extend(self._load_value(quad.Arg2, "$t1"))
        lines.append(f"    li $t2, {WORD_SIZE}")
        lines.append("    mult $t1, $t2")
        lines.append("    mflo $t1")
        lines.append("    add $t2, $t0, $t1")
        lines.extend(self._store_raw_word(quad.Arg3, "$t2"))
        return lines

    def _emit_read(self, target: Optional[inter_code.ARG]) -> List[str]:
        lines = ["    li $v0, 5", "    syscall"]
        lines.extend(self._store_value(target, "$v0"))
        return lines

    def _emit_write(self, arg: Optional[inter_code.ARG]) -> List[str]:
        lines = self._load_value(arg, "$a0")
        lines.extend(["    li $v0, 1", "    syscall"])
        lines.extend(["    la $a0, __snl_newline", "    li $v0, 4", "    syscall"])
        return lines

    def _emit_jump0(self, quad: inter_code.Quadruple) -> List[str]:
        lines = self._load_value(quad.Arg1, "$t0")
        lines.append(f"    beq $t0, $zero, {self._quad_label(quad.Arg2)}")
        return lines

    def _emit_argument(self, quad: inter_code.Quadruple) -> List[str]:
        lines = ["    addi $sp, $sp, -4"]
        if quad.codekind == inter_code.Operation.VARACT:
            lines.extend(self._load_address(quad.Arg1, "$t0"))
        else:
            lines.extend(self._load_value(quad.Arg1, "$t0"))
        lines.append("    sw $t0, 0($sp)")
        self.pending_arg_bytes += WORD_SIZE
        return lines

    def _emit_call(self, quad: inter_code.Quadruple) -> List[str]:
        name = self._text_value(quad.Arg1)
        lines = [f"    jal {self._proc_label(name)}"]
        if self.pending_arg_bytes:
            lines.append(f"    addi $sp, $sp, {self.pending_arg_bytes}")
            self.pending_arg_bytes = 0
        return lines

    def _emit_return(self, quad: inter_code.Quadruple) -> List[str]:
        lines: List[str] = []
        if quad.Arg1 is not None:
            lines.extend(self._load_value(quad.Arg1, "$v0"))
        lines.append("    jr $ra")
        return lines

    def _emit_procedure_entry(self, quad: inter_code.Quadruple) -> List[str]:
        proc_name = self._text_value(quad.Arg2)
        params = self.proc_param_map.get(proc_name, [])
        lines = [f"{self._proc_label(proc_name)}:"]
        for offset, param_idx in enumerate(reversed(params)):
            var = self.symtab.get_var(param_idx)
            if var is None:
                continue
            lines.append(f"    lw $t0, {offset * WORD_SIZE}($sp)")
            lines.extend(self._store_word_to_label(self._var_label(var.idx), "$t0"))
        return lines

    def _emit_procedure_exit(self) -> List[str]:
        return ["    jr $ra"]

    def _emit_exit(self) -> List[str]:
        return ["    li $v0, 10", "    syscall"]

    def _load_value(self, arg: Optional[inter_code.ARG], reg: str) -> List[str]:
        if isinstance(arg, inter_code.ValueARG):
            return [f"    li {reg}, {arg.value}"]
        if isinstance(arg, inter_code.AddrARG):
            if self._is_indirect_addr(arg):
                lines = self._load_word_from_label(self._var_label(arg.idx), "$t9")
                lines.append(f"    lw {reg}, 0($t9)")
                return lines
            return self._load_word_from_label(self._var_label(arg.idx), reg)
        raise ValueError(f"cannot load value from {inter_code.format_arg(arg)}")

    def _load_address(self, arg: Optional[inter_code.ARG], reg: str) -> List[str]:
        if isinstance(arg, inter_code.AddrARG):
            if self._is_indirect_addr(arg):
                return self._load_word_from_label(self._var_label(arg.idx), reg)
            return [f"    la {reg}, {self._var_label(arg.idx)}"]
        raise ValueError(f"cannot load address from {inter_code.format_arg(arg)}")

    def _store_value(self, target: Optional[inter_code.ARG], reg: str) -> List[str]:
        if isinstance(target, inter_code.AddrARG):
            if self._is_indirect_addr(target):
                lines = self._load_word_from_label(self._var_label(target.idx), "$t9")
                lines.append(f"    sw {reg}, 0($t9)")
                return lines
            return self._store_word_to_label(self._var_label(target.idx), reg)
        raise ValueError(f"cannot store value to {inter_code.format_arg(target)}")

    def _store_raw_word(self, target: Optional[inter_code.ARG], reg: str) -> List[str]:
        if isinstance(target, inter_code.AddrARG):
            return self._store_word_to_label(self._var_label(target.idx), reg)
        raise ValueError(f"cannot store word to {inter_code.format_arg(target)}")

    def _load_word_from_label(self, label: str, reg: str) -> List[str]:
        return [f"    la $t8, {label}", f"    lw {reg}, 0($t8)"]

    def _store_word_to_label(self, label: str, reg: str) -> List[str]:
        return [f"    la $t8, {label}", f"    sw {reg}, 0($t8)"]

    def _is_indirect_addr(self, arg: inter_code.AddrARG) -> bool:
        var = self.symtab.get_var(arg.idx)
        return arg.idx in self.address_results or (var is not None and not var.Access)

    def _quad_label(self, arg: Optional[inter_code.ARG]) -> str:
        if not isinstance(arg, inter_code.LabelARG):
            raise ValueError(f"expected label argument, got {inter_code.format_arg(arg)}")
        if arg.value not in self.label_map:
            self.label_map[arg.value] = f"__snl_{arg.value}"
        return self.label_map[arg.value]

    def _new_runtime_label(self, prefix: str) -> str:
        self.runtime_labels += 1
        return f"__snl_{prefix}_{self.runtime_labels}"

    def _var_label(self, idx: Optional[int]) -> str:
        if idx is None:
            raise ValueError("variable without symbol-table index")
        return f"__snl_var_{idx}"

    def _proc_label(self, name: str) -> str:
        return f"__snl_proc_{self._safe_name(name)}"

    def _safe_name(self, name: str) -> str:
        return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name) or "anonymous"

    def _text_value(self, arg: Optional[inter_code.ARG]) -> str:
        if isinstance(arg, inter_code.TextARG):
            return arg.text
        raise ValueError(f"expected text argument, got {inter_code.format_arg(arg)}")


def generate_mips(quads: List[inter_code.Quadruple], symtab: semantic_analyzer.symbol_table) -> str:
    return MIPSGenerator(symtab).generate(quads)


def print_mips(quads: List[inter_code.Quadruple], symtab: semantic_analyzer.symbol_table) -> None:
    print(generate_mips(quads, symtab))
