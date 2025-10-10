SELECT DISTINCT
    CASE
        WHEN m.country IN ('cn', 'tw', 'hk', 'jp', 'kr')
            THEN COALESCE(p.surname, '') || ' ' || COALESCE(p.first_name, '')
            ELSE COALESCE(p.first_name, '') || ' ' || COALESCE(p.surname, '')
    END AS director
    FROM movies AS m
        JOIN credits AS c
            ON c.movieid  = m.movieid
        JOIN people AS p
            ON p.peopleid = c.peopleid
    WHERE c.credited_as = 'D'
        AND m.year_released = 2015;