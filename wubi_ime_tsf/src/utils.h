#pragma once

#include <windows.h>
#include <string>
#include <utility>

namespace wubi_tsf {

// Get current caret position in screen coordinates.
// Falls back to mouse cursor position.
std::pair<int, int> GetCaretPosition();

// Get the module file name of the current DLL.
std::wstring GetModulePath();

// Get the directory containing the current DLL.
std::wstring GetModuleDirectory();

// Get the HMODULE of the current DLL.
HMODULE GetCurrentModule();

}  // namespace wubi_tsf
