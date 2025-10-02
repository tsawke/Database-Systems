# #!/usr/bin/env python3
# """
# PostgreSQL数据库设置脚本
# 创建filmdb数据库，创建表结构，并导入数据
# """

# import psycopg2
# import psycopg2.extensions
# import os
# import sys
# from pathlib import Path

# # 数据库连接配置
# DB_CONFIG = {
#     'host': 'localhost',
#     'port': 5432,
#     'user': 'postgres',
#     'password': 'postgres'
# }

# # 目标数据库名
# TARGET_DB = 'filmdb'

# def connect_to_postgres():
#     """连接到PostgreSQL服务器（不指定数据库）"""
#     try:
#         conn = psycopg2.connect(
#             host=DB_CONFIG['host'],
#             port=DB_CONFIG['port'],
#             user=DB_CONFIG['user'],
#             password=DB_CONFIG['password'],
#             database='postgres'  # 连接到默认数据库
#         )
#         conn.autocommit = True
#         print(f"✓ 成功连接到PostgreSQL服务器")
#         return conn
#     except psycopg2.Error as e:
#         print(f"✗ 连接PostgreSQL失败: {e}")
#         sys.exit(1)

# def create_database(conn):
#     """创建filmdb数据库"""
#     try:
#         cursor = conn.cursor()
        
#         # 检查数据库是否已存在
#         cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TARGET_DB,))
#         if cursor.fetchone():
#             print(f"✓ 数据库 '{TARGET_DB}' 已存在")
#             return True
            
#         # 创建数据库
#         cursor.execute(f"CREATE DATABASE {TARGET_DB}")
#         print(f"✓ 成功创建数据库 '{TARGET_DB}'")
#         return True
        
#     except psycopg2.Error as e:
#         print(f"✗ 创建数据库失败: {e}")
#         return False
#     finally:
#         cursor.close()

# def connect_to_filmdb():
#     """连接到filmdb数据库"""
#     try:
#         conn = psycopg2.connect(
#             host=DB_CONFIG['host'],
#             port=DB_CONFIG['port'],
#             user=DB_CONFIG['user'],
#             password=DB_CONFIG['password'],
#             database=TARGET_DB
#         )
#         conn.autocommit = True
#         print(f"✓ 成功连接到数据库 '{TARGET_DB}'")
#         return conn
#     except psycopg2.Error as e:
#         print(f"✗ 连接数据库 '{TARGET_DB}' 失败: {e}")
#         sys.exit(1)

# def create_tables(conn):
#     """创建表结构"""
#     try:
#         cursor = conn.cursor()
        
#         # 删除现有表（如果存在）
#         cursor.execute("DROP TABLE IF EXISTS movies CASCADE")
#         cursor.execute("DROP TABLE IF EXISTS countries CASCADE")
#         print("✓ 删除现有表")
        
#         # 创建countries表
#         cursor.execute("""
#             CREATE TABLE countries (
#                 country_code VARCHAR(20) PRIMARY KEY,
#                 country_name VARCHAR(100) NOT NULL,
#                 continent VARCHAR(50) NOT NULL
#             )
#         """)
#         print("✓ 创建countries表")
        
#         # 创建movies表
#         cursor.execute("""
#             CREATE TABLE movies (
#                 movieid SERIAL PRIMARY KEY,
#                 title VARCHAR(255) NOT NULL,
#                 country VARCHAR(100) NOT NULL,
#                 year_released INTEGER,
#                 runtime INTEGER,
#                 FOREIGN KEY (country) REFERENCES countries(country_code)
#             )
#         """)
#         print("✓ 创建movies表")
        
#         return True
        
#     except psycopg2.Error as e:
#         print(f"✗ 创建表失败: {e}")
#         return False
#     finally:
#         cursor.close()

# def import_countries_data(conn):
#     """导入countries数据"""
#     try:
#         cursor = conn.cursor()
        
#         # 表已经重新创建，无需清空数据
        
#         # 读取countries.txt文件
#         countries_file = Path("src/main/java/com/example/countries.txt")
#         if not countries_file.exists():
#             print(f"✗ 找不到文件: {countries_file}")
#             return False
            
#         with open(countries_file, 'r', encoding='utf-8') as f:
#             lines = f.readlines()
            
#         # 跳过标题行，导入数据
#         imported_count = 0
#         for line in lines[1:]:  # 跳过第一行标题
#             line = line.strip()
#             if line:
#                 parts = line.split(';')
#                 if len(parts) >= 3:
#                     country_code = parts[0].strip()
#                     country_name = parts[1].strip()
#                     continent = parts[2].strip()
                    
#                     cursor.execute("""
#                         INSERT INTO countries (country_code, country_name, continent)
#                         VALUES (%s, %s, %s)
#                         ON CONFLICT (country_code) DO UPDATE SET
#                         country_name = EXCLUDED.country_name,
#                         continent = EXCLUDED.continent
#                     """, (country_code, country_name, continent))
#                     imported_count += 1
                    
#         print(f"✓ 成功导入 {imported_count} 条countries数据")
#         return True
        
#     except Exception as e:
#         print(f"✗ 导入countries数据失败: {e}")
#         return False
#     finally:
#         cursor.close()

# def import_movies_data(conn):
#     """导入movies数据"""
#     try:
#         cursor = conn.cursor()
        
#         # 表已经重新创建，无需清空数据
        
#         # 读取movies.txt文件
#         movies_file = Path("src/main/java/com/example/movies.txt")
#         if not movies_file.exists():
#             print(f"✗ 找不到文件: {movies_file}")
#             return False
            
#         with open(movies_file, 'r', encoding='utf-8') as f:
#             lines = f.readlines()
            
#         # 跳过标题行，导入数据
#         imported_count = 0
#         for line in lines[1:]:  # 跳过第一行标题
#             line = line.strip()
#             if line:
#                 parts = line.split(';')
#                 if len(parts) >= 5:
#                     movieid = int(parts[0].strip()) if parts[0].strip().isdigit() else None
#                     title = parts[1].strip()
#                     country = parts[2].strip()
#                     year_released = int(parts[3].strip()) if parts[3].strip().isdigit() else None
#                     runtime = int(parts[4].strip()) if parts[4].strip() != 'null' and parts[4].strip().isdigit() else None
                    
#                     cursor.execute("""
#                         INSERT INTO movies (movieid, title, country, year_released, runtime)
#                         VALUES (%s, %s, %s, %s, %s)
#                         ON CONFLICT (movieid) DO UPDATE SET
#                         title = EXCLUDED.title,
#                         country = EXCLUDED.country,
#                         year_released = EXCLUDED.year_released,
#                         runtime = EXCLUDED.runtime
#                     """, (movieid, title, country, year_released, runtime))
#                     imported_count += 1
                    
#         print(f"✓ 成功导入 {imported_count} 条movies数据")
#         return True
        
#     except Exception as e:
#         print(f"✗ 导入movies数据失败: {e}")
#         return False
#     finally:
#         cursor.close()

# def verify_data(conn):
#     """验证导入的数据"""
#     try:
#         cursor = conn.cursor()
        
#         # 检查countries表
#         cursor.execute("SELECT COUNT(*) FROM countries")
#         countries_count = cursor.fetchone()[0]
#         print(f"✓ countries表中有 {countries_count} 条记录")
        
#         # 检查movies表
#         cursor.execute("SELECT COUNT(*) FROM movies")
#         movies_count = cursor.fetchone()[0]
#         print(f"✓ movies表中有 {movies_count} 条记录")
        
#         # 检查一些示例数据
#         cursor.execute("SELECT * FROM countries LIMIT 3")
#         print("✓ countries表示例数据:")
#         for row in cursor.fetchall():
#             print(f"  {row}")
            
#         cursor.execute("SELECT * FROM movies LIMIT 3")
#         print("✓ movies表示例数据:")
#         for row in cursor.fetchall():
#             print(f"  {row}")
            
#         return True
        
#     except Exception as e:
#         print(f"✗ 验证数据失败: {e}")
#         return False
#     finally:
#         cursor.close()

# def main():
#     """主函数"""
#     print("=== PostgreSQL数据库设置脚本 ===")
#     print(f"目标数据库: {TARGET_DB}")
#     print(f"连接配置: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
#     print()
    
#     # 步骤1: 连接到PostgreSQL服务器
#     print("步骤1: 连接PostgreSQL服务器...")
#     postgres_conn = connect_to_postgres()
    
#     # 步骤2: 创建数据库
#     print("\n步骤2: 创建数据库...")
#     if not create_database(postgres_conn):
#         sys.exit(1)
#     postgres_conn.close()
    
#     # 步骤3: 连接到filmdb数据库
#     print("\n步骤3: 连接filmdb数据库...")
#     filmdb_conn = connect_to_filmdb()
    
#     # 步骤4: 创建表结构
#     print("\n步骤4: 创建表结构...")
#     if not create_tables(filmdb_conn):
#         sys.exit(1)
    
#     # 步骤5: 导入countries数据
#     print("\n步骤5: 导入countries数据...")
#     if not import_countries_data(filmdb_conn):
#         sys.exit(1)
    
#     # 步骤6: 导入movies数据
#     print("\n步骤6: 导入movies数据...")
#     if not import_movies_data(filmdb_conn):
#         sys.exit(1)
    
#     # 步骤7: 验证数据
#     print("\n步骤7: 验证导入的数据...")
#     if not verify_data(filmdb_conn):
#         sys.exit(1)
    
#     filmdb_conn.close()
    
#     print("\n=== 数据库设置完成! ===")
#     print("现在可以运行Java程序测试数据库连接了:")
#     print("mvn -DskipTests exec:java")

# if __name__ == "__main__":
#     main()



#!/usr/bin/env python3
"""
PostgreSQL数据库设置脚本（健壮CSV解析版）
- 创建 filmdb 数据库与表
- 导入 countries 与 movies（支持国家代码或名称）
- 逐行校验并记录问题行，避免整批失败
"""

import csv
import os
import sys
from pathlib import Path
import psycopg2
import psycopg2.extensions

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres'
}

# 目标数据库名
TARGET_DB = 'filmdb'

# 数据文件默认相对路径（优先顺序）
DATA_CANDIDATE_DIRS = [
    Path("src/main/java/com/example"),
    Path("."),                 # 当前目录
    Path("/mnt/data"),         # 若在Notebook/容器环境
]

COUNTRIES_FILENAME = "countries.txt"
MOVIES_FILENAME = "movies.txt"

def find_file(filename: str) -> Path | None:
    """在候选目录中查找文件"""
    for base in DATA_CANDIDATE_DIRS:
        p = base / filename
        if p.exists():
            return p
    return None

def connect_to_postgres():
    """连接到PostgreSQL服务器（不指定数据库）"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database='postgres'
        )
        conn.autocommit = True
        print("✓ 成功连接到PostgreSQL服务器")
        return conn
    except psycopg2.Error as e:
        print(f"✗ 连接PostgreSQL失败: {e}")
        sys.exit(1)

def create_database(conn):
    """创建filmdb数据库"""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TARGET_DB,))
        if cursor.fetchone():
            print(f"✓ 数据库 '{TARGET_DB}' 已存在")
            return True
        cursor.execute(f"CREATE DATABASE {TARGET_DB}")
        print(f"✓ 成功创建数据库 '{TARGET_DB}'")
        return True
    except psycopg2.Error as e:
        print(f"✗ 创建数据库失败: {e}")
        return False
    finally:
        cursor.close()

def connect_to_filmdb():
    """连接到filmdb数据库"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=TARGET_DB
        )
        conn.autocommit = True
        print(f"✓ 成功连接到数据库 '{TARGET_DB}'")
        return conn
    except psycopg2.Error as e:
        print(f"✗ 连接数据库 '{TARGET_DB}' 失败: {e}")
        sys.exit(1)

def create_tables(conn):
    """创建表结构"""
    cursor = conn.cursor()
    try:
        cursor.execute("DROP TABLE IF EXISTS movies CASCADE")
        cursor.execute("DROP TABLE IF EXISTS countries CASCADE")
        print("✓ 删除现有表")

        cursor.execute("""
            CREATE TABLE countries (
                country_code VARCHAR(20) PRIMARY KEY,
                country_name VARCHAR(100) NOT NULL,
                continent    VARCHAR(50)  NOT NULL
            )
        """)
        print("✓ 创建countries表")

        cursor.execute("""
            CREATE TABLE movies (
                movieid       INTEGER PRIMARY KEY,
                title         VARCHAR(255) NOT NULL,
                country       VARCHAR(100) NOT NULL,
                year_released INTEGER,
                runtime       INTEGER,
                FOREIGN KEY (country) REFERENCES countries(country_code)
            )
        """)
        print("✓ 创建movies表")
        return True
    except psycopg2.Error as e:
        print(f"✗ 创建表失败: {e}")
        return False
    finally:
        cursor.close()

def import_countries_data(conn):
    """导入countries数据（要求表头：country_code;country_name;continent）"""
    cursor = conn.cursor()
    try:
        path = find_file(COUNTRIES_FILENAME)
        if not path:
            print(f"✗ 找不到 {COUNTRIES_FILENAME}（在 {', '.join(map(str, DATA_CANDIDATE_DIRS))} 任一目录）")
            return False

        imported = 0
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            required = {"country_code", "country_name", "continent"}
            if not required.issubset(set(reader.fieldnames or [])):
                print(f"✗ {COUNTRIES_FILENAME} 表头缺失，实际表头: {reader.fieldnames}")
                print("  需要字段: country_code;country_name;continent")
                return False

            for row in reader:
                code = (row.get("country_code") or "").strip()
                name = (row.get("country_name") or "").strip()
                cont = (row.get("continent") or "").strip()
                if not code or not name or not cont:
                    continue
                cursor.execute("""
                    INSERT INTO countries (country_code, country_name, continent)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (country_code) DO UPDATE SET
                        country_name = EXCLUDED.country_name,
                        continent    = EXCLUDED.continent
                """, (code, name, cont))
                imported += 1
        print(f"✓ 成功导入 {imported} 条countries数据")
        return True
    except Exception as e:
        print(f"✗ 导入countries数据失败: {e}")
        return False
    finally:
        cursor.close()

def _load_country_maps(conn):
    """从countries生成：代码集合、名称->代码、代码->名称"""
    cur = conn.cursor()
    cur.execute("SELECT country_code, country_name FROM countries")
    code_set = set()
    name_to_code = {}
    code_to_name = {}
    for code, name in cur.fetchall():
        code = (code or "").strip()
        name = (name or "").strip()
        if code:
            code_set.add(code)
            code_to_name[code] = name
        if name and code and name not in name_to_code:
            name_to_code[name] = code
    cur.close()
    return code_set, name_to_code, code_to_name

def import_movies_data(conn):
    """导入movies数据（按表头解析；国家支持代码或名称；记录问题行）"""
    cursor = conn.cursor()
    try:
        path = find_file(MOVIES_FILENAME)
        if not path:
            print(f"✗ 找不到 {MOVIES_FILENAME}（在 {', '.join(map(str, DATA_CANDIDATE_DIRS))} 任一目录）")
            return False

        code_set, name_to_code, _ = _load_country_maps(conn)

        imported = 0
        skipped = 0
        problems = []

        with open(path, "r", encoding="utf-8", newline="") as f:
            # 期望表头：movieid;title;country;year_released;runtime
            reader = csv.DictReader(f, delimiter=";")
            required = {"movieid", "title", "country", "year_released", "runtime"}
            if not required.issubset(set(reader.fieldnames or [])):
                print(f"✗ {MOVIES_FILENAME} 表头缺失，实际表头: {reader.fieldnames}")
                print("  需要字段: movieid;title;country;year_released;runtime")
                return False

            for idx, row in enumerate(reader, start=2):
                try:
                    raw_id   = (row.get("movieid") or "").strip()
                    title    = (row.get("title") or "").strip()
                    raw_ctry = (row.get("country") or "").strip()
                    raw_year = (row.get("year_released") or "").strip()
                    raw_run  = (row.get("runtime") or "").strip()

                    if not title:
                        problems.append(f"第{idx}行：标题为空，跳过")
                        skipped += 1
                        continue

                    movieid = int(raw_id) if raw_id.isdigit() else None
                    year_released = int(raw_year) if raw_year.isdigit() else None

                    runtime = None
                    if raw_run and raw_run.lower() not in {"null", "none"} and raw_run.isdigit():
                        runtime = int(raw_run)

                    # 国家：先当代码匹配，不行则按名称映射
                    country_code = raw_ctry if raw_ctry in code_set else name_to_code.get(raw_ctry)
                    if not country_code:
                        problems.append(f"第{idx}行：无法识别国家“{raw_ctry}”，片名《{title}》，已跳过")
                        skipped += 1
                        continue

                    cursor.execute("""
                        INSERT INTO movies (movieid, title, country, year_released, runtime)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (movieid) DO UPDATE SET
                          title         = EXCLUDED.title,
                          country       = EXCLUDED.country,
                          year_released = EXCLUDED.year_released,
                          runtime       = EXCLUDED.runtime
                    """, (movieid, title, country_code, year_released, runtime))
                    imported += 1

                except Exception as row_e:
                    problems.append(f"第{idx}行：解析/插入异常：{row_e}")
                    skipped += 1
                    continue

        print(f"✓ 成功导入 {imported} 条 movies 数据")
        if skipped:
            print(f"⚠ 有 {skipped} 行已跳过（示例最多20条）：")
            for msg in problems[:20]:
                print("  - " + msg)
            if len(problems) > 20:
                print(f"  … 其余 {len(problems) - 20} 条省略")
        return True
    except Exception as e:
        print(f"✗ 导入movies数据失败: {e}")
        return False
    finally:
        cursor.close()

def verify_data(conn):
    """验证导入的数据，并打印少量样例"""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM countries")
        c_cnt = cursor.fetchone()[0]
        print(f"✓ countries表中有 {c_cnt} 条记录")

        cursor.execute("SELECT COUNT(*) FROM movies")
        m_cnt = cursor.fetchone()[0]
        print(f"✓ movies表中有 {m_cnt} 条记录")

        cursor.execute("SELECT * FROM countries ORDER BY country_code LIMIT 3")
        print("✓ countries表示例数据:")
        for row in cursor.fetchall():
            print(f"  {row}")

        cursor.execute("SELECT movieid, title, country, year_released, runtime FROM movies ORDER BY movieid LIMIT 3")
        print("✓ movies表示例数据:")
        for row in cursor.fetchall():
            print(f"  {row}")
        return True
    except Exception as e:
        print(f"✗ 验证数据失败: {e}")
        return False
    finally:
        cursor.close()

def check_bad_movie_countries(conn):
    """列出movies中无法在countries里匹配国家代码的记录（最多50条）"""
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT m.movieid, m.title, m.country
            FROM movies m
            LEFT JOIN countries c ON m.country = c.country_code
            WHERE c.country_code IS NULL
            ORDER BY m.movieid NULLS LAST
            LIMIT 50
        """)
        rows = cur.fetchall()
        if rows:
            print("⚠ 以下 movies.country 无法在 countries.country_code 中找到：")
            for r in rows:
                print(f"  id={r[0]} | {r[1]} | country='{r[2]}'")
        else:
            print("✓ 所有 movies.country 均能在 countries 中匹配")
    finally:
        cur.close()

def main():
    print("=== PostgreSQL数据库设置脚本 ===")
    print(f"目标数据库: {TARGET_DB}")
    print(f"连接配置: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print()

    # 步骤1: 连接到PostgreSQL服务器
    print("步骤1: 连接PostgreSQL服务器...")
    postgres_conn = connect_to_postgres()

    # 步骤2: 创建数据库
    print("\n步骤2: 创建数据库...")
    if not create_database(postgres_conn):
        sys.exit(1)
    postgres_conn.close()

    # 步骤3: 连接到filmdb数据库
    print("\n步骤3: 连接filmdb数据库...")
    filmdb_conn = connect_to_filmdb()

    # 步骤4: 创建表结构
    print("\n步骤4: 创建表结构...")
    if not create_tables(filmdb_conn):
        sys.exit(1)

    # 步骤5: 导入countries数据
    print("\n步骤5: 导入countries数据...")
    if not import_countries_data(filmdb_conn):
        sys.exit(1)

    # 步骤6: 导入movies数据
    print("\n步骤6: 导入movies数据...")
    if not import_movies_data(filmdb_conn):
        sys.exit(1)

    # 步骤7: 验证数据
    print("\n步骤7: 验证导入的数据...")
    if not verify_data(filmdb_conn):
        sys.exit(1)

    # 额外检查：是否存在无效国家代码
    print("\n额外检查: 校验movies.country的外键有效性...")
    check_bad_movie_countries(filmdb_conn)

    filmdb_conn.close()

    print("\n=== 数据库设置完成! ===")
    print("现在可以运行Java程序测试数据库连接了:")
    print("mvn -DskipTests exec:java")

if __name__ == "__main__":
    main()
