#include "text_service.h"

#include <new>
#include <string>
#include <vector>

#include "common.h"
#include "engine.h"
#include "utils.h"

namespace wubi_tsf {

TextService::TextService() {
    engine_ = CreateDefaultEngine();
}

TextService::~TextService() {
    Deactivate();
}

IFACEMETHODIMP TextService::QueryInterface(REFIID riid, void** ppv) {
    if (!ppv) return E_INVALIDARG;
    *ppv = nullptr;

    if (IsEqualIID(riid, IID_IUnknown)) {
        *ppv = static_cast<IUnknown*>(static_cast<ITfTextInputProcessorEx*>(this));
    } else if (IsEqualIID(riid, IID_ITfTextInputProcessor) ||
               IsEqualIID(riid, IID_ITfTextInputProcessorEx)) {
        *ppv = static_cast<ITfTextInputProcessorEx*>(this);
    } else if (IsEqualIID(riid, IID_ITfThreadMgrEventSink)) {
        *ppv = static_cast<ITfThreadMgrEventSink*>(this);
    } else if (IsEqualIID(riid, IID_ITfKeyEventSink)) {
        *ppv = static_cast<ITfKeyEventSink*>(this);
    } else if (IsEqualIID(riid, IID_ITfCompositionSink)) {
        *ppv = static_cast<ITfCompositionSink*>(this);
    } else {
        return E_NOINTERFACE;
    }

    AddRef();
    return S_OK;
}

IFACEMETHODIMP_(ULONG) TextService::AddRef() {
    return InterlockedIncrement(&ref_count_);
}

IFACEMETHODIMP_(ULONG) TextService::Release() {
    LONG count = InterlockedDecrement(&ref_count_);
    if (count == 0) {
        delete this;
    }
    return count;
}

IFACEMETHODIMP TextService::Activate(ITfThreadMgr* thread_mgr, TfClientId client_id) {
    if (!thread_mgr) return E_INVALIDARG;

    thread_mgr_ = thread_mgr;
    thread_mgr_->AddRef();
    client_id_ = client_id;

    // Load encoding table from DLL directory.
    std::wstring data_path = GetModuleDirectory() + L"\\data\\wubi_86.json";
    engine_->LoadFromFile(data_path);

    // Create candidate window.
    candidate_window_ = std::make_unique<CandidateWindow>();
    candidate_window_->Create(GetCurrentModule());
    candidate_window_->SetSelectCallback([this](int index) { OnCandidateSelected(index); });

    // Install thread manager event sink.
    ITfSource* source = nullptr;
    if (SUCCEEDED(thread_mgr_->QueryInterface(IID_ITfSource, reinterpret_cast<void**>(&source)))) {
        source->AdviseSink(IID_ITfThreadMgrEventSink,
                           static_cast<ITfThreadMgrEventSink*>(this),
                           &thread_mgr_event_sink_cookie_);
        source->Release();
    }

    InitKeyEventSink();

    active_ = true;
    return S_OK;
}

IFACEMETHODIMP TextService::ActivateEx(ITfThreadMgr* thread_mgr, TfClientId client_id, DWORD dwFlags) {
    // For this skeleton, ignore the extra flags and use the standard activation path.
    UNREFERENCED_PARAMETER(dwFlags);
    return Activate(thread_mgr, client_id);
}

IFACEMETHODIMP TextService::Deactivate() {
    if (!active_) return S_OK;
    active_ = false;

    UninitKeyEventSink();

    if (thread_mgr_event_sink_cookie_ != TF_INVALID_COOKIE) {
        ITfSource* source = nullptr;
        if (SUCCEEDED(thread_mgr_->QueryInterface(IID_ITfSource, reinterpret_cast<void**>(&source)))) {
            source->UnadviseSink(thread_mgr_event_sink_cookie_);
            source->Release();
        }
        thread_mgr_event_sink_cookie_ = TF_INVALID_COOKIE;
    }

    if (composition_) {
        composition_->EndComposition(0);
        composition_->Release();
        composition_ = nullptr;
    }

    candidate_window_.reset();
    engine_->Reset();

    SAFE_RELEASE(thread_mgr_);
    client_id_ = TF_CLIENTID_NULL;

    return S_OK;
}

HRESULT TextService::InitKeyEventSink() {
    if (!thread_mgr_) return E_FAIL;

    ITfKeystrokeMgr* ks_mgr = nullptr;
    if (FAILED(thread_mgr_->QueryInterface(IID_ITfKeystrokeMgr, reinterpret_cast<void**>(&ks_mgr)))) {
        return E_FAIL;
    }

    HRESULT hr = ks_mgr->AdviseKeyEventSink(client_id_, static_cast<ITfKeyEventSink*>(this), TRUE);
    ks_mgr->Release();
    return hr;
}

HRESULT TextService::UninitKeyEventSink() {
    if (!thread_mgr_) return E_FAIL;

    ITfKeystrokeMgr* ks_mgr = nullptr;
    if (FAILED(thread_mgr_->QueryInterface(IID_ITfKeystrokeMgr, reinterpret_cast<void**>(&ks_mgr)))) {
        return E_FAIL;
    }

    HRESULT hr = ks_mgr->UnadviseKeyEventSink(client_id_);
    ks_mgr->Release();
    return hr;
}

// ITfThreadMgrEventSink stubs
IFACEMETHODIMP TextService::OnInitDocumentMgr(ITfDocumentMgr* doc_mgr) { return S_OK; }
IFACEMETHODIMP TextService::OnUninitDocumentMgr(ITfDocumentMgr* doc_mgr) { return S_OK; }
IFACEMETHODIMP TextService::OnSetFocus(ITfDocumentMgr* doc_mgr, ITfDocumentMgr* prev_doc_mgr) {
    return S_OK;
}
IFACEMETHODIMP TextService::OnPushContext(ITfContext* context) { return S_OK; }
IFACEMETHODIMP TextService::OnPopContext(ITfContext* context) { return S_OK; }

// ITfKeyEventSink
IFACEMETHODIMP TextService::OnSetFocus(BOOL foreground) { return S_OK; }

IFACEMETHODIMP TextService::OnTestKeyDown(ITfContext* context, WPARAM wparam, LPARAM lparam, BOOL* eaten) {
    if (!eaten) return E_INVALIDARG;
    *eaten = IsKeyEaten(wparam, lparam) ? TRUE : FALSE;
    return S_OK;
}

IFACEMETHODIMP TextService::OnTestKeyUp(ITfContext* context, WPARAM wparam, LPARAM lparam, BOOL* eaten) {
    if (!eaten) return E_INVALIDARG;
    *eaten = FALSE;
    return S_OK;
}

IFACEMETHODIMP TextService::OnKeyDown(ITfContext* context, WPARAM wparam, LPARAM lparam, BOOL* eaten) {
    if (!eaten) return E_INVALIDARG;

    if (!IsKeyEaten(wparam, lparam)) {
        *eaten = FALSE;
        return S_OK;
    }

    *eaten = TRUE;

    std::string key_name = VirtualKeyToName(wparam, lparam);
    if (key_name.empty()) return S_OK;

    auto result = engine_->ProcessKey(key_name);

    if (result.committed && !result.committed_text.empty()) {
        CommitText(context, result.committed_text);
        if (composition_) {
            composition_->EndComposition(0);
            composition_->Release();
            composition_ = nullptr;
        }
        candidate_window_->Hide();
    } else if (result.consumed) {
        if (engine_->GetCompositionString().empty()) {
            if (composition_) {
                composition_->EndComposition(0);
                composition_->Release();
                composition_ = nullptr;
            }
            candidate_window_->Hide();
        } else {
            UpdateComposition(context, engine_->GetCompositionString());
        }
        if (result.need_update_ui) {
            UpdateCandidateWindow();
        }
    }

    return S_OK;
}

IFACEMETHODIMP TextService::OnKeyUp(ITfContext* context, WPARAM wparam, LPARAM lparam, BOOL* eaten) {
    if (!eaten) return E_INVALIDARG;
    *eaten = FALSE;
    return S_OK;
}

IFACEMETHODIMP TextService::OnPreservedKey(ITfContext* context, REFGUID rguid, BOOL* eaten) {
    if (!eaten) return E_INVALIDARG;
    *eaten = FALSE;
    return S_OK;
}

IFACEMETHODIMP TextService::OnCompositionTerminated(TfEditCookie ecWrite, ITfComposition* composition) {
    if (composition_) {
        composition_->Release();
        composition_ = nullptr;
    }
    engine_->Reset();
    candidate_window_->Hide();
    return S_OK;
}

bool TextService::IsKeyEaten(WPARAM wparam, LPARAM lparam) {
    // Don't eat keys when shift/ctrl/alt/win are pressed, except for our own hotkeys.
    // We do want a-z, 0-9, space, backspace, esc, pageup, pagedown when appropriate.

    bool ctrl = (GetKeyState(VK_CONTROL) & 0x8000) != 0;
    bool alt = (GetKeyState(VK_MENU) & 0x8000) != 0;
    bool shift = (GetKeyState(VK_SHIFT) & 0x8000) != 0;
    bool win = (GetKeyState(VK_LWIN) & 0x8000) || (GetKeyState(VK_RWIN) & 0x8000);

    if (ctrl || alt || win) return false;

    if (wparam >= 'A' && wparam <= 'Z') return true;
    if (wparam >= '0' && wparam <= '9') {
        return !engine_->GetCompositionString().empty();
    }

    switch (wparam) {
        case VK_SPACE:
        case VK_BACK:
        case VK_ESCAPE:
        case VK_PRIOR:  // PageUp
        case VK_NEXT:   // PageDown
            return !engine_->GetCompositionString().empty();
        default:
            return false;
    }
}

std::string TextService::VirtualKeyToName(WPARAM wparam, LPARAM lparam) {
    if (wparam >= 'A' && wparam <= 'Z') {
        char c = static_cast<char>('a' + (wparam - 'A'));
        return std::string(1, c);
    }
    if (wparam >= '0' && wparam <= '9') {
        return std::string(1, static_cast<char>(wparam));
    }

    switch (wparam) {
        case VK_SPACE: return "space";
        case VK_BACK: return "backspace";
        case VK_ESCAPE: return "esc";
        case VK_PRIOR: return "pageup";
        case VK_NEXT: return "pagedown";
        case VK_RETURN: return "return";
        case VK_TAB: return "tab";
        default: return {};
    }
}

void TextService::UpdateCandidateWindow() {
    if (!candidate_window_) return;

    auto candidates = engine_->GetCandidates();
    auto page_info = engine_->GetPageInfo();

    if (candidates.empty()) {
        candidate_window_->Hide();
        return;
    }

    auto [x, y] = GetCaretPosition();
    candidate_window_->Update(engine_->GetCompositionString(), candidates,
                              page_info.first, page_info.second);
    candidate_window_->MoveTo(x, y);
    candidate_window_->Show();
}

void TextService::OnCandidateSelected(int index) {
    if (!thread_mgr_) return;

    ITfDocumentMgr* doc_mgr = nullptr;
    if (FAILED(thread_mgr_->GetFocus(&doc_mgr)) || !doc_mgr) return;

    ITfContext* context = nullptr;
    if (FAILED(doc_mgr->GetTop(&context))) {
        doc_mgr->Release();
        return;
    }

    auto candidates = engine_->GetCandidates();
    if (index >= 0 && index < static_cast<int>(candidates.size())) {
        CommitText(context, candidates[index]);
        if (composition_) {
            composition_->EndComposition(0);
            composition_->Release();
            composition_ = nullptr;
        }
        engine_->Reset();
        candidate_window_->Hide();
    }

    context->Release();
    doc_mgr->Release();
}

HRESULT TextService::StartComposition(ITfContext* context) {
    if (!context) return E_INVALIDARG;

    ITfContextComposition* ctx_comp = nullptr;
    if (FAILED(context->QueryInterface(IID_ITfContextComposition, reinterpret_cast<void**>(&ctx_comp)))) {
        return E_FAIL;
    }

    // TfEditCookie 0 is acceptable for synchronous composition creation.
    HRESULT hr = ctx_comp->StartComposition(0, nullptr, static_cast<ITfCompositionSink*>(this), &composition_);
    ctx_comp->Release();
    return hr;
}

HRESULT TextService::EndComposition(ITfContext* context) {
    if (composition_) {
        composition_->EndComposition(0);
        composition_->Release();
        composition_ = nullptr;
    }
    return S_OK;
}

HRESULT TextService::UpdateComposition(ITfContext* context, const std::wstring& text) {
    if (!context) return E_INVALIDARG;
    if (text.empty()) return S_OK;

    if (!composition_) {
        HRESULT hr = StartComposition(context);
        if (FAILED(hr)) return hr;
    }

    ITfRange* range = nullptr;
    if (FAILED(composition_->GetRange(&range))) {
        return E_FAIL;
    }

    TfEditCookie cookie = 0;
    ITfEditSession* edit_session = nullptr;

    // Simple approach: set text on range via ITfRange::SetText in an edit session.
    // For simplicity, we use TF_ES_SYNC edit session inline via a lambda-like helper.
    // However, TSF edit sessions require a COM object. We use a small local class.
    class SetTextEditSession : public ITfEditSession {
    public:
        SetTextEditSession(ITfRange* range, const std::wstring& text)
            : range_(range), text_(text) {
            range_->AddRef();
        }
        ~SetTextEditSession() { range_->Release(); }

        IFACEMETHODIMP QueryInterface(REFIID riid, void** ppv) {
            if (!ppv) return E_INVALIDARG;
            if (IsEqualIID(riid, IID_IUnknown) || IsEqualIID(riid, IID_ITfEditSession)) {
                *ppv = this;
                AddRef();
                return S_OK;
            }
            return E_NOINTERFACE;
        }
        IFACEMETHODIMP_(ULONG) AddRef() { return InterlockedIncrement(&ref_); }
        IFACEMETHODIMP_(ULONG) Release() {
            LONG c = InterlockedDecrement(&ref_);
            if (c == 0) delete this;
            return c;
        }
        IFACEMETHODIMP DoEditSession(TfEditCookie ec) {
            return range_->SetText(ec, 0, text_.c_str(), static_cast<LONG>(text_.length()));
        }
    private:
        LONG ref_ = 1;
        ITfRange* range_;
        std::wstring text_;
    };

    SetTextEditSession* session = new (std::nothrow) SetTextEditSession(range, text);
    range->Release();
    if (!session) return E_OUTOFMEMORY;

    HRESULT hr = context->RequestEditSession(client_id_, session, TF_ES_SYNC | TF_ES_READWRITE, &hr);
    session->Release();
    return hr;
}

HRESULT TextService::CommitText(ITfContext* context, const std::wstring& text) {
    if (!context || text.empty()) return E_INVALIDARG;

    class CommitEditSession : public ITfEditSession {
    public:
        CommitEditSession(ITfContext* context, const std::wstring& text)
            : context_(context), text_(text) {
            context_->AddRef();
        }
        ~CommitEditSession() { context_->Release(); }

        IFACEMETHODIMP QueryInterface(REFIID riid, void** ppv) {
            if (!ppv) return E_INVALIDARG;
            if (IsEqualIID(riid, IID_IUnknown) || IsEqualIID(riid, IID_ITfEditSession)) {
                *ppv = this;
                AddRef();
                return S_OK;
            }
            return E_NOINTERFACE;
        }
        IFACEMETHODIMP_(ULONG) AddRef() { return InterlockedIncrement(&ref_); }
        IFACEMETHODIMP_(ULONG) Release() {
            LONG c = InterlockedDecrement(&ref_);
            if (c == 0) delete this;
            return c;
        }
        IFACEMETHODIMP DoEditSession(TfEditCookie ec) {
            ITfInsertAtSelection* insert = nullptr;
            if (FAILED(context_->QueryInterface(IID_ITfInsertAtSelection, reinterpret_cast<void**>(&insert)))) {
                return E_FAIL;
            }
            ITfRange* range = nullptr;
            HRESULT hr = insert->InsertTextAtSelection(ec, 0, text_.c_str(), static_cast<LONG>(text_.length()), &range);
            if (range) range->Release();
            insert->Release();
            return hr;
        }
    private:
        LONG ref_ = 1;
        ITfContext* context_;
        std::wstring text_;
    };

    CommitEditSession* session = new (std::nothrow) CommitEditSession(context, text);
    if (!session) return E_OUTOFMEMORY;

    HRESULT hr = context->RequestEditSession(client_id_, session, TF_ES_SYNC | TF_ES_READWRITE, nullptr);
    session->Release();
    return hr;
}

}  // namespace wubi_tsf
