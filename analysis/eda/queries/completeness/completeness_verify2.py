import duckdb
P = "read_parquet('/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet')"

# journal coverage by decade to test "worst decade 2010s at 77.1%"
print("=== journal nonnull pct by decade ===")
for r in duckdb.sql(f"SELECT (publication_year//10)*10 AS dec, COUNT(*) n, 100.0*SUM(CASE WHEN journal IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*) AS jnn FROM {P} WHERE publication_year>=1900 GROUP BY 1 ORDER BY jnn ASC LIMIT 6").fetchall():
    print(r)

# cbc zero share ordered to test min/max of the "range 46.5% books to 96.9% paratext"
print("=== cbc_zero_pct extremes (types with n>=1000) ===")
print("min:", duckdb.sql(f"SELECT type,n,p FROM (SELECT type,COUNT(*) n,100.0*SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END)/COUNT(*) p FROM {P} GROUP BY 1) WHERE n>=1000 ORDER BY p ASC LIMIT 3").fetchall())
print("max:", duckdb.sql(f"SELECT type,n,p FROM (SELECT type,COUNT(*) n,100.0*SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END)/COUNT(*) p FROM {P} GROUP BY 1) WHERE n>=1000 ORDER BY p DESC LIMIT 3").fetchall())
