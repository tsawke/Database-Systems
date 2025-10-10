SELECT DISTINCT r.title, r.country, r.year_released
    FROM movies AS r
        JOIN movies AS m
            ON m.title = r.title
                AND m.year_released < r.year_released;