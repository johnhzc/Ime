# 五笔输入法 Python 原型版本

> 这是项目的早期原型版本，使用 Python + 全局键盘钩子 + `SendInput` 实现。
> 
> 当前项目主推版本为 **Windows Text Services Framework (TSF) 原生输入法 DLL**，位于 [`wubi_ime_tsf/`](../wubi_ime_tsf/README.md)。该 Python 版本目前仅作为参考、学习与备用。

一个适用于 Windows 的纯 Python 五笔输入法程序。

## 功能特性

- 五笔86版编码支持
- 全局键盘监听（支持所有应用程序）
- 候选窗口跟随光标
- 支持简码输入（一级/二级/三级简码）
- 支持词组输入
- 中英文切换
- 用户自定义词库

## 安装要求

- Windows 10/11
- Python 3.8+
- 依赖：`pynput`, `tkinter`（Python 自带）

## 安装方法

```bash
pip install -r requirements.txt
```

## 使用方法

### 运行输入法

```bash
python main.py
```

运行后，输入法将在后台运行。按 `Ctrl+Alt+W` 激活/关闭输入法。

### 基本操作

- 五笔编码输入：直接键入字母编码（如 `w` → `人`）
- 选词：按 `1~9` 选择候选字，或按空格选择第一个
- 翻页：`PageUp`/`PageDown` 或 `+`/`-`
- 取消输入：`Esc` 或退格清空编码
- 中英文切换：`Shift` 键

## 项目结构

```
wubi_ime/
├── main.py                  # 主程序入口
├── engine.py                # 五笔编码引擎
├── wubi_table.py            # 五笔编码表/字库
├── keyboard_handler.py      # 全局键盘监听
├── config.py                # 配置管理
├── ui/
│   ├── candidate_window.py  # 候选窗口
│   └── status_window.py     # 状态窗口
├── data/
│   └── wubi_86.json         # 86版五笔编码表
└── tests/
    └── test_engine.py       # 单元测试
```

## 开发说明

本项目使用 Python 实现，通过 `pynput` 库监听全局键盘事件，通过 `SendInput` API 发送输出到目标应用程序。候选窗口使用 `tkinter` 实现。

## 许可证

MIT License
