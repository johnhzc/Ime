# 五笔输入法 (Wubi IME) — Agent 开发指南

> 本文件面向 AI 编程 Agent。假设读者对项目一无所知，请按以下实际内容操作，不要依赖假设或通用推断。

## 1. 项目概述

这是一个面向 Windows 10/11 的五笔 86 版输入法项目，当前同时维护两套实现：

- **当前主推实现**：`wubi_ime_tsf/` 下的 **Windows Text Services Framework (TSF) 原生输入法 DLL**（C++17）。它作为系统输入法出现在语言栏中，可在所有现代 UWP / Win32 应用中使用。
- **早期原型实现**：`wubi_ime/` 下的纯 Python 版本（全局键盘钩子 + `SendInput`），目前仅作为参考、学习与备用。

本指南同时涵盖两个版本，但**请以 TSF 版本为优先**。

- 项目语言：中文（代码注释、文档、UI 文本均为中文）
- 版本：`1.0.0`
- 许可证：MIT License

## 2. 版本说明与技术栈

### 2.1 TSF 版本（主推）

| 项目 | 内容 |
|------|------|
| 语言 | C++17 |
| 框架 | Windows Text Services Framework (TSF) |
| 接口 | COM / Windows SDK（`msctf.h`） |
| 构建系统 | CMake 3.16+ |
| JSON 解析 | nlohmann/json（单头文件，位于 `wubi_ime_tsf/include/nlohmann/`） |
| 候选窗口 | Win32 GDI 自绘，无边框工具窗口 |
| 字符集 | Unicode（UTF-8 源码、UTF-16 运行时 wide string） |

### 2.2 Python 原型版本

| 项目 | 内容 |
|------|------|
| 语言 | Python 3.8+ |
| 全局键盘钩子 | `keyboard`（WH_KEYBOARD_LL） |
| 辅助监听 | `pynput` |
| Windows API | `pywin32` / `ctypes` + `SendInput` |
| UI | `tkinter`（候选窗口、状态窗口） |
| 托盘图标 | `pystray` + `Pillow`（已提供，但当前未在主流程中启用） |
| 数据格式 | JSON |
| 打包 | PyInstaller |

## 3. 项目结构

```
.
├── AGENTS.md                     # 本文件（Agent 开发指南）
├── README.md                     # 项目总览（主推 TSF 版本）
├── wubi_config.json              # Python 原型版本运行时配置
├── build.py                      # Python 版本 PyInstaller 打包脚本
├── WubiIME.spec                  # PyInstaller spec 文件
├── build_tsf_in_venv.py          # 在 venv 中构建 TSF DLL（旧版）
├── build_tsf_in_venv2.py         # 在 venv 中构建 TSF DLL（新版，统一输出到 build/）
├── test_wubi_simple.py           # Python 版本诊断脚本
├── test_candidate_window_fix.py  # TSF 候选窗修复验证脚本
├── wubi_ime/                     # 早期 Python 原型版本
│   ├── __init__.py               # 包初始化，定义 __version__ = "1.0.0"
│   ├── main.py                   # 主程序入口与 WubiIME 协调类
│   ├── launcher.py               # PyInstaller 打包入口
│   ├── engine.py                 # 五笔编码引擎（WubiEngine）
│   ├── wubi_table.py             # 编码表加载与查询
│   ├── keyboard_handler.py       # 全局键盘监听
│   ├── config.py                 # 配置管理
│   ├── requirements.txt          # Python 依赖
│   ├── ui/
│   │   ├── candidate_window.py   # tkinter 候选窗口
│   │   ├── status_window.py      # tkinter 状态窗口
│   │   └── tray_icon.py          # 系统托盘图标（未启用）
│   ├── data/
│   │   └── wubi_86.json          # 86 版五笔编码表
│   ├── tests/
│   │   └── test_engine.py        # WubiEngine 单元测试
│   ├── README.md                 # Python 版本说明
│   └── SPEC.md                   # Python 版本接口契约
├── wubi_ime_tsf/                 # 当前主推：C++ TSF 输入法 DLL
│   ├── CMakeLists.txt            # CMake 构建配置
│   ├── build_cmake.bat           # 自动构建脚本（调用便携版 CMake + Ninja）
│   ├── build_cmake.ps1           # 自动构建脚本（PowerShell 版）
│   ├── check_env.ps1             # 环境检查脚本
│   ├── src/                      # C++ 源码
│   │   ├── dllmain.cpp           # DLL 入口、DllRegisterServer / DllUnregisterServer
│   │   ├── factory.cpp/.h        # COM 类工厂
│   │   ├── text_service.cpp/.h   # TSF 文本服务核心
│   │   ├── engine.cpp/.h         # 编码引擎接口 + 五笔实现
│   │   ├── candidate_window.cpp/.h # GDI 候选窗口
│   │   ├── utils.cpp/.h          # 日志、DLL 路径、插入符位置
│   │   ├── common.h              # CLSID、GUID、LANGID、输入法名称
│   │   ├── resource.rc           # 版本资源
│   │   └── WubiIME_TSF.def       # DLL 导出符号
│   ├── include/nlohmann/         # nlohmann/json 单头文件
│   ├── data/
│   │   └── wubi_86.json          # 86 版五笔编码表
│   ├── scripts/
│   │   ├── register.bat          # 注册输入法
│   │   ├── unregister.bat        # 卸载输入法
│   │   └── diagnose_registration.ps1 # 注册表诊断
│   ├── build/                    # CMake 构建输出目录
│   ├── build2/ ~ build9/         # 历史/备用构建输出（已弃用）
│   └── README.md                 # TSF 版本详细说明
├── debug/                        # 诊断报告与日志
│   ├── latest_wubi_log.txt
│   ├── 诊断报告-五笔输入法不能出字.md
│   └── 诊断报告-候选框不出来.md
└── .venv/                        # 项目本地虚拟环境
```

## 4. 关键配置文件

### `wubi_ime_tsf/CMakeLists.txt`

- 项目名：`WubiIME_TSF`，版本 `1.0.0`
- C++ 标准：C++17
- 构建目标：`SHARED` DLL
- 源文件：`src/` 下所有 `.cpp/.h/.rc/.def`
- 链接库：`user32`、`gdi32`、`shell32`、`ole32`、`oleaut32`、`uuid`、`pathcch`
- 编译定义：`_WIN32_WINNT_WIN10`、`WIN32_LEAN_AND_MEAN`、`NOMINMAX`、`UNICODE`、`_UNICODE`
- MSVC 选项：`/utf-8`
- 输出目录：`${CMAKE_BINARY_DIR}/bin`
- 构建后自动复制 `data/` 到输出目录

### `wubi_ime/requirements.txt`

```
pynput>=1.7.6
pywin32>=306
keyboard>=0.13.5
pystray>=0.19.4
pillow>=10.0.0
```

### `build.py` / `WubiIME.spec`

用于打包 Python 原型版本为单文件可执行程序：

- 入口：`wubi_ime/launcher.py`
- 参数：`--onefile --name WubiIME --clean --noconfirm`
- 数据文件：`--add-data wubi_ime{sep}wubi_ime`
- 隐藏导入：`keyboard`、`pynput.keyboard._win32`、`pynput.mouse._win32`
- 输出：`dist/WubiIME.exe`

### `wubi_config.json`

Python 版本运行时生成的配置文件，默认内容：

```json
{
  "_description": "本配置仅适用于 wubi_ime/ 下的 Python 原型版本。当前主推实现为 wubi_ime_tsf/ 下的 TSF 原生输入法 DLL。",
  "activation_hotkey": "ctrl+alt+w",
  "candidates_per_page": 9,
  "wubi_table_path": null,
  "user_dict_path": "user_dict.json",
  "auto_commit_single": true,
  "show_status_window": true,
  "theme": "default"
}
```

配置项在 `wubi_ime/config.py` 的 `DEFAULT_CONFIG` 中定义。

### `.gitignore`

- Python 构建产物、虚拟环境、IDE 配置
- 项目特定：`wubi_config.json`、`user_dict.json`、`wubi_ime_tsf/cmake/`、`wubi_ime_tsf/cmake-portable.zip`、`wubi_ime_tsf/build2/` ~ `build9/`、`wubi_ime_tsf/scripts/latest_build_dir.txt`

### `wubi_ime_tsf/src/resource.rc`

DLL 版本资源：文件/产品版本 `1.0.0.0`，语言 `0804`（简体中文），文件描述/产品名称为中文“五笔输入法 TSF 骨架”。

### `wubi_ime_tsf/src/WubiIME_TSF.def`

DLL 导出符号：`DllGetClassObject`、`DllCanUnloadNow`、`DllRegisterServer`、`DllUnregisterServer`。

## 5. 代码组织与模块职责

### 5.1 TSF 版本（`wubi_ime_tsf/src`）

| 文件 | 关键类/函数 | 职责 |
|------|-------------|------|
| `common.h` | `CLSID_WubiIME_Service`、`GUID_WubiIME_Profile`、`GUID_WubiIME_DisplayAttr`、`kLangId`、`kImeName` | CLSID/GUID/常量 |
| `dllmain.cpp` | `DllMain`、`DllGetClassObject`、`DllCanUnloadNow`、`DllRegisterServer`、`DllUnregisterServer`、`RegisterProfile`、`UnregisterProfile`、`RegisterCategories` | DLL 入口、COM/TSF 注册、注册日志 `%TEMP%\WubiIME_Register.log` |
| `factory.cpp/.h` | `ClassFactory` | COM 类工厂，创建 `TextService` 实例 |
| `text_service.cpp/.h` | `TextService`、`CompositionEditSession`、`RequestCompositionEditSession` | TSF 文本服务核心：激活/反激活、按键处理、合成更新/提交、候选窗更新 |
| `engine.cpp/.h` | `ImeEngine`（抽象接口）、`WubiEngine`（实现）、`ProcessKeyResult` | 编码引擎：加载 JSON、按键处理、候选分页、简码、四码自动上屏 |
| `candidate_window.cpp/.h` | `CandidateWindow` | GDI 自绘候选窗口；创建/显示/移动/绘制/点击选词；DPI 缩放 |
| `utils.cpp/.h` | `RuntimeLog`、`GetModulePath`、`GetModuleDirectory`、`GetCaretPosition`、`SetInstanceHandle` | 运行时日志、DLL 路径、插入符位置 |
| `resource.rc` | 版本信息 | DLL 资源 |
| `WubiIME_TSF.def` | 导出符号 | DLL 导出 |

### 5.2 Python 版本（`wubi_ime/`）

| 文件 | 关键类/函数 | 职责 |
|------|-------------|------|
| `main.py` | `WubiIME`、`_send_output`、`_on_key`、`_on_activation_hotkey` | 主协调类：事件循环、SendInput 输出、布局切换 |
| `launcher.py` | `main()` | PyInstaller 入口 |
| `engine.py` | `Action` 枚举、`WubiEngine.process_key`、`select_candidate`、`get_page_info` | 编码引擎逻辑 |
| `wubi_table.py` | `WubiTable`、`get_wubi_table` | JSON 编码表加载、精确/前缀匹配 |
| `keyboard_handler.py` | `KeyboardHandler` | 全局键盘钩子、按键入队、unhook/rehook、系统热键兼容 |
| `config.py` | `Config`、`DEFAULT_CONFIG` | 配置读写 |
| `ui/candidate_window.py` | `CandidateWindow`、`get_cursor_position` | tkinter 候选窗 |
| `ui/status_window.py` | `StatusWindow` | 状态窗（中/英、全角、可拖动、点击切换） |
| `ui/tray_icon.py` | `TrayIcon`、`DummyTrayIcon` | 系统托盘图标（存在但未在 `main.py` 中启用） |
| `tests/test_engine.py` | `TestWubiEngine` | 引擎单元测试 |

### 5.3 模块边界

- `wubi_table.py`：只管理编码表数据，不涉及 UI
- `engine.py`：只处理编码逻辑，不直接操作键盘或 UI
- `keyboard_handler.py`：只处理键盘事件，不处理编码逻辑
- `candidate_window.py`：只处理 UI 显示，不处理业务逻辑
- `main.py`：负责模块协调和事件分发

## 6. 构建、运行与部署

### 6.1 TSF 版本

#### 构建要求

- Windows 10/11
- Visual Studio 2019/2022（安装 C++ 桌面开发 + Windows SDK）
- CMake 3.16+
- 项目脚本默认使用 `wubi_ime_tsf/cmake/bin/cmake.exe`（便携版 CMake，已加入 `.gitignore`，本地需存在或自行解压 `cmake-portable.zip`）

#### 构建步骤

使用项目脚本（推荐）：

```bash
cd wubi_ime_tsf
build_cmake.bat
# 或
build_cmake.ps1
# 或（统一输出到 build/）
python ..\build_tsf_in_venv2.py
```

> 注意：`build_cmake.bat`、`build_cmake.ps1`、`build_tsf_in_venv2.py`、`check_env.ps1` 中硬编码了 VS BuildTools 路径 `D:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat`，若你的环境不同，请先修改脚本。

`build_tsf_in_venv2.py` 额外行为：

- 统一输出到 `wubi_ime_tsf/build/bin/WubiIME_TSF.dll`
- 构建前检测 DLL 是否被 TSF 服务占用
- 管理员模式下可自动调用 `unregister.bat` 释放旧 DLL
- 若无法释放，会提示注销/重启后再构建

手动构建：

```bash
cd wubi_ime_tsf
scripts\unregister.bat      # 如已注册旧版
mkdir build && cd build
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release
```

构建产物位于 `wubi_ime_tsf/build/bin/WubiIME_TSF.dll`，编码表会被复制到 `wubi_ime_tsf/build/bin/data/wubi_86.json`。

#### 注册 / 卸载

需要**管理员权限**：

```bash
# 注册
wubi_ime_tsf\scripts\register.bat

# 卸载
wubi_ime_tsf\scripts\unregister.bat
```

`register.bat` 流程：

1. 删除旧 `%TEMP%\WubiIME_Register.log`
2. 调用 `regsvr32 /s <DLL>`，DLL 内部执行 `DllRegisterServer`：
   - 初始化 COM
   - 注册 `HKEY_CLASSES_ROOT\CLSID\{A1B2C3D4-E5F6-7890-1234-567890ABCDEF}` + `InprocServer32`
   - 注册 TSF Category（`GUID_TFCAT_TIP_KEYBOARD` 等）
   - 注册 TSF Profile（首选 `ITfInputProcessorProfileMgr`，回退旧 API）
3. 注册后需**注销/重新登录（或重启）**使语言栏刷新
4. 在 **设置 > 时间和语言 > 语言和区域 > 中文（简体）> 语言选项 > 键盘** 中确认或添加“五笔输入法 (TSF)”

### 6.2 Python 原型版本

#### 安装依赖并运行

```bash
cd wubi_ime
pip install -r requirements.txt
python main.py
```

运行后按 `Ctrl+Alt+W` 激活/关闭输入法。

#### 运行根目录诊断脚本

```bash
python test_wubi_simple.py
```

#### 打包为可执行文件

```bash
python build.py
```

打包完成后产物位于 `dist/WubiIME.exe`。

## 7. 核心行为约定

| 操作 | Python 版本行为 | TSF 版本行为 |
|------|-----------------|--------------|
| 激活/关闭热键 | `Ctrl+Alt+W` | 由系统语言栏/输入法切换控制 |
| 中英文切换 | 单独按 `Shift` | 单独按 `Shift` |
| 候选选择 | 数字键 `1-9` 或空格选第一个 | 数字键 `1-9` 或空格选第一个 |
| 翻页 | `PageUp`/`PageDown` 或 `+`/`-` | `PageUp`/`PageDown` 或 `[`/`]` 或 `,`/`.` |
| 取消输入 | `Esc` 或退格清空编码 | `Esc` 或退格清空编码 |
| 每页候选数 | 固定 9 个 | 固定 9 个 |
| 四码唯一自动上屏 | 输入满 4 位且精确匹配唯一候选时自动提交 | 输入满 4 位且精确匹配唯一候选时自动提交 |
| 编码键 | 仅 `a-z`（输入时统一小写处理） | 仅 `a-z`（输入时统一小写处理） |

> 注意：TSF 版本当前实际代码中翻页键为 `[`/`]` 和 `,`/`.`，与 README 中描述的 `+`/`-` 不一致。修改时请同步更新文档。

## 8. 测试与诊断

### 8.1 Python 版本单元测试

```bash
cd wubi_ime
python -m unittest tests.test_engine
# 或
python tests/test_engine.py
```

`tests/test_engine.py` 覆盖：

- 添加编码字符
- 数字键选择候选
- 空格提交第一个候选
- 退格删除编码
- Esc 取消输入
- Shift 切换中英文模式
- 四码唯一自动上屏
- 选择候选后状态清空

> 注意：`WubiEngine.process_key` 对 `SWITCH_MODE` 和 `SELECT_CANDIDATE` 只返回动作，不直接修改状态；调用方（如 `main.py`）需显式调用 `toggle_mode()` 或 `select_candidate(index)`。

### 8.2 诊断脚本

| 脚本 | 作用 |
|------|------|
| `test_wubi_simple.py` | 1. 检查 `keyboard` 库；2. 验证 `SendInput` 的 `INPUT` 结构体大小是否为 40 字节；3. 测试键盘钩子能否在不拦截模式下检测按键；4. 实际通过 `SendInput` 发送 Unicode 字符“人”（U+4EBA）到当前窗口。 |
| `test_candidate_window_fix.py` | 验证 TSF 候选窗修复：检查 `candidate_window.cpp` 是否包含 `PeekMessage + PM_NOREMOVE`、WM_NCCREATE 返回 TRUE、DLL 是否已重新构建、导出符号是否完整。 |
| `wubi_ime_tsf/scripts/diagnose_registration.ps1` | 检查 COM CLSID、TSF TIP、语言资料注册表项，并显示 `%TEMP%\WubiIME_Register.log` 末尾内容。 |

### 8.3 TSF 版本测试

TSF 版本目前没有自动化单元测试。修改后需在 Windows 下重新构建、注册、注销/重启后测试。

## 9. 调试与日志

### 9.1 TSF 版本日志

| 日志 | 路径 |
|------|------|
| 运行时日志 | `%TEMP%\WubiIME_Runtime.log` |
| 注册/卸载日志 | `%TEMP%\WubiIME_Register.log` |

`RuntimeLog` 会写入 UTF-8 BOM，避免中文乱码。

**不能出字时检查项：**

- `[Activate]` 是否成功加载编码表（`result=1` 表示成功）
- `[OnTestKeyDown]` 和 `[OnKeyDown]` 是否有按键进入
- `[DoEditSession]` 中 `SetText` / `EndComposition` / `InsertTextAtSelection` 是否返回成功
- `[CandidateWindow::Create]` 是否成功创建窗口（错误码如 `1400` 表示窗口句柄问题）

### 9.2 Python 版本调试

- 运行 `python test_wubi_simple.py` 验证 `SendInput` 和键盘钩子
- 控制台会输出状态、错误和按键处理信息
- 注意 `SendInput` 的 `INPUT` 结构体大小必须为 40 字节，否则静默失败

### 9.3 诊断报告

- `debug/诊断报告-五笔输入法不能出字.md`：记录了 Python 版本早期 `INPUT` 结构体错误、启动未切英文布局、锁重入等问题及修复建议。当前代码已按报告修复了主要 P0 问题。
- `debug/诊断报告-候选框不出来.md`：记录了 TSF 候选窗 `CreateWindowExW` 返回 `1400 (ERROR_INVALID_WINDOW_HANDLE)` 的根因及修复方向。当前 `candidate_window.cpp` 已加入 `PeekMessage + PM_NOREMOVE` 并在 `WM_NCCREATE` 中返回 `TRUE`，owner 为 `nullptr`。

## 10. 数据文件格式

`wubi_86.json` 格式为：

```json
{
  "汉字": "编码",
  "词组": ["编码1", "编码2"],
  ...
}
```

实际文件中，一个汉字可对应单个编码（字符串）或多个编码（数组），按使用频率/权重排序，例如：

```json
{
  "工": ["a", "aaa", "aaaa"],
  "了": ["b", "bnh"],
  "以": ["c", "nyw", "nywy"]
}
```

- **TSF 版本**：`text_service.cpp` 激活时从 DLL 所在目录加载 `GetModuleDirectory() + L"\\data\\wubi_86.json"`；由 CMake 构建后自动复制。
- **Python 版本**：`wubi_table.py` 兼容 PyInstaller 打包环境（优先 `sys._MEIPASS/wubi_ime/data/wubi_86.json` 或 `sys._MEIPASS/data/wubi_86.json`）和开发环境（模块所在目录 `data/wubi_86.json`）。

### 查询逻辑

- 精确匹配：`code_to_chars[code]`
- 前缀匹配：遍历所有编码，返回以当前编码开头的汉字，去重并按权重顺序
- 候选排序：先精确匹配，再前缀匹配，去重

## 11. 代码风格指南

### 11.1 文档与注释

- 项目语言为中文：代码注释、文档字符串、README、UI 文本均使用中文
- Python 模块使用中文文档字符串说明模块/类职责
- C++ 源码注释也为中文

### 11.2 命名规范

| 语言 | 规范 |
|------|------|
| Python | 类名大驼峰（`WubiEngine`），函数/变量下划线命名（`process_key`, `current_code`），常量全大写（`CANDIDATES_PER_PAGE`） |
| C++ | 类名大驼峰（`TextService`），成员变量带下划线后缀（`ref_count_`, `thread_mgr_`），常量 `k` 前缀（`kImeName`, `kPageSize`） |

### 11.3 缩进与导入

- Python 缩进 4 个空格
- 导入顺序：标准库 → 第三方库 → 本项目模块

### 11.4 类型注解

Python 公开接口使用 `typing` 模块进行类型注解，如 `Optional[str]`、`List[str]`、`Tuple[int, int]`、`Callable[[int], None]`。

## 12. 安全与注意事项

### 12.1 管理员权限

- TSF DLL 的注册与卸载必须以管理员身份运行
- `register.bat` / `unregister.bat` 开头会检查管理员权限，否则提示并退出
- Python 版本在 Windows 11 下 `keyboard` 库的低级键盘钩子通常不需要管理员权限，但某些程序可能需要

### 12.2 Python 版本递归输出风险

Python 版本在调用 `SendInput` 发送输出前，必须：

1. 调用 `keyboard.unhook()` 解除钩子
2. 调用 `SendInput` 发送输出
3. 调用 `keyboard.rehook()` 重新注册钩子

`main.py` 的 `_send_output` 方法已完整实现该流程；`_show_startup_dialog` 中也使用相同模式暂停钩子。修改时切勿破坏此顺序，否则会导致自己发送的按键事件重新进入处理逻辑，造成递归或死锁。

### 12.3 键盘布局切换

Python 版本启动和激活时会调用 `_switch_to_english_layout()` 切换到英文（美国）键盘布局（HKL `0x04090409`），避免百度、微信等 TSF 输入法抢占按键。关闭时通过保存的 `_previous_hkl` 恢复之前的布局。

### 12.4 锁与死锁

`main.py` 使用 `self._lock` 保护引擎状态。`_on_activation_hotkey()` 由 `_on_key()` 在持锁状态下调用，因此 `_on_activation_hotkey()` 自身不再重复加锁，避免死锁。

### 12.5 配置与用户词库

- `wubi_config.json` 与 `user_dict.json` 已加入 `.gitignore`，不会被提交
- 建议 Python 版本依赖通过 `pip` 安装在虚拟环境中

### 12.6 构建脚本路径

`build_cmake.bat`、`build_cmake.ps1`、`build_tsf_in_venv.py`、`build_tsf_in_venv2.py`、`check_env.ps1` 中硬编码了 Visual Studio 环境路径，使用前请确认本地路径是否匹配。

### 12.7 TSF DLL 被占用

已注册的 DLL 可能被 TSF 服务占用，导致重新构建失败。`build_tsf_in_venv2.py` 会检测占用并提示清理步骤；管理员模式下可自动调用 `unregister.bat`。

### 12.8 TSF 候选窗口实现细节

当前 `candidate_window.cpp` 将候选窗口作为独立顶层工具窗口创建，owner 为 `nullptr`，并在创建前通过 `PeekMessage(..., PM_NOREMOVE)` 确保线程消息队列已初始化。`WindowProc` 必须在 `WM_NCCREATE` 中返回 `TRUE`，否则 `CreateWindowExW` 会失败并返回错误码 `1400 (ERROR_INVALID_WINDOW_HANDLE)`。

## 13. 开发前必读

1. 先阅读 `wubi_ime/SPEC.md`（Python 版本接口契约）和 `wubi_ime_tsf/README.md`（TSF 版本详细说明）
2. TSF 版本修改后必须重新构建并注册测试
3. Python 版本修改键盘拦截逻辑前，务必运行 `test_wubi_simple.py` 验证
4. Python 版本修改输出逻辑时，必须保证 `unhook` → `SendInput` → `rehook` 的防递归流程完整
5. 修改 `AGENTS.md` 时，请确保信息与当前代码、配置文件、README 保持一致
