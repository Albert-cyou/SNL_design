# 前端演示
# 输入代码进行分析

import io
import json
import os
import tkinter as tk
from contextlib import redirect_stdout
from tkinter import filedialog, messagebox, ttk


try:
    from lexer import Tokenizer
    import recursive_descent_parser as syntax
    import semantic_analyzer as semantic_analysis
    import ll1_parser
    import inter_code
    import inter_code_optimizer
    import mips_generator

    recursive_syntax_analysis = syntax.syntax_analysis
    ll1_syntax_analysis = ll1_parser.Program
    semantic_analyze = semantic_analysis.semantic_analysis
    generate_intermediate_code = inter_code.generate_intermediate_code
    optimize_quadruples = inter_code_optimizer.optimize_quadruples
    generate_mips = mips_generator.generate_mips
except (ImportError, FileNotFoundError, AttributeError):
    class Tokenizer:
        def __init__(self, code):
            self.code = code
        def tokenize(self):
            return []
    def recursive_syntax_analysis(tokens):
        return None, "依赖模块未找到，请检查 lexer.py 和 recursive_descent_parser.py"
    def ll1_syntax_analysis(tokens):
        return None, "依赖模块未找到，请检查 ll1_parser.py"
    def semantic_analyze(program):
        return None, ["依赖模块未找到，请检查 semantic_analyzer.py"]
    def generate_intermediate_code(program, symtab):
        return [], symtab
    def optimize_quadruples(quads):
        return quads
    def generate_mips(quads, symtab):
        return ""


class SNLAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SNL 实时前端分析器")
        self.geometry("1120x720")
        self.resizable(True, True)

        self.parser_mode = tk.StringVar(value="recursive")
        self._parse_after_id = None
        self.current_asm_code = ""
        self.error_cases = []
        self.error_case_names = []
        self.error_case_path = os.path.join(os.path.dirname(__file__), "error_cases.json")

        # 高亮标签样式
        self.highlight_tag = "current_line"

        self._load_error_cases()
        self._build_ui()
        self._schedule_parse()

        # 绑定光标移动事件和文本变更事件来更新行号和高亮
        self.source_text.bind("<KeyRelease>", self._on_editor_update)
        self.source_text.bind("<ButtonRelease-1>", self._on_editor_update)
        self.source_text.bind("<Configure>", self._update_line_numbers)
        self.source_text.bind("<<Modified>>", self._on_source_modified)
        
        # 初始化行号和高亮
        self._update_line_numbers()
        self._highlight_current_line()

    def _build_ui(self):
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_pane)
        right_frame = ttk.Frame(main_pane)

        main_pane.add(left_frame, weight=2)
        main_pane.add(right_frame, weight=3)

        self._build_editor(left_frame)
        self._build_right_panel(right_frame)

    def _build_editor(self, parent):
        label = ttk.Label(parent, text="SNL 源代码输入")
        label.pack(anchor=tk.W, padx=8, pady=(8, 0))

        # 创建编辑区域容器（行号 + 代码编辑）
        editor_container = ttk.Frame(parent)
        editor_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # 行号显示文本框
        self.line_number_text = tk.Text(
            editor_container,
            width=4,
            wrap=tk.NONE,
            font=("Consolas", 11),
            state=tk.DISABLED,
            bg="#f0f0f0",
            relief=tk.FLAT,
            padx=2
        )
        self.line_number_text.pack(fill=tk.Y, side=tk.LEFT)

        # 代码编辑文本框
        self.source_text = tk.Text(
            editor_container,
            wrap=tk.NONE,
            undo=True,
            font=("Consolas", 11)
        )
        self.source_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # 添加高亮标签
        self.source_text.tag_configure(
            self.highlight_tag,
            background="#e8f4fd"  # 浅蓝色高亮背景
        )

        # 滚动条配置
        # 水平滚动条（同时控制行号和代码框）
        x_scroll = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self._xview)
        x_scroll.pack(fill=tk.X, side=tk.BOTTOM, padx=8)
        self.source_text.configure(xscrollcommand=x_scroll.set)
        self.line_number_text.configure(xscrollcommand=x_scroll.set)

        # 垂直滚动条（同时控制行号和代码框）
        y_scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self._yview)
        y_scroll.pack(fill=tk.Y, side=tk.RIGHT, padx=(0, 8))
        self.source_text.configure(yscrollcommand=y_scroll.set)
        self.line_number_text.configure(yscrollcommand=y_scroll.set)

    def _xview(self, *args):
        """同步行号和代码框的水平滚动"""
        self.source_text.xview(*args)
        self.line_number_text.xview(*args)

    def _yview(self, *args):
        """同步行号和代码框的垂直滚动"""
        self.source_text.yview(*args)
        self.line_number_text.yview(*args)
        # 滚动时更新高亮
        self._highlight_current_line()

    def _load_error_cases(self):
        self.error_cases = []
        self.error_case_names = []
        if not os.path.exists(self.error_case_path):
            return
        try:
            with open(self.error_case_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.error_cases = data.get("cases", [])
            elif isinstance(data, list):
                self.error_cases = data
            self.error_case_names = [case.get("name", f"测试用例 {i+1}") for i, case in enumerate(self.error_cases)]
        except Exception:
            self.error_cases = []
            self.error_case_names = []

    def _apply_selected_case(self):
        name = self.case_combobox.get()
        case = next((item for item in self.error_cases if item.get("name") == name), None)
        if not case:
            return
        self.source_text.delete("1.0", tk.END)
        self.source_text.insert("1.0", case.get("source", ""))
        self._update_line_numbers()
        self._schedule_parse()

    def _update_line_numbers(self, event=None):
        """更新行号显示 - 修复兼容问题"""
        # 兼容所有 Python 版本的获取行数方法
        line_count = int(self.source_text.index('end-1c').split('.')[0])
        
        # 更新行号文本框
        self.line_number_text.configure(state=tk.NORMAL)
        self.line_number_text.delete("1.0", tk.END)
        
        # 插入行号
        for i in range(1, line_count + 1):
            self.line_number_text.insert(tk.END, f"{i}\n")
        
        self.line_number_text.configure(state=tk.DISABLED)
        
        # 更新当前行高亮
        self._highlight_current_line()

    def _highlight_current_line(self):
        """高亮光标所在行"""
        # 移除之前的高亮
        self.source_text.tag_remove(self.highlight_tag, "1.0", tk.END)
        
        # 获取当前光标位置
        cursor_pos = self.source_text.index(tk.INSERT)
        line = cursor_pos.split(".")[0]
        
        # 高亮当前行
        self.source_text.tag_add(
            self.highlight_tag,
            f"{line}.0",
            f"{line}.end"
        )

    def _build_right_panel(self, parent):
        option_frame = ttk.LabelFrame(parent, text="分析选项")
        option_frame.pack(fill=tk.X, padx=8, pady=8)

        ttk.Radiobutton(option_frame, text="递归下降法", value="recursive", variable=self.parser_mode, command=self._schedule_parse).pack(side=tk.LEFT, padx=6, pady=6)
        ttk.Radiobutton(option_frame, text="LL(1) 法", value="ll1", variable=self.parser_mode, command=self._schedule_parse).pack(side=tk.LEFT, padx=6, pady=6)

        self.export_asm_button = ttk.Button(option_frame, text="生成 ASM 文件", command=self._export_asm_file, state=tk.DISABLED)
        self.export_asm_button.pack(side=tk.RIGHT, padx=6, pady=6)

        self._build_case_selector(parent)

        self.tab_control = ttk.Notebook(parent)
        self.tab_control.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self._build_tokens_tab()
        self._build_syntax_tree_tab()
        self._build_semantic_tab()
        self._build_future_stage_tabs()
        self._build_message_bar(parent)

    def _build_tokens_tab(self):
        token_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(token_tab, text="Token 表")

        columns = ("line", "lex", "type")
        self.token_tree = ttk.Treeview(token_tab, columns=columns, show="headings", selectmode="browse")
        self.token_tree.heading("line", text="行号")
        self.token_tree.heading("lex", text="词素")
        self.token_tree.heading("type", text="类型")
        self.token_tree.column("line", width=60, anchor=tk.CENTER)
        self.token_tree.column("lex", width=180, anchor=tk.W)
        self.token_tree.column("type", width=220, anchor=tk.W)
        self.token_tree.tag_configure("error", foreground="red")
        self.token_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(8, 0), pady=8)

        scrollbar = ttk.Scrollbar(token_tab, orient=tk.VERTICAL, command=self.token_tree.yview)
        self.token_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT, padx=(0, 8), pady=8)

    def _build_syntax_tree_tab(self):
        syntax_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(syntax_tab, text="语法树")

        # 启用自动换行，长的符号/节点描述将按单词边界换行显示
        self.syntax_tree_text = tk.Text(syntax_tab, wrap=tk.WORD, font=("Consolas", 11), state=tk.NORMAL)
        self.syntax_tree_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        x_scroll = ttk.Scrollbar(syntax_tab, orient=tk.HORIZONTAL, command=self.syntax_tree_text.xview)
        y_scroll = ttk.Scrollbar(syntax_tab, orient=tk.VERTICAL, command=self.syntax_tree_text.yview)
        self.syntax_tree_text.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)
        x_scroll.pack(fill=tk.X, side=tk.BOTTOM, padx=8)
        y_scroll.pack(fill=tk.Y, side=tk.RIGHT, padx=(0, 8))

    def _build_semantic_tab(self):
        semantic_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(semantic_tab, text="语义分析")

        self.semantic_text = tk.Text(semantic_tab, wrap=tk.WORD, font=("Consolas", 11), state=tk.NORMAL)
        self.semantic_text.insert("1.0", "等待输入源代码。")
        self.semantic_text.configure(state=tk.DISABLED)
        self.semantic_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _build_future_stage_tabs(self):
        self.intermediate_text = self._build_placeholder_tab("中间代码生成")
        self.optimized_text = self._build_placeholder_tab("中间代码优化")
        self.target_text = self._build_placeholder_tab("目标代码生成")

    def _build_placeholder_tab(self, title):
        tab = ttk.Frame(self.tab_control)
        self.tab_control.add(tab, text=title)
        text = tk.Text(tab, wrap=tk.WORD, font=("Consolas", 11), state=tk.NORMAL)
        text.insert("1.0", f"{title}模块预留，等待后续实现。")
        text.configure(state=tk.DISABLED)
        text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        return text

    def _build_case_selector(self, parent):
        case_frame = ttk.LabelFrame(parent, text="错误测试用例")
        case_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        self.case_combobox = ttk.Combobox(case_frame, values=self.error_case_names, state="readonly")
        self.case_combobox.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(8, 0), pady=8)
        self.case_combobox.bind("<<ComboboxSelected>>", lambda e: self._apply_selected_case())

        self.case_load_button = ttk.Button(case_frame, text="载入", command=self._apply_selected_case, state=tk.NORMAL if self.error_case_names else tk.DISABLED)
        self.case_load_button.pack(side=tk.RIGHT, padx=8, pady=8)

    def _build_message_bar(self, parent):
        message_frame = ttk.Frame(parent)
        message_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        self.message_label = ttk.Label(message_frame, text="就绪", anchor=tk.W)
        self.message_label.pack(fill=tk.X)

    def _on_source_modified(self, event=None):
        self.source_text.edit_modified(False)
        self._schedule_parse()
        self._update_line_numbers()  # 文本变更时更新行号

    def _on_editor_update(self, event=None):
        self._update_line_numbers()
        self._schedule_parse()

    def _schedule_parse(self):
        if self._parse_after_id is not None:
            self.after_cancel(self._parse_after_id)
        self._parse_after_id = self.after(1000, self._parse_source)

    def _parse_source(self):
        if self._parse_after_id is not None:
            self.after_cancel(self._parse_after_id)
            self._parse_after_id = None

        source_code = self.source_text.get("1.0", "end-1c")
        tokens = []
        syntax_tree = None
        syntax_error = None
        semantic_errors = []
        symtab = None
        quads = []
        optimized_quads = []
        asm_code = ""
        inter_error = None
        opt_error = None
        target_error = None
        lexical_errors = []

        if source_code.strip():
            tokenizer = Tokenizer(source_code)
            tokens, lexical_errors = tokenizer.tokenize(return_errors=True)
            if lexical_errors:
                syntax_error = None
            else:
                if self.parser_mode.get() == "recursive":
                    syntax_tree, syntax_error = recursive_syntax_analysis(tokens)
                else:
                    syntax_tree, syntax_error = ll1_syntax_analysis(tokens)

                if syntax_error is None and syntax_tree is not None:
                    symtab, semantic_errors = semantic_analyze(syntax_tree)

            if not syntax_error and not semantic_errors and syntax_tree is not None and symtab is not None:
                try:
                    quads, symtab = generate_intermediate_code(syntax_tree, symtab)
                except Exception as exc:
                    inter_error = f"中间代码生成错误：{exc}"

            if not inter_error and quads and symtab is not None:
                try:
                    optimized_quads = optimize_quadruples(quads)
                except Exception as exc:
                    opt_error = f"中间代码优化错误：{exc}"

            if not opt_error and optimized_quads and symtab is not None:
                try:
                    asm_code = generate_mips(optimized_quads, symtab)
                except Exception as exc:
                    target_error = f"目标代码生成错误：{exc}"

            if lexical_errors:
                message = f"词法分析发现 {len(lexical_errors)} 个错误。"
            elif syntax_error:
                message = syntax_error
            elif semantic_errors:
                message = f"语义分析发现 {len(semantic_errors)} 个错误。"
            elif inter_error:
                message = inter_error
            elif opt_error:
                message = opt_error
            elif target_error:
                message = target_error
            else:
                message = "词法、语法、语义、中间代码、优化和目标代码生成完成。"
        else:
            message = "请输入 SNL 代码以开始分析。"

        self.current_asm_code = asm_code
        self._update_token_table(tokens)
        self._update_syntax_tree(syntax_tree, syntax_error)
        self._update_semantic_result(symtab, semantic_errors, syntax_error, lexical_errors, bool(source_code.strip()))
        self._update_future_stage_tabs(
            syntax_error,
            semantic_errors,
            inter_error,
            opt_error,
            target_error,
            quads,
            optimized_quads,
            asm_code,
            bool(source_code.strip()),
        )
        self._update_messages(message)

    def _update_token_table(self, tokens):
        for item in self.token_tree.get_children():
            self.token_tree.delete(item)
        for index, token in enumerate(tokens):
            token_type = token.Sem.name if hasattr(token.Sem, "name") else str(token.Sem)
            tag = "error" if token_type == "ERROR" else ""
            self.token_tree.insert("", tk.END, values=(token.Lineshow, token.Lex, token_type), tags=(tag,))

    def _update_syntax_tree(self, syntax_tree, syntax_error):
        self.syntax_tree_text.configure(state=tk.NORMAL)
        self.syntax_tree_text.delete("1.0", tk.END)
        if syntax_error is not None:
            self.syntax_tree_text.insert("1.0", f"语法分析错误：{syntax_error}\n")
            if syntax_tree is not None:
                self.syntax_tree_text.insert("end", "\n当前语法树：\n")
                self.syntax_tree_text.insert("end", self._get_tree_text(syntax_tree))
        elif syntax_tree is None:
            self.syntax_tree_text.insert("1.0", "暂无语法树。请输入代码并选择递归下降法分析。")
        else:
            printed = self._get_tree_text(syntax_tree)
            self.syntax_tree_text.insert("1.0", printed)
        self.syntax_tree_text.configure(state=tk.DISABLED)

    def _update_semantic_result(self, symtab, semantic_errors, syntax_error, lexical_errors, has_source):
        self.semantic_text.configure(state=tk.NORMAL)
        self.semantic_text.delete("1.0", tk.END)

        if not has_source:
            self.semantic_text.insert("1.0", "等待输入源代码。")
        elif lexical_errors:
            self.semantic_text.insert("1.0", "词法分析错误：\n")
            for line, lex, message in lexical_errors:
                self.semantic_text.insert("end", f"Line {line}: {message} -> {lex}\n")
        elif syntax_error:
            self.semantic_text.insert("1.0", "语法分析未通过，暂不执行语义分析。")
        elif semantic_errors:
            self.semantic_text.insert("1.0", "\n".join(semantic_errors))
        elif symtab is not None:
            self.semantic_text.insert("1.0", self._get_symbol_table_text(symtab))
        else:
            self.semantic_text.insert("1.0", "语义分析完成，未发现错误。")

        self.semantic_text.configure(state=tk.DISABLED)

    def _update_future_stage_tabs(
        self,
        syntax_error,
        semantic_errors,
        inter_error,
        opt_error,
        target_error,
        quads,
        optimized_quads,
        asm_code,
        has_source,
    ):
        if not has_source:
            intermediate_status = "等待输入源代码。"
            optimized_status = "等待输入源代码。"
            target_status = "等待输入源代码。"
        elif syntax_error:
            intermediate_status = "前序语法分析未通过，暂不执行中间代码生成。"
            optimized_status = "前序语法分析未通过，暂不执行中间代码优化。"
            target_status = "前序语法分析未通过，暂不执行目标代码生成。"
        elif semantic_errors:
            intermediate_status = "前序语义分析未通过，暂不执行中间代码生成。"
            optimized_status = "前序语义分析未通过，暂不执行中间代码优化。"
            target_status = "前序语义分析未通过，暂不执行目标代码生成。"
        elif inter_error:
            intermediate_status = inter_error
            optimized_status = "中间代码生成未通过，暂不执行中间代码优化。"
            target_status = "中间代码生成未通过，暂不执行目标代码生成。"
        elif opt_error:
            intermediate_status = self._get_quadruple_text(quads)
            optimized_status = opt_error
            target_status = "中间代码优化未通过，暂不执行目标代码生成。"
        elif target_error:
            intermediate_status = self._get_quadruple_text(quads)
            optimized_status = self._get_quadruple_text(optimized_quads)
            target_status = target_error
        else:
            intermediate_status = self._get_quadruple_text(quads)
            optimized_status = self._get_quadruple_text(optimized_quads)
            target_status = asm_code if asm_code.strip() else "目标代码生成完成，但 ASM 内容为空。"

        self._set_text_content(self.intermediate_text, intermediate_status)
        self._set_text_content(self.optimized_text, optimized_status)
        self._set_text_content(self.target_text, target_status)
        self.export_asm_button.configure(state=tk.NORMAL if asm_code.strip() else tk.DISABLED)

    def _set_text_content(self, text_widget, content):
        text_widget.configure(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", content)
        text_widget.configure(state=tk.DISABLED)

    def _export_asm_file(self):
        if not self.current_asm_code.strip():
            messagebox.showwarning("无法生成 ASM 文件", "当前没有可导出的目标代码。")
            return

        path = filedialog.asksaveasfilename(
            title="生成 ASM 文件",
            defaultextension=".asm",
            filetypes=(("ASM files", "*.asm"), ("Text files", "*.txt"), ("All files", "*.*")),
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8", newline="\n") as asm_file:
                asm_file.write(self.current_asm_code)
        except OSError as exc:
            messagebox.showerror("生成 ASM 文件失败", str(exc))
            return

        self._update_messages(f"ASM 文件已生成：{path}")

    @staticmethod
    def _get_tree_text(syntax_tree):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            syntax_tree.print()
        return buffer.getvalue()

    @staticmethod
    def _get_symbol_table_text(symtab):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            symtab.print_table()
        text = buffer.getvalue()
        return text if text.strip() else "语义分析完成，符号表为空。"

    @staticmethod
    def _get_quadruple_text(quads):
        if not quads:
            return "中间代码生成完成，但四元式列表为空。"
        return "\n".join(f"{index:03}: {quad}" for index, quad in enumerate(quads))

    def _update_messages(self, message):
        self.message_label.config(text=message)


if __name__ == "__main__":
    app = SNLAnalyzerApp()
    app.mainloop()
