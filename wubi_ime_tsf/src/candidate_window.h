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

    bool Create(HINSTANCE instance, HWND parent = nullptr);
    void Destroy();

    void Show(HWND parent = nullptr);
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
    HWND parent_ = nullptr;
    HINSTANCE instance_ = nullptr;
    double dpi_scale_ = 1.0;
    std::wstring class_name_;
    std::wstring composition_;
    std::vector<std::wstring> candidates_;
    int page_ = 1;
    int total_pages_ = 1;
    SelectCallback on_select_;

    // Layout metrics (logical pixels, scaled by dpi_scale_ at runtime)
    int item_height_ = 38;
    int padding_ = 10;
    int code_height_ = 26;
    int page_height_ = 20;
    int item_width_ = 64;

    int Scale(int value) const { return static_cast<int>(value * dpi_scale_); }

    static constexpr wchar_t kClassName[] = L"WubiTSFCandidateWindow";
};

}  // namespace wubi_tsf
