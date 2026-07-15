import duckdb
P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"
qs = {
"4_article_only_le2015": "SELECT ROUND(100.0*SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero, COUNT(*) AS n FROM read_parquet('%s') WHERE publication_year <= 2015 AND type='article'" % P,
"4_journal_notnull_le2015": "SELECT ROUND(100.0*SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero, COUNT(*) AS n FROM read_parquet('%s') WHERE publication_year <= 2015 AND journal IS NOT NULL" % P,
"6_2020s_article_journalnotnull": "SELECT ROUND(100.0*SUM(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero, COUNT(*) AS n FROM read_parquet('%s') WHERE publication_year >= 2020 AND type='article' AND journal IS NOT NULL" % P,
"6_2020s_journalnotnull": "SELECT ROUND(100.0*SUM(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero, COUNT(*) AS n FROM read_parquet('%s') WHERE publication_year >= 2020 AND journal IS NOT NULL" % P,
}
for k in sorted(qs):
    print("===", k, "===")
    print(duckdb.sql(qs[k]).df().to_string(index=False))
    print()
