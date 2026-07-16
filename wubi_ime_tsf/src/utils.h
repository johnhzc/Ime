#pragma once

#include <windows.h>
#include <string>
#include <utility>

namespace wubi_tsf {

// Append a timestamped message to %TEMP%\WubiIME_Runtime.log.
void RuntimeLog(const wchar_t* format, ...);

// Set the DLL instance handle (called from DllMain).
void SetInstanceHandle(HINSTANCE instance);

// Get the DLL instance handle, falling back to the host process module.
HINSTANCE GetInstanceHandle();

// Get current caret position in screen coordinates.
// Falls back to mouse cursor position.
std::pair<int, int> GetCaretPosition();

// Get the module file name of the current DLL.
std::wstring GetModulePath();

// Get the directory containing the current DLL.
std::wstring GetModuleDirectory();

// Get the HMODULE of the current DLL.
HMODULE GetCurrentModule();

// Create a consistent IME font using the project-wide Chinese font face.
// The caller is responsible for deleting the returned HFONT.
HFONT CreateImeFont(int height, int weight = FW_NORMAL);

}  // namespace wubi_tsf
