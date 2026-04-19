#include <cassert>
#include <iostream>
#include <sstream>
#include <string>

#include "Material.h"
#include "Box3D.h"
#include "KitchenCabinet.h"
#include "Appliance.h"
#include "KitchenPlan.h"
#include "PrefixTree.h"

#ifdef _WIN32
#include <windows.h>
#endif

static Material parseMaterial(const std::string &s) {
    if (s == "wood")    return Material::Wood;
    if (s == "metal")   return Material::Metal;
    if (s == "glass")   return Material::Glass;
    if (s == "mdf")     return Material::MDF;
    if (s == "plastic") return Material::Plastic;
    throw std::invalid_argument("unknown material");
}

static void printKitchenShort(const KitchenPlan &kp) {
    const Box3D &r = kp.room();
    std::size_t cabCount = 0;
    std::size_t appCount = 0;

    for (const auto &ptr : kp.entities()) {
        if (dynamic_cast<const KitchenCabinet*>(ptr.get())) ++cabCount;
        else if (dynamic_cast<const Appliance*>(ptr.get())) ++appCount;
    }

    std::cout << "room: w=" << r.w() << " d=" << r.d() << " h=" << r.h()
              << " | cabinets=" << cabCount
              << " appliances=" << appCount << "\n";
}

static void printCliHelp() {
    std::cout
        << "Kitchen store (PrefixTree<KitchenPlan>) commands:\n"
        << "  help\n"
        << "  new_kitchen <name> <w> <d> <h>          - create/overwrite kitchen\n"
        << "  add_cab    <name> <mat> x y z w d h     - add cabinet to kitchen\n"
        << "       mat = wood|metal|glass|mdf|plastic\n"
        << "  add_app    <name> <appName> x y z w d h - add appliance to kitchen\n"
        << "  info       <name>                       - short info about kitchen\n"
        << "  validate   <name> [minDist eps]         - validate kitchen\n"
        << "  list                                     - list all kitchens (keys)\n"
        << "  save_store <filename>                   - save store to file\n"
        << "  load_store <filename>                   - load store from file\n"
        << "  quit                                     - exit\n";
}

static void runCli() {
    PrefixTree<KitchenPlan> store;

    std::cout << "Kitchen store CLI mode\n";
    printCliHelp();

    std::string line;
    while (true) {
        std::cout << "> ";
        if (!std::getline(std::cin, line))
            break;

        if (line.empty())
            continue;

        try {
            std::istringstream iss(line);
            std::string cmd;
            iss >> cmd;
            if (!iss) continue;

            if (cmd == "help") {
                printCliHelp();

            } else if (cmd == "new_kitchen") {
                std::string name;
                double w,d,h;
                iss >> name >> w >> d >> h;
                if (!iss) { std::cout << "bad args\n"; continue; }

                KitchenPlan kp(w,d,h);
                store.add(name, kp);
                std::cout << "kitchen '" << name << "' created\n";

            } else if (cmd == "add_cab") {
                std::string name, ms;
                double x,y,z,w,d,h;
                iss >> name >> ms >> x >> y >> z >> w >> d >> h;
                if (!iss) { std::cout << "bad args\n"; continue; }

                if (!store.contains(name)) {
                    std::cout << "no such kitchen\n";
                    continue;
                }
                KitchenPlan &kp = store[name];
                Material m = parseMaterial(ms);
                kp.addCabinet(KitchenCabinet(m, Box3D(x,y,z,w,d,h)));
                std::cout << "cabinet added to '" << name << "'\n";

            } else if (cmd == "add_app") {
                std::string name, appName;
                double x,y,z,w,d,h;
                iss >> name >> appName >> x >> y >> z >> w >> d >> h;
                if (!iss) { std::cout << "bad args\n"; continue; }

                if (!store.contains(name)) {
                    std::cout << "no such kitchen\n";
                    continue;
                }
                KitchenPlan &kp = store[name];
                kp.addAppliance(Appliance(appName, Box3D(x,y,z,w,d,h)));
                std::cout << "appliance added to '" << name << "'\n";

            } else if (cmd == "info") {
                std::string name;
                iss >> name;
                if (!iss) { std::cout << "bad args\n"; continue; }

                if (!store.contains(name)) {
                    std::cout << "no such kitchen\n";
                    continue;
                }
                KitchenPlan &kp = store[name];
                std::cout << "kitchen '" << name << "': ";
                printKitchenShort(kp);

            } else if (cmd == "validate") {
                std::string name;
                double minDist = 2.0, eps = 1e-6;
                iss >> name;
                if (!iss) { std::cout << "bad args\n"; continue; }
                if (iss.good()) iss >> minDist >> eps;

                if (!store.contains(name)) {
                    std::cout << "no such kitchen\n";
                    continue;
                }
                KitchenPlan &kp = store[name];
                auto res = kp.validate(minDist, eps);
                std::cout << "valid=" << static_cast<int>(res.first)
                          << " reason=" << res.second << "\n";

            } else if (cmd == "list") {
                store.forEach([](const std::string &key, const KitchenPlan &kp){
                    std::cout << key << " : ";
                    printKitchenShort(kp);
                });

            } else if (cmd == "save_store") {
                std::string file;
                iss >> file;
                if (!iss) { std::cout << "bad args\n"; continue; }
                try {
                    store.save(file);
                    std::cout << "store saved\n";
                } catch (const std::exception &e) {
                    std::cout << "error: " << e.what() << "\n";
                }

            } else if (cmd == "load_store") {
                std::string file;
                iss >> file;
                if (!iss) { std::cout << "bad args\n"; continue; }
                try {
                    store.load(file);
                    std::cout << "store loaded\n";
                } catch (const std::exception &e) {
                    std::cout << "error: " << e.what() << "\n";
                }

            } else if (cmd == "quit") {
                break;

            } else {
                std::cout << "unknown command\n";
            }
        } catch (const std::exception &e) {
            std::cout << "error: " << e.what() << "\n";
        }
    }
}

#ifdef _WIN32

static PrefixTree<KitchenPlan> g_store;

enum {
    IDC_EDIT_KEY   = 1001,
    IDC_EDIT_W     = 1002,
    IDC_EDIT_D     = 1003,
    IDC_EDIT_H     = 1004,
    IDC_EDIT_FILE  = 1005,
    IDC_BTN_ADD    = 1101,
    IDC_BTN_LIST   = 1102,
    IDC_BTN_SAVE   = 1103,
    IDC_BTN_LOAD   = 1104,
    IDC_BTN_VALIDATE = 1105,
    IDC_BTN_EXIT   = 1106,
    IDC_EDIT_LOG   = 1201
};

static std::string getEditTextA(HWND hEdit) {
    int len = GetWindowTextLengthA(hEdit);
    if (len <= 0) return {};
    std::string s(len, '\0');
    GetWindowTextA(hEdit, s.data(), len + 1);
    if (!s.empty() && s.back() == '\0')
        s.pop_back();
    return s;
}

static void setEditTextA(HWND hEdit, const std::string &text) {
    SetWindowTextA(hEdit, text.c_str());
}

static void appendLog(HWND hLog, const std::string &line) {
    std::string cur = getEditTextA(hLog);
    if (!cur.empty() && cur.back() != '\n')
        cur.push_back('\n');
    cur += line;
    setEditTextA(hLog, cur);
}

static LRESULT CALLBACK MainWndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    static HWND hEditKey, hEditW, hEditD, hEditH, hEditFile, hEditLog;

    switch (msg) {
    case WM_CREATE: {
        hEditKey = CreateWindowExA(0, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER,
                                   10, 10, 120, 20, hwnd, (HMENU)IDC_EDIT_KEY, nullptr, nullptr);
        CreateWindowExA(0, "STATIC", "key(a-z):", WS_CHILD | WS_VISIBLE,
                        140, 10, 80, 20, hwnd, nullptr, nullptr, nullptr);

        hEditW = CreateWindowExA(0, "EDIT", "6", WS_CHILD | WS_VISIBLE | WS_BORDER,
                                 10, 40, 40, 20, hwnd, (HMENU)IDC_EDIT_W, nullptr, nullptr);
        hEditD = CreateWindowExA(0, "EDIT", "2", WS_CHILD | WS_VISIBLE | WS_BORDER,
                                 60, 40, 40, 20, hwnd, (HMENU)IDC_EDIT_D, nullptr, nullptr);
        hEditH = CreateWindowExA(0, "EDIT", "3", WS_CHILD | WS_VISIBLE | WS_BORDER,
                                 110, 40, 40, 20, hwnd, (HMENU)IDC_EDIT_H, nullptr, nullptr);
        CreateWindowExA(0, "STATIC", "W D H:", WS_CHILD | WS_VISIBLE,
                        160, 40, 80, 20, hwnd, nullptr, nullptr, nullptr);

        hEditFile = CreateWindowExA(0, "EDIT", "store.txt", WS_CHILD | WS_VISIBLE | WS_BORDER,
                                    10, 70, 140, 20, hwnd, (HMENU)IDC_EDIT_FILE, nullptr, nullptr);
        CreateWindowExA(0, "STATIC", "file:", WS_CHILD | WS_VISIBLE,
                        160, 70, 40, 20, hwnd, nullptr, nullptr, nullptr);

        CreateWindowExA(0, "BUTTON", "Add/Upd kitchen", WS_CHILD | WS_VISIBLE,
                        10, 100, 130, 25, hwnd, (HMENU)IDC_BTN_ADD, nullptr, nullptr);
        CreateWindowExA(0, "BUTTON", "List", WS_CHILD | WS_VISIBLE,
                        150, 100, 60, 25, hwnd, (HMENU)IDC_BTN_LIST, nullptr, nullptr);
        CreateWindowExA(0, "BUTTON", "Validate", WS_CHILD | WS_VISIBLE,
                        220, 100, 80, 25, hwnd, (HMENU)IDC_BTN_VALIDATE, nullptr, nullptr);

        CreateWindowExA(0, "BUTTON", "Save store", WS_CHILD | WS_VISIBLE,
                        10, 130, 100, 25, hwnd, (HMENU)IDC_BTN_SAVE, nullptr, nullptr);
        CreateWindowExA(0, "BUTTON", "Load store", WS_CHILD | WS_VISIBLE,
                        120, 130, 100, 25, hwnd, (HMENU)IDC_BTN_LOAD, nullptr, nullptr);
        CreateWindowExA(0, "BUTTON", "Exit", WS_CHILD | WS_VISIBLE,
                        230, 130, 60, 25, hwnd, (HMENU)IDC_BTN_EXIT, nullptr, nullptr);

        hEditLog = CreateWindowExA(WS_EX_CLIENTEDGE, "EDIT", "",
                                   WS_CHILD | WS_VISIBLE | WS_VSCROLL |
                                   ES_MULTILINE | ES_AUTOVSCROLL | ES_READONLY,
                                   10, 170, 280, 150, hwnd, (HMENU)IDC_EDIT_LOG, nullptr, nullptr);
        return 0;
    }

    case WM_COMMAND: {
        switch (LOWORD(wParam)) {
        case IDC_BTN_ADD: {
            std::string key = getEditTextA(hEditKey);
            std::string sW  = getEditTextA(hEditW);
            std::string sD  = getEditTextA(hEditD);
            std::string sH  = getEditTextA(hEditH);
            try {
                double W = std::stod(sW);
                double D = std::stod(sD);
                double H = std::stod(sH);
                KitchenPlan kp(W,D,H);
                g_store.add(key, kp);
                appendLog(hEditLog, "added/updated kitchen '" + key + "'");
            } catch (const std::exception &e) {
                appendLog(hEditLog, std::string("error: ") + e.what());
            }
            return 0;
        }
        case IDC_BTN_LIST: {
            setEditTextA(hEditLog, "");
            g_store.forEach([&](const std::string &k, const KitchenPlan &kp){
                std::ostringstream oss;
                const Box3D &r = kp.room();
                oss << k << " : w=" << r.w() << " d=" << r.d() << " h=" << r.h();
                appendLog(hEditLog, oss.str());
            });
            return 0;
        }
        case IDC_BTN_VALIDATE: {
            std::string key = getEditTextA(hEditKey);
            try {
                if (!g_store.contains(key)) {
                    appendLog(hEditLog, "no such kitchen '" + key + "'");
                    return 0;
                }
                KitchenPlan &kp = g_store[key];
                auto res = kp.validate(2.0, 1e-6);
                std::string msg = "kitchen '" + key + "': valid=" +
                                  std::to_string((int)res.first) +
                                  " reason=" + res.second;
                appendLog(hEditLog, msg);
            } catch (const std::exception &e) {
                appendLog(hEditLog, std::string("error: ") + e.what());
            }
            return 0;
        }
        case IDC_BTN_SAVE: {
            std::string file = getEditTextA(hEditFile);
            try {
                g_store.save(file);
                appendLog(hEditLog, "store saved to " + file);
            } catch (const std::exception &e) {
                appendLog(hEditLog, std::string("error: ") + e.what());
            }
            return 0;
        }
        case IDC_BTN_LOAD: {
            std::string file = getEditTextA(hEditFile);
            try {
                g_store.load(file);
                appendLog(hEditLog, "store loaded from " + file);
            } catch (const std::exception &e) {
                appendLog(hEditLog, std::string("error: ") + e.what());
            }
            return 0;
        }
        case IDC_BTN_EXIT: {
            PostQuitMessage(0);
            return 0;
        }
        }
        break;
    }

    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}

static int runGui(HINSTANCE hInstance) {
    const char CLASS_NAME[] = "KitchenStoreWindowClass";

    WNDCLASSEXA wc = {};
    wc.cbSize        = sizeof(WNDCLASSEXA);
    wc.lpfnWndProc   = MainWndProc;
    wc.hInstance     = hInstance;
    wc.hCursor       = LoadCursor(nullptr, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW+1);
    wc.lpszClassName = CLASS_NAME;

    if (!RegisterClassExA(&wc)) {
        MessageBoxA(nullptr, "Failed to register window class", "Error", MB_ICONERROR);
        return 1;
    }

    HWND hwnd = CreateWindowExA(
        0, CLASS_NAME, "Kitchen Store GUI (Trie)",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, 320, 380,
        nullptr, nullptr, hInstance, nullptr
    );

    if (!hwnd) {
        MessageBoxA(nullptr, "Failed to create window", "Error", MB_ICONERROR);
        return 1;
    }

    ShowWindow(hwnd, SW_SHOW);
    UpdateWindow(hwnd);

    MSG msg;
    while (GetMessageA(&msg, nullptr, 0, 0) > 0) {
        TranslateMessage(&msg);
        DispatchMessageA(&msg);
    }
    return (int)msg.wParam;
}

#endif

int main(int argc, char* argv[]) {
    if (argc > 1 && std::string(argv[1]) == "gui") {
#ifdef _WIN32
        return runGui(GetModuleHandle(nullptr));
#else
        std::cout << "GUI mode is only available on Windows.\n";
        return 1;
#endif
    }
    runCli();
    return 0;
}