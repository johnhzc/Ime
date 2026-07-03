#include "factory.h"

#include <new>

#include "text_service.h"

namespace wubi_tsf {

ClassFactory::ClassFactory() {
    AddRef();
}

IFACEMETHODIMP ClassFactory::QueryInterface(REFIID riid, void** ppv) {
    if (!ppv) return E_INVALIDARG;
    *ppv = nullptr;

    if (IsEqualIID(riid, IID_IUnknown) || IsEqualIID(riid, IID_IClassFactory)) {
        *ppv = static_cast<IClassFactory*>(this);
    } else {
        return E_NOINTERFACE;
    }

    AddRef();
    return S_OK;
}

IFACEMETHODIMP_(ULONG) ClassFactory::AddRef() {
    return InterlockedIncrement(&ref_count_);
}

IFACEMETHODIMP_(ULONG) ClassFactory::Release() {
    LONG count = InterlockedDecrement(&ref_count_);
    if (count == 0) {
        delete this;
    }
    return count;
}

IFACEMETHODIMP ClassFactory::CreateInstance(IUnknown* outer, REFIID riid, void** ppv) {
    if (!ppv) return E_INVALIDARG;
    *ppv = nullptr;

    if (outer) {
        return CLASS_E_NOAGGREGATION;
    }

    TextService* service = new (std::nothrow) TextService();
    if (!service) {
        return E_OUTOFMEMORY;
    }

    HRESULT hr = service->QueryInterface(riid, ppv);
    service->Release();
    return hr;
}

IFACEMETHODIMP ClassFactory::LockServer(BOOL lock) {
    if (lock) {
        InterlockedIncrement(&ref_count_);
    } else {
        InterlockedDecrement(&ref_count_);
    }
    return S_OK;
}

}  // namespace wubi_tsf
