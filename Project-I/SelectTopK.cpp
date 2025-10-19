// #define _USE_MATH_DEFINES
// #include <bits/stdc++.h>

// #define PI M_PI
// #define E M_E

// using namespace std;

// mt19937 rnd(random_device{}());
// int rndd(int l, int r){return rnd() % (r - l + 1) + l;}

// typedef unsigned int uint;
// typedef unsigned long long unll;
// typedef long long ll;

// template < typename T = int >
// inline T read(void);

// const char *INPUT_PATH = "/root/Database-Systems/Project-I/data/clickstream/clickstream-enwiki-2025-09.tsv";

// int main(){
//     int K(20);
//     const char *in_path = INPUT_PATH;

//     ifstream fin(in_path);
//     if(!fin)exit(1);

//     auto st = chrono::steady_clock::now();

//     unordered_map < string, ll > agg;
//     agg.reserve(1u << 22);
//     // agg.max_load_factor(0.7f);

//     string line;
//     int rows = 0;
//     while(getline(fin, line)){
//         if(line.empty()){++rows; continue;}
//         auto p1 = line.find('\t');
//         if(p1 == string::npos){++rows; continue;}
//         auto p2 = line.find('\t', p1 + 1);
//         if(p2 == string::npos){++rows; continue;}
//         auto p3 = line.find('\t', p2 + 1);
//         if(p3 == string::npos){++rows; continue; }

//         auto curr_beg = p1 + 1;
//         auto curr_len = p2 - curr_beg;
//         auto n_beg = p3 + 1;
//         if(n_beg >= line.size()){++rows; continue;}

//         string curr = line.substr(curr_beg, curr_len);
//         const char* n_str = line.c_str() + n_beg;
//         ll v = atoll(n_str);
//         agg[curr] += v;
//         ++rows;
//     }

//     vector < pair < ll, string > > vec;
//     for(auto &kv : agg)vec.push_back({kv.second, kv.first});

//     if((int)vec.size() > K){
//         nth_element(vec.begin(), vec.begin() + K, vec.end(), [](const auto &a, const auto &b){return a.first > b.first;});
//         sort(vec.begin(), vec.begin() + K, [](const auto &a, const auto &b){return a.first > b.first;});
//         vec.resize(K);
//     }else sort(vec.begin(), vec.end(), [](const auto &a, const auto &b){ return a.first > b.first; });

//     auto ed = chrono::steady_clock::now();
//     double ms = chrono::duration < double, milli >(ed - st).count();

//     int rnk(0);
//     cout << ms << " ms\n";

//     return 0;
// }



// template < typename T >
// inline T read(void){
//     T ret(0);
//     short flag(1);
//     char c = getchar();
//     while(c != '-' && !isdigit(c))c = getchar();
//     if(c == '-')flag = -1, c = getchar();
//     while(isdigit(c)){
//         ret *= 10;
//         ret += int(c - '0');
//         c = getchar();
//     }
//     ret *= flag;
//     return ret;
// }



//
// Memory Limit Exceeded -> killed
//

#define _USE_MATH_DEFINES
#include <bits/stdc++.h>
#include <unistd.h>  // for getpid()


#define PI M_PI
#define E  M_E

using namespace std;

mt19937 rnd(random_device{}());
int rndd(int l, int r){ return rnd() % (r - l + 1) + l; }

typedef unsigned int        uint;
typedef unsigned long long  unll;
typedef long long           ll;

template < typename T = int >
inline T read(void);

// ====== 可调参数（根据你的机器限制作小幅调整） ======
const size_t MAX_DISTINCT_IN_MEM = 600000;   // 每轮允许在内存中的不同 curr 键数量上限
const int    K_TOP                = 20;       // Top-K
const char  *INPUT_PATH           = "/root/Database-Systems/Project-I/data/clickstream/clickstream-enwiki-2025-09.tsv";
const char  *TMP_DIR              = "/tmp";   // 临时文件目录（需可写、空间足）

// 生成唯一临时文件名
static string make_tmp_path(size_t idx){
    char buf[512];
    snprintf(buf, sizeof(buf), "%s/topk_flush_%d_%zu.tmp", TMP_DIR, (int)getpid(), idx);
    return string(buf);
}

// 将当前内存哈希表聚合结果写入一个已排序（按 key 升序）的临时文件
static void flush_chunk_to_file(unordered_map<string, ll> &agg, const string &path){
    vector<pair<string, ll>> vec;
    vec.reserve(agg.size());
    for(auto &kv : agg) vec.emplace_back(kv.first, kv.second);
    sort(vec.begin(), vec.end(), [](const auto &a, const auto &b){ return a.first < b.first; });

    ofstream fout(path, ios::binary);
    if(!fout){ fprintf(stderr, "Cannot write tmp %s\n", path.c_str()); exit(2); }

    // 每行：key \t value \n
    for(auto &kv : vec){
        fout << kv.first << '\t' << kv.second << '\n';
    }
    fout.close();
    // 清空并缩容，降低峰值
    unordered_map<string, ll>().swap(agg);
}

// 从排序好的临时文件读一条记录（key\tvalue），读到返回 true，否则 false
static bool read_record(ifstream &fin, string &key, ll &val){
    string line;
    if(!std::getline(fin, line)) return false;
    size_t tab = line.find('\t');
    if(tab == string::npos){
        key.clear(); val = 0;
        return true; // 容错：跳过异常行
    }
    key = line.substr(0, tab);
    const char *p = line.c_str() + tab + 1;
    val = atoll(p);
    return true;
}

int main(){
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    const char *in_path = INPUT_PATH;
    ifstream fin(in_path);
    if(!fin) exit(1);

    auto st = chrono::steady_clock::now();

    // 1) 流式读入，分块聚合并落盘
    unordered_map<string, ll> agg;
    agg.reserve(MAX_DISTINCT_IN_MEM * 2); // 预留更大桶数，减少 rehash
    agg.max_load_factor(0.7f);

    vector<string> tmp_files;
    tmp_files.reserve(64);

    string line;
    size_t rows = 0, flush_id = 0;
    while(getline(fin, line)){
        if(line.empty()){ ++rows; continue; }
        // TSV: prev \t curr \t type \t n
        size_t p1 = line.find('\t');                if(p1 == string::npos){ ++rows; continue; }
        size_t p2 = line.find('\t', p1 + 1);        if(p2 == string::npos){ ++rows; continue; }
        size_t p3 = line.find('\t', p2 + 1);        if(p3 == string::npos){ ++rows; continue; }
        size_t curr_beg = p1 + 1;
        size_t curr_len = p2 - curr_beg;
        size_t n_beg    = p3 + 1;
        if(n_beg >= line.size()){ ++rows; continue; }

        string curr = line.substr(curr_beg, curr_len);
        const char *n_str = line.c_str() + n_beg;
        ll v = atoll(n_str);
        auto it = agg.find(curr);
        if(it == agg.end()){
            agg.emplace(std::move(curr), v);
            if(agg.size() >= MAX_DISTINCT_IN_MEM){
                string tmp = make_tmp_path(flush_id++);
                flush_chunk_to_file(agg, tmp);
                tmp_files.push_back(std::move(tmp));
                // 重新 reserve + 设置负载因子
                agg.reserve(MAX_DISTINCT_IN_MEM * 2);
                agg.max_load_factor(0.7f);
            }
        }else{
            it->second += v;
        }
        ++rows;
    }
    fin.close();

    // 最后一块也落盘（如果 tmp_files 为空，说明都在内存里）
    if(!agg.empty()){
        if(tmp_files.empty()){
            // 直接在内存里完成 Top-K（无需归并）
            vector<pair<ll, string>> vec;
            vec.reserve(agg.size());
            for(auto &kv : agg) vec.emplace_back(kv.second, kv.first);

            if((int)vec.size() > K_TOP){
                nth_element(vec.begin(), vec.begin() + K_TOP, vec.end(),
                            [](const auto &a, const auto &b){ return a.first > b.first; });
                sort(vec.begin(), vec.begin() + K_TOP,
                     [](const auto &a, const auto &b){ return a.first > b.first; });
                vec.resize(K_TOP);
            }else{
                sort(vec.begin(), vec.end(),
                     [](const auto &a, const auto &b){ return a.first > b.first; });
            }

            auto ed = chrono::steady_clock::now();
            double ms = chrono::duration<double, std::milli>(ed - st).count();

            // 输出仅耗时（保持你原来最简输出习惯）
            cout << ms << " ms\n";
            return 0;
        }else{
            string tmp = make_tmp_path(flush_id++);
            flush_chunk_to_file(agg, tmp);
            tmp_files.push_back(std::move(tmp));
        }
    }

    // 2) 多路归并所有临时文件，并在线维护 Top-K
    struct Node{
        string key;
        ll     val;
        int    idx; // 来自哪个文件
    };
    struct Cmp {
        bool operator()(const Node &a, const Node &b) const {
            return a.key > b.key; // 小根堆（按 key 升序）
        }
    };

    vector<ifstream> fins(tmp_files.size());
    for(size_t i=0;i<tmp_files.size();++i){
        fins[i].open(tmp_files[i], ios::binary);
        if(!fins[i]){ fprintf(stderr, "Cannot open tmp %s\n", tmp_files[i].c_str()); exit(3); }
    }

    // 初始化堆
    priority_queue<Node, vector<Node>, Cmp> pq;
    for(size_t i=0;i<fins.size();++i){
        string k; ll v;
        if(read_record(fins[i], k, v)){
            if(!k.empty()){ pq.push(Node{k, v, (int)i}); }
        }
    }

    // 维护 Top-K 的最小堆：存 (sum, key)，堆顶为当前 Top-K 中最小的 sum
    using Pair = pair<ll,string>;
    auto cmp_min = [](const Pair &a, const Pair &b){ return a.first > b.first; };
    priority_queue<Pair, vector<Pair>, decltype(cmp_min)> topk(cmp_min);

    // 归并 + 聚合相同 key
    while(!pq.empty()){
        Node cur = pq.top(); pq.pop();
        string cur_key = std::move(cur.key);
        ll     total   = cur.val;

        // 把所有相同 key 的记录合并
        while(!pq.empty() && pq.top().key == cur_key){
            total += pq.top().val;
            int j = pq.top().idx; pq.pop();
            string k; ll v;
            if(read_record(fins[j], k, v)){
                if(!k.empty()){ pq.push(Node{std::move(k), v, j}); }
            }
        }

        // 当前弹出的那条来自文件 cur.idx，推进该文件下一条
        {
            string k; ll v;
            if(read_record(fins[cur.idx], k, v)){
                if(!k.empty()){ pq.push(Node{std::move(k), v, cur.idx}); }
            }
        }

        // 在线更新 Top-K
        if((int)topk.size() < K_TOP){
            topk.emplace(total, cur_key);
        }else if(total > topk.top().first){
            topk.pop();
            topk.emplace(total, cur_key);
        }
    }

    // 收尾：整理 Top-K 输出顺序
    vector<Pair> ans;
    ans.reserve(topk.size());
    while(!topk.empty()){ ans.push_back(std::move(topk.top())); topk.pop(); }
    sort(ans.begin(), ans.end(), [](const Pair &a, const Pair &b){ return a.first > b.first; });

    auto ed = chrono::steady_clock::now();
    double ms = chrono::duration<double, std::milli>(ed - st).count();

    // 仅输出耗时（与你当前行为一致）；如果想打印 Top-K，把下面注释解开
    cout << ms << " ms\n";
    // for(size_t i=0;i<ans.size();++i){
    //     printf("%d\t%s\t%lld\t%.3f\n", (int)i+1, ans[i].second.c_str(), (long long)ans[i].first, ms);
    // }

    // 清理临时文件（可选）
    for(auto &p : tmp_files){ std::remove(p.c_str()); }

    return 0;
}

// 快速整数读入（保留习惯；本程序未直接使用）
template < typename T >
inline T read(void){
    T ret(0);
    short flag(1);
    int c = getchar();
    while(c != '-' && !isdigit(c)) c = getchar();
    if(c == '-') flag = -1, c = getchar();
    while(isdigit(c)){
        ret = ret * 10 + (c - '0');
        c = getchar();
    }
    ret *= flag;
    return ret;
}
