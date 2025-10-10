SELECT m.*
    FROM movies AS m
        JOIN credits AS c
            ON c.movieid  = m.movieid
        JOIN people AS p
            ON p.peopleid = c.peopleid
    WHERE c.credited_as = 'D'
        AND p.first_name = 'John'
        AND p.surname = 'Woo';