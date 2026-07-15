import duckdb
P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"
# max book-chapter count over all years (is 2023's 90,725 an all-time high?)
print(duckdb.sql(f"SELECT publication_year, COUNT(*) AS chapters FROM read_parquet('{P}') WHERE type='book-chapter' GROUP BY 1 ORDER BY chapters DESC LIMIT 3").df().to_string(index=False))
# 2011 count (context for 'lowest since 2012')
print(duckdb.sql(f"SELECT COUNT(*) AS n2011 FROM read_parquet('{P}') WHERE publication_year=2011").df().to_string(index=False))
