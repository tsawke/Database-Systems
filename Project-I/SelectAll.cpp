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

const char *INPUT_PATH = "/root/Database-Systems/Project-I/data/clickstream/clickstream-enwiki-2025-09.tsv";

int main(){
    ifstream fin(INPUT_PATH);
    if(!fin)exit(1);

    auto st = chrono::steady_clock::now();

    ll cnt(0);

    string str;
    while(getline(fin, str)){
        auto p1 = str.find('\t');
        if(p1 == string::npos)continue;
        auto p2 = str.find('\t', p1 + 1);
        if(p2 == string::npos)continue;

        string curr = str.substr(p1 + 1, p2 - p1 - 1);
        for(char &c : curr)c = tolower(c);
        
        if(curr.find("main") != string::npos)++cnt;
    }

    printf("Find %d results in total\n", cnt);

    auto ed = chrono::steady_clock::now();
    double ms = chrono::duration < double, milli >(ed - st).count();
    cout << ms << " ms" << endl;
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