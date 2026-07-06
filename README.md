# 五笔输入法 (Wubi IME)

> 当前主推版本为 **Windows Text Services Framework (TSF) 原生输入法 DLL** 实现，位于 `wubi_ime_tsf/`。根目录下的 `wubi_ime/` 为早期 Python 原型版本，目前仅作为参考与备用。

一个适用于 Windows 10/11 的五笔 86 版输入法，采用系统级 TSF 文本服务框架实现，可作为标准输入法出现在系统语言栏中，支持所有现代 UWP / Win32 应用程序。

## 功能特性

- 五笔 86 版编码支持
- 原生 Windows TSF 输入法 DLL，与系统输入法并列显示在语言栏
- 候选窗口跟随光标，支持 GDI 自绘
- 支持简码输入（一级/二级/三级简码）
- 支持词组输入
- 中英文模式切换
- 数字键 `1~9` 与空格选词
- 用户可替换自定义编码表

## 项目结构

```
.
├── wubi_ime_tsf/              # 当前主推版本：C++ TSF 输入法 DLL
│   ├── src/                   # C++ 源码
│   ├── data/wubi_86.json      # 86 版五笔编码表
│   ├── scripts/               # 注册/卸载脚本
│   ├── CMakeLists.txt         # CMake 构建配置
│   └── README.md              # TSF 版本详细说明
├── wubi_ime/                  # 早期 Python 原型（参考/备用）
│   ├── main.py
│   ├── engine.py
│   └── ...
└── README.md                  # 本文件
```

## 快速开始（TSF 版本）

### 构建要求

- Windows 10/11
- Visual Studio 2019/2022（安装 C++ 桌面开发 + Windows SDK）
- CMake 3.16+

### 构建步骤

```bash
cd wubi_ime_tsf

# 如果已注册旧版，先卸载（管理员权限）
scripts\unregister.bat

# 构建
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release
```

或使用项目提供的脚本：

```bash
cd wubi_ime_tsf
build_cmake.bat
```

构建产物位于 `wubi_ime_tsf/build/bin/WubiIME_TSF.dll`。

### 安装与使用

1. 以管理员身份运行 `wubi_ime_tsf/scripts/register.bat`。
2. 注销并重新登录（或重启），使语言栏刷新。
3. 进入 **设置 > 时间和语言 > 语言和区域 > 中文（简体）> 语言选项 > 键盘**，
   确认“五笔输入法 (TSF)”已列出。
4. 在语言栏切换到“五笔输入法 (TSF)”即可使用。

### 卸载

以管理员身份运行 `wubi_ime_tsf/scripts/unregister.bat`。

更多 TSF 版本细节（诊断日志、编码表替换、扩展开发）请查看 [`wubi_ime_tsf/README.md`](wubi_ime_tsf/README.md)。

## Python 原型版本

`wubi_ime/` 目录下的版本使用 Python + `keyboard` 全局钩子 + `SendInput` 实现，是项目早期的原型验证版本。当前不再作为主推实现，但仍可用于快速调试、学习或临时使用。

```bash
cd wubi_ime
pip install -r requirements.txt
python main.py
```

运行后按 `Ctrl+Alt+W` 激活/关闭输入法。

## 基本操作

- 五笔编码输入：直接键入字母编码（如 `w` → `人`）
- 选词：按 `1~9` 选择候选字，或按空格选择第一个
- 翻页：`PageUp`/`PageDown` 或 `+`/`-`
- 取消输入：`Esc` 或退格清空编码
- 中英文切换：`Shift` 键

## 许可证

MIT License
