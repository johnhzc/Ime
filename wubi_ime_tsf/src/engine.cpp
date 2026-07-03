#include "engine.h"

#include <windows.h>

#include <algorithm>
#include <fstream>
#include <map>
#include <set>
#include <sstream>
#include <string>

#include "nlohmann/json.hpp"

namespace wubi_tsf {

namespace {

// Convert UTF-8 string to wide string
std::wstring Utf8ToWide(const std::string& utf8) {
    if (utf8.empty()) return {};
    int size = MultiByteToWideChar(CP_UTF8, 0, utf8.c_str(), -1, nullptr, 0);
    if (size <= 0) return {};
    std::wstring result(size - 1, L'\0');
    MultiByteToWideChar(CP_UTF8, 0, utf8.c_str(), -1, result.data(), size);
    return result;
}

// Convert wide string to UTF-8
std::string WideToUtf8(const std::wstring& wide) {
    if (wide.empty()) return {};
    int size = WideCharToMultiByte(CP_UTF8, 0, wide.c_str(), -1, nullptr, 0, nullptr, nullptr);
    if (size <= 0) return {};
    std::string result(size - 1, '\0');
    WideCharToMultiByte(CP_UTF8, 0, wide.c_str(), -1, result.data(), size, nullptr, nullptr);
    return result;
}

class WubiEngine : public ImeEngine {
public:
    bool LoadFromFile(const std::wstring& path) override {
        char_to_codes_.clear();
        code_to_chars_.clear();

        std::ifstream file(WideToUtf8(path));
        if (!file.is_open()) {
            return false;
        }

        try {
            nlohmann::json j;
            file >> j;

            for (auto it = j.begin(); it != j.end(); ++it) {
                std::wstring ch = Utf8ToWide(it.key());
                if (ch.empty()) continue;

                std::vector<std::wstring> codes;
                auto& value = it.value();
                if (value.is_string()) {
                    codes.push_back(Utf8ToWide(value.get<std::string>()));
                } else if (value.is_array()) {
                    for (const auto& code : value) {
                        if (code.is_string()) {
                            codes.push_back(Utf8ToWide(code.get<std::string>()));
                        }
                    }
                }

                char_to_codes_[ch] = codes;
                for (const auto& code : codes) {
                    if (std::find(code_to_chars_[code].begin(), code_to_chars_[code].end(), ch) ==
                        code_to_chars_[code].end()) {
                        code_to_chars_[code].push_back(ch);
                    }
                }
            }
        } catch (...) {
            return false;
        }

        return !code_to_chars_.empty();
    }

    ProcessKeyResult ProcessKey(const std::string& key) override {
        ProcessKeyResult result;

        if (key.length() == 1 && key[0] >= 'a' && key[0] <= 'z') {
            if (code_.length() < 4) {
                code_ += key[0];
                UpdateCandidates();
                result.consumed = true;
                result.need_update_ui = true;

                // Auto-commit on exact unique 4-code match
                if (code_.length() == 4) {
                    auto exact = GetExactCandidates();
                    if (exact.size() == 1) {
                        result.committed = true;
                        result.committed_text = exact[0];
                        Reset();
                        result.need_update_ui = false;
                    }
                }
            }
            return result;
        }

        if (key.length() == 1 && key[0] >= '1' && key[0] <= '9') {
            int index = key[0] - '1';
            auto page = GetPageCandidates();
            if (index >= 0 && index < static_cast<int>(page.size())) {
                result.committed = true;
                result.committed_text = page[index];
                result.consumed = true;
                Reset();
            }
            return result;
        }

        if (key == "space") {
            auto page = GetPageCandidates();
            if (!page.empty()) {
                result.committed = true;
                result.committed_text = page[0];
                result.consumed = true;
                Reset();
            }
            return result;
        }

        if (key == "backspace") {
            if (!code_.empty()) {
                code_.pop_back();
                UpdateCandidates();
                result.consumed = true;
                result.need_update_ui = true;
            }
            return result;
        }

        if (key == "esc") {
            if (!code_.empty()) {
                Reset();
                result.consumed = true;
                result.need_update_ui = true;
            }
            return result;
        }

        if (key == "pageup") {
            if (page_ > 0) {
                --page_;
                result.consumed = true;
                result.need_update_ui = true;
            }
            return result;
        }

        if (key == "pagedown") {
            int total = (static_cast<int>(candidates_.size()) + kPageSize - 1) / kPageSize;
            if (page_ < total - 1) {
                ++page_;
                result.consumed = true;
                result.need_update_ui = true;
            }
            return result;
        }

        return result;
    }

    std::wstring GetCompositionString() const override {
        return Utf8ToWide(code_);
    }

    std::vector<std::wstring> GetCandidates() const override {
        return GetPageCandidates();
    }

    std::pair<int, int> GetPageInfo() const override {
        int total = (static_cast<int>(candidates_.size()) + kPageSize - 1) / kPageSize;
        if (total == 0) total = 1;
        return {page_, total};
    }

    void Reset() override {
        code_.clear();
        candidates_.clear();
        page_ = 0;
    }

private:
    static constexpr int kPageSize = 9;

    std::vector<std::wstring> GetExactCandidates() const {
        auto it = code_to_chars_.find(Utf8ToWide(code_));
        if (it != code_to_chars_.end()) {
            return it->second;
        }
        return {};
    }

    std::vector<std::wstring> GetPrefixCandidates() const {
        std::vector<std::wstring> result;
        std::set<std::wstring> seen;
        std::wstring prefix = Utf8ToWide(code_);
        for (const auto& pair : code_to_chars_) {
            if (pair.first.find(prefix) == 0) {
                for (const auto& ch : pair.second) {
                    if (seen.insert(ch).second) {
                        result.push_back(ch);
                    }
                }
            }
        }
        return result;
    }

    std::vector<std::wstring> GetPageCandidates() const {
        int start = page_ * kPageSize;
        if (start >= static_cast<int>(candidates_.size())) {
            return {};
        }
        int end = std::min(start + kPageSize, static_cast<int>(candidates_.size()));
        return std::vector<std::wstring>(candidates_.begin() + start, candidates_.begin() + end);
    }

    void UpdateCandidates() {
        candidates_.clear();
        page_ = 0;
        std::set<std::wstring> seen;
        for (const auto& ch : GetExactCandidates()) {
            if (seen.insert(ch).second) {
                candidates_.push_back(ch);
            }
        }
        for (const auto& ch : GetPrefixCandidates()) {
            if (seen.insert(ch).second) {
                candidates_.push_back(ch);
            }
        }
    }

    std::map<std::wstring, std::vector<std::wstring>> char_to_codes_;
    std::map<std::wstring, std::vector<std::wstring>> code_to_chars_;
    std::string code_;
    std::vector<std::wstring> candidates_;
    int page_ = 0;
};

}  // namespace

std::unique_ptr<ImeEngine> CreateDefaultEngine() {
    return std::make_unique<WubiEngine>();
}

}  // namespace wubi_tsf
