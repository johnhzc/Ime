#include "lang_bar_item.h"

#include <combaseapi.h>
#include <windows.h>

#include "common.h"
#include "utils.h"

namespace wubi_tsf {

namespace {

// 语言栏按钮 GUID（唯一标识本按钮）。
// {A1B2C3D4-E5F6-7890-1234-567890ABCDEF} 已用于 service CLSID，
// 这里换一个独立的 GUID。
constexpr GUID kGuidWubiLangBarButton = {
    0xA1B2C3D5, 0xE5F6, 0x7890, {0x12, 0x34, 0x56, 0x78, 0x90, 0xAB, 0xCD, 0xEF}};

}  // namespace

LangBarItem::LangBarItem(ToggleCallback on_click) : on_click_(std::move(on_click)) {}

LangBarItem::~LangBarItem() {
    if (sink_) {
        sink_->Release();
    }
}

void LangBarItem::SetChineseMode(bool chinese) {
    chinese_mode_ = chinese;
}

void LangBarItem::Update() {
    if (sink_) {
        sink_->OnUpdate(TF_LBI_TEXT | TF_LBI_STATUS);
    }
}

IFACEMETHODIMP LangBarItem::QueryInterface(REFIID riid, void** ppv) {
    if (!ppv) return E_INVALIDARG;
    *ppv = nullptr;

    if (IsEqualIID(riid, IID_IUnknown) ||
        IsEqualIID(riid, IID_ITfLangBarItem) ||
        IsEqualIID(riid, IID_ITfLangBarItemButton)) {
        *ppv = static_cast<ITfLangBarItemButton*>(this);
    } else if (IsEqualIID(riid, IID_ITfSource)) {
        *ppv = static_cast<ITfSource*>(this);
    } else {
        return E_NOINTERFACE;
    }

    AddRef();
    return S_OK;
}

IFACEMETHODIMP_(ULONG) LangBarItem::AddRef() {
    return InterlockedIncrement(&ref_count_);
}

IFACEMETHODIMP_(ULONG) LangBarItem::Release() {
    LONG count = InterlockedDecrement(&ref_count_);
    if (count == 0) {
        delete this;
    }
    return count;
}

IFACEMETHODIMP LangBarItem::GetInfo(TF_LANGBARITEMINFO* pInfo) {
    if (!pInfo) return E_INVALIDARG;
    ZeroMemory(pInfo, sizeof(*pInfo));
    pInfo->clsidService = CLSID_WubiIME_Service;
    pInfo->guidItem = kGuidWubiLangBarButton;
    pInfo->dwStyle = TF_LBI_STYLE_BTN_BUTTON;
    pInfo->ulSort = 0;
    lstrcpyW(pInfo->szDescription, L"五笔输入法中/英文切换");
    return S_OK;
}

IFACEMETHODIMP LangBarItem::GetStatus(DWORD* pdwStatus) {
    if (!pdwStatus) return E_INVALIDARG;
    *pdwStatus = 0;
    return S_OK;
}

IFACEMETHODIMP LangBarItem::Show(BOOL /*fShow*/) {
    return S_OK;
}

IFACEMETHODIMP LangBarItem::GetTooltipString(BSTR* pbstrToolTip) {
    if (!pbstrToolTip) return E_INVALIDARG;
    *pbstrToolTip = SysAllocString(chinese_mode_ ? L"中文模式" : L"英文模式");
    return *pbstrToolTip ? S_OK : E_OUTOFMEMORY;
}

IFACEMETHODIMP LangBarItem::OnClick(TfLBIClick /*click*/, POINT /*pt*/, const RECT* /*prcArea*/) {
    if (on_click_) {
        on_click_();
    }
    return S_OK;
}

IFACEMETHODIMP LangBarItem::InitMenu(ITfMenu* /*pMenu*/) {
    return E_NOTIMPL;
}

IFACEMETHODIMP LangBarItem::OnMenuSelect(UINT /*wID*/) {
    return E_NOTIMPL;
}

IFACEMETHODIMP LangBarItem::GetIcon(HICON* phIcon) {
    if (!phIcon) return E_INVALIDARG;
    *phIcon = nullptr;
    return S_OK;
}

IFACEMETHODIMP LangBarItem::GetText(BSTR* pbstrText) {
    if (!pbstrText) return E_INVALIDARG;
    *pbstrText = SysAllocString(chinese_mode_ ? L"中" : L"英");
    return *pbstrText ? S_OK : E_OUTOFMEMORY;
}

IFACEMETHODIMP LangBarItem::AdviseSink(REFIID riid, IUnknown* punk, DWORD* pdwCookie) {
    if (!pdwCookie || !punk) return E_INVALIDARG;
    *pdwCookie = 0;

    if (!IsEqualIID(riid, IID_ITfLangBarItemSink)) {
        return E_FAIL;
    }

    ITfLangBarItemSink* new_sink = nullptr;
    HRESULT hr = punk->QueryInterface(IID_ITfLangBarItemSink, reinterpret_cast<void**>(&new_sink));
    if (FAILED(hr) || !new_sink) {
        return hr;
    }

    if (sink_) {
        sink_->Release();
    }
    sink_ = new_sink;
    *pdwCookie = 1;
    return S_OK;
}

IFACEMETHODIMP LangBarItem::UnadviseSink(DWORD dwCookie) {
    if (dwCookie != 1) {
        return E_FAIL;
    }
    if (sink_) {
        sink_->Release();
        sink_ = nullptr;
    }
    return S_OK;
}

}  // namespace wubi_tsf
