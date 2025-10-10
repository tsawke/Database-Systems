SELECT p.first_name, p.surname,
    CASE c.credited_as
        WHEN 'A' THEN 'Actor'
        WHEN 'D' THEN 'Director'
    END AS credited_as
    FROM movies AS m
        JOIN credits AS c
            ON c.movieid = m.movieid
        JOIN people AS p
            ON p.peopleid = c.peopleid
    WHERE m.title = 'Treasure Island'
        AND m.country = 'us'
        AND m.year_released = 1950;