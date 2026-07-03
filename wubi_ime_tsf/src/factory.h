#pragma once

#include <windows.h>
#include <unknwn.h>

namespace wubi_tsf {

// COM class factory for the TSF text service.
class ClassFactory : public IClassFactory {
public:
    // IUnknown
    IFACEMETHODIMP QueryInterface(REFIID riid, void** ppv) override;
    IFACEMETHODIMP_(ULONG) AddRef() override;
    IFACEMETHODIMP_(ULONG) Release() override;

    // IClassFactory
    IFACEMETHODIMP CreateInstance(IUnknown* outer, REFIID riid, void** ppv) override;
    IFACEMETHODIMP LockServer(BOOL lock) override;

    ClassFactory();

private:
    LONG ref_count_ = 1;
};

}  // namespace wubi_tsf
