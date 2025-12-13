-- Returns the last TMDb sync date used by the delta layer
SELECT v AS tmdb_last_sync
FROM pipeline_state
WHERE k = 'tmdb_last_sync';
