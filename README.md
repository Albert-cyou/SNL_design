# SNL 编译器设计思路

本项目是一个基于 Python 的 SNL 语言编译实验，实现了从前端分析到中间代码 / MIPS 目标代码生成的基本流程。当前仓库包含词法分析、语法分析、语义分析、中间代码生成、MIPS 代码生成以及 GUI 前端与测试脚本。

## 一、项目概览

- 目标：构建一个可运行的 SNL 编译器实现，并提供可选的语法分析器与可视化前端。
- 范围：前端分析（词法、语法、语义） + 四元式中间代码生成 + MIPS 汇编生成。
- 说明：`predict_set_builder.py`、`grammar_debug.py`、LL(1) 表生成等工具属于辅助脚本，不在主编译流程内。

## 二、主要文件说明

| 文件 | 作用 |
| --- | --- |
| `lexer.py` | 词法分析器。将 SNL 源代码转换成 Token 序列。 |
| `recursive_descent_parser.py` | 递归下降语法分析器。把 Token 序列解析成 AST。 |
| `ll1_parser.py` | LL(1) 表驱动语法分析器。作为可选语法分析方案。 |
| `ll1_table.json` | LL(1) 分析表数据。`ll1_parser.py` 运行时读取该文件。 |
| `semantic_analyzer.py` | 语义分析器。检查作用域、重复定义、类型匹配、过程调用参数等语义规则。 |
| `inter_code.py` | 中间代码生成。把语法树与符号表转换成四元式列表。 |
| `inter_code_optimizer.py` | 中间代码优化。对生成的四元式进行优化，减少冗余。 |
| `mips_generator.py` | MIPS 目标代码生成器。将四元式转换成 MIPS 汇编代码。 |
| `snl_frontend_app.py` | GUI 前端入口。自动调用词法、语法、语义分析并展示结果。 |
| `semantic_tests.py` | 语义测试入口。用于验证语义分析器的正确性。 |
| `inter_code_test.py` | 中间代码测试入口。用于验证四元式生成逻辑。 |
| `print_symbol_table_test.py` | 符号表打印与测试辅助脚本。 |
| `predict_set_builder.py` | 预测集生成脚本。辅助 LL(1) 表构建。 |
| `predict_table.md` | 预测表说明文档。 |
| `grammar_debug.py` | 语法调试辅助脚本。 |
| `tmp_ll1_test.py` | LL(1) 相关测试脚本。 |
| `基础指令.md` | MIPS 基础指令说明。 |
| `SNL文法/` | SNL 语言文法资料与示例。 |
| `目标代码/` | 示例生成目标代码。 |

## 三、主编译流程

```text
SNL 源代码
  |
  v
lexer.py
  Tokenizer.tokenize()
  生成 Token 序列
  |
  v
语法分析（可选）
  |
  |-- recursive_descent_parser.py
  |-- ll1_parser.py（读取 ll1_table.json）
  |
  v
生成 AST 语法树
  |
  v
semantic_analyzer.py
  semantic_analysis(program)
  |
  v
如果语义检查通过
  |
  v
inter_code.py
  生成四元式
  |
  v
mips_generator.py
  生成 MIPS 汇编
```

## 四、GUI 使用说明

```bash
python .\snl_frontend_app.py
```

界面流程：

- 输入 SNL 源程序
- 1 秒无修改后自动触发分析
- `lexer.py` 生成 Token 表
- 选择语法分析器：递归下降或 LL(1)
- `semantic_analyzer.py` 执行语义分析
- 界面显示 Token 表、语法树、语义错误、符号表等

## 五、测试运行

语义测试：

```bash
python .\semantic_tests.py
```

中间代码测试：

```bash
python .\inter_code_test.py
```

符号表打印测试：

```bash
python .\print_symbol_table_test.py
```

## 六、当前语义分析能力

`semantic_analyzer.py` 当前支持以下检查：

- 同一作用域内类型、变量、过程重复定义检查
- 过程参数重复定义检查
- 未声明变量检查
- 未定义类型检查
- 未定义过程检查
- 数组下标类型检查
- 记录字段存在性检查
- 赋值语句左右类型匹配检查
- 算术表达式操作数类型检查
- 关系表达式左右类型兼容检查
- 过程调用参数个数和类型检查
- `var` 参数必须传入变量的检查

## 七、目录说明

- `SNL文法/`：SNL 语言文法及示例文件。
- `目标代码/`：示例生成的 MIPS 目标代码。
- `基础指令.md`：汇编指令参考。