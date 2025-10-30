#!/usr/bin/env python3

import os
import sys
import json
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List, Set, Tuple, Dict

# Reuse normalization logic from CLI module
try:
    from dedupe_us_numbers import normalize_us_number, read_lines_from_file, write_lines_to_file, dedupe_numbers
except Exception as e:
    print("Failed to import dedupe_us_numbers.py. Ensure it is in the same directory.", file=sys.stderr)
    raise


class DedupeGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("美国号码去重 | Base vs New")
        self.geometry("1100x700")

        self.base_path_var = tk.StringVar()
        self.new_path_var = tk.StringVar()
        self.keep_order_var = tk.BooleanVar(value=True)
        self.sort_output_var = tk.BooleanVar(value=False)

        self.duplicates: List[str] = []
        self.uniques_new: List[str] = []  # unique numbers present only in new file
        self.base_unique: List[str] = []   # normalized & unique from base
        self.new_unique_all: List[str] = []  # for multiple new files combined

        self.prefs_path = os.path.join(os.path.dirname(__file__), "app_prefs.json")
        self._load_prefs()

        self._build_ui()
        self._apply_prefs()

    def _build_ui(self) -> None:
        # Menu bar
        menubar = tk.Menu(self)
        menu_file = tk.Menu(menubar, tearoff=0)
        menu_file.add_command(label="打开底库文件夹…", command=self._choose_base_dir)
        menu_file.add_command(label="打开底库文件(单个TXT)…", command=self._choose_base_file, accelerator="Cmd+B")
        menu_file.add_command(label="打开新导入…", command=self._choose_new_multi, accelerator="Cmd+N")
        menu_file.add_separator()
        menu_file.add_command(label="导出重复…", command=self._export_duplicates)
        menu_file.add_command(label="导出仅新唯一…", command=self._export_uniques)
        menu_file.add_command(label="导出详细CSV报告…", command=self._export_csv_report)
        menu_file.add_separator()
        menu_file.add_command(label="清空会话", command=self._clear_session)
        menu_file.add_separator()
        menu_file.add_command(label="退出", command=self.destroy)
        menubar.add_cascade(label="文件", menu=menu_file)

        menu_actions = tk.Menu(menubar, tearoff=0)
        menu_actions.add_command(label="分析对比", command=self._analyze, accelerator="Cmd+Enter")
        menu_actions.add_command(label="更新底库=底库∪新唯一…", command=self._update_base)
        menu_actions.add_command(label="将仅新唯一另存为新底库…", command=self._save_uniques_as_base)
        menubar.add_cascade(label="操作", menu=menu_actions)

        menu_view = tk.Menu(menubar, tearoff=0)
        menu_view.add_checkbutton(label="保持原始顺序", variable=self.keep_order_var, command=self._refresh_lists)
        menu_view.add_checkbutton(label="按号码排序显示", variable=self.sort_output_var, command=self._refresh_lists)
        menubar.add_cascade(label="视图", menu=menu_view)

        menu_help = tk.Menu(menubar, tearoff=0)
        menu_help.add_command(label="关于", command=self._show_about)
        menubar.add_cascade(label="帮助", menu=menu_help)

        self.config(menu=menubar)

        # Top area
        frm_top = ttk.Frame(self)
        frm_top.pack(fill=tk.X, padx=10, pady=10)

        # Base path row (folder or single TXT)
        ttk.Label(frm_top, text="底库路径（文件夹或TXT）:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(frm_top, textvariable=self.base_path_var, width=80).grid(row=0, column=1, padx=6)
        btns = ttk.Frame(frm_top)
        btns.grid(row=0, column=2)
        ttk.Button(btns, text="选文件夹", command=self._choose_base_dir).pack(side=tk.LEFT)
        ttk.Button(btns, text="选文件", command=self._choose_base_file).pack(side=tk.LEFT, padx=(6,0))

        # New file row
        ttk.Label(frm_top, text="新导入文件(可多选):").grid(row=1, column=0, sticky=tk.W, pady=(6, 0))
        ttk.Entry(frm_top, textvariable=self.new_path_var, width=80).grid(row=1, column=1, padx=6, pady=(6, 0))
        ttk.Button(frm_top, text="选择…", command=self._choose_new_multi).grid(row=1, column=2, pady=(6, 0))

        # Actions
        frm_actions = ttk.Frame(self)
        frm_actions.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(frm_actions, text="分析对比", command=self._analyze).pack(side=tk.LEFT)
        ttk.Button(frm_actions, text="导出重复", command=self._export_duplicates).pack(side=tk.LEFT, padx=8)
        ttk.Button(frm_actions, text="导出仅新文件唯一", command=self._export_uniques).pack(side=tk.LEFT)
        ttk.Button(frm_actions, text="导出详细CSV报告", command=self._export_csv_report).pack(side=tk.LEFT, padx=8)
        ttk.Button(frm_actions, text="更新底库=底库∪新唯一(另存)", command=self._update_base).pack(side=tk.LEFT)
        ttk.Button(frm_actions, text="清理并规范化底库(覆盖)", command=self._clean_base_file).pack(side=tk.LEFT, padx=8)
        ttk.Button(frm_actions, text="追加新唯一到底库(覆盖)", command=self._append_uniques_to_base).pack(side=tk.LEFT)
        ttk.Button(frm_actions, text="将仅新唯一另存为新底库", command=self._save_uniques_as_base).pack(side=tk.LEFT, padx=8)

        # Stats
        self.stats_var = tk.StringVar(value="请选择文件并点击‘分析对比’…")
        ttk.Label(self, textvariable=self.stats_var).pack(fill=tk.X, padx=10)

        # Paned view for lists
        paned = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Duplicates panel
        frm_dup = ttk.Labelframe(paned, text="重复（出现在两边）")
        self.list_duplicates = tk.Listbox(frm_dup)
        scrollbar_dup = ttk.Scrollbar(frm_dup, orient=tk.VERTICAL, command=self.list_duplicates.yview)
        self.list_duplicates.configure(yscrollcommand=scrollbar_dup.set)
        self.list_duplicates.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_dup.pack(side=tk.RIGHT, fill=tk.Y)

        # Uniques panel
        frm_unique = ttk.Labelframe(paned, text="仅新文件中的唯一（可加入底库）")
        self.list_uniques = tk.Listbox(frm_unique)
        scrollbar_uni = ttk.Scrollbar(frm_unique, orient=tk.VERTICAL, command=self.list_uniques.yview)
        self.list_uniques.configure(yscrollcommand=scrollbar_uni.set)
        self.list_uniques.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_uni.pack(side=tk.RIGHT, fill=tk.Y)

        paned.add(frm_dup, weight=1)
        paned.add(frm_unique, weight=1)
        self.frm_dup = frm_dup
        self.frm_unique = frm_unique

        # Status bar
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = ttk.Label(status_frame, anchor=tk.W, text="就绪")
        self.status_label.pack(fill=tk.X, padx=10, pady=(0, 4))
        self.progress = ttk.Progressbar(status_frame, mode="determinate", maximum=100)
        self.progress.pack(fill=tk.X, padx=10, pady=(0, 8))

        # Shortcuts
        self.bind_all("<Command-b>", lambda e: self._choose_base())
        self.bind_all("<Command-n>", lambda e: self._choose_new_multi())
        self.bind_all("<Command-Return>", lambda e: self._analyze())

    def _choose_base_file(self) -> None:
        path = filedialog.askopenfilename(title="选择底库 TXT", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            self.base_path_var.set(path)
            self._set_status(f"底库文件已选择：{os.path.basename(path)}")
    
    def _choose_base_dir(self) -> None:
        path = filedialog.askdirectory(title="选择底库文件夹")
        if path:
            self.base_path_var.set(path)
            self._set_status(f"底库文件夹已选择：{os.path.basename(path)}")

    def _iter_txt_files(self, folder: str) -> List[str]:
        try:
            names = sorted(os.listdir(folder))
        except Exception:
            return []
        out: List[str] = []
        for name in names:
            p = os.path.join(folder, name)
            if os.path.isfile(p) and name.lower().endswith('.txt'):
                out.append(p)
        return out
    
    # no folder iterator needed for fixed file mode

    def _choose_new_multi(self) -> None:
        paths = filedialog.askopenfilenames(title="选择新导入 TXT（可多选）", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not paths:
            return
        self.new_path_var.set("; ".join(paths))
        self._set_status(f"新导入已选择：{len(paths)} 个文件")

    def _read_and_normalize(self, path: str) -> List[str]:
        lines = list(read_lines_from_file(path))
        normalized: List[str] = []
        for line in lines:
            ok, e164 = normalize_us_number(line)
            if ok:
                normalized.append(e164)
        unique = list(dict.fromkeys(normalized))  # preserve order unique
        return unique

    def _analyze(self) -> None:
        base = self.base_path_var.get().strip()
        new_value = self.new_path_var.get().strip()
        if not base or (not os.path.isfile(base) and not os.path.isdir(base)):
            messagebox.showerror("错误", "请先选择有效的底库路径（文件夹或TXT）")
            return
        if not new_value:
            messagebox.showerror("错误", "请先选择有效的新导入 TXT 文件(可多选)")
            return

        try:
            paths_new: List[str] = []
            for p in new_value.split(";"):
                p = p.strip()
                if not p:
                    continue
                if not os.path.isfile(p):
                    continue
                paths_new.append(p)

            total_steps = 1 + len(paths_new)
            step_idx = 0
            self._progress_start(total_steps, label="读取底库…")

            # read base: folder of .txt files OR single TXT file
            if os.path.isdir(base):
                base_files = self._iter_txt_files(base)
                base_numbers: List[str] = []
                for fp in base_files:
                    base_numbers.extend(self._read_and_normalize(fp))
                self.base_unique = list(dict.fromkeys(base_numbers))
            else:
                self.base_unique = self._read_and_normalize(base)
            step_idx += 1
            self._progress_step(step_idx, total_steps, label="读取新文件…")

            new_unique_all: List[str] = []
            for p in paths_new:
                new_unique_all.extend(self._read_and_normalize(p))
                step_idx += 1
                self._progress_step(step_idx, total_steps, label=f"已处理 {step_idx}/{total_steps}")
            # order-unique combined
            self.new_unique_all = list(dict.fromkeys(new_unique_all))
        except Exception as e:
            messagebox.showerror("读取失败", str(e))
            return
        finally:
            self._progress_done()

        set_base: Set[str] = set(self.base_unique)
        set_new: Set[str] = set(self.new_unique_all)

        self.duplicates = [n for n in self.new_unique_all if n in set_base]
        self.uniques_new = [n for n in self.new_unique_all if n not in set_base]

        self._refresh_lists()

        self.stats_var.set(
            f"底库有效唯一：{len(self.base_unique)}，新文件有效唯一：{len(set_new)}；重复：{len(self.duplicates)}，仅新唯一：{len(self.uniques_new)}"
        )
        try:
            self.frm_dup.configure(text=f"重复（出现在两边）— {len(self.duplicates)} 条")
            self.frm_unique.configure(text=f"仅新文件中的唯一（可加入底库）— {len(self.uniques_new)} 条")
        except Exception:
            pass
        self._set_status("分析完成")
        self._progress_done()

    def _refresh_lists(self) -> None:
        self.list_duplicates.delete(0, tk.END)
        self.list_uniques.delete(0, tk.END)
        dupes = list(self.duplicates)
        uniques = list(self.uniques_new)
        if self.sort_output_var.get():
            dupes.sort()
            uniques.sort()
        for n in dupes:
            self.list_duplicates.insert(tk.END, n)
        for n in uniques:
            self.list_uniques.insert(tk.END, n)

    def _suggest_path(self, base_path: str, suffix: str) -> str:
        if os.path.isdir(base_path):
            return os.path.join(base_path, f"base_{suffix}.txt")
        root, ext = os.path.splitext(base_path)
        return f"{root}.{suffix}.txt"

    def _export_duplicates(self) -> None:
        if not self.duplicates:
            messagebox.showinfo("提示", "没有可导出的重复数据")
            return
        base = self.base_path_var.get().strip() or os.getcwd()
        default_path = self._suggest_path(base, "duplicates")
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=os.path.basename(default_path))
        if not path:
            return
        try:
            write_lines_to_file(path, self.duplicates)
            messagebox.showinfo("成功", f"已导出重复：{len(self.duplicates)} 条\n{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def _export_uniques(self) -> None:
        if not self.uniques_new:
            messagebox.showinfo("提示", "没有可导出的仅新文件唯一数据")
            return
        new = self.new_path_var.get().strip() or os.getcwd()
        default_path = self._suggest_path(new, "uniques")
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=os.path.basename(default_path))
        if not path:
            return
        try:
            write_lines_to_file(path, self.uniques_new)
            messagebox.showinfo("成功", f"已导出仅新唯一：{len(self.uniques_new)} 条\n{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def _export_csv_report(self) -> None:
        base = self.base_unique
        new_all = self.new_unique_all
        if not base and not new_all:
            messagebox.showinfo("提示", "请先点击‘分析对比’生成结果")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="report.csv")
        if not path:
            return
        try:
            set_base = set(base)
            set_new = set(new_all)
            all_numbers = list(dict.fromkeys(base + new_all))
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["number", "in_base", "in_new", "status"])  # status: duplicate/new_unique/base_only
                for n in all_numbers:
                    in_base = n in set_base
                    in_new = n in set_new
                    if in_base and in_new:
                        status = "duplicate"
                    elif in_new and not in_base:
                        status = "new_unique"
                    else:
                        status = "base_only"
                    writer.writerow([n, int(in_base), int(in_new), status])
            messagebox.showinfo("成功", f"已导出 CSV 报告\n{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def _update_base(self) -> None:
        if not self.base_unique and not self.uniques_new:
            messagebox.showinfo("提示", "请先点击‘分析对比’生成结果")
            return
        merged = list(dict.fromkeys(self.base_unique + self.uniques_new))
        base = self.base_path_var.get().strip()
        default_path = self._suggest_path(base, "updated_base")
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=os.path.basename(default_path))
        if not path:
            return
        try:
            write_lines_to_file(path, merged)
            messagebox.showinfo("成功", f"已写入新的底库数据，共 {len(merged)} 条\n{path}")
        except Exception as e:
            messagebox.showerror("写入失败", str(e))

    def _clean_base_file(self) -> None:
        base = self.base_path_var.get().strip()
        if not base or not os.path.isfile(base):
            messagebox.showerror("错误", "当前操作需要选择‘单个TXT’作为底库文件")
            return
        cleaned = self._read_and_normalize(base)
        try:
            write_lines_to_file(base, cleaned)
            self.base_unique = cleaned
            self._set_status(f"已清理并规范化底库，共 {len(cleaned)} 条")
            messagebox.showinfo("成功", f"已清理并规范化底库，共 {len(cleaned)} 条\n{base}")
        except Exception as e:
            messagebox.showerror("写入失败", str(e))

    def _append_uniques_to_base(self) -> None:
        base = self.base_path_var.get().strip()
        if not base or not os.path.isfile(base):
            messagebox.showerror("错误", "请先选择有效的固定底库 TXT 文件")
            return
        if not self.uniques_new and not self.base_unique:
            messagebox.showinfo("提示", "请先分析，或无可追加数据")
            return
        merged = list(dict.fromkeys(self.base_unique + self.uniques_new))
        try:
            write_lines_to_file(base, merged)
            self.base_unique = merged
            self._set_status(f"已将新唯一追加到底库，共 {len(merged)} 条")
            messagebox.showinfo("成功", f"已将新唯一追加到底库，共 {len(merged)} 条\n{base}")
        except Exception as e:
            messagebox.showerror("写入失败", str(e))

    def _save_uniques_as_base(self) -> None:
        if not self.uniques_new:
            messagebox.showinfo("提示", "暂无‘仅新唯一’可保存")
            return
        base = self.base_path_var.get().strip() or os.getcwd()
        default_path = self._suggest_path(base, "new_base_uniques")
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=os.path.basename(default_path))
        if not path:
            return
        try:
            write_lines_to_file(path, self.uniques_new)
            messagebox.showinfo("成功", f"已保存为新底库，共 {len(self.uniques_new)} 条\n{path}")
        except Exception as e:
            messagebox.showerror("写入失败", str(e))

    def _clear_session(self) -> None:
        self.base_path_var.set("")
        self.new_path_var.set("")
        self.duplicates = []
        self.uniques_new = []
        self.base_unique = []
        self.new_unique_all = []
        self._refresh_lists()
        self.stats_var.set("已清空当前会话")
        self._set_status("已清空")

    def _show_about(self) -> None:
        messagebox.showinfo("关于", "美国号码去重工具\nE.164 标准化 + 去重\n支持多文件对比、CSV 报告与底库更新")

    def _set_status(self, text: str) -> None:
        self.status_label.configure(text=text)
        self.update_idletasks()

    def _progress_start(self, total: int, label: str = "处理中…") -> None:
        try:
            self.progress.configure(maximum=100, value=0, mode="determinate")
            self._set_status(label)
            self.update_idletasks()
        except Exception:
            pass

    def _progress_step(self, current: int, total: int, label: str = "") -> None:
        try:
            pct = int(current * 100 / max(total, 1))
            self.progress.configure(value=pct)
            if label:
                self._set_status(label)
            self.update_idletasks()
        except Exception:
            pass

    def _progress_done(self) -> None:
        try:
            self.progress.configure(value=0)
            self.update_idletasks()
        except Exception:
            pass

    def _load_prefs(self) -> None:
        try:
            if os.path.isfile(self.prefs_path):
                with open(self.prefs_path, "r", encoding="utf-8") as f:
                    data: Dict[str, str] = json.load(f)
                self.base_path_var.set(data.get("last_base", ""))
                self.new_path_var.set(data.get("last_new", ""))
                self.keep_order_var.set(bool(data.get("keep_order", True)))
                self.sort_output_var.set(bool(data.get("sort_output", False)))
        except Exception:
            pass

    def _apply_prefs(self) -> None:
        try:
            self.after(100, self._save_prefs)
        except Exception:
            pass

    def _save_prefs(self) -> None:
        try:
            data = {
                "last_base": self.base_path_var.get(),
                "last_new": self.new_path_var.get(),
                "keep_order": bool(self.keep_order_var.get()),
                "sort_output": bool(self.sort_output_var.get()),
            }
            with open(self.prefs_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        finally:
            # save periodically
            self.after(2000, self._save_prefs)


def main() -> int:
    app = DedupeGUI()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


