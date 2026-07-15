import duckdb

P = "read_parquet('/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet')"

def run(i, sql):
    print(f"===== CLAIM {i} =====")
    try:
        rows = duckdb.sql(sql).fetchall()
        cols = duckdb.sql(sql).columns
        print("cols:", cols)
        for r in rows:
            print(r)
    except Exception as e:
        print("ERROR:", repr(e))
    print()

# Claim 1
run(1, f"SELECT COUNT(*) AS total, SUM(CASE WHEN abstract IS NULL THEN 1 ELSE 0 END) AS abs_null, 100.0*SUM(CASE WHEN abstract IS NULL THEN 1 ELSE 0 END)/COUNT(*) AS abs_null_pct FROM {P}")

# Claim 2
run(2, f"SELECT (publication_year // 10) * 10 AS decade, COUNT(*) AS n, SUM(CASE WHEN doi IS NULL THEN 1 ELSE 0 END) AS doi_null, 100.0*SUM(CASE WHEN doi IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*) AS doi_nonnull_pct FROM {P} GROUP BY 1 ORDER BY 1")
# also overall doi null for claim 2 headline number
run("2b", f"SELECT COUNT(*) AS total, SUM(CASE WHEN doi IS NULL THEN 1 ELSE 0 END) AS doi_null, 100.0*SUM(CASE WHEN doi IS NULL THEN 1 ELSE 0 END)/COUNT(*) AS doi_null_pct FROM {P}")

# Claim 3
run(3, f"SELECT COUNT(*) AS total, SUM(CASE WHEN referenced_works_count = 0 THEN 1 ELSE 0 END) AS rwc_zero, 100.0*SUM(CASE WHEN referenced_works_count = 0 THEN 1 ELSE 0 END)/COUNT(*) AS rwc_zero_pct FROM {P}")
# journal articles rwc zero share
run("3b", f"SELECT type, COUNT(*) AS n, 100.0*SUM(CASE WHEN referenced_works_count = 0 THEN 1 ELSE 0 END)/COUNT(*) AS rwc_zero_pct FROM {P} WHERE type='article' GROUP BY 1")

# Claim 4
run(4, f"SELECT type, COUNT(*) AS n, 100.0*SUM(CASE WHEN cited_by_count = 0 THEN 1 ELSE 0 END)/COUNT(*) AS cbc_zero_pct FROM {P} GROUP BY 1 ORDER BY n DESC")
run("4b", f"SELECT COUNT(*) AS total, SUM(CASE WHEN cited_by_count = 0 THEN 1 ELSE 0 END) AS cbc_zero, 100.0*SUM(CASE WHEN cited_by_count = 0 THEN 1 ELSE 0 END)/COUNT(*) AS cbc_zero_pct FROM {P}")

# Claim 5
run(5, f"SELECT SUM(CASE WHEN first_author IS NULL AND author_count = 0 THEN 1 ELSE 0 END) AS both_missing, SUM(CASE WHEN first_author IS NULL AND author_count > 0 THEN 1 ELSE 0 END) AS fa_null_only, SUM(CASE WHEN first_author IS NOT NULL AND author_count = 0 THEN 1 ELSE 0 END) AS ac0_only, COUNT(*) AS total, 100.0*SUM(CASE WHEN first_author IS NULL AND author_count = 0 THEN 1 ELSE 0 END)/COUNT(*) AS both_missing_pct FROM {P}")

# Claim 6
run(6, f"SELECT SUM(CASE WHEN publication_date IS NULL THEN 1 ELSE 0 END) AS pd_null, SUM(CASE WHEN publication_date IS NOT NULL AND TRY_CAST(publication_date AS DATE) IS NULL THEN 1 ELSE 0 END) AS pd_unparseable, SUM(CASE WHEN TRY_CAST(publication_date AS DATE) IS NOT NULL AND year(TRY_CAST(publication_date AS DATE)) <> publication_year THEN 1 ELSE 0 END) AS year_mismatch FROM {P}")

# Claim 7
run(7, f"SELECT publication_year, COUNT(*) AS n, 100.0*SUM(CASE WHEN language IS NULL THEN 1 ELSE 0 END)/COUNT(*) AS lang_null_pct FROM {P} WHERE publication_year BETWEEN 2019 AND 2025 GROUP BY 1 ORDER BY 1")

# Claim 8
run(8, f"SELECT COUNT(*) AS total, SUM(CASE WHEN journal IS NULL THEN 1 ELSE 0 END) AS journal_null, 100.0*SUM(CASE WHEN journal IS NULL THEN 1 ELSE 0 END)/COUNT(*) AS journal_null_pct, SUM(CASE WHEN title IS NULL OR title = '' THEN 1 ELSE 0 END) AS title_missing, 100.0*SUM(CASE WHEN title IS NULL OR title = '' THEN 1 ELSE 0 END)/COUNT(*) AS title_missing_pct FROM {P}")
# 2010s journal coverage for claim 8
run("8b", f"SELECT 100.0*SUM(CASE WHEN journal IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*) AS journal_nonnull_pct_2010s FROM {P} WHERE publication_year BETWEEN 2010 AND 2019")
