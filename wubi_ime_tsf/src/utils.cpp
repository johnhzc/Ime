#include "utils.h"

#include <windows.h>
#include <pathcch.h>
#include <vector>

#pragma comment(lib, "pathcch.lib")

namespace wubi_tsf {

std::pair<int, int> GetCaretPosition() {
    GUITHREADINFO gui_info = {};
    gui_info.cbSize = sizeof(GUITHREADINFO);

    HWND hwnd_fore = GetForegroundWindow();
    if (hwnd_fore) {
        DWORD tid = GetWindowThreadProcessId(hwnd_fore, nullptr);
        if (GetGUIThreadInfo(tid, &gui_info)) {
            int x = gui_info.rcCaret.left;
            int y = gui_info.rcCaret.bottom + 2;
            HWND hwnd_caret = gui_info.hwndCaret ? gui_info.hwndCaret : gui_info.hwndFocus;
            if (hwnd_caret) {
                POINT pt = {x, y};
                ClientToScreen(hwnd_caret, &pt);
                return {pt.x, pt.y};
            }
            return {x, y};
        }
    }

    // Fallback to mouse cursor.
    POINT pt = {};
    GetCursorPos(&pt);
    return {pt.x, pt.y + 20};
}

std::wstring GetModulePath() {
    std::vector<wchar_t> buffer(MAX_PATH);
    HMODULE module = nullptr;
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
                                GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                            reinterpret_cast<LPCWSTR>(&GetModulePath), &module)) {
        module = GetModuleHandleW(nullptr);
    }
    DWORD size = GetModuleFileNameW(module, buffer.data(), static_cast<DWORD>(buffer.size()));
    while (size == buffer.size()) {
        buffer.resize(buffer.size() * 2);
        size = GetModuleFileNameW(module, buffer.data(), static_cast<DWORD>(buffer.size()));
    }
    return std::wstring(buffer.data(), size);
}

std::wstring GetModuleDirectory() {
    std::wstring path = GetModulePath();
    wchar_t* file_part = nullptr;
    std::vector<wchar_t> buffer(path.begin(), path.end());
    buffer.push_back(L'\0');
    PathCchRemoveFileSpec(buffer.data(), buffer.size());
    return std::wstring(buffer.data());
}

HMODULE GetCurrentModule() {
    HMODULE module = nullptr;
    GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
                           GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                       reinterpret_cast<LPCWSTR>(&GetCurrentModule), &module);
    return module;
}

}  // namespace wubi_tsf
