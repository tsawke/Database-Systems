SELECT m.title, m.year_released, m.country
    FROM movies AS m
    LEFT JOIN credits AS c
        ON c.movieid = m.movieid
            AND c.credited_as = 'D'
    WHERE m.year_released >= 2010
        AND c.movieid IS NULL;
