#pragma once

#include <memory>
#include <string>
#include <vector>

namespace wubi_tsf {

// Result of processing a single key
struct ProcessKeyResult {
    bool consumed = false;       // true if the IME consumed the key
    bool need_update_ui = false; // true if candidate window should refresh
    bool committed = false;      // true if a character was committed
    std::wstring committed_text; // text to commit if committed
};

// Abstract encoding engine interface
class ImeEngine {
public:
    virtual ~ImeEngine() = default;

    // Load encoding table from a file path
    virtual bool LoadFromFile(const std::wstring& path) = 0;

    // Process a key name (e.g. "a", "space", "1", "backspace", "shift")
    virtual ProcessKeyResult ProcessKey(const std::string& key) = 0;

    // Get current composition string (the encoding)
    virtual std::wstring GetCompositionString() const = 0;

    // Get current candidates (first page)
    virtual std::vector<std::wstring> GetCandidates() const = 0;

    // Get current page info (page_index, total_pages)
    virtual std::pair<int, int> GetPageInfo() const = 0;

    // Reset the engine state
    virtual void Reset() = 0;
};

// Factory to create the default engine (Wubi)
std::unique_ptr<ImeEngine> CreateDefaultEngine();

}  // namespace wubi_tsf
