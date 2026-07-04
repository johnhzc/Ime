#include "utils.h"

#include <windows.h>
#include <pathcch.h>
#include <stdarg.h>
#include <stdio.h>
#include <string>
#include <vector>

#pragma comment(lib, "pathcch.lib")

namespace wubi_tsf {

namespace {

HINSTANCE g_module_instance = nullptr;

}  // namespace

void RuntimeLog(const wchar_t* format, ...) {
    wchar_t temp_path[MAX_PATH] = {};
    if (GetEnvironmentVariableW(L"TEMP", temp_path, MAX_PATH) == 0) {
        GetCurrentDirectoryW(MAX_PATH, temp_path);
    }
    std::wstring log_path = std::wstring(temp_path) + L"\\WubiIME_Runtime.log";

    HANDLE file = CreateFileW(log_path.c_str(), FILE_APPEND_DATA, FILE_SHARE_READ,
                              nullptr, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) {
        return;
    }

    SYSTEMTIME st = {};
    GetLocalTime(&st);

    wchar_t buf[2048] = {};
    int len = swprintf_s(buf, L"[%04d-%02d-%02d %02d:%02d:%02d] ",
                         st.wYear, st.wMonth, st.wDay,
                         st.wHour, st.wMinute, st.wSecond);

    va_list args;
    va_start(args, format);
    len += vswprintf_s(buf + len, _countof(buf) - len, format, args);
    va_end(args);

    len += swprintf_s(buf + len, _countof(buf) - len, L"\r\n");

    DWORD written = 0;
    WriteFile(file, buf, static_cast<DWORD>(len * sizeof(wchar_t)), &written, nullptr);
    CloseHandle(file);
}

void SetInstanceHandle(HINSTANCE instance) {
    g_module_instance = instance;
}

HINSTANCE GetInstanceHandle() {
    if (!g_module_instance) {
        g_module_instance = GetModuleHandleW(nullptr);
    }
    return g_module_instance;
}

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
