#include "text_service.h"

#include <new>
#include <stdarg.h>
#include <stdio.h>
#include <string>
#include <vector>

#include "common.h"
#include "engine.h"
#include "utils.h"

namespace wubi_tsf {

class CompositionEditSession : public ITfEditSession {
public:
    enum class Mode { Update, Commit };

    CompositionEditSession(TextService* service, ITfContext* context,
                           const std::wstring& text, Mode mode)
        : service_(service), context_(context), text_(text), mode_(mode) {
        context_->AddRef();
    }
    ~CompositionEditSession() { context_->Release(); }

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
        RuntimeLog(L"[DoEditSession] mode=%s text='%s' composition=0x%p",
                   mode_ == Mode::Commit ? L"commit" : L"update",
                   text_.c_str(), service_->composition_);

        HRESULT hr = S_OK;
        ITfContextComposition* ctx_comp = nullptr;
        hr = context_->QueryInterface(IID_ITfContextComposition,
                                      reinterpret_cast<void**>(&ctx_comp));
        if (FAILED(hr) || !ctx_comp) {
            RuntimeLog(L"[DoEditSession] QueryInterface ITfContextComposition failed hr=0x%08X", hr);
            return hr;
        }

        // Start a composition if we don't have one and this is an update.
        if (mode_ == Mode::Update && !service_->composition_) {
            hr = ctx_comp->StartComposition(ec, nullptr,
                                            static_cast<ITfCompositionSink*>(service_),
                                            &service_->composition_);
            RuntimeLog(L"[DoEditSession] StartComposition hr=0x%08X", hr);
            if (FAILED(hr)) {
                ctx_comp->Release();
                return hr;
            }
        }

        if (service_->composition_) {
            ITfRange* range = nullptr;
            hr = service_->composition_->GetRange(&range);
            if (SUCCEEDED(hr) && range) {
                // For commit with non-empty text, replace the composition content.
                // For empty commit (e.g. Esc cleared the code), just end the composition
                // without replacing, to avoid deleting application text.
                if (!text_.empty() || mode_ == Mode::Update) {
                    hr = range->SetText(ec, 0, text_.c_str(),
                                        static_cast<LONG>(text_.length()));
                    RuntimeLog(L"[DoEditSession] SetText hr=0x%08X len=%d", hr,
                               static_cast<int>(text_.length()));
                }
                range->Release();

                if (mode_ == Mode::Commit) {
                    hr = service_->composition_->EndComposition(ec);
                    RuntimeLog(L"[DoEditSession] EndComposition hr=0x%08X", hr);
                    service_->composition_->Release();
                    service_->composition_ = nullptr;
                    service_->engine_->Reset();
                    if (service_->candidate_window_) {
                        service_->candidate_window_->Hide();
                    }
                }
            } else {
                RuntimeLog(L"[DoEditSession] GetRange failed hr=0x%08X", hr);
            }
        } else if (mode_ == Mode::Commit && !text_.empty()) {
            // No active composition: just insert the text at the selection.
            ITfInsertAtSelection* insert = nullptr;
            hr = context_->QueryInterface(IID_ITfInsertAtSelection,
                                          reinterpret_cast<void**>(&insert));
            if (SUCCEEDED(hr) && insert) {
                ITfRange* range = nullptr;
                hr = insert->InsertTextAtSelection(ec, 0, text_.c_str(),
                                                   static_cast<LONG>(text_.length()), &range);
                RuntimeLog(L"[DoEditSession] InsertTextAtSelection hr=0x%08X", hr);
                if (range) range->Release();
                insert->Release();
            } else {
                RuntimeLog(L"[DoEditSession] QueryInterface ITfInsertAtSelection failed hr=0x%08X", hr);
            }
            service_->engine_->Reset();
            if (service_->candidate_window_) {
                service_->candidate_window_->Hide();
            }
        }

        ctx_comp->Release();
        return S_OK;
    }

private:
    LONG ref_ = 1;
    TextService* service_ = nullptr;
    ITfContext* context_ = nullptr;
    std::wstring text_;
    Mode mode_ = Mode::Update;
};

HRESULT RequestCompositionEditSession(TextService* service, ITfContext* context,
                                      const std::wstring& text,
                                      CompositionEditSession::Mode mode) {
    if (!context) return E_INVALIDARG;

    CompositionEditSession* session =
        new (std::nothrow) CompositionEditSession(service, context, text, mode);
    if (!session) return E_OUTOFMEMORY;

    HRESULT hr_session = S_OK;
    HRESULT hr = context->RequestEditSession(service->client_id(), session,
                                             TF_ES_ASYNCDONTCARE | TF_ES_READWRITE, &hr_session);
    session->Release();
    if (FAILED(hr)) {
        RuntimeLog(L"[RequestCompositionEditSession] RequestEditSession failed hr=0x%08X", hr);
        return hr;
    }
    if (FAILED(hr_session)) {
        RuntimeLog(L"[RequestCompositionEditSession] EditSession failed hr=0x%08X", hr_session);
        return hr_session;
    }
    return S_OK;
}

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

    RuntimeLog(L"[Activate] client_id=%u module_dir='%s'", client_id, GetModuleDirectory().c_str());

    // Load encoding table from DLL directory.
    std::wstring data_path = GetModuleDirectory() + L"\\data\\wubi_86.json";
    bool loaded = engine_->LoadFromFile(data_path);
    RuntimeLog(L"[Activate] loading '%s' result=%d", data_path.c_str(), loaded);
    if (!loaded) {
        RuntimeLog(L"[Activate] WARNING: failed to load encoding table");
    }

    // Create candidate window.
    candidate_window_ = std::make_unique<CandidateWindow>();
    if (!candidate_window_->Create(GetInstanceHandle())) {
        RuntimeLog(L"[Activate] CandidateWindow::Create failed");
    }
    candidate_window_->SetSelectCallback([this](int index) { OnCandidateSelected(index); });

    // Install thread manager event sink.
    ITfSource* source = nullptr;
    if (SUCCEEDED(thread_mgr_->QueryInterface(IID_ITfSource, reinterpret_cast<void**>(&source)))) {
        source->AdviseSink(IID_ITfThreadMgrEventSink,
                           static_cast<ITfThreadMgrEventSink*>(this),
                           &thread_mgr_event_sink_cookie_);
        source->Release();
    }

    HRESULT hr = InitKeyEventSink();
    RuntimeLog(L"[Activate] InitKeyEventSink hr=0x%08X", hr);

    active_ = true;
    return S_OK;
}

IFACEMETHODIMP TextService::ActivateEx(ITfThreadMgr* thread_mgr, TfClientId client_id, DWORD dwFlags) {
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
    bool eaten_bool = IsKeyEaten(wparam, lparam);
    *eaten = eaten_bool ? TRUE : FALSE;
    if (wparam >= 'A' && wparam <= 'Z') {
        RuntimeLog(L"[OnTestKeyDown] vk=0x%02X eaten=%d chinese=%d",
                   wparam, eaten_bool, engine_->IsChineseMode());
    }
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

    RuntimeLog(L"[OnKeyDown] key=%S eaten=1", key_name.c_str());

    auto result = engine_->ProcessKey(key_name);
    RuntimeLog(L"[OnKeyDown] consumed=%d committed=%d text='%s'",
               result.consumed, result.committed, result.committed_text.c_str());

    if (result.committed && !result.committed_text.empty()) {
        HRESULT hr = CommitText(context, result.committed_text);
        RuntimeLog(L"[OnKeyDown] CommitText hr=0x%08X", hr);
        // Ensure candidate window is hidden after a successful commit.
        if (SUCCEEDED(hr) && candidate_window_) {
            candidate_window_->Hide();
        }
    } else if (result.consumed) {
        if (engine_->GetCompositionString().empty()) {
            HRESULT hr = EndComposition(context);
            RuntimeLog(L"[OnKeyDown] EndComposition hr=0x%08X", hr);
        } else {
            HRESULT hr = UpdateComposition(context, engine_->GetCompositionString());
            RuntimeLog(L"[OnKeyDown] UpdateComposition hr=0x%08X", hr);
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
    RuntimeLog(L"[OnCompositionTerminated]");
    if (composition_) {
        composition_->Release();
        composition_ = nullptr;
    }
    engine_->Reset();
    if (candidate_window_) {
        candidate_window_->Hide();
    }
    return S_OK;
}

bool TextService::IsKeyEaten(WPARAM wparam, LPARAM lparam) {
    bool ctrl = (GetKeyState(VK_CONTROL) & 0x8000) != 0;
    bool alt = (GetKeyState(VK_MENU) & 0x8000) != 0;
    bool win = (GetKeyState(VK_LWIN) & 0x8000) || (GetKeyState(VK_RWIN) & 0x8000);

    if (ctrl || alt || win) return false;

    // Letter keys are only consumed in Chinese mode.
    if (wparam >= 'A' && wparam <= 'Z') {
        return engine_->IsChineseMode();
    }

    // Standalone Shift toggles Chinese/English mode.
    if (wparam == VK_SHIFT) {
        return true;
    }

    if (wparam >= '0' && wparam <= '9') {
        return !engine_->GetCompositionString().empty();
    }

    switch (wparam) {
        case VK_SPACE:
        case VK_BACK:
        case VK_ESCAPE:
        case VK_PRIOR:
        case VK_NEXT:
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
        case VK_SHIFT: return "shift";
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
    }

    context->Release();
    doc_mgr->Release();
}

HRESULT TextService::StartComposition(ITfContext* context) {
    return RequestCompositionEditSession(this, context, L"", CompositionEditSession::Mode::Update);
}

HRESULT TextService::EndComposition(ITfContext* context) {
    if (!context) return E_INVALIDARG;
    if (!composition_) return S_OK;

    CompositionEditSession* session =
        new (std::nothrow) CompositionEditSession(this, context, L"", CompositionEditSession::Mode::Commit);
    if (!session) return E_OUTOFMEMORY;

    // Passing an empty commit session will end the existing composition.
    HRESULT hr_session = S_OK;
    HRESULT hr = context->RequestEditSession(client_id_, session,
                                             TF_ES_ASYNCDONTCARE | TF_ES_READWRITE, &hr_session);
    session->Release();
    if (FAILED(hr)) {
        RuntimeLog(L"[EndComposition] RequestEditSession failed hr=0x%08X", hr);
        return hr;
    }
    if (FAILED(hr_session)) {
        RuntimeLog(L"[EndComposition] EditSession failed hr=0x%08X", hr_session);
        return hr_session;
    }
    return S_OK;
}

HRESULT TextService::UpdateComposition(ITfContext* context, const std::wstring& text) {
    RuntimeLog(L"[UpdateComposition] text='%s'", text.c_str());
    return RequestCompositionEditSession(this, context, text, CompositionEditSession::Mode::Update);
}

HRESULT TextService::CommitText(ITfContext* context, const std::wstring& text) {
    RuntimeLog(L"[CommitText] text='%s'", text.c_str());
    return RequestCompositionEditSession(this, context, text, CompositionEditSession::Mode::Commit);
}

}  // namespace wubi_tsf
