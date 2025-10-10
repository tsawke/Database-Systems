SELECT m.title, m.country, m.year_released, m.runtime
    FROM movies AS m
        JOIN credits AS c
            ON c.movieid = m.movieid
        JOIN people AS p
            ON p.peopleid = c.peopleid
    WHERE c.credited_as = 'D'
        AND p.gender = 'F'
        AND m.runtime IS NOT NULL
    ORDER BY m.runtime DESC NULLS LAST
    FETCH FIRST 1 ROW WITH TIES;