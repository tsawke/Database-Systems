# DBMS Performance Evaluation - DS-Project-I

## Context

> DBMS can help us manage data conveniently and significantly improve the efficiency of data retrieval.
>
> PostgreSQL is a popular open-source RDBMS known for its robustness, advanced features, and strong compliance with SQL standards. openGauss is an enterprise-grade open-source RDBMS developed by Huawei, designed for high performance, security, and scalability in demanding business environments.

## Preface

### Environment

System: Alibaba Cloud Linux 3.2104 LTS 64位

IP: 47.115.128.238

#### openGauss (docker)

- Version: openGauss-Docker-6.0.2-x86_64
- Port: 15432:5432
- User: omm (Operation & Maintenance Manager)
- Password: opengauss

#### PostgreSQL

- Version: 17.6
- Port: 5432
- User: postgres
- Password: postgres

### Datasets

[Clickstream](https://dumps.wikimedia.org/other/clickstream/2025-09/)

> The Clickstream dataset aggregates counts of `(referrer, resource)` pairs from Wikipedia request logs, showing how readers arrive at an article and what they click next. 

Run `DownloadDatasets.sh` to download all the datasets.

To import datasets to PostgreSQL, run:

```sh
psql "postgresql://postgres:postgres@127.0.0.1:5432/project1" -f './ImportDatasets.sql'
```

Results:

```sh
 rows_loaded 
-------------
    35512282
```

## What are the unique advantages of a DBMS compared with data operations in files?

### Purpose: Find all events that contains 'main' in 'curr'(current).

#### PostgreSQL

```sql
EXPLAIN (ANALYZE)
SELECT * FROM clickstream.events WHERE curr ILIKE '%main%';
```

```
                                                           QUERY PLAN                                                            
---------------------------------------------------------------------------------------------------------------------------------
 Gather  (cost=1000.00..547907.69 rows=124279 width=47) (actual time=0.437..24740.854 rows=162828 loops=1)
   Workers Planned: 2
   Workers Launched: 2
   ->  Parallel Seq Scan on events  (cost=0.00..534479.79 rows=51783 width=47) (actual time=2.401..24640.354 rows=54276 loops=3)
         Filter: (curr ~~* '%main%'::text)
         Rows Removed by Filter: 11783151
 Planning Time: 1.428 ms
 Execution Time: 24750.391 ms
(8 rows)
```

During 5 tests, the average result is **24662.1ms**.

#### C++

```sh
g++ ./SelectAll.cpp -o SelectAll -std=c++17 -O2 && ./SelectAll
```

```sh
Find 162828 results in total
21234.4 ms
```

```sh
g++ ./SelectAll.cpp -o SelectAll -std=c++17 && ./SelectAll
```

```sh

```

During 5 tests, the average result is **20116.2ms**.

### Purpose: Update every '_' in 'curr' to '^'.

#### PostgreSQL

```sql
EXPLAIN (ANALYZE)
UPDATE clickstream.events SET curr = REPLACE(curr, '_', '^') WHERE curr LIKE '%_%';
```

```
                                                          QUERY PLAN                                                          
------------------------------------------------------------------------------------------------------------------------------
 Update on events  (cost=0.00..882401.93 rows=0 width=0) (actual time=225011.949..225014.086 rows=0 loops=1)
   ->  Seq Scan on events  (cost=0.00..882401.93 rows=35522510 width=38) (actual time=0.024..41868.876 rows=35512282 loops=1)
         Filter: (curr ~~ '%_%'::text)
 Planning Time: 10.490 ms
 Execution Time: 225019.108 ms
(5 rows)
```

During test, the average result is **225019.1ms**.

#### C++

```sh
g++ ./UpdateAll.cpp -o UpdateAll -std=c++17 -O2 && ./UpdateAll
```

```sh
Update 30866250 results in total
61515.7 ms
```

During the test, the result is **61515.7ms**.



## Which DBMS is better? PostgreSQL or openGauss, and by which standard?



## Remarks

### How to connect?

#### PostgreSQL

```sh
sudo -u postgres psql -p 5432 -d postgres
```

```sh
psql -h 127.0.0.1 -p 5432 -U postgres -d postgres
```

```sh
psql "postgresql://postgres:postgres@127.0.0.1:5432/project1"
```

#### openGauss

```sh
sudo podman exec -it opengauss15432 /bin/sh
su - omm
gsql -h 127.0.0.1 -p 5432 -d postgres -U omm
```

```sh
sudo podman exec -it opengauss15432 /bin/sh -lc \
"su - omm -c \"gsql -h 127.0.0.1 -p 5432 -d postgres -U omm -c 'select version();'\""
```

```sh
gsql -h 127.0.0.1 -p 15432 -d postgres -U omm
```

```sh
podman exec -it opengauss15432 gsql "opengauss://omm:opengauss@127.0.0.1:15432/project1"
```



### Force password of openGauss to 'opengauss'.

```sh
sudo podman exec -it opengauss15432 /bin/sh
su - omm
echo "$PGDATA"
PGDATA_DIR=${PGDATA:-$(gsql -d postgres -p 5432 -Atc "show data_directory;")}
echo "PGDATA_DIR=$PGDATA_DIR"
gs_guc reload -D "$PGDATA_DIR" -c "password_policy=0"
gsql -d postgres -p 5432 -c "show password_policy;"   # should be 0
gsql -d postgres -p 5432 -c "ALTER ROLE omm IDENTIFIED BY 'opengauss' REPLACE 'Opengauss@1';"
exit
echo 'omm:opengauss' | chpasswd    # echo opengauss | passwd --stdin omm
```



