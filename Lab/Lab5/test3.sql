SELECT COUNT(DISTINCT m.movieid) AS films
    FROM people AS p
        JOIN credits AS c
            ON c.peopleid = p.peopleid
        JOIN movies AS m
            ON m.movieid  = c.movieid
    WHERE c.credited_as = 'A'
        AND p.first_name = 'Marilyn'
        AND p.surname = 'Monroe'
        AND m.year_released = 1952;
