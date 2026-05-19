import io
import tkinter as tk
from contextlib import redirect_stdout
from tkinter import ttk
import importlib


try:
    make_token = importlib.import_module("1_lexer")
    syntax = importlib.import_module("2_recursive_descent_parser")
    semantic_analysis = importlib.import_module("3_semantic_analyzer")
    ll1_parser = importlib.import_module("ll1_parser")
    Tokenizer = make_token.Tokenizer
    recursive_syntax_analysis = syntax.syntax_analysis
    ll1_syntax_analysis = ll1_parser.Program
    semantic_analyze = semantic_analysis.semantic_analysis
except (ImportError, FileNotFoundError, AttributeError):
    class Tokenizer:
        def __init__(self, code):
            self.code = code
        def tokenize(self):
            return []
    def recursive_syntax_analysis(tokens):
        return None, "依赖模块未找到，请检查 1_lexer.py 和 2_recursive_descent_parser.py"
    def ll1_syntax_analysis(tokens):
        return None, "依赖模块未找到，请检查 ll1_parser.py"
    def semantic_analyze(program):
        return None, ["依赖模块未找到，请检查 3_semantic_analyzer.py"]


class SNLAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SNL 实时前端分析器")
        self.geometry("1120x720")
        self.resizable(True, True)

        self.parser_mode = tk.StringVar(value="recursive")
        self._parse_after_id = None

        # 高亮标签样式
        self.highlight_tag = "current_line"

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
        self.token_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(8, 0), pady=8)

        scrollbar = ttk.Scrollbar(token_tab, orient=tk.VERTICAL, command=self.token_tree.yview)
        self.token_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT, padx=(0, 8), pady=8)

    def _build_syntax_tree_tab(self):
        syntax_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(syntax_tab, text="语法树")

        self.syntax_tree_text = tk.Text(syntax_tab, wrap=tk.NONE, font=("Consolas", 11), state=tk.NORMAL)
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

        if source_code.strip():
            tokenizer = Tokenizer(source_code)
            tokens = tokenizer.tokenize()
            if self.parser_mode.get() == "recursive":
                syntax_tree, syntax_error = recursive_syntax_analysis(tokens)
            else:
                syntax_tree, syntax_error = ll1_syntax_analysis(tokens)

            if syntax_error is None and syntax_tree is not None:
                symtab, semantic_errors = semantic_analyze(syntax_tree)

            if syntax_error:
                message = syntax_error
            elif semantic_errors:
                message = f"语义分析发现 {len(semantic_errors)} 个错误。"
            else:
                message = "词法、语法、语义分析完成。"
        else:
            message = "请输入 SNL 代码以开始分析。"

        self._update_token_table(tokens)
        self._update_syntax_tree(syntax_tree, syntax_error)
        self._update_semantic_result(symtab, semantic_errors, syntax_error, bool(source_code.strip()))
        self._update_future_stage_tabs(syntax_error, semantic_errors, bool(source_code.strip()))
        self._update_messages(message)

    def _update_token_table(self, tokens):
        for item in self.token_tree.get_children():
            self.token_tree.delete(item)
        for index, token in enumerate(tokens):
            token_type = token.Sem.name if hasattr(token.Sem, "name") else str(token.Sem)
            self.token_tree.insert("", tk.END, values=(token.Lineshow, token.Lex, token_type))

    def _update_syntax_tree(self, syntax_tree, syntax_error):
        self.syntax_tree_text.configure(state=tk.NORMAL)
        self.syntax_tree_text.delete("1.0", tk.END)
        if syntax_error:
            self.syntax_tree_text.insert("1.0", f"语法分析错误：{syntax_error}\n")
        elif syntax_tree is None:
            self.syntax_tree_text.insert("1.0", "暂无语法树。请输入代码并选择递归下降法分析。")
        else:
            printed = self._get_tree_text(syntax_tree)
            self.syntax_tree_text.insert("1.0", printed)
        self.syntax_tree_text.configure(state=tk.DISABLED)

    def _update_semantic_result(self, symtab, semantic_errors, syntax_error, has_source):
        self.semantic_text.configure(state=tk.NORMAL)
        self.semantic_text.delete("1.0", tk.END)

        if not has_source:
            self.semantic_text.insert("1.0", "等待输入源代码。")
        elif syntax_error:
            self.semantic_text.insert("1.0", "语法分析未通过，暂不执行语义分析。")
        elif semantic_errors:
            self.semantic_text.insert("1.0", "\n".join(semantic_errors))
        elif symtab is not None:
            self.semantic_text.insert("1.0", self._get_symbol_table_text(symtab))
        else:
            self.semantic_text.insert("1.0", "语义分析完成，未发现错误。")

        self.semantic_text.configure(state=tk.DISABLED)

    def _update_future_stage_tabs(self, syntax_error, semantic_errors, has_source):
        if not has_source:
            status = "等待输入源代码。"
        elif syntax_error:
            status = "前序语法分析未通过，暂不执行该阶段。"
        elif semantic_errors:
            status = "前序语义分析未通过，暂不执行该阶段。"
        else:
            status = "前序分析已通过。本模块预留，等待后续实现。"

        for text in (self.intermediate_text, self.optimized_text, self.target_text):
            text.configure(state=tk.NORMAL)
            text.delete("1.0", tk.END)
            text.insert("1.0", status)
            text.configure(state=tk.DISABLED)

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

    def _update_messages(self, message):
        self.message_label.config(text=message)


if __name__ == "__main__":
    app = SNLAnalyzerApp()
    app.mainloop()
