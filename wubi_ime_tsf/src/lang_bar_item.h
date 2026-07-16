#pragma once

#include <ctfutb.h>
#include <functional>
#include <string>

namespace wubi_tsf {

// 语言栏按钮：显示当前中/英文状态，点击可切换。
// 实现 ITfLangBarItemButton + ITfSource。
class LangBarItem : public ITfLangBarItemButton,
                    public ITfSource {
public:
    using ToggleCallback = std::function<void()>;

    explicit LangBarItem(ToggleCallback on_click);
    ~LangBarItem();

    // 设置当前是否为中文模式并刷新语言栏显示。
    void SetChineseMode(bool chinese);
    void Update();

    // IUnknown
    IFACEMETHODIMP QueryInterface(REFIID riid, void** ppv) override;
    IFACEMETHODIMP_(ULONG) AddRef() override;
    IFACEMETHODIMP_(ULONG) Release() override;

    // ITfLangBarItem (通过 ITfLangBarItemButton 继承)
    IFACEMETHODIMP GetInfo(TF_LANGBARITEMINFO* pInfo) override;
    IFACEMETHODIMP GetStatus(DWORD* pdwStatus) override;
    IFACEMETHODIMP Show(BOOL fShow) override;
    IFACEMETHODIMP GetTooltipString(BSTR* pbstrToolTip) override;

    // ITfLangBarItemButton
    IFACEMETHODIMP OnClick(TfLBIClick click, POINT pt, const RECT* prcArea) override;
    IFACEMETHODIMP InitMenu(ITfMenu* pMenu) override;
    IFACEMETHODIMP OnMenuSelect(UINT wID) override;
    IFACEMETHODIMP GetIcon(HICON* phIcon) override;
    IFACEMETHODIMP GetText(BSTR* pbstrText) override;

    // ITfSource
    IFACEMETHODIMP AdviseSink(REFIID riid, IUnknown* punk, DWORD* pdwCookie) override;
    IFACEMETHODIMP UnadviseSink(DWORD dwCookie) override;

private:
    LONG ref_count_ = 1;
    ToggleCallback on_click_;
    bool chinese_mode_ = true;
    ITfLangBarItemSink* sink_ = nullptr;
    DWORD sink_cookie_ = 0;
};

}  // namespace wubi_tsf
