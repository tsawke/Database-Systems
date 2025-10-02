SELECT * FROM movies WHERE country = 'pt' OR country = 'br';

SELECT * FROM movies WHERE country = 'us' AND year_released = 2006;

SELECT * FROM movies
    WHERE country = 'sp'
    AND LOWER(title) NOT LIKE '%a%'
    AND LOWER(title) NOT LIKE '%o%';

SELECT * FROM movies
    WHERE country in ('cn', 'hk', 'tw', 'mo')
    AND year_released BETWEEN 1940 AND 1949;

SELECT * FROM people
    WHERE born <= 1920
    AND died IS NULL;

SELECT * FROM alt_titles
    WHERE title LIKE '%山%';

SELECT * FROM movies
    WHERE LOWER(title) ~* '[[:<:]]man[[:>:]]';

SELECT * FROM people
    WHERE born + 100 <= died;

SELECT * FROM people
    WHERE born + 100 <= died
    OR (died IS NULL AND born + 100 <= EXTRACT(YEAR FROM CURRENT_DATE));

SELECT * FROM people
    WHERE surname LIKE '%''%';

SELECT * FROM countries
    WHERE continent = 'EUROPE'
    AND country_code LIKE 'c%';

SELECT * FROM people
    WHERE LOWER(LEFT(first_name, 1)) = LOWER(LEFT(surname, 1));

SELECT 2025 - MAX(born) AS age FROM people;

SELECT country, COUNT(*)
    FROM movies
    WHERE country like 'm%'
    GROUP BY country;

SELECT COUNT(DISTINCT country)
    FROM movies;

SELECT MIN(year_released)
    FROM movies
    WHERE country IN ('cn', 'tw', 'hk');

SELECT COUNT(*)
    FROM movies
    WHERE year_released = 2010;

SELECT year_released AS year, COUNT(*)
    FROM movies
    WHERE year_released >= 1960
    GROUP BY year_released;

SELECT COUNT(*)
    FROM movies
    WHERE country = 'gb' AND year_released = 1949;

SELECT directors, COUNT(*)
    FROM (
        SELECT movieid, COUNT(*) AS directors
            FROM credits
            WHERE credited_as = 'D'
            GROUP BY movieid
    )
    GROUP BY directors
    ORDER BY directors;

SELECT COUNT(*) AS total,
        COUNT(*) FILTER (WHERE died IS NULL)  AS alive,
        COUNT(*) FILTER (WHERE died IS NOT NULL) AS dead
    FROM people;

SELECT MAX(cnt) AS max_count
    FROM (
        SELECT LOWER(surname), COUNT(*) AS cnt
            FROM people
            WHERE surname <> ''
            GROUP BY LOWER(surname)
    );

SELECT COUNT(DISTINCT peopleid)
    FROM (
        SELECT peopleid, movieid
            FROM credits
            WHERE credited_as IN ('A', 'D')
            GROUP BY peopleid, movieid
            HAVING COUNT(DISTINCT credited_as) = 2
    );

SELECT ROUND(
        100.0 * COUNT(CASE WHEN gender = 'F' THEN 1 END) / NULLIF(COUNT(*), 0)
        , 1
    ) AS percentage
    FROM people;

SELECT country, COUNT(*)
    FROM movies
    WHERE runtime >= 180
    GROUP BY country;
