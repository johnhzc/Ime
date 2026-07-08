#include "candidate_window.h"

#include <windowsx.h>
#include <algorithm>
#include <sstream>

#include "utils.h"

namespace wubi_tsf {

CandidateWindow::CandidateWindow() = default;

CandidateWindow::~CandidateWindow() {
    Destroy();
}

bool CandidateWindow::Create(HINSTANCE instance, HWND parent) {
    instance_ = instance ? instance : GetInstanceHandle();
    parent_ = parent;
    RuntimeLog(L"[CandidateWindow::Create] instance=0x%p parent=0x%p", instance_, parent_);

    // 生成一个尽量唯一的窗口类名；如果上一次注册仍有窗口残留，尝试不同后缀。
    static int suffix_counter = 0;
    DWORD pid = GetCurrentProcessId();
    for (int attempt = 0; attempt < 16; ++attempt) {
        class_name_ = kClassName;
        class_name_ += L"_";
        class_name_ += std::to_wstring(pid);
        class_name_ += L"_";
        class_name_ += std::to_wstring(suffix_counter++);

        if (UnregisterClassW(class_name_.c_str(), instance_)) {
            break;  // 成功注销旧注册
        }

        DWORD err = GetLastError();
        if (err == ERROR_CLASS_DOES_NOT_EXIST) {
            break;  // 没有旧注册
        }
        if (err == ERROR_CLASS_HAS_WINDOWS) {
            RuntimeLog(L"[CandidateWindow::Create] class still has windows, retrying suffix err=%lu", err);
            continue;
        }
        RuntimeLog(L"[CandidateWindow::Create] UnregisterClassW failed err=%lu", err);
    }

    WNDCLASSEXW wc = {};
    wc.cbSize = sizeof(WNDCLASSEXW);
    wc.lpfnWndProc = CandidateWindow::WindowProc;
    wc.hInstance = instance_;
    wc.lpszClassName = class_name_.c_str();
    wc.hbrBackground = CreateSolidBrush(RGB(243, 243, 243));
    wc.hCursor = LoadCursor(nullptr, IDC_ARROW);

    ATOM atom = RegisterClassExW(&wc);
    if (!atom) {
        DWORD err = GetLastError();
        if (err != ERROR_CLASS_ALREADY_EXISTS) {
            RuntimeLog(L"[CandidateWindow::Create] RegisterClassExW failed err=%lu", err);
            return false;
        }
    }
    RuntimeLog(L"[CandidateWindow::Create] RegisterClassExW atom=0x%04X class='%s'",
               atom, class_name_.c_str());

    // 候选窗口作为独立的顶层工具窗口创建，不依赖外部窗口句柄。
    // 早期尝试用 GetDesktopWindow() 作为 owner 仍会失败；根本原因是
    // WindowProc 未在 WM_NCCREATE 中返回 TRUE。此处 owner 使用 nullptr。
    HWND owner = nullptr;
    RuntimeLog(L"[CandidateWindow::Create] owner=0x%p", owner);

    // 确保线程存在消息队列（某些 TSF 宿主可能没有）。
    // PeekMessage + PM_NOREMOVE 是零副作用的消息队列初始化惯用写法。
    MSG msg;
    PeekMessage(&msg, nullptr, 0, 0, PM_NOREMOVE);

    SetLastError(0);
    hwnd_ = CreateWindowExW(
        WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_TOPMOST,
        class_name_.c_str(),
        L"WubiTSF",
        WS_POPUP,
        CW_USEDEFAULT, CW_USEDEFAULT, 400, 120,
        owner,
        nullptr,
        instance_,
        this);

    if (!hwnd_) {
        DWORD err = GetLastError();
        RuntimeLog(L"[CandidateWindow::Create] CreateWindowExW failed err=%lu atom=0x%04X class='%s'",
                   err, atom, class_name_.c_str());
        return false;
    }

    ShowWindow(hwnd_, SW_HIDE);
    RuntimeLog(L"[CandidateWindow::Create] succeeded hwnd=0x%p", hwnd_);
    return true;
}

void CandidateWindow::Destroy() {
    if (hwnd_) {
        DestroyWindow(hwnd_);
        hwnd_ = nullptr;
    }
}

void CandidateWindow::Show(HWND parent) {
    if (parent) {
        parent_ = parent;
    }
    if (!hwnd_) {
        if (!Create(instance_ ? instance_ : GetInstanceHandle(), parent_)) {
            return;
        }
    }
    ShowWindow(hwnd_, SW_SHOWNA);
    SetWindowPos(hwnd_, HWND_TOPMOST, 0, 0, 0, 0,
                 SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW);
}

void CandidateWindow::Hide() {
    if (hwnd_) {
        ShowWindow(hwnd_, SW_HIDE);
    }
}

bool CandidateWindow::IsVisible() const {
    if (!hwnd_) return false;
    return IsWindowVisible(hwnd_) == TRUE;
}

void CandidateWindow::MoveTo(int x, int y) {
    if (!hwnd_) return;

    int width = padding_ * 2 + static_cast<int>(candidates_.size()) * item_width_;
    width = std::max(width, 200);
    int height = padding_ * 2 + code_height_ + item_height_ + page_height_;

    HMONITOR monitor = MonitorFromWindow(hwnd_, MONITOR_DEFAULTTONEAREST);
    MONITORINFO mi = {};
    mi.cbSize = sizeof(MONITORINFO);
    if (GetMonitorInfo(monitor, &mi)) {
        int screen_w = mi.rcWork.right - mi.rcWork.left;
        int screen_h = mi.rcWork.bottom - mi.rcWork.top;
        if (x + width > screen_w) x = screen_w - width - 10;
        if (y + height > screen_h) y = y - height - 20;
        if (y < 0) y = 10;
    }

    SetWindowPos(hwnd_, nullptr, x, y, width, height,
                 SWP_NOZORDER | SWP_NOACTIVATE);
}

void CandidateWindow::Update(const std::wstring& composition,
                             const std::vector<std::wstring>& candidates,
                             int page,
                             int total_pages) {
    composition_ = composition;
    candidates_ = candidates;
    page_ = page + 1;
    total_pages_ = total_pages;

    if (hwnd_) {
        InvalidateRect(hwnd_, nullptr, TRUE);
    }
}

void CandidateWindow::SetSelectCallback(SelectCallback callback) {
    on_select_ = callback;
}

LRESULT CALLBACK CandidateWindow::WindowProc(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam) {
    if (msg == WM_NCCREATE) {
        LPCREATESTRUCT cs = reinterpret_cast<LPCREATESTRUCT>(lparam);
        SetWindowLongPtrW(hwnd, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(cs->lpCreateParams));
        // WM_NCCREATE 必须返回 TRUE，否则 Windows 会终止窗口创建并返回 nullptr。
        return TRUE;
    }

    CandidateWindow* window = reinterpret_cast<CandidateWindow*>(GetWindowLongPtrW(hwnd, GWLP_USERDATA));
    if (window) {
        return window->HandleMessage(msg, wparam, lparam);
    }
    return DefWindowProcW(hwnd, msg, wparam, lparam);
}

LRESULT CandidateWindow::HandleMessage(UINT msg, WPARAM wparam, LPARAM lparam) {
    switch (msg) {
        case WM_PAINT: {
            PAINTSTRUCT ps;
            HDC hdc = BeginPaint(hwnd_, &ps);
            Paint(hdc);
            EndPaint(hwnd_, &ps);
            return 0;
        }
        case WM_LBUTTONUP: {
            int x = GET_X_LPARAM(lparam);
            int y = GET_Y_LPARAM(lparam);
            int index = HitTest(x, y);
            if (index >= 0 && on_select_) {
                on_select_(index);
            }
            return 0;
        }
        case WM_MOUSEACTIVATE:
            return MA_NOACTIVATE;
        default:
            break;
    }
    return DefWindowProcW(hwnd_, msg, wparam, lparam);
}

void CandidateWindow::Paint(HDC hdc) {
    RECT rc;
    GetClientRect(hwnd_, &rc);

    // Background
    HBRUSH bg_brush = CreateSolidBrush(RGB(243, 243, 243));
    FillRect(hdc, &rc, bg_brush);
    DeleteObject(bg_brush);

    // Border
    HPEN border_pen = CreatePen(PS_SOLID, 1, RGB(209, 209, 209));
    HGDIOBJ old_pen = SelectObject(hdc, border_pen);
    HGDIOBJ old_brush = SelectObject(hdc, GetStockObject(NULL_BRUSH));
    Rectangle(hdc, rc.left, rc.top, rc.right, rc.bottom);
    SelectObject(hdc, old_pen);
    SelectObject(hdc, old_brush);
    DeleteObject(border_pen);

    // Composition code
    HFONT code_font = CreateFontW(16, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE,
                                  DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                                  DEFAULT_QUALITY, DEFAULT_PITCH | FF_SWISS, L"Microsoft YaHei UI");
    HGDIOBJ old_font = SelectObject(hdc, code_font);
    SetTextColor(hdc, RGB(0, 120, 212));
    SetBkMode(hdc, TRANSPARENT);

    RECT code_rc = {padding_, padding_, rc.right - padding_, padding_ + code_height_};
    DrawTextW(hdc, composition_.c_str(), -1, &code_rc, DT_LEFT | DT_VCENTER | DT_SINGLELINE);

    // Candidates
    HFONT cand_font = CreateFontW(20, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE,
                                  DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                                  DEFAULT_QUALITY, DEFAULT_PITCH | FF_SWISS, L"Microsoft YaHei UI");
    SelectObject(hdc, cand_font);
    SetTextColor(hdc, RGB(31, 31, 31));

    int y = padding_ + code_height_;
    for (size_t i = 0; i < candidates_.size(); ++i) {
        int x = padding_ + static_cast<int>(i) * item_width_;

        // Index
        SetTextColor(hdc, RGB(0, 120, 212));
        std::wstringstream idx_ss;
        idx_ss << (i + 1) << L".";
        RECT idx_rc = {x, y, x + 20, y + item_height_};
        DrawTextW(hdc, idx_ss.str().c_str(), -1, &idx_rc, DT_LEFT | DT_VCENTER | DT_SINGLELINE);

        // Character
        SetTextColor(hdc, RGB(31, 31, 31));
        RECT char_rc = {x + 20, y, x + item_width_, y + item_height_};
        DrawTextW(hdc, candidates_[i].c_str(), -1, &char_rc, DT_LEFT | DT_VCENTER | DT_SINGLELINE);
    }

    // Page info
    HFONT page_font = CreateFontW(12, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
                                  DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                                  DEFAULT_QUALITY, DEFAULT_PITCH | FF_SWISS, L"Microsoft YaHei UI");
    SelectObject(hdc, page_font);
    SetTextColor(hdc, RGB(102, 102, 102));
    std::wstringstream page_ss;
    page_ss << L"[" << page_ << L"/" << total_pages_ << L"]";
    RECT page_rc = {padding_, rc.bottom - padding_ - page_height_,
                    rc.right - padding_, rc.bottom - padding_};
    DrawTextW(hdc, page_ss.str().c_str(), -1, &page_rc, DT_RIGHT | DT_VCENTER | DT_SINGLELINE);

    SelectObject(hdc, old_font);
    DeleteObject(code_font);
    DeleteObject(cand_font);
    DeleteObject(page_font);
}

int CandidateWindow::HitTest(int x, int y) const {
    int y_start = padding_ + code_height_;
    if (y < y_start || y > y_start + item_height_) return -1;
    int index = (x - padding_) / item_width_;
    if (index >= 0 && index < static_cast<int>(candidates_.size())) {
        return index;
    }
    return -1;
}

}  // namespace wubi_tsf
