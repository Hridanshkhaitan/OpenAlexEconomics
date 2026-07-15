import duckdb
P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"
qs = {
"6_2020s_all_works": "SELECT ROUND(100.0*SUM(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero, COUNT(*) AS n FROM read_parquet('%s') WHERE publication_year >= 2020" % P,
"6_2020_2025_articles_by_year": "SELECT publication_year, ROUND(100.0*SUM(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero FROM read_parquet('%s') WHERE publication_year >= 2020 AND type='article' GROUP BY 1 ORDER BY 1" % P,
}
for k in sorted(qs):
    print("===", k, "===")
    print(duckdb.sql(qs[k]).df().to_string(index=False))
    print()
