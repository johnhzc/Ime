# 五笔输入法 (Wubi IME) — Agent 开发指南

> 本文件面向 AI 编程 Agent。假设读者对项目一无所知，请按以下实际内容操作，不要依赖假设或通用推断。

## 项目概述

这是一个面向 Windows 10/11 的纯 Python 五笔输入法程序，采用五笔 86 版编码表。程序通过全局键盘钩子拦截编码键，使用 Windows `SendInput` API 向当前应用程序输出 Unicode 文本，并用 `tkinter` 绘制候选窗口与状态窗口。

- 项目语言：中文（代码注释、文档、UI 文本均为中文）
- 版本：`1.0.0`
- 许可证：MIT License

## 技术栈

- **Python 3.8+**
- **keyboard**：全局键盘监听与按键拦截（WH_KEYBOARD_LL 钩子）
- **pynput**：早期/辅助键盘监听依赖
- **pywin32**：Windows API 调用（SendInput）
- **tkinter**：候选窗口、状态窗口 UI（Python 自带）
- **pystray**：系统托盘图标（可选）
- **Pillow**：用于动态生成托盘图标
- **json**：五笔编码表数据存储
- **PyInstaller**：打包为单文件可执行程序 `WubiIME.exe`

## 项目结构

```
.
├── wubi_ime/                  # 主包
│   ├── __init__.py            # 包初始化，定义 __version__ = "1.0.0"
│   ├── main.py                # 主程序入口与 WubiIME 协调类
│   ├── launcher.py            # PyInstaller 打包入口，处理 sys._MEIPASS 路径
│   ├── engine.py              # 五笔编码引擎（Action 枚举、WubiEngine 类）
│   ├── wubi_table.py          # 编码表加载与查询（WubiTable 类）
│   ├── keyboard_handler.py    # 全局键盘监听（KeyboardHandler 类）
│   ├── config.py              # 配置管理（Config 类）
│   ├── ui/                    # UI 模块
│   │   ├── __init__.py
│   │   ├── candidate_window.py # 候选窗口
│   │   ├── status_window.py   # 状态窗口
│   │   └── tray_icon.py       # 系统托盘图标
│   ├── data/                  # 数据文件
│   │   └── wubi_86.json       # 86 版五笔编码表
│   └── tests/                 # 单元测试目录（当前为空）
├── wubi_config.json           # 用户配置文件（运行时生成）
├── requirements.txt           # 依赖列表（位于 wubi_ime/requirements.txt）
├── build.py                   # PyInstaller 打包脚本
├── WubiIME.spec               # PyInstaller spec 文件
├── test_wubi_simple.py        # 键盘钩子与输出诊断脚本
├── build/                     # PyInstaller 构建输出
└── dist/                      # 打包产物目录
```

## 主要模块与边界

| 文件 | 职责 | 禁止事项 |
|------|------|----------|
| `wubi_table.py` | 加载 `wubi_86.json`，维护 `char→code` 与 `code→chars` 映射，提供精确匹配与前缀查询 | 不涉及 UI 或键盘 |
| `engine.py` | 处理按键，维护当前编码、候选列表、分页、中英文模式，返回 `Action` 枚举 | 不直接操作键盘或 UI |
| `keyboard_handler.py` | 使用 `keyboard` 库注册全局钩子；钩子回调只做快速拦截判断并将事件加入线程安全队列，由主线程取出处理 | 不处理编码逻辑；禁止在钩子回调中执行 UI 更新或 SendInput |
| `ui/candidate_window.py` | 显示候选窗口、编码提示、页码，支持鼠标点击选词 | 不处理业务逻辑 |
| `ui/status_window.py` | 显示屏幕右下角中/英文状态，支持点击切换 | 不处理业务逻辑 |
| `ui/tray_icon.py` | 可选的系统托盘图标与右键菜单 | 不处理业务逻辑 |
| `main.py` | 整合所有模块，处理 engine 与 keyboard_handler、UI 之间的交互 | — |
| `launcher.py` | 打包入口，确保路径兼容 PyInstaller | 不直接包含业务逻辑 |

## 运行方式

### 开发环境运行

```bash
cd wubi_ime
pip install -r requirements.txt
python main.py
```

或直接运行根目录诊断脚本：

```bash
python test_wubi_simple.py
```

### 打包为可执行文件

```bash
python build.py
```

打包完成后产物位于 `dist/WubiIME.exe`。该脚本会：

1. 清理旧的 `build/` 和 `dist/` 目录；
2. 调用 PyInstaller，以 `wubi_ime/launcher.py` 为入口；
3. 将 `wubi_ime/` 目录作为数据文件打包；
4. 输出 `WubiIME.exe`。

## 用户配置

默认配置文件为 `wubi_config.json`，字段含义：

```json
{
  "activation_hotkey": "ctrl+alt+w",  // 激活/关闭输入法热键
  "candidates_per_page": 9,             // 每页候选字数量（对应数字键 1-9）
  "wubi_table_path": null,              // 自定义编码表路径，null 使用内置表
  "user_dict_path": "user_dict.json",   // 用户词库路径
  "auto_commit_single": true,           // 单候选字是否自动提交
  "show_status_window": true,           // 是否显示状态窗口
  "theme": "default"                    // 主题（当前仅保留字段）
}
```

配置项在 `config.py` 的 `DEFAULT_CONFIG` 中定义，启动时会与现有文件合并，缺失键使用默认值。

## 核心行为约定

- **激活/关闭热键**：`Ctrl+Alt+W`
- **中英文切换**：单独按 `Shift`
- **候选选择**：数字键 `1-9` 或空格选第一个
- **翻页**：`PageUp`/`PageDown` 或 `+`/`-`
- **取消输入**：`Esc` 或退格清空编码
- **每页候选数**：固定 9 个
- **四码唯一自动上屏**：输入满 4 位且精确匹配唯一候选时自动提交
- **系统输入法热键不拦截**：`Ctrl+Shift`、`Win+Space`、`Alt+Shift` 保持系统默认行为

## 代码风格指南

- 使用 **中文注释** 和中文文档字符串；新增的模块级/函数级注释也应使用中文。
- 类型注解：使用 `typing` 模块注解公开接口，如 `Optional[str]`、`List[str]`、`Callable[[int], None]`。
- 命名：类名使用大驼峰（`WubiEngine`），函数/变量使用下划线命名法（`current_code`、`get_candidates`）。
- 缩进：4 个空格。
- 导入顺序：标准库 → 第三方库 → 本项目模块。
- 模块边界：保持“数据/UI/业务/输入”分离，不要把 UI 或键盘逻辑写入 `engine.py` 或 `wubi_table.py`。
- 线程安全：涉及跨线程状态（如 UI 更新、键盘回调）使用 `threading.Lock` 保护。
- Windows 专用代码：使用 `ctypes` 调用 Win32 API 时应内联定义结构体，不依赖外部 C 扩展。

## 测试说明

- 项目目前没有正式单元测试文件；`wubi_ime/tests/` 目录为空。
- 诊断/验证请使用根目录脚本：
  ```bash
  python test_wubi_simple.py
  ```
  该脚本会依次检测：
  1. `keyboard` 库是否安装；
  2. 非拦截模式键盘钩子是否正常；
  3. 拦截模式下能否将 `w` 替换为 `人`。
- 如需新增测试，建议在 `wubi_ime/tests/` 目录下创建 `test_engine.py`、`test_wubi_table.py` 等，使用 `unittest` 或 `pytest`。

## 安全与权限注意事项

- **管理员权限**：虽然 Windows 11 下 `keyboard` 库的低级键盘钩子通常不需要管理员权限，但在某些受保护进程或高完整性级别的窗口中可能失效。如用户反馈无法输入，建议以管理员身份运行。
- **全局钩子风险**：`keyboard` 库会拦截所有按键；修改 `keyboard_handler.py` 时应避免误拦截系统快捷键（如 `Ctrl+Shift`、`Win+Space`、`Alt+Shift`）。
- **SendInput 递归**：`main.py` 在发送输出前调用 `keyboard.unhook()`，发送后调用 `keyboard.rehook()`，以防止 `SendInput` 触发的按键事件重新进入钩子造成死循环。任何新增输出逻辑都必须遵循此模式。
- **配置与用户词库**：`wubi_config.json` 与 `user_dict.json` 已加入 `.gitignore`，不应提交到版本控制。
- **依赖来源**：依赖通过 `pip` 安装，建议使用虚拟环境，避免污染系统 Python。

## 依赖清单

详见 `wubi_ime/requirements.txt`：

```
pynput>=1.7.6
pywin32>=306
keyboard>=0.13.5
pystray>=0.19.4
pillow>=10.0.0
```

## 打包与部署

- 标准部署：运行 `python build.py` 生成 `dist/WubiIME.exe`，分发给最终用户。
- 数据文件路径：代码需同时兼容开发环境与 PyInstaller 打包环境。打包后资源通过 `sys._MEIPASS` 查找，编码表路径在 `wubi_table.py` 中已有兼容处理。
- 入口脚本：`launcher.py` 使用 `multiprocessing.freeze_support()`，这是 Windows 上单文件 PyInstaller 程序的必要设置。

## 开发前必读

1. 先阅读 `wubi_ime/SPEC.md`：其中定义了模块接口契约、共享契约与文件边界。
2. 修改键盘拦截逻辑前，务必在 Windows 上运行 `test_wubi_simple.py` 验证钩子行为；当前实现把按键事件加入队列由主线程处理，钩子回调应保持轻量。
3. 修改输出逻辑时，必须保证 `unhook` → `SendInput` → `rehook` 的防递归流程完整，且 `_send_output` 运行在主线程。
4. 不要假设 `wubi_ime/tests/` 中已有测试；新增功能时请补充对应测试。
