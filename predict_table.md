# SNL 文法 Predict 集表

| 序号 | 语句 | Predict 集合 |
|------|------|-------------|
| 1 | Program → ProgramHead DeclarePart ProgramBody . | {PROGRAM} |
| 2 | ProgramHead → PROGRAM ProgramName | {PROGRAM} |
| 3 | ProgramName → ID | {ID} |
| 4 | DeclarePart → TypeDecpart VarDecpart ProcDecpart | {BEGIN, PROCEDURE, TYPE, VAR} |
| 5 | TypeDecpart → ε | {BEGIN, PROCEDURE, VAR} |
| 6 | TypeDecpart → TypeDec | {TYPE} |
| 7 | TypeDec → TYPE TypeDecList | {TYPE} |
| 8 | TypeDecList → TypeId = TypeDef ; TypeDecMore | {ID} |
| 9 | TypeDecMore → ε | {BEGIN, PROCEDURE, VAR} |
| 10 | TypeDecMore → TypeDecList | {ID} |
| 11 | TypeId → ID | {ID} |
| 12 | TypeDef → BaseType | {CHAR, INTEGER} |
| 13 | TypeDef → StructureType | {ARRAY, RECORD} |
| 14 | TypeDef → ID | {ID} |
| 15 | BaseType → INTEGER | {INTEGER} |
| 16 | BaseType → CHAR | {CHAR} |
| 17 | StructureType → ArrayType | {ARRAY} |
| 18 | StructureType → RecType | {RECORD} |
| 19 | ArrayType → ARRAY [ low .. top ] OF BaseType | {ARRAY} |
| 20 | Low → INTC | {INTC} |
| 21 | Top → INTC | {INTC} |
| 22 | RecType → RECORD FieldDecList END | {RECORD} |
| 23 | FieldDecList → BaseType IdList ; FieldDecMore | {CHAR, INTEGER} |
| 24 | FieldDecList → ArrayType IdList ; FieldDecMore | {ARRAY} |
| 25 | FieldDecMore → ε | {END} |
| 26 | FieldDecMore → FieldDecList | {ARRAY, CHAR, INTEGER} |
| 27 | IdList → ID IdMore | {ID} |
| 28 | IdMore → ε | {;} |
| 29 | IdMore → , IdList | {,} |
| 30 | VarDecpart → ε | {BEGIN, PROCEDURE} |
| 31 | VarDecpart → VarDec | {VAR} |
| 32 | VarDec → VAR VarDecList | {VAR} |
| 33 | VarDecList → TypeDef VarIdList ; VarDecMore | {ARRAY, CHAR, ID, INTEGER, RECORD} |
| 34 | VarDecMore → ε | {BEGIN, PROCEDURE} |
| 35 | VarDecMore → VarDecList | {ARRAY, CHAR, ID, INTEGER, RECORD} |
| 36 | VarIdList → ID VarIdMore | {ID} |
| 37 | VarIdMore → ε | {;} |
| 38 | VarIdMore → , VarIdList | {,} |
| 39 | ProcDecpart → ε | {BEGIN} |
| 40 | ProcDecpart → ProcDec | {PROCEDURE} |
| 41 | ProcDec → PROCEDURE ProcName ( ParamList ) ; ProcDecPart ProcBody ProcDecMore | {PROCEDURE} |
| 42 | ProcDecMore → ε | {BEGIN} |
| 43 | ProcDecMore → ProcDec | {PROCEDURE} |
| 44 | ProcName → ID | {ID} |
| 45 | ParamList → ε | {)} |
| 46 | ParamList → ParamDecList | {ARRAY, CHAR, ID, INTEGER, RECORD, VAR} |
| 47 | ParamDecList → Param ParamMore | {ARRAY, CHAR, ID, INTEGER, RECORD, VAR} |
| 48 | ParamMore → ε | {)} |
| 49 | ParamMore → ; ParamDecList | {;} |
| 50 | Param → TypeDef FormList | {ARRAY, CHAR, ID, INTEGER, RECORD} |
| 51 | Param → VAR TypeDef FormList | {VAR} |
| 52 | FormList → ID FidMore | {ID} |
| 53 | FidMore → ε | {), ;} |
| 54 | FidMore → , FormList | {,} |
| 55 | ProcDecPart → DeclarePart | {BEGIN, PROCEDURE, TYPE, VAR} |
| 56 | ProcBody → ProgramBody | {BEGIN} |
| 57 | ProgramBody → BEGIN StmList END | {BEGIN} |
| 58 | StmList → Stm StmMore | {ID, IF, READ, RETURN, WHILE, WRITE} |
| 59 | StmMore → ε | {ELSE, END, ENDWH, FI} |
| 60 | StmMore → ; StmList | {;} |
| 61 | Stm → ConditionalStm | {IF} |
| 62 | Stm → LoopStm | {WHILE} |
| 63 | Stm → InputStm | {READ} |
| 64 | Stm → OutputStm | {WRITE} |
| 65 | Stm → ReturnStm | {RETURN} |
| 66 | Stm → IDAssCall | {ID} |
| 67 | IDAssCall → ID AssCall | {ID} |
| 68 | AssCall → AssignmentRest | {., :=, [} |
| 69 | AssCall → CallStmRest | {(} |
| 70 | AssignmentRest → VariMore := Exp | {., :=, [} |
| 71 | ConditionalStm → IF RelExp THEN StmList ELSE StmList FI | {IF} |
| 72 | LoopStm → WHILE RelExp DO StmList ENDWH | {WHILE} |
| 73 | InputStm → READ ( Invar ) | {READ} |
| 74 | Invar → ID | {ID} |
| 75 | OutputStm → WRITE ( Exp ) | {WRITE} |
| 76 | ReturnStm → RETURN | {RETURN} |
| 77 | CallStmRest → ( ActParamList ) | {(} |
| 78 | ActParamList → ε | {)} |
| 79 | ActParamList → Exp ActParamMore | {(, ID, INTC} |
| 80 | ActParamMore → ε | {)} |
| 81 | ActParamMore → , ActParamList | {,} |
| 82 | RelExp → Exp OtherRelE | {(, ID, INTC} |
| 83 | OtherRelE → CmpOp Exp | {<, =} |
| 84 | Exp → Term OtherTerm | {(, ID, INTC} |
| 85 | OtherTerm → ε | {), ,, ;, <, =, DO, ELSE, END, ENDWH, FI, THEN, ]} |
| 86 | OtherTerm → AddOp Exp | {+, -} |
| 87 | Term → Factor OtherFactor | {(, ID, INTC} |
| 88 | OtherFactor → ε | {), +, ,, -, ;, <, =, DO, ELSE, END, ENDWH, FI, THEN, ]} |
| 89 | OtherFactor → MultOp Term | {*, /} |
| 90 | Factor → ( Exp ) | {(} |
| 91 | Factor → INTC | {INTC} |
| 92 | Factor → Variable | {ID} |
| 93 | Variable → ID VariMore | {ID} |
| 94 | VariMore → ε | {), *, +, ,, -, /, :=, ;, <, =, DO, ELSE, END, ENDWH, FI, THEN, ]} |
| 95 | VariMore → [ Exp ] | {[} |
| 96 | VariMore → . FieldVar | {.} |
| 97 | FieldVar → ID FieldVarMore | {ID} |
| 98 | FieldVarMore → ε | {), *, +, ,, -, /, :=, ;, <, =, DO, ELSE, END, ENDWH, FI, THEN, ]} |
| 99 | FieldVarMore → [ Exp ] | {[} |
| 100 | CmpOp → < | {<} |
| 101 | CmpOp → = | {=} |
| 102 | AddOp → + | {+} |
| 103 | AddOp → - | {-} |
| 104 | MultOp → * | {*} |
| 105 | MultOp → / | {/} |
