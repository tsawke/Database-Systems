SELECT r.title, r.country, r.year_released
    FROM movies AS r
    WHERE EXISTS (
        SELECT 1
        FROM movies AS m
        WHERE m.title = r.title
            AND m.year_released < r.year_released
    )
ORDER BY r.title, r.year_released, r.country;
