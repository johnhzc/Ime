<!-- From: d:\BeansWorkingSpace\lyt\2026中山大学学生第二课堂\coding\AGENTS.md -->
# 五笔输入法 (Wubi IME) — Agent 开发指南

> 本文件面向 AI 编程 Agent。假设读者对项目一无所知，请按以下实际内容操作，不要依赖假设或通用推断。

## 项目概述

这是一个面向 Windows 10/11 的五笔输入法项目，采用五笔 86 版编码表。

- **当前主推实现**：`wubi_ime_tsf/` 下的 **Windows Text Services Framework (TSF) 原生输入法 DLL**（C++）。
- **早期原型实现**：`wubi_ime/` 下的纯 Python 版本（全局键盘钩子 + `SendInput`），目前仅作为参考与备用。

本指南同时涵盖两个版本，但请以 TSF 版本为优先。

- 项目语言：中文（代码注释、文档、UI 文本均为中文）
- 版本：`1.0.0`
- 许可证：MIT License

## 技术栈

### TSF 版本（主推）

- **C++17**
- **Windows Text Services Framework (TSF)**
- **COM / Windows SDK**
- **CMake**：构建系统
- **nlohmann/json**：编码表解析
- **GDI**：候选窗口自绘

### Python 原型版本

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
├── wubi_ime_tsf/              # 当前主推版本：C++ TSF 输入法 DLL
│   ├── CMakeLists.txt         # CMake 构建配置
│   ├── src/                   # C++ 源码
│   │   ├── dllmain.cpp        # DLL 入口与注册
│   │   ├── factory.*          # COM 类工厂
│   │   ├── text_service.*     # TSF 文本服务核心
│   │   ├── engine.*           # 编码引擎接口 + 五笔实现
│   │   ├── candidate_window.* # GDI 候选窗口
│   │   ├── utils.*            # 工具函数
│   │   ├── common.h           # GUID、常量
│   │   └── resource.rc        # 版本资源
│   ├── include/nlohmann/      # nlohmann/json 单头文件
│   ├── data/
│   │   └── wubi_86.json       # 86 版五笔编码表
│   ├── scripts/               # 注册/卸载脚本
│   │   ├── register.bat
│   │   └── unregister.bat
│   ├── build_cmake.bat        # 自动构建脚本
│   ├── build_cmake.ps1
│   └── README.md              # TSF 版本详细说明
├── wubi_ime/                  # 早期 Python 原型（参考/备用）
│   ├── __init__.py            # 包初始化，定义 __version__ = "1.0.0"
│   ├── main.py                # 主程序入口与 WubiIME 协调类
│   ├── launcher.py            # PyInstaller 打包入口
│   ├── engine.py              # 五笔编码引擎
│   ├── wubi_table.py          # 编码表加载与查询
│   ├── keyboard_handler.py    # 全局键盘监听
│   ├── config.py              # 配置管理
│   ├── ui/                    # UI 模块
│   ├── data/
│   │   └── wubi_86.json
│   ├── tests/
│   └── README.md
├── wubi_config.json           # 用户配置文件（Python 版本运行时生成）
├── requirements.txt           # Python 版本依赖（位于 wubi_ime/requirements.txt）
├── build.py                   # PyInstaller 打包脚本
├── WubiIME.spec               # PyInstaller spec 文件
├── test_wubi_simple.py        # Python 版本键盘钩子与输出诊断脚本
├── README.md                  # 项目总览（主推 TSF 版本）
└── AGENTS.md                  # 本文件
```

## 运行与构建方式

### TSF 版本（推荐）

```bash
cd wubi_ime_tsf
build_cmake.bat
```

构建完成后：

```bash
# 安装（管理员权限）
scripts\register.bat

# 卸载（管理员权限）
scripts\unregister.bat
```

安装后需注销/重启使语言栏刷新。

### Python 原型版本

```bash
cd wubi_ime
pip install -r requirements.txt
python main.py
```

或运行根目录诊断脚本：

```bash
python test_wubi_simple.py
```

### Python 版本打包为可执行文件

```bash
python build.py
```

打包完成后产物位于 `dist/WubiIME.exe`。

## 用户配置（Python 版本）

默认配置文件为 `wubi_config.json`，字段含义：

```json
{
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

## 核心行为约定

- **激活/关闭热键**：`Ctrl+Alt+W`（Python 版本）
- **中英文切换**：单独按 `Shift`
- **候选选择**：数字键 `1-9` 或空格选第一个
- **翻页**：`PageUp`/`PageDown` 或 `+`/`-`
- **取消输入**：`Esc` 或退格清空编码
- **每页候选数**：固定 9 个
- **四码唯一自动上屏**：输入满 4 位且精确匹配唯一候选时自动提交

## 代码风格指南

- 使用 **中文注释** 和中文文档字符串。
- 类型注解：使用 `typing` 模块注解公开接口。
- 命名：类名使用大驼峰，函数/变量使用下划线命名法。
- 缩进：4 个空格。
- 导入顺序：标准库 → 第三方库 → 本项目模块。
- 模块边界：保持“数据/UI/业务/输入”分离。
- 线程安全：涉及跨线程状态使用 `threading.Lock` 保护。
- Windows 专用代码：使用 `ctypes` 调用 Win32 API 时应内联定义结构体。

## 测试说明

- TSF 版本目前没有自动化单元测试；修改后建议在 Windows 环境下重新构建并注册测试。
- Python 版本目前没有正式单元测试文件；`wubi_ime/tests/` 目录为空。
- 诊断/验证请使用根目录脚本：
  ```bash
  python test_wubi_simple.py
  ```
- 如需新增测试，建议在对应版本目录下创建测试文件。

## 安全与权限注意事项

- **管理员权限**：注册/卸载 TSF DLL 必须以管理员身份运行。
- **Python 版本全局钩子风险**：`keyboard` 库会拦截所有按键；修改 `wubi_ime/keyboard_handler.py` 时应避免误拦截系统快捷键。
- **SendInput 递归**：Python 版本在发送输出前调用 `keyboard.unhook()`，发送后调用 `keyboard.rehook()`，以防止递归。
- **配置与用户词库**：`wubi_config.json` 与 `user_dict.json` 已加入 `.gitignore`。
- **依赖来源**：Python 版本依赖通过 `pip` 安装，建议使用虚拟环境。

## 依赖清单（Python 版本）

详见 `wubi_ime/requirements.txt`：

```
pynput>=1.7.6
pywin32>=306
keyboard>=0.13.5
pystray>=0.19.4
pillow>=10.0.0
```

## 打包与部署

- **标准部署**：运行 `python build.py` 生成 `dist/WubiIME.exe`（Python 版本）。
- **TSF 部署**：构建并运行 `scripts/register.bat`，作为系统输入法使用。
- 数据文件路径：Python 版本代码需同时兼容开发环境与 PyInstaller 打包环境。

## 开发前必读

1. 先阅读 `wubi_ime/SPEC.md`（Python 版本接口契约）。
2. TSF 版本修改后必须重新构建并注册测试。
3. Python 版本修改键盘拦截逻辑前，务必运行 `test_wubi_simple.py` 验证。
4. Python 版本修改输出逻辑时，必须保证 `unhook` → `SendInput` → `rehook` 的防递归流程完整。
