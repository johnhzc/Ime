#pragma once

#include <functional>
#include <string>
#include <vector>
#include <windows.h>

namespace wubi_tsf {

class CandidateWindow {
public:
    using SelectCallback = std::function<void(int)>;

    CandidateWindow();
    ~CandidateWindow();

    bool Create(HINSTANCE instance);
    void Destroy();

    void Show();
    void Hide();
    bool IsVisible() const;

    void MoveTo(int x, int y);
    void Update(const std::wstring& composition,
                const std::vector<std::wstring>& candidates,
                int page,
                int total_pages);

    void SetSelectCallback(SelectCallback callback);

private:
    static LRESULT CALLBACK WindowProc(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam);
    LRESULT HandleMessage(UINT msg, WPARAM wparam, LPARAM lparam);

    void Paint(HDC hdc);
    int HitTest(int x, int y) const;

    HWND hwnd_ = nullptr;
    HINSTANCE instance_ = nullptr;
    std::wstring composition_;
    std::vector<std::wstring> candidates_;
    int page_ = 1;
    int total_pages_ = 1;
    SelectCallback on_select_;

    // Layout metrics
    int item_height_ = 28;
    int padding_ = 8;
    int code_height_ = 24;
    int page_height_ = 18;
    int item_width_ = 48;

    static constexpr wchar_t kClassName[] = L"WubiTSFCandidateWindow";
};

}  // namespace wubi_tsf
