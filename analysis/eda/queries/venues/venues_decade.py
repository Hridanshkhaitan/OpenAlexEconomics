import duckdb
P = "read_parquet('/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet')"
# Decade null rate among decades with substantial data (>=1000 works), highest pct
r = duckdb.sql(f"SELECT (publication_year/10)*10 AS decade, round(100.0*sum(CASE WHEN journal IS NULL THEN 1 ELSE 0 END)/count(*),2) AS pct_null, count(*) AS n FROM {P} WHERE publication_year>=1900 GROUP BY decade ORDER BY pct_null DESC LIMIT 8").fetchall()
print("DECADE PEAK (>=1900):", r)
# Explicit 2010s
r2 = duckdb.sql(f"SELECT round(100.0*sum(CASE WHEN journal IS NULL THEN 1 ELSE 0 END)/count(*),2) AS pct_null, count(*) AS n FROM {P} WHERE publication_year>=2010 AND publication_year<2020").fetchall()
print("2010s decade:", r2)
