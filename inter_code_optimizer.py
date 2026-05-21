# 中间代码优化
# 输入：inter_code.py 生成的四元式
# 输出：优化后的四元式

from dataclasses import replace
from typing import Dict, List, Optional, Set, Tuple

import inter_code


ARITHMETIC_OPS = {
    inter_code.Operation.ADD,
    inter_code.Operation.SUB,
    inter_code.Operation.MULT,
    inter_code.Operation.DIV,
}

COMPARISON_OPS = {
    inter_code.Operation.EQC,
    inter_code.Operation.LTC,
}

PURE_OPS = ARITHMETIC_OPS | COMPARISON_OPS

BLOCK_END_OPS = {
    inter_code.Operation.LABEL,
    inter_code.Operation.JUMP,
    inter_code.Operation.JUMP0,
    inter_code.Operation.CALL,
    inter_code.Operation.PENTRY,
    inter_code.Operation.ENDPENTRY,
}


def optimize_quadruples(quads: List[inter_code.Quadruple]) -> List[inter_code.Quadruple]:
    optimized = clone_quads(quads)
    optimized = fold_constant_expressions(optimized)
    optimized = eliminate_common_subexpressions(optimized)
    optimized = hoist_loop_invariants(optimized)
    return optimized


def clone_quads(quads: List[inter_code.Quadruple]) -> List[inter_code.Quadruple]:
    return [replace(quad) for quad in quads]


def fold_constant_expressions(quads: List[inter_code.Quadruple]) -> List[inter_code.Quadruple]:
    result = []
    for quad in quads:
        if quad.codekind in ARITHMETIC_OPS | COMPARISON_OPS and is_value(quad.Arg1) and is_value(quad.Arg2):
            folded = evaluate_constant(quad.codekind, quad.Arg1.value, quad.Arg2.value)
            if folded is not None:
                result.append(inter_code.Quadruple(inter_code.Operation.ASSIG, quad.Arg3, inter_code.ValueARG(folded)))
                continue
        result.append(quad)
    return result


def evaluate_constant(op: inter_code.Operation, left: int, right: int) -> Optional[int]:
    if op == inter_code.Operation.ADD:
        return left + right
    if op == inter_code.Operation.SUB:
        return left - right
    if op == inter_code.Operation.MULT:
        return left * right
    if op == inter_code.Operation.DIV:
        if right == 0:
            return None
        return left // right
    if op == inter_code.Operation.EQC:
        return 1 if left == right else 0
    if op == inter_code.Operation.LTC:
        return 1 if left < right else 0
    return None


def eliminate_common_subexpressions(quads: List[inter_code.Quadruple]) -> List[inter_code.Quadruple]:
    expression_table: Dict[Tuple, inter_code.ARG] = {}
    replacements: Dict[int, inter_code.ARG] = {}
    optimized = []

    for quad in quads:
        rewritten = rewrite_quad_args(quad, replacements)

        if starts_new_basic_block(rewritten):
            expression_table.clear()
            replacements.clear()

        if rewritten.codekind in PURE_OPS and isinstance(rewritten.Arg3, inter_code.AddrARG):
            key = expression_key(rewritten)
            previous_result = expression_table.get(key)
            if previous_result is not None:
                replacements[rewritten.Arg3.idx] = previous_result
                optimized.append(inter_code.Quadruple(inter_code.Operation.ASSIG, rewritten.Arg3, previous_result))
                continue
            expression_table[key] = rewritten.Arg3

        if defines_variable(rewritten):
            remove_expressions_using(expression_table, defined_idx(rewritten))

        optimized.append(rewritten)

    return optimized


def rewrite_quad_args(quad: inter_code.Quadruple, replacements: Dict[int, inter_code.ARG]) -> inter_code.Quadruple:
    return inter_code.Quadruple(
        quad.codekind,
        rewrite_arg(quad.Arg1, replacements),
        rewrite_arg(quad.Arg2, replacements),
        quad.Arg3,
    )


def rewrite_arg(arg: Optional[inter_code.ARG], replacements: Dict[int, inter_code.ARG]) -> Optional[inter_code.ARG]:
    if isinstance(arg, inter_code.AddrARG):
        return replacements.get(arg.idx, arg)
    return arg


def expression_key(quad: inter_code.Quadruple) -> Tuple:
    left = arg_key(quad.Arg1)
    right = arg_key(quad.Arg2)
    if quad.codekind in {inter_code.Operation.ADD, inter_code.Operation.MULT, inter_code.Operation.EQC}:
        left, right = sorted([left, right])
    return quad.codekind, left, right


def starts_new_basic_block(quad: inter_code.Quadruple) -> bool:
    return quad.codekind in BLOCK_END_OPS


def remove_expressions_using(expression_table: Dict[Tuple, inter_code.ARG], idx: Optional[int]) -> None:
    if idx is None:
        return
    stale_keys = [key for key in expression_table if idx in indexes_in_key(key)]
    for key in stale_keys:
        del expression_table[key]


def indexes_in_key(key: Tuple) -> Set[int]:
    indexes = set()
    for item in key:
        if isinstance(item, tuple) and item and item[0] == "addr":
            indexes.add(item[1])
    return indexes


def hoist_loop_invariants(quads: List[inter_code.Quadruple]) -> List[inter_code.Quadruple]:
    optimized = clone_quads(quads)
    loops = find_simple_loops(optimized)

    for loop in reversed(loops):
        start, jump_back = loop
        body_start = find_loop_body_start(optimized, start, jump_back)
        if body_start is None:
            continue
        defined_in_loop = collect_defined_indexes(optimized[body_start:jump_back])
        movable_indexes = []

        for index in range(body_start, jump_back):
            quad = optimized[index]
            if is_loop_invariant_quad(quad, defined_in_loop):
                movable_indexes.append(index)

        if not movable_indexes:
            continue

        movable_quads = [optimized[index] for index in movable_indexes]
        optimized = [
            *optimized[:start],
            *movable_quads,
            *[quad for index, quad in enumerate(optimized[start:]) if start + index not in movable_indexes],
        ]

    return optimized


def find_simple_loops(quads: List[inter_code.Quadruple]) -> List[Tuple[int, int]]:
    label_positions = {
        quad.Arg1.value: index
        for index, quad in enumerate(quads)
        if quad.codekind == inter_code.Operation.LABEL and isinstance(quad.Arg1, inter_code.LabelARG)
    }
    loops = []
    for index, quad in enumerate(quads):
        if quad.codekind == inter_code.Operation.JUMP and isinstance(quad.Arg1, inter_code.LabelARG):
            start = label_positions.get(quad.Arg1.value)
            if start is not None and start < index:
                loops.append((start, index))
    return loops


def find_loop_body_start(quads: List[inter_code.Quadruple], start: int, jump_back: int) -> Optional[int]:
    for index in range(start + 1, jump_back):
        if quads[index].codekind == inter_code.Operation.JUMP0:
            return index + 1
    return None


def collect_defined_indexes(quads: List[inter_code.Quadruple]) -> Set[int]:
    indexes = set()
    for quad in quads:
        idx = defined_idx(quad)
        if idx is not None:
            indexes.add(idx)
    return indexes


def is_loop_invariant_quad(quad: inter_code.Quadruple, defined_in_loop: Set[int]) -> bool:
    if quad.codekind not in PURE_OPS:
        return False
    if not isinstance(quad.Arg3, inter_code.AddrARG):
        return False
    if quad.Arg3.idx not in defined_in_loop:
        return False
    return arg_is_loop_invariant(quad.Arg1, defined_in_loop) and arg_is_loop_invariant(quad.Arg2, defined_in_loop)


def arg_is_loop_invariant(arg: Optional[inter_code.ARG], defined_in_loop: Set[int]) -> bool:
    if isinstance(arg, inter_code.AddrARG):
        return arg.idx not in defined_in_loop
    return True


def defines_variable(quad: inter_code.Quadruple) -> bool:
    return defined_idx(quad) is not None


def defined_idx(quad: inter_code.Quadruple) -> Optional[int]:
    if quad.codekind == inter_code.Operation.ASSIG and isinstance(quad.Arg1, inter_code.AddrARG):
        return quad.Arg1.idx
    if quad.codekind in PURE_OPS | {inter_code.Operation.AADD} and isinstance(quad.Arg3, inter_code.AddrARG):
        return quad.Arg3.idx
    return None


def is_value(arg: Optional[inter_code.ARG]) -> bool:
    return isinstance(arg, inter_code.ValueARG)


def arg_key(arg: Optional[inter_code.ARG]) -> Tuple:
    if arg is None:
        return ("none",)
    if isinstance(arg, inter_code.ValueARG):
        return ("value", arg.value)
    if isinstance(arg, inter_code.LabelARG):
        return ("label", arg.value)
    if isinstance(arg, inter_code.AddrARG):
        return ("addr", arg.idx)
    if isinstance(arg, inter_code.TextARG):
        return ("text", arg.text)
    return ("unknown", repr(arg))
