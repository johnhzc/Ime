# 五笔输入法项目开发规范

## 项目概述
开发一个 Windows 下可用的五笔输入法，使用 Python 实现，包含完整的编码引擎、全局键盘监听和 UI 界面。

## 技术栈
- Python 3.8+
- pynput: 全局键盘监听
- pywin32: Windows API (SendInput)
- tkinter: 候选窗口 UI (Python 自带)
- json: 五笔编码表数据存储

## 模块接口规范

### 1. wubi_table.py（编码表）
- `load_wubi_table()` → dict[str, str]: 加载编码表
- `get_char_code(char)` → str: 获取汉字的五笔编码
- `get_candidates(code)` → list[str]: 根据编码获取候选字列表
- `WubiTable` 类管理编码表数据

### 2. engine.py（编码引擎）
- `WubiEngine` 类:
  - `process_key(key)` → Action: 处理按键，返回动作（如添加编码、选词、提交）
  - `get_candidates()` → list[str]: 获取当前编码对应的候选字
  - `select_candidate(index)` → str: 选择候选字
  - `clear()` → None: 清空当前编码
  - `current_code` → str: 当前输入的编码
  - `current_candidates` → list[str]: 当前候选列表

### 3. keyboard_handler.py（键盘监听）
- `KeyboardHandler` 类:
  - `start()`: 启动键盘监听
  - `stop()`: 停止键盘监听
  - `on_press(key)`: 按键按下回调
  - `on_release(key)`: 按键释放回调
  - `set_callback(callback)`: 设置按键处理回调

### 4. ui/candidate_window.py（候选窗口）
- `CandidateWindow` 类:
  - `show(x, y)`: 显示候选窗口在指定位置
  - `hide()`: 隐藏窗口
  - `update_candidates(candidates, code)`: 更新候选字列表和编码显示
  - `set_page(page, total_pages)`: 设置当前页码

### 5. main.py（主程序）
- 整合所有模块
- 主事件循环
- 处理 engine 与 keyboard_handler、UI 之间的交互

## 共享契约
- 编码表使用 JSON 格式，键为汉字，值为五笔编码
- 所有按键处理使用统一的 Action 枚举: `ADD_KEY`, `SELECT_CANDIDATE`, `DELETE`, `CANCEL`, `SUBMIT`, `SWITCH_MODE`, `PAGE_UP`, `PAGE_DOWN`
- 候选字每页显示 9 个（对应数字键 1-9）
- 输入法激活/关闭快捷键: `Ctrl+Shift+W`
- 中英文切换: `Shift` 键

## 文件边界
- wubi_table.py: 只管理编码表数据，不涉及 UI
- engine.py: 只处理编码逻辑，不直接操作键盘或 UI
- keyboard_handler.py: 只处理键盘事件，不处理编码逻辑
- candidate_window.py: 只处理 UI 显示，不处理业务逻辑
- main.py: 负责模块间的协调和事件分发
