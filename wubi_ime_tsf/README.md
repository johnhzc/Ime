# 五笔输入法 TSF 骨架

基于 Windows Text Services Framework (TSF) 的输入法骨架，可与系统输入法并列显示在语言栏中。

## 项目结构

```
wubi_ime_tsf/
├── CMakeLists.txt      # CMake 构建配置
├── src/                # C++ 源码
│   ├── dllmain.cpp     # DLL 入口与注册
│   ├── factory.*       # COM 类工厂
│   ├── text_service.*  # TSF 文本服务核心
│   ├── engine.*        # 编码引擎接口 + 五笔实现
│   ├── candidate_window.*  # GDI 候选窗口
│   ├── utils.*         # 工具函数
│   ├── common.h        # GUID、常量
│   └── resource.rc     # 版本资源
├── include/nlohmann/   # nlohmann/json 单头文件
├── data/               # 编码表 JSON
│   └── wubi_86.json
└── scripts/            # 注册/卸载脚本
    ├── register.bat
    └── unregister.bat
```

## 构建要求

- Windows 10/11
- Visual Studio 2019/2022（安装 C++ 桌面开发 + Windows SDK）
- CMake 3.16+

## 构建步骤

```bash
cd wubi_ime_tsf
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release
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

## 替换编码表

1. 修改或替换 `data/wubi_86.json`。
2. JSON 格式为：`{"汉字": "编码", ...}` 或 `{"汉字": ["编码1", "编码2"], ...}`。
3. 重新构建或复制新的 JSON 到 `build/bin/data/`。

## 后续扩展

- 实现 `ITfDisplayAttributeProvider` 为组合串加下划线。
- 增加用户词库、调频、皮肤。
- 用新的 `ImeEngine` 子类替换五笔引擎。
