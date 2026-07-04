#include <windows.h>
#include <msctf.h>
#include <new>
#include <objbase.h>
#include <stdarg.h>
#include <stdio.h>
#include <string>

#include "common.h"
#include "factory.h"
#include "utils.h"

namespace wubi_tsf {

namespace {

LONG g_lock_count = 0;

std::wstring GuidToString(REFGUID guid) {
    OLECHAR buf[40] = {};
    StringFromGUID2(guid, buf, 40);
    return std::wstring(buf);
}

void LogMessage(const wchar_t* format, ...) {
    wchar_t temp_path[MAX_PATH] = {};
    if (GetEnvironmentVariableW(L"TEMP", temp_path, MAX_PATH) == 0) {
        GetCurrentDirectoryW(MAX_PATH, temp_path);
    }
    std::wstring log_path = std::wstring(temp_path) + L"\\WubiIME_Register.log";

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

std::wstring GetDllPath() {
    wchar_t path[MAX_PATH] = {};
    HMODULE module = nullptr;
    GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
                           GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                       reinterpret_cast<LPCWSTR>(&GetDllPath), &module);
    GetModuleFileNameW(module, path, MAX_PATH);
    return std::wstring(path);
}

HRESULT RegisterProfile(const std::wstring& dll_path) {
    // Prefer the modern profile manager (Vista+), which enables the profile by default.
    ITfInputProcessorProfileMgr* mgr = nullptr;
    HRESULT hr = CoCreateInstance(CLSID_TF_InputProcessorProfiles, nullptr,
                                  CLSCTX_INPROC_SERVER,
                                  IID_ITfInputProcessorProfileMgr,
                                  reinterpret_cast<void**>(&mgr));
    if (SUCCEEDED(hr) && mgr) {
        hr = mgr->RegisterProfile(CLSID_WubiIME_Service,
                                  kLangId,
                                  GUID_WubiIME_Profile,
                                  kImeName,
                                  static_cast<ULONG>(wcslen(kImeName)),
                                  dll_path.c_str(),
                                  static_cast<ULONG>(dll_path.length()),
                                  0,        // icon index
                                  nullptr,  // hklSubstitute
                                  0,        // dwPreferredLayout
                                  TRUE,     // bEnabledByDefault
                                  0);       // dwFlags
        LogMessage(L"ProfileMgr::RegisterProfile hr=0x%08X", hr);
        mgr->Release();
        return hr;
    }
    if (mgr) {
        mgr->Release();
    }
    LogMessage(L"ProfileMgr unavailable (0x%08X), using fallback", hr);

    // Fallback to the older ITfInputProcessorProfiles API.
    ITfInputProcessorProfiles* profiles = nullptr;
    hr = CoCreateInstance(CLSID_TF_InputProcessorProfiles, nullptr,
                          CLSCTX_INPROC_SERVER,
                          IID_ITfInputProcessorProfiles,
                          reinterpret_cast<void**>(&profiles));
    if (FAILED(hr)) {
        LogMessage(L"CoCreate TF_InputProcessorProfiles failed 0x%08X", hr);
        return hr;
    }

    hr = profiles->Register(CLSID_WubiIME_Service);
    LogMessage(L"Profiles::Register hr=0x%08X", hr);

    if (SUCCEEDED(hr)) {
        hr = profiles->AddLanguageProfile(CLSID_WubiIME_Service,
                                          kLangId,
                                          GUID_WubiIME_Profile,
                                          kImeName,
                                          static_cast<ULONG>(wcslen(kImeName)),
                                          dll_path.c_str(),
                                          static_cast<ULONG>(dll_path.length()),
                                          0);
        LogMessage(L"Profiles::AddLanguageProfile hr=0x%08X", hr);

        if (SUCCEEDED(hr)) {
            hr = profiles->EnableLanguageProfileByDefault(CLSID_WubiIME_Service,
                                                          kLangId,
                                                          GUID_WubiIME_Profile,
                                                          TRUE);
            LogMessage(L"Profiles::EnableLanguageProfileByDefault hr=0x%08X", hr);
        }
    }

    profiles->Release();
    return hr;
}

HRESULT UnregisterProfile() {
    ITfInputProcessorProfileMgr* mgr = nullptr;
    HRESULT hr = CoCreateInstance(CLSID_TF_InputProcessorProfiles, nullptr,
                                  CLSCTX_INPROC_SERVER,
                                  IID_ITfInputProcessorProfileMgr,
                                  reinterpret_cast<void**>(&mgr));
    if (SUCCEEDED(hr) && mgr) {
        hr = mgr->UnregisterProfile(CLSID_WubiIME_Service, kLangId, GUID_WubiIME_Profile, 0);
        mgr->Release();
        return hr;
    }
    if (mgr) {
        mgr->Release();
    }

    ITfInputProcessorProfiles* profiles = nullptr;
    hr = CoCreateInstance(CLSID_TF_InputProcessorProfiles, nullptr,
                          CLSCTX_INPROC_SERVER,
                          IID_ITfInputProcessorProfiles,
                          reinterpret_cast<void**>(&profiles));
    if (FAILED(hr)) {
        return hr;
    }
    profiles->RemoveLanguageProfile(CLSID_WubiIME_Service, kLangId, GUID_WubiIME_Profile);
    profiles->Unregister(CLSID_WubiIME_Service);
    profiles->Release();
    return S_OK;
}

HRESULT RegisterCategories() {
    const GUID* categories[] = {
        &GUID_TFCAT_TIP_KEYBOARD,
        &GUID_TFCAT_TIPCAP_UIELEMENTENABLED,
        &GUID_TFCAT_TIPCAP_SECUREMODE,
    };

    ITfCategoryMgr* cat_mgr = nullptr;
    HRESULT hr = CoCreateInstance(CLSID_TF_CategoryMgr, nullptr,
                                  CLSCTX_INPROC_SERVER,
                                  IID_ITfCategoryMgr,
                                  reinterpret_cast<void**>(&cat_mgr));
    if (FAILED(hr)) {
        LogMessage(L"CoCreate TF_CategoryMgr failed 0x%08X", hr);
        return hr;
    }

    for (const GUID* cat : categories) {
        HRESULT h = cat_mgr->RegisterCategory(CLSID_WubiIME_Service, *cat, CLSID_WubiIME_Service);
        LogMessage(L"RegisterCategory %s hr=0x%08X", GuidToString(*cat).c_str(), h);
    }

    cat_mgr->Release();
    return S_OK;
}

HRESULT UnregisterCategories() {
    const GUID* categories[] = {
        &GUID_TFCAT_TIP_KEYBOARD,
        &GUID_TFCAT_TIPCAP_UIELEMENTENABLED,
        &GUID_TFCAT_TIPCAP_SECUREMODE,
    };

    ITfCategoryMgr* cat_mgr = nullptr;
    HRESULT hr = CoCreateInstance(CLSID_TF_CategoryMgr, nullptr,
                                  CLSCTX_INPROC_SERVER,
                                  IID_ITfCategoryMgr,
                                  reinterpret_cast<void**>(&cat_mgr));
    if (FAILED(hr)) {
        return hr;
    }

    for (const GUID* cat : categories) {
        cat_mgr->UnregisterCategory(CLSID_WubiIME_Service, *cat, CLSID_WubiIME_Service);
    }

    cat_mgr->Release();
    return S_OK;
}

}  // namespace

}  // namespace wubi_tsf

BOOL APIENTRY DllMain(HMODULE module, DWORD reason, LPVOID reserved) {
    switch (reason) {
        case DLL_PROCESS_ATTACH:
            DisableThreadLibraryCalls(module);
            wubi_tsf::SetInstanceHandle(module);
            break;
        case DLL_PROCESS_DETACH:
            break;
    }
    return TRUE;
}

STDAPI DllGetClassObject(REFCLSID rclsid, REFIID riid, void** ppv) {
    if (!ppv) return E_INVALIDARG;
    *ppv = nullptr;

    if (!IsEqualIID(rclsid, wubi_tsf::CLSID_WubiIME_Service)) {
        return CLASS_E_CLASSNOTAVAILABLE;
    }

    wubi_tsf::ClassFactory* factory = new (std::nothrow) wubi_tsf::ClassFactory();
    if (!factory) return E_OUTOFMEMORY;

    HRESULT hr = factory->QueryInterface(riid, ppv);
    factory->Release();
    return hr;
}

STDAPI DllCanUnloadNow() {
    return InterlockedCompareExchange(&wubi_tsf::g_lock_count, 0, 0) == 0 ? S_OK : S_FALSE;
}

STDAPI DllRegisterServer() {
    wubi_tsf::LogMessage(L"DllRegisterServer start");

    HRESULT hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
    bool com_initialized = SUCCEEDED(hr);
    if (FAILED(hr) && hr != RPC_E_CHANGED_MODE) {
        wubi_tsf::LogMessage(L"CoInitializeEx failed 0x%08X", hr);
        return hr;
    }
    wubi_tsf::LogMessage(L"CoInitializeEx com_initialized=%d", com_initialized);

    std::wstring dll_path = wubi_tsf::GetDllPath();
    wubi_tsf::LogMessage(L"DLL path: %s", dll_path.c_str());

    // Register COM CLSID.
    OLECHAR clsid_str[40] = {};
    StringFromGUID2(wubi_tsf::CLSID_WubiIME_Service, clsid_str, 40);
    std::wstring key_path = std::wstring(L"CLSID\\") + clsid_str;

    HKEY hkey = nullptr;
    LSTATUS status = RegCreateKeyExW(HKEY_CLASSES_ROOT, key_path.c_str(), 0, nullptr, 0,
                                     KEY_WRITE, nullptr, &hkey, nullptr);
    if (status == ERROR_SUCCESS) {
        RegSetValueExW(hkey, nullptr, 0, REG_SZ,
                       reinterpret_cast<const BYTE*>(wubi_tsf::kImeName),
                       static_cast<DWORD>((wcslen(wubi_tsf::kImeName) + 1) * sizeof(wchar_t)));
        HKEY inproc = nullptr;
        if (RegCreateKeyExW(hkey, L"InprocServer32", 0, nullptr, 0,
                            KEY_WRITE, nullptr, &inproc, nullptr) == ERROR_SUCCESS) {
            RegSetValueExW(inproc, nullptr, 0, REG_SZ,
                           reinterpret_cast<const BYTE*>(dll_path.c_str()),
                           static_cast<DWORD>((dll_path.length() + 1) * sizeof(wchar_t)));
            RegSetValueExW(inproc, L"ThreadingModel", 0, REG_SZ,
                           reinterpret_cast<const BYTE*>(L"Apartment"),
                           10 * sizeof(wchar_t));
            RegCloseKey(inproc);
        }
        RegCloseKey(hkey);
        wubi_tsf::LogMessage(L"CLSID registered");
    } else {
        wubi_tsf::LogMessage(L"RegCreateKeyEx CLSID failed LSTATUS=%lu", status);
    }

    HRESULT reg_cat = wubi_tsf::RegisterCategories();
    HRESULT reg_prof = wubi_tsf::RegisterProfile(dll_path);

    if (com_initialized) {
        CoUninitialize();
    }

    wubi_tsf::LogMessage(L"DllRegisterServer result: reg_prof=0x%08X reg_cat=0x%08X",
                         reg_prof, reg_cat);

    if (FAILED(reg_prof)) return reg_prof;
    if (FAILED(reg_cat)) return reg_cat;
    return S_OK;
}

STDAPI DllUnregisterServer() {
    wubi_tsf::LogMessage(L"DllUnregisterServer start");

    HRESULT hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
    bool com_initialized = SUCCEEDED(hr);
    if (FAILED(hr) && hr != RPC_E_CHANGED_MODE) {
        return hr;
    }

    wubi_tsf::UnregisterProfile();
    wubi_tsf::UnregisterCategories();

    OLECHAR clsid_str[40] = {};
    StringFromGUID2(wubi_tsf::CLSID_WubiIME_Service, clsid_str, 40);
    std::wstring key_path = std::wstring(L"CLSID\\") + clsid_str;
    RegDeleteTreeW(HKEY_CLASSES_ROOT, key_path.c_str());

    if (com_initialized) {
        CoUninitialize();
    }

    wubi_tsf::LogMessage(L"DllUnregisterServer done");
    return S_OK;
}
