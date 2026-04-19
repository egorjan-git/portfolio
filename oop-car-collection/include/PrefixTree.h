#ifndef PREFIXTREE_H
#define PREFIXTREE_H

#include <array>
#include <memory>
#include <string>
#include <fstream>
#include <stdexcept>
#include <vector>
#include <functional>
#include <cctype>

template<typename T>
class PrefixTree {
private:
    struct Node {
        std::array<std::unique_ptr<Node>, 26> next{};
        std::unique_ptr<T> value = nullptr;
        bool terminal = false;

        Node() = default;

        Node(const Node& other) {
            terminal = other.terminal;
            if (other.value)
                value = std::make_unique<T>(*other.value);
            for (std::size_t i = 0; i < 26; ++i) {
                if (other.next[i])
                    next[i] = std::make_unique<Node>(*other.next[i]);
            }
        }
    };

    std::unique_ptr<Node> root;
    std::size_t count_values = 0;

    static std::string normalize(const std::string& s) {
        if (s.empty())
            throw std::invalid_argument("empty key");
        std::string out;
        out.reserve(s.size());
        for (char c : s) {
            unsigned char uc = static_cast<unsigned char>(c);
            char lc = static_cast<char>(std::tolower(uc));
            if (lc < 'a' || lc > 'z')
                throw std::invalid_argument("invalid key (only a-z)");
            out.push_back(lc);
        }
        return out;
    }

    Node* findNode(const std::string& key) const {
        Node* cur = root.get();
        for (char c : key) {
            int idx = c - 'a';
            if (!cur->next[idx])
                return nullptr;
            cur = cur->next[idx].get();
        }
        return cur;
    }

    void clearNode(std::unique_ptr<Node>& node) {
        if (!node) return;
        for (auto& p : node->next)
            clearNode(p);
        node.reset();
    }

    static bool equalNodes(const std::unique_ptr<Node>& a,
                           const std::unique_ptr<Node>& b) {
        if (!a && !b) return true;
        if (!a || !b) return false;
        if (a->terminal != b->terminal) return false;
        if (bool(a->value) != bool(b->value)) return false;
        if (a->value && b->value && !(*a->value == *b->value))
            return false;
        for (std::size_t i = 0; i < 26; ++i) {
            if (!equalNodes(a->next[i], b->next[i]))
                return false;
        }
        return true;
    }

public:
    PrefixTree() {
        root = std::make_unique<Node>();
        count_values = 0;
    }

    PrefixTree(const PrefixTree& other) {
        root = std::make_unique<Node>(*other.root);
        count_values = other.count_values;
    }

    PrefixTree& operator=(const PrefixTree& other) {
        if (this == &other)
            return *this;
        root = std::make_unique<Node>(*other.root);
        count_values = other.count_values;
        return *this;
    }

    ~PrefixTree() {
        clear();
    }

    void add(const std::string& key_raw, const T& value) {
        std::string key = normalize(key_raw);
        Node* cur = root.get();
        for (char c : key) {
            int idx = c - 'a';
            if (!cur->next[idx])
                cur->next[idx] = std::make_unique<Node>();
            cur = cur->next[idx].get();
        }
        if (!cur->terminal) {
            cur->terminal = true;
            ++count_values;
        }
        cur->value = std::make_unique<T>(value);
    }

    PrefixTree& operator<<(const std::pair<std::string, T>& kv) {
        add(kv.first, kv.second);
        return *this;
    }

    bool remove(const std::string& key_raw) {
        std::string key = normalize(key_raw);
        std::vector<Node*> path;
        path.reserve(key.size() + 1);
        Node* cur = root.get();
        path.push_back(cur);
        for (char c : key) {
            int idx = c - 'a';
            if (!cur->next[idx])
                return false;
            cur = cur->next[idx].get();
            path.push_back(cur);
        }
        if (!cur->terminal)
            return false;
        cur->terminal = false;
        cur->value.reset();
        --count_values;
        for (int i = static_cast<int>(key.size()); i > 0; --i) {
            Node* node = path[i];
            bool has_children = false;
            for (auto& ch : node->next) {
                if (ch) { has_children = true; break; }
            }
            if (node->terminal || node->value || has_children)
                break;
            Node* parent = path[i - 1];
            int idx = key[static_cast<std::size_t>(i - 1)] - 'a';
            parent->next[idx].reset();
        }
        return true;
    }

    void clear() {
        clearNode(root);
        root = std::make_unique<Node>();
        count_values = 0;
    }

    std::size_t size() const {
        return count_values;
    }

    bool contains(const std::string& key_raw) const {
        std::string key = normalize(key_raw);
        Node* n = findNode(key);
        return (n && n->terminal);
    }

    T& operator[](const std::string& key_raw) {
        std::string key = normalize(key_raw);
        Node* cur = root.get();
        for (char c : key) {
            int idx = c - 'a';
            if (!cur->next[idx])
                cur->next[idx] = std::make_unique<Node>();
            cur = cur->next[idx].get();
        }
        if (!cur->terminal) {
            cur->terminal = true;
            cur->value = std::make_unique<T>();
            ++count_values;
        }
        return *cur->value;
    }

    bool operator==(const PrefixTree& other) const {
        return equalNodes(root, other.root);
    }

    PrefixTree operator&&(const PrefixTree& other) const {
        PrefixTree out;
        std::function<void(Node*, Node*, const std::string&)> dfs =
            [&](Node* a, Node* b, const std::string& cur_key) {
                if (!a || !b) return;
                if (a->terminal && b->terminal && a->value && b->value) {
                    out.add(cur_key, *a->value);
                }
                for (int i = 0; i < 26; ++i) {
                    if (a->next[i] && b->next[i]) {
                        dfs(a->next[i].get(), b->next[i].get(),
                            cur_key + static_cast<char>('a' + i));
                    }
                }
            };
        dfs(root.get(), other.root.get(), "");
        return out;
    }

    void save(const std::string& path) const {
        std::ofstream f(path);
        if (!f)
            throw std::runtime_error("cannot open file for writing");
        std::function<void(Node*, const std::string&)> dfs =
            [&](Node* n, const std::string& key) {
                if (!n) return;
                if (n->terminal && n->value) {
                    f << key << ' ' << *n->value << '\n';
                }
                for (int i = 0; i < 26; ++i) {
                    if (n->next[i]) {
                        dfs(n->next[i].get(),
                            key + static_cast<char>('a' + i));
                    }
                }
            };
        dfs(root.get(), "");
    }

    void load(const std::string& path) {
        clear();
        std::ifstream f(path);
        if (!f)
            throw std::runtime_error("cannot open file for reading");
        std::string key;
        T temp;
        while (f >> key >> temp) {
            add(key, temp);
        }
    }

    void forEach(const std::function<void(const std::string&, const T&)>& fn) const {
        std::function<void(Node*, const std::string&)> dfs =
            [&](Node* n, const std::string& key) {
                if (!n) return;
                if (n->terminal && n->value) {
                    fn(key, *n->value);
                }
                for (int i = 0; i < 26; ++i) {
                    if (n->next[i]) {
                        dfs(n->next[i].get(),
                            key + static_cast<char>('a' + i));
                    }
                }
            };
        dfs(root.get(), "");
    }
};

#endif