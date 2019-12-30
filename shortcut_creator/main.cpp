#include <algorithm>
#include <atlcomcli.h>
#include <iostream>
#include <netfw.h>
#include <set>
#include <shlobj.h>
#include <string>
#include <windows.h>

bool InitializeCOM()
{
    HRESULT hres = CoInitialize(NULL);
    return SUCCEEDED(hres);
}

bool endsWith(const std::wstring fullString, const std::wstring ending)
{
    return (fullString.length() >= ending.length() &&
        (fullString.compare(fullString.length() - ending.length(), ending.length(), ending) == 0));
}

bool GetTribesAscendLocationsFromFirewallRules(std::set<std::wstring> &executables)
{
    HRESULT hr;

    executables.clear();

    INetFwPolicy2* pNetFwPolicy2;
    hr = CoCreateInstance(__uuidof(NetFwPolicy2), NULL, CLSCTX_INPROC_SERVER, 
                          __uuidof(INetFwPolicy2), (void**)&pNetFwPolicy2);

    if (SUCCEEDED(hr))
    {
        INetFwRules* pFwRules = NULL;
        hr = pNetFwPolicy2->get_Rules(&pFwRules);

        if (SUCCEEDED(hr))
        {
            IUnknown* pEnumerator;
            IEnumVARIANT* pVariant = NULL;

            pFwRules->get__NewEnum(&pEnumerator);

            if (pEnumerator)
            {
                hr = pEnumerator->QueryInterface(__uuidof(IEnumVARIANT), (void**) &pVariant);
            }

            while (SUCCEEDED(hr) && hr != S_FALSE)
            {
                CComVariant var;
                ULONG cFetched = 0;
                INetFwRule* pFwRule = NULL;

                hr = pVariant->Next(1, &var, &cFetched);

                if (S_FALSE != hr)
                {
                    if (SUCCEEDED(hr))
                    {
                        hr = var.ChangeType(VT_DISPATCH);
                    }
                    if (SUCCEEDED(hr))
                    {
                        hr = (V_DISPATCH(&var))->QueryInterface(__uuidof(INetFwRule), reinterpret_cast<void**>(&pFwRule));
                    }

                    if (SUCCEEDED(hr))
                    {
                        BSTR bstrVal;
                        if (SUCCEEDED(pFwRule->get_ApplicationName(&bstrVal)))
                        {
                            if (bstrVal != NULL)
                            {
                                std::wstring exeName = bstrVal;
                                std::transform(exeName.begin(), exeName.end(), exeName.begin(), towlower);
                                if (endsWith(exeName, L"tribesascend.exe"))
                                {
                                    WIN32_FIND_DATAW findData;
                                    HANDLE findHandle = FindFirstFileW(exeName.c_str(), &findData);
                                    if (findHandle != INVALID_HANDLE_VALUE)
                                    {
                                        FindClose(findHandle);
                                        executables.insert(exeName);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    return SUCCEEDED(hr);
}


bool CreateShortcut(const std::wstring target, const std::wstring pathToShortcut)
{
    HRESULT hr;

    IShellLinkW* pShellLink = NULL;
    hr = CoCreateInstance(CLSID_ShellLink, NULL, CLSCTX_INPROC_SERVER,
                          IID_IShellLinkW, (void**)&pShellLink);

    if (SUCCEEDED(hr))
    {
        pShellLink->SetPath(target.c_str());
        pShellLink->SetArguments(L"-hostx=18.197.240.229");

        IPersistFile* pPersistFile;
        hr = pShellLink->QueryInterface(IID_IPersistFile, (void**)&pPersistFile);

        if (SUCCEEDED(hr))
        {
            hr = pPersistFile->Save(pathToShortcut.c_str(), TRUE);
            pPersistFile->Release();
        }
        else
        {
            std::cout << "Failed to get IPersistFile interface" << std::endl;
        }
        pShellLink->Release();
    }
    else
    {
        std::cout << "Failed to get IShellLink interface" << std::endl;
    }

    return SUCCEEDED(hr);
}

bool ConstructPathToShortcut(std::wstring &pathToShortcut)
{
    wchar_t* pPathToDesktop;

    HRESULT hres = SHGetKnownFolderPath(FOLDERID_Desktop, 0, 0, &pPathToDesktop);
    if (SUCCEEDED(hres))
    {
        pathToShortcut = std::wstring(pPathToDesktop) + L"\\TribesAscend community.lnk";
        CoTaskMemFree(pPathToDesktop);
    }

    return SUCCEEDED(hres);
}


int main()
{
    bool ok = true;
    std::wstring pathToShortcut;
    if(InitializeCOM())
    {
        if(ConstructPathToShortcut(pathToShortcut))
        {
            std::set<std::wstring> executables;
            if (GetTribesAscendLocationsFromFirewallRules(executables))
            {
                if (!executables.empty())
                {
                    std::wstring pathToExe = *executables.begin();
                    if (executables.size() > 1)
                    {
                        std::wcout << "Warning: more than one TribesAscend.exe found. Creating shortcut for " << pathToExe << std::endl;
                    }
                    if (CreateShortcut(pathToExe, pathToShortcut))
                    {
                        std::cout << "Shortcut created successfully." << std::endl;
                    }
                    else
                    {
                        std::cerr << "Failed to create shortcut" << std::endl;
                        ok = false;
                    }
                }
                else
                {
                    std::cerr << "Unable to find any TribesAscend.exe. No shortcut created." << std::endl;
                    ok = false;
                }
            }
            else
            {
                std::cerr << "Failed to get executable names from firewall rules" << std::endl;
                ok = false;
            }
        }
        else
        {
            std::cerr << "Failed to construct path to shortcut" << std::endl;
            ok = false;
        }
        CoUninitialize();
    }
    else
    {
        std::cerr << "Failed to initialize COM" << std::endl;
        ok = false;
    }
    return ok ? 0 : -1;
}
