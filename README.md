## 美国号码去重工具（TXT + GUI）

一个简单的命令行工具，读取 TXT 文件中的美国手机号码，自动归一化为 E.164 格式（+1XXXXXXXXXX），并完成去重与导出。

特点：
- 支持多种常见格式：如 (123) 456-7890、123-456-7890、+1 123 456 7890、1-123-456-7890 等
- 自动忽略分隔符、括号、小数点、空格、分机（x / ext / # 后内容）
- 严格校验为美国号码（10 位 NANP，或 1 开头的 11 位，或 +1 开头的 10 位）
- 输出为标准 E.164：`+1XXXXXXXXXX`
- 支持保持原始顺序或排序输出，支持统计信息

### 环境要求
- macOS（已在 Apple Silicon M2 Max 上可用）
- Python 3.8+（macOS 通常自带；如需可通过 Homebrew 安装）

### 文件说明
- `dedupe_us_numbers.py`：命令行主程序
- `gui_dedupe.py`：图形界面（Tkinter）
- `启动号码去重GUI.command`：双击启动 GUI
- `打包macOS应用.command`：一键打包为 .app

### 快速开始
1. 打开终端，进入项目目录：

```bash
cd "/Users/hello/短信料/去重"
```

2. 运行命令行工具（最简单用法，输入文件为 `input.txt`）：

```bash
python3 dedupe_us_numbers.py input.txt
```
### 图形界面（GUI）
1. 启动：

```bash
python3 gui_dedupe.py
```

或直接双击：

- Finder 进入目录：`/Users/hello/短信料/去重`
- 双击 `启动号码去重GUI.command`
打不开怎么办
- 第一次被阻止：右键 `启动号码去重GUI.command` → 打开；或到“系统设置 → 隐私与安全性”里允许。
- 仍打不开：打开终端运行以下命令查看错误日志（同目录会生成 `last_run.log`）：

```bash
cd "/Users/hello/短信料/去重"
./启动号码去重GUI.command
open last_run.log
```

- 如果提示“未找到 python3”：安装 Python3 后再试：`brew install python`
- 如果提示“权限/隔离”问题：

```bash
chmod +x "启动号码去重GUI.command"
xattr -d com.apple.quarantine "启动号码去重GUI.command" 2>/dev/null || true
```

### 一键自检
- 双击 `运行自检.command`，自动检测 Python/Tkinter/核心模块，弹窗显示结果；详细日志见 `self_check.log`。


2. 在界面中：
- 选择底库路径：支持选择“文件夹”（会读取该文件夹下所有 .txt）或“单个 TXT 文件”（仅读取该文件）
- 选择新导入 TXT（支持多选，自动合并）
- 点击“分析对比”查看：
  - 重复（同时出现在底库与新导入）
  - 仅新文件中的唯一（可加入底库）
- 可执行：
  - “导出重复” → 保存重复号码列表
  - “导出仅新文件唯一” → 保存仅新唯一列表
  - “导出详细CSV报告” → 包含每个号码是否在底库/新文件、状态（duplicate/new_unique/base_only）
  - “更新底库=底库∪新唯一(另存)” → 生成新的底库文件（将新唯一合并到旧底库，自动去重、保持顺序）
  - “清理并规范化底库(覆盖)” → 直接把当前底库文件清洗、归一化并去重后覆盖写回
  - “追加新唯一到底库(覆盖)” → 将“仅新唯一”合并写回到底库文件
  - “将仅新唯一另存为新底库” → 以仅新唯一保存成新的底库

3. 高级与偏好
- 菜单栏：文件、操作、视图、帮助
- 视图选项：保持原始顺序 / 按号码排序显示
- 记忆上次选择：自动保存上次选择的底库和新文件
- 快捷键：打开底库 Cmd+B；打开新导入 Cmd+N；分析对比 Cmd+Enter

4. 常见问题（GUI/双击）
### 打包为 macOS 应用（.app）
- 前提：首次需安装 PyInstaller（脚本会自动安装）
- 双击 `打包macOS应用.command` 或在终端执行：

```bash
cd "/Users/hello/短信料/去重"
./打包macOS应用.command
```

完成后会在 `dist/` 目录生成 `美国号码去重.app`，可像普通软件一样双击运行。

注意：`dist/` 里若出现两个同名项（`美国号码去重.app` 和 没有扩展名的 `美国号码去重`），请双击 `.app` 结尾的那个；另一个是构建产物，已在脚本中自动清理，如仍出现可手动删除。
- 双击无反应或提示“未找到 python3”：
  - 终端执行 `python3 --version` 检查
  - 未安装可用 Homebrew：`brew install python`
- 双击时被系统安全阻止：
  - 右键 `启动号码去重GUI.command` → 打开（或在“系统设置-隐私与安全性”允许）



默认会在同目录生成 `input.deduped.txt`，文件内每行一个唯一的 E.164 格式号码。

### 常用用法
- 指定输出文件：

```bash
python3 dedupe_us_numbers.py input.txt -o output.txt
```

- 输出前显示统计信息（总行数、有效美国号码数、去重后唯一数量）：

```bash
python3 dedupe_us_numbers.py input.txt --show-stats
```

- 不保留原始顺序、以字典序排序输出：

```bash
python3 dedupe_us_numbers.py input.txt --no-keep-order
```

### 输入格式说明
- 输入文件为 TXT，每行一个号码（允许混合格式，工具会自动识别和规范化）
- 示例可被识别：
  - `1234567890`
  - `(123) 456-7890`
  - `123-456-7890`
  - `+1 123 456 7890`
  - `1-123-456-7890`
  - `123.456.7890 x123`（分机会被忽略）

### 输出格式
- 仅导出有效的美国号码，格式统一为 `+1XXXXXXXXXX`

### 失败/过滤规则
- 不是 10 位美国号码或不属于 `+1` 的，将被过滤
- 含有无效字符或长度不匹配的行将被忽略

### 例子
假设 `numbers.txt` 内容如下：

```
(415) 555-1234
1-415-555-1234
+1 415 555 1234
415.555.1234 x200
999
```

运行：

```bash
python3 dedupe_us_numbers.py numbers.txt --show-stats
```

输出（`numbers.deduped.txt`）：

```
+14155551234
```

终端统计示例：

```
Total lines: 5
Valid US numbers: 4
Unique after dedupe: 1
Wrote 1 unique numbers to: /path/to/numbers.deduped.txt
```

### 常见问题
- 报 `input file not found`：请检查传入的文件路径是否正确，建议使用绝对路径。
- Python 版本问题：运行 `python3 --version` 查看版本，如需更新可用 Homebrew：`brew install python`


