#pragma once

#include <msctf.h>
#include <memory>
#include <string>

#include "candidate_window.h"
#include "common.h"
#include "lang_bar_item.h"

namespace wubi_tsf {

class ImeEngine;
class CompositionEditSession;

class TextService : public ITfTextInputProcessorEx,
                    public ITfThreadMgrEventSink,
                    public ITfKeyEventSink,
                    public ITfCompositionSink {
    friend class CompositionEditSession;

public:
    TextService();
    virtual ~TextService();

    // IUnknown
    IFACEMETHODIMP QueryInterface(REFIID riid, void** ppv) override;
    IFACEMETHODIMP_(ULONG) AddRef() override;
    IFACEMETHODIMP_(ULONG) Release() override;

    // ITfTextInputProcessor
    IFACEMETHODIMP Activate(ITfThreadMgr* thread_mgr, TfClientId client_id) override;
    IFACEMETHODIMP Deactivate() override;

    // ITfTextInputProcessorEx
    IFACEMETHODIMP ActivateEx(ITfThreadMgr* thread_mgr, TfClientId client_id, DWORD dwFlags) override;

    // ITfThreadMgrEventSink
    IFACEMETHODIMP OnInitDocumentMgr(ITfDocumentMgr* doc_mgr) override;
    IFACEMETHODIMP OnUninitDocumentMgr(ITfDocumentMgr* doc_mgr) override;
    IFACEMETHODIMP OnSetFocus(ITfDocumentMgr* doc_mgr, ITfDocumentMgr* prev_doc_mgr) override;
    IFACEMETHODIMP OnPushContext(ITfContext* context) override;
    IFACEMETHODIMP OnPopContext(ITfContext* context) override;

    // ITfKeyEventSink
    IFACEMETHODIMP OnSetFocus(BOOL foreground) override;
    IFACEMETHODIMP OnTestKeyDown(ITfContext* context, WPARAM wparam, LPARAM lparam, BOOL* eaten) override;
    IFACEMETHODIMP OnTestKeyUp(ITfContext* context, WPARAM wparam, LPARAM lparam, BOOL* eaten) override;
    IFACEMETHODIMP OnKeyDown(ITfContext* context, WPARAM wparam, LPARAM lparam, BOOL* eaten) override;
    IFACEMETHODIMP OnKeyUp(ITfContext* context, WPARAM wparam, LPARAM lparam, BOOL* eaten) override;
    IFACEMETHODIMP OnPreservedKey(ITfContext* context, REFGUID rguid, BOOL* eaten) override;

    // ITfCompositionSink
    IFACEMETHODIMP OnCompositionTerminated(TfEditCookie ecWrite, ITfComposition* composition) override;

    TfClientId client_id() const { return client_id_; }

private:
    HRESULT InitKeyEventSink();
    HRESULT UninitKeyEventSink();

    HRESULT StartComposition(ITfContext* context);
    HRESULT EndComposition(ITfContext* context, bool clear_text = false);
    HRESULT UpdateComposition(ITfContext* context, const std::wstring& text);
    HRESULT CommitText(ITfContext* context, const std::wstring& text);

    bool IsKeyEaten(WPARAM wparam, LPARAM lparam);
    std::string VirtualKeyToName(WPARAM wparam, LPARAM lparam);
    void UpdateCandidateWindow(ITfContext* context);
    void OnCandidateSelected(int index);

    LONG ref_count_ = 1;

    ITfThreadMgr* thread_mgr_ = nullptr;
    TfClientId client_id_ = TF_CLIENTID_NULL;
    DWORD thread_mgr_event_sink_cookie_ = TF_INVALID_COOKIE;

    ITfComposition* composition_ = nullptr;

    std::unique_ptr<ImeEngine> engine_;
    std::unique_ptr<CandidateWindow> candidate_window_;
    std::unique_ptr<LangBarItem> lang_bar_item_;

    bool active_ = false;
};

}  // namespace wubi_tsf
