# Results - Lab8

```sql
BEGIN;

DROP TABLE IF EXISTS emp;
CREATE TABLE emp (
    id integer PRIMARY KEY,
    name varchar(30),
    age integer,
    dept_code integer,
    office_loc varchar(100),
    salary integer DEFAULT 0
);

INSERT INTO emp VALUES
    (1,'张三',22,1,'宝安',6000),
    (2,'李四',31,1,'宝安',7000),
    (3,'王五',25,2,'福田',6000),
    (4,'赵六',24,1,'宝安',5000),
    (5,'庄七',22,3,'光明',8000),
    (6,'康八',45,2,'福田',15000),
    (7,'聂九',34,3,'光明',7500),
    (8,'刘二麻子',56,4,'光明',17000),
    (9,'孙小毛',17,1,'宝安',3000),
    (10,'陈老大',37,1,'宝安',7000);
    
COMMIT;

SELECT count(*) AS tot FROM emp;

SELECT id, name, salary
    FROM emp
    ORDER BY id;

```

![image-20251031024536191](./assets/image-20251031024536191.png)

![image-20251031024530740](./assets/image-20251031024530740.png)

![image-20251031024623396](./assets/image-20251031024623396.png)

![image-20251031024704045](./assets/image-20251031024704045.png)

![image-20251031025638239](./assets/image-20251031025638239.png)

![image-20251031025645023](./assets/image-20251031025645023.png)

![image-20251031025730175](./assets/image-20251031025730175.png)

![image-20251031030538795](./assets/image-20251031030538795.png)

![image-20251031030635621](./assets/image-20251031030635621.png)

![image-20251031031254686](./assets/image-20251031031254686.png)

![image-20251031031302358](./assets/image-20251031031302358.png)

![image-20251031031623316](./assets/image-20251031031623316.png)

![image-20251031031632692](./assets/image-20251031031632692.png)
