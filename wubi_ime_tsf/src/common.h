#pragma once

#ifndef _WIN32_WINNT
#define _WIN32_WINNT _WIN32_WINNT_WIN10
#endif

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif

#include <windows.h>
#include <msctf.h>
#include <string>
#include <memory>
#include <vector>

// COM helpers
#define SAFE_RELEASE(p) \
    do {                 \
        if (p) {         \
            (p)->Release(); \
            (p) = nullptr;  \
        }                  \
    } while (0)

namespace wubi_tsf {

// {A1B2C3D4-E5F6-7890-1234-567890ABCDEF}
// CLSID for WubiIME TSF Text Service
inline constexpr CLSID CLSID_WubiIME_Service = {
    0xa1b2c3d4, 0xe5f6, 0x7890, {0x12, 0x34, 0x56, 0x78, 0x90, 0xab, 0xcd, 0xef}
};

// {B2C3D4E5-F6A7-8901-2345-678901BCDEF0}
// GUID for display attribute (underline composition)
inline constexpr GUID GUID_WubiIME_DisplayAttr = {
    0xb2c3d4e5, 0xf6a7, 0x8901, {0x23, 0x45, 0x67, 0x89, 0x01, 0xbc, 0xde, 0xf0}
};

// Profile GUID
inline constexpr GUID GUID_WubiIME_Profile = {
    0xc3d4e5f6, 0xa7b8, 0x9012, {0x34, 0x56, 0x78, 0x90, 0x12, 0xcd, 0xef, 0x01}
};

// LANGID for Chinese (Simplified)
inline constexpr LANGID kLangId = MAKELANGID(LANG_CHINESE, SUBLANG_CHINESE_SIMPLIFIED);

// Constants
inline constexpr wchar_t kImeName[] = L"五笔输入法 (TSF)";
inline constexpr wchar_t kImeDescription[] = L"基于 TSF 的五笔输入法骨架";
inline constexpr wchar_t kImeIconPath[] = L"";  // Can be set to DLL path with icon resource

}  // namespace wubi_tsf
