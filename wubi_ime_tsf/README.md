# 五笔输入法 TSF 版本

基于 Windows Text Services Framework (TSF) 的原生输入法 DLL，可与系统输入法并列显示在语言栏中，是本项目当前主推的实现方式。

## 功能特性

- 原生 Windows TSF 文本服务，注册后出现在系统语言栏
- 五笔 86 版编码支持
- GDI 自绘候选窗口，跟随光标显示
- 支持简码输入（一级/二级/三级简码）
- 支持词组输入
- 中英文模式切换（`Shift`）
- 数字键 `1~9` 与空格选词
- 支持 `PageUp`/`PageDown`、`+`/`-` 翻页
- 用户可替换自定义编码表

## 项目结构

```
wubi_ime_tsf/
├── CMakeLists.txt            # CMake 构建配置
├── src/                      # C++ 源码
│   ├── dllmain.cpp           # DLL 入口与注册
│   ├── factory.*             # COM 类工厂
│   ├── text_service.*        # TSF 文本服务核心
│   ├── engine.*              # 编码引擎接口 + 五笔实现
│   ├── candidate_window.*    # GDI 候选窗口
│   ├── utils.*               # 工具函数
│   ├── common.h              # GUID、常量
│   └── resource.rc           # 版本资源
├── include/nlohmann/         # nlohmann/json 单头文件
├── data/                     # 编码表 JSON
│   └── wubi_86.json
└── scripts/                  # 注册/卸载脚本
    ├── register.bat
    └── unregister.bat
```

## 构建要求

- Windows 10/11
- Visual Studio 2019/2022（安装 C++ 桌面开发 + Windows SDK）
- CMake 3.16+

## 构建步骤

> **注意**：如果之前已经注册过旧版 DLL，重新编译前请先卸载，否则链接时可能因文件被占用而失败。

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

或使用项目提供的脚本（会自动设置 VS 环境）：

```bash
cd wubi_ime_tsf
build_cmake.bat
```

构建产物位于 `build/bin/WubiIME_TSF.dll`，同时 `build/bin/data/` 下会复制编码表。

## 安装与卸载

### 安装

1. 以管理员身份运行 `scripts/register.bat`。
2. 注销并重新登录（或重启），使语言栏刷新。
3. 进入 **设置 > 时间和语言 > 语言和区域 > 中文（简体）> 语言选项 > 键盘**，
   确认“五笔输入法 (TSF)”已列出。如未列出，点击“添加键盘”手动添加。

### 卸载

以管理员身份运行 `scripts/unregister.bat`。

## 使用

- 在语言栏切换到“五笔输入法 (TSF)”。
- 直接输入字母编码，候选窗口会跟随光标显示。
- 按 `1~9` 或空格选择候选，按 `Esc` 或 `Backspace` 取消/删除。
- 按 `Shift` 切换中文/英文模式（英文模式下字母直接输出到应用）。

## 诊断日志

运行时日志写入：

```
%TEMP%\WubiIME_Runtime.log
```

注册/卸载日志写入：

```
%TEMP%\WubiIME_Register.log
```

如果输入法不能出字，请先查看 `%TEMP%\WubiIME_Runtime.log`，检查：

- `[Activate]` 是否成功加载编码表（`result=1` 表示成功）。
- `[OnTestKeyDown]` 和 `[OnKeyDown]` 是否有按键进入。
- `[DoEditSession]` 中 `SetText` / `EndComposition` / `InsertTextAtSelection` 是否返回成功。

## 替换编码表

1. 修改或替换 `data/wubi_86.json`。
2. JSON 格式为：`{"汉字": "编码", ...}` 或 `{"汉字": ["编码1", "编码2"], ...}`。
3. 重新构建或复制新的 JSON 到 `build/bin/data/`。

## 后续扩展

- 实现 `ITfDisplayAttributeProvider` 为组合串加下划线。
- 增加用户词库、调频、皮肤。
- 用新的 `ImeEngine` 子类替换五笔引擎。

## 许可证

MIT License
