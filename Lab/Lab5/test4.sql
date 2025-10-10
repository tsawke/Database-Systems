SELECT p.first_name, p.surname, p.peopleid
    FROM (
        SELECT c.peopleid
            FROM credits AS c
            JOIN movies AS m
                ON m.movieid = c.movieid
            WHERE c.credited_as = 'D'
            GROUP BY c.peopleid
            HAVING COUNT(DISTINCT m.country) > 1
    ) AS x
    JOIN people AS p
        ON p.peopleid = x.peopleid;