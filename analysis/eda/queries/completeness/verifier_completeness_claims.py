import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"

queries = {
1: f"SELECT COUNT(*) AS total, SUM(CASE WHEN abstract IS NULL THEN 1 ELSE 0 END) AS abs_null, 100.0*SUM(CASE WHEN abstract IS NULL THEN 1 ELSE 0 END)/COUNT(*) AS abs_null_pct FROM read_parquet('{P}')",
2: f"SELECT (publication_year // 10) * 10 AS decade, COUNT(*) AS n, SUM(CASE WHEN doi IS NULL THEN 1 ELSE 0 END) AS doi_null, 100.0*SUM(CASE WHEN doi IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*) AS doi_nonnull_pct FROM read_parquet('{P}') GROUP BY 1 ORDER BY 1",
3: f"SELECT COUNT(*) AS total, SUM(CASE WHEN referenced_works_count = 0 THEN 1 ELSE 0 END) AS rwc_zero, 100.0*SUM(CASE WHEN referenced_works_count = 0 THEN 1 ELSE 0 END)/COUNT(*) AS rwc_zero_pct FROM read_parquet('{P}')",
4: f"SELECT type, COUNT(*) AS n, 100.0*SUM(CASE WHEN cited_by_count = 0 THEN 1 ELSE 0 END)/COUNT(*) AS cbc_zero_pct FROM read_parquet('{P}') GROUP BY 1 ORDER BY n DESC",
5: f"SELECT SUM(CASE WHEN first_author IS NULL AND author_count = 0 THEN 1 ELSE 0 END) AS both_missing, SUM(CASE WHEN first_author IS NULL AND author_count > 0 THEN 1 ELSE 0 END) AS fa_null_only, SUM(CASE WHEN first_author IS NOT NULL AND author_count = 0 THEN 1 ELSE 0 END) AS ac0_only FROM read_parquet('{P}')",
6: f"SELECT SUM(CASE WHEN publication_date IS NULL THEN 1 ELSE 0 END) AS pd_null, SUM(CASE WHEN publication_date IS NOT NULL AND TRY_CAST(publication_date AS DATE) IS NULL THEN 1 ELSE 0 END) AS pd_unparseable, SUM(CASE WHEN TRY_CAST(publication_date AS DATE) IS NOT NULL AND year(TRY_CAST(publication_date AS DATE)) <> publication_year THEN 1 ELSE 0 END) AS year_mismatch FROM read_parquet('{P}')",
7: f"SELECT publication_year, COUNT(*) AS n, 100.0*SUM(CASE WHEN language IS NULL THEN 1 ELSE 0 END)/COUNT(*) AS lang_null_pct FROM read_parquet('{P}') WHERE publication_year BETWEEN 2019 AND 2025 GROUP BY 1 ORDER BY 1",
8: f"SELECT COUNT(*) AS total, SUM(CASE WHEN journal IS NULL THEN 1 ELSE 0 END) AS journal_null, SUM(CASE WHEN title IS NULL OR title = '' THEN 1 ELSE 0 END) AS title_missing FROM read_parquet('{P}')",
}

# extra queries needed to check sub-parts of claims not covered by the headline SQL:
extras = {
"3b_journal_articles_rwc0": f"SELECT 100.0*SUM(CASE WHEN referenced_works_count = 0 THEN 1 ELSE 0 END)/COUNT(*) AS pct FROM read_parquet('{P}') WHERE type = 'article'",
"4b_overall_cbc0": f"SELECT COUNT(*) AS total, SUM(CASE WHEN cited_by_count = 0 THEN 1 ELSE 0 END) AS cbc_zero, 100.0*SUM(CASE WHEN cited_by_count = 0 THEN 1 ELSE 0 END)/COUNT(*) AS pct FROM read_parquet('{P}')",
"8b_journal_by_decade": f"SELECT (publication_year // 10) * 10 AS decade, COUNT(*) AS n, 100.0*SUM(CASE WHEN journal IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*) AS journal_nonnull_pct FROM read_parquet('{P}') GROUP BY 1 ORDER BY 1",
}

for idx in sorted(queries):
    try:
        df = duckdb.sql(queries[idx]).df()
        print(f"=== CLAIM {idx} ===")
        print(df.to_string(index=False))
    except Exception as e:
        print(f"=== CLAIM {idx} ERROR: {e}")

for k in extras:
    try:
        df = duckdb.sql(extras[k]).df()
        print(f"=== EXTRA {k} ===")
        print(df.to_string(index=False))
    except Exception as e:
        print(f"=== EXTRA {k} ERROR: {e}")
