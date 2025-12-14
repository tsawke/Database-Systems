COPY staging_movies_tmdb_delta(tmdb_id,imdb_id,title,original_title,original_language,release_date,runtime,country_iso2,popularity,vote_average,vote_count,budget,revenue) 
FROM '/tmp/tmdb_delta.csv' 
WITH (FORMAT csv, HEADER true);
