#define _USE_MATH_DEFINES
#include <bits/stdc++.h>

#define PI M_PI
#define E M_E

using namespace std;

mt19937 rnd(random_device{}());
int rndd(int l, int r){return rnd() % (r - l + 1) + l;}

typedef unsigned int uint;
typedef unsigned long long unll;
typedef long long ll;

template < typename T = int >
inline T read(void);

const char* INPUT_PATH  = "/root/Database-Systems/Project-I/data/clickstream/clickstream-enwiki-2025-09.tsv";
const char* OUTPUT_PATH = "/root/Database-Systems/Project-I/data/clickstream/clickstream-enwiki-2025-09.updated.tsv";

int main() {
    ifstream fin(INPUT_PATH);
    if(!fin)exit(1);

    ofstream fout(OUTPUT_PATH, ios::trunc);
    if(!fout)exit(1);

    auto st = chrono::steady_clock::now();

    ll cnt(0);
    string line;

    while(getline(fin, line)){
        auto p1 = line.find('\t');
        if(p1 == string::npos){fout << line << endl; continue;}
        auto p2 = line.find('\t', p1 + 1);
        if(p2 == string::npos){fout << line << endl; continue;}

        string curr = line.substr(p1 + 1, p2 - p1 - 1);

        if(curr.find('_') != string::npos) {
            for(char &ch : curr)ch = ch == '_' ? '^' : ch;
            ++cnt;
            string out = line.substr(0, p1 + 1);
            out += curr;
            out += line.substr(p2);
            fout << out << endl;
        }else fout << line << endl;
    }

    auto ed = chrono::steady_clock::now();
    double ms = chrono::duration < double, std::milli >(ed - st).count();

    printf("Update %lld results in total\n", cnt);
    cout << ms << " ms\n";

    return 0;
}

template < typename T >
inline T read(void){
    T ret(0);
    short flag(1);
    char c = getchar();
    while(c != '-' && !isdigit(c))c = getchar();
    if(c == '-')flag = -1, c = getchar();
    while(isdigit(c)){
        ret *= 10;
        ret += int(c - '0');
        c = getchar();
    }
    ret *= flag;
    return ret;
}