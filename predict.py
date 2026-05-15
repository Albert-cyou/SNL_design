from collections import defaultdict

# =========================
# 文法定义：字典形式
# 非终结符 -> 多个产生式（右部列表）
# =========================
grammar = {
    # 总程序
    "Program": [["ProgramHead", "DeclarePart", "ProgramBody","."]],
    # 程序头
    "ProgramHead": [["PROGRAM", "ProgramName"]],
    "ProgramName": [["ID"]],
    # 程序声明
    "DeclarePart": [["TypeDecpart", "VarDecpart", "ProcDecpart"]],
    # 类型声明
    "TypeDecpart": [["ε"], ["TypeDec"]],
    "TypeDec": [["TYPE", "TypeDecList"]],
    "TypeDecList": [["TypeId", "=", "TypeDef", ";", "TypeDecMore"]],
    "TypeDecMore": [["ε"], ["TypeDecList"]],
    "TypeId": [["ID"]],
    # 类型
    "TypeDef": [["BaseType"], ["StructureType"], ["ID"]],
    "BaseType": [["INTEGER"], ["CHAR"]],
    "StructureType": [["ArrayType"], ["RecType"]],
    "ArrayType": [["ARRAY", "[", "low", "..", "top", "]", "OF", "BaseType"]],
    "Low": [["INTC"]],
    "Top": [["INTC"]],
    "RecType": [["RECORD", "FieldDecList", "END"]],
    "FieldDecList": [["BaseType", "IdList", ";", "FieldDecMore"], ["ArrayType", "IdList", ";", "FieldDecMore"]],
    "FieldDecMore": [["ε"], ["FieldDecList"]],
    "IdList": [["ID", "IdMore"]],
    "IdMore": [["ε"], [",", "IdList"]],
    # 变量声明
    "VarDecpart": [["ε"], ["VarDec"]],
    "VarDec": [["VAR", "VarDecList"]],
    "VarDecList": [["TypeDef", "VarIdList", ";", "VarDecMore"]],
    "VarDecMore": [["ε"], ["VarDecList"]],
    "VarIdList": [["ID", "VarIdMore"]],
    "VarIdMore": [["ε"], [",", "VarIdList"]],
    # 过程声明
    "ProcDecpart": [["ε"], ["ProcDec"]],
    "ProcDec": [["PROCEDURE", "ProcName", "(", "ParamList", ")", ";", "ProcDecPart", "ProcBody", "ProcDecMore"]],
    "ProcDecMore": [["ε"], ["ProcDeclaration"]],
    "ProcName": [["ID"]],
    # 参数声明
    "ParamList": [["ε"], ["ParamDecList"]],
    "ParamDecList": [["Param", "ParamMore"]],
    "ParamMore": [["ε"], [";", "ParamDecList"]],
    "Param": [["TypeDef", "FormList"], ["VAR", "TypeDef", "FormList"]],
    "FormList": [["ID", "FidMore"]],
    "FidMore": [["ε"], [",", "FormList"]],
    # 过程中的声明部分
    "ProcDecPart": [["DeclarePart"]],
    # 过程体
    "ProcBody": [["ProgramBody"]],
    # 主程序体
    "ProgramBody": [["BEGIN", "StmList", "END"]],
    # 语句序列
    "StmList": [["Stm", "StmMore"]],
    "StmMore": [["ε"], [";", "StmList"]],
    # 语句
    "Stm": [["ConditionalStm"], ["LoopStm"], ["InputStm"], ["OutputStm"], ["ReturnStm"], ["IDAssCall"]],
    "IDAssCall": [["ID", "AssCall"]],
    "AssCall": [["AssignmentRest"], ["CallStmRest"]],
    # 赋值语句
    "AssignmentRest": [["VariMore", ":=", "Exp"]],
    # 条件语句
    "ConditionalStm": [["IF", "RelExp", "THEN", "StmList", "ELSE", "StmList", "FI"]],
    # 循环语句
    "LoopStm": [["WHILE", "RelExp", "DO", "StmList", "ENDWH"]],
    # 输入语句
    "InputStm": [["READ", "(", "Invar", ")"]],
    "Invar": [["ID"]],
    # 输出语句
    "OutputStm": [["WRITE", "(", "Exp", ")"]],
    # 返回语句
    "ReturnStm": [["RETURN"]],
    # 过程调用语句
    "CallStmRest": [["(", "ActParamList", ")"]],
    "ActParamList": [["ε"], ["Exp", "ActParamMore"]],
    "ActParamMore": [["ε"], [",", "ActParamList"]],
    # 条件表达式
    "RelExp": [["Exp", "OtherRelE"]],
    "OtherRelE": [["CmpOp", "Exp"]],
    # 算术表达式
    "Exp": [["Term", "OtherTerm"]],
    "OtherTerm": [["ε"], ["AddOp", "Exp"]],
    # 项
    "Term": [["Factor", "OtherFactor"]],
    "OtherFactor": [["ε"], ["MultOp", "Term"]],
    # 因子
    "Factor": [["(", "Exp", ")"], ["INTC"], ["Variable"]],
    "Variable": [["ID", "VariMore"]],
    "VariMore": [["ε"], ["[", "Exp", "]"], [".", "FieldVar"]],
    "FieldVar": [["ID", "FieldVarMore"]],
    "FieldVarMore": [["ε"], ["[", "Exp", "]"]],
    # 运算符
    "CmpOp": [["<"], ["="]],
    "AddOp": [["+"], ["-"]],
    "MultOp": [["*"], ["/"]]
}

# 自动区分终结符 / 非终结符
nonterminals = set(grammar.keys())
terminals = set()
for head, prods in grammar.items():
    for prod in prods:
        for sym in prod:
            if sym not in nonterminals and sym != "ε":
                terminals.add(sym)

# =========================
# FIRST 集计算
# =========================
FIRST = defaultdict(set)

def compute_first(symbol):
    if symbol in terminals or symbol == "ε":
        return {symbol}
    res = set()
    for prod in grammar[symbol]:
        for sym in prod:
            sf = compute_first(sym)
            res.update(sf - {"ε"})
            if "ε" not in sf:
                break
        else:
            res.add("ε")
    return res

for nt in nonterminals:
    FIRST[nt] = compute_first(nt)

# =========================
# FOLLOW 集计算
# =========================
FOLLOW = defaultdict(set)
start = "Program"
FOLLOW[start].add("$")

changed = True
while changed:
    changed = False
    for head, prods in grammar.items():
        for prod in prods:
            for i, sym in enumerate(prod):
                if sym not in nonterminals:
                    continue
                trailer = set()
                all_empty = True
                for s in prod[i+1:]:
                    sf = compute_first(s)
                    trailer.update(sf - {"ε"})
                    if "ε" not in sf:
                        all_empty = False
                        break
                if all_empty:
                    trailer.update(FOLLOW[head])
                before = len(FOLLOW[sym])
                FOLLOW[sym].update(trailer)
                if len(FOLLOW[sym]) > before:
                    changed = True

# =========================
# Predict 集计算
# =========================
predict_list = []
idx = 1
for head, prods in grammar.items():
    for prod in prods:
        p = set()
        all_empty = True
        for s in prod:
            sf = compute_first(s)
            p.update(sf - {"ε"})
            if "ε" not in sf:
                all_empty = False
                break
        if all_empty:
            p.update(FOLLOW[head])
        stmt = f"{head} → {' '.join(prod)}"
        predict_list.append((idx, stmt, p))
        idx += 1

# =========================
# 输出为 .md 表格文件
# =========================
with open("predict_table.md", "w", encoding="utf-8") as f:
    f.write("# SNL 文法 Predict 集表\n\n")
    f.write("| 序号 | 语句 | Predict 集合 |\n")
    f.write("|------|------|-------------|\n")
    for idx, stmt, pset in predict_list:
        p_str = "{" + ", ".join(sorted(pset)) + "}"
        f.write(f"| {idx} | {stmt} | {p_str} |\n")

print("✅ 已生成：predict_table.md")