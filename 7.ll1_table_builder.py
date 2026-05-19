from collections import defaultdict
import json

# =========================
# 文法定义（复用原有文法）
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
    "ProcDecMore": [["ε"], ["ProcDec"]],
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

# =========================
# 自动区分终结符 / 非终结符（复用原有逻辑）
# =========================
nonterminals = set(grammar.keys())
terminals = set()
for head, prods in grammar.items():
    for prod in prods:
        for sym in prod:
            if sym not in nonterminals and sym != "ε":
                terminals.add(sym)
# 增加结束符 $
terminals.add("$")

# =========================
# FIRST 集计算（复用原有逻辑）
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
# FOLLOW 集计算（复用原有逻辑）
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
# 生成LL1状态转移表核心逻辑
# =========================
def build_ll1_table():
    # LL1表结构：ll1_table[非终结符][终结符] = 产生式右部列表
    ll1_table = defaultdict(dict)
    # 记录冲突（用于检查是否为LL1文法）
    conflicts = []

    # 遍历所有产生式，填充LL1表
    for nonterm, productions in grammar.items():
        for prod in productions:
            # 计算当前产生式的Predict集
            predict_set = set()
            all_empty = True
            for sym in prod:
                sf = compute_first(sym)
                predict_set.update(sf - {"ε"})
                if "ε" not in sf:
                    all_empty = False
                    break
            if all_empty:
                predict_set.update(FOLLOW[nonterm])
            
            # 为Predict集中的每个终结符映射产生式
            for term in predict_set:
                if term in ll1_table[nonterm]:
                    # 检测冲突：同一(非终结符,终结符)对应多个产生式
                    conflicts.append(
                        f"冲突：非终结符 {nonterm} + 终结符 {term} 已映射到 {ll1_table[nonterm][term]}，无法再映射到 {prod}"
                    )
                else:
                    # 存储产生式（注意：ε用空列表表示，便于后续解析）
                    ll1_table[nonterm][term] = prod if prod != ["ε"] else []
    
    # 输出冲突信息（如果有）
    if conflicts:
        print("❌ 检测到LL1文法冲突：")
        for conflict in conflicts:
            print(conflict)
    else:
        print("✅ 未检测到LL1文法冲突，转移表生成成功")
    
    return ll1_table

# =========================
# 保存LL1表到文件（JSON格式）
# =========================
def save_ll1_table(ll1_table, file_path="ll1_table.json"):
    # defaultdict转普通dict（便于JSON序列化）
    ll1_table_normal = {
        nonterm: {term: prod for term, prod in term_dict.items()}
        for nonterm, term_dict in ll1_table.items()
    }
    # 写入文件
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(ll1_table_normal, f, ensure_ascii=False, indent=4)
    print(f"✅ LL1状态转移表已保存到：{file_path}")

# =========================
# 执行生成流程
# =========================
if __name__ == "__main__":
    # 生成LL1表
    ll1_table = build_ll1_table()
    # 保存到文件
    save_ll1_table(ll1_table)