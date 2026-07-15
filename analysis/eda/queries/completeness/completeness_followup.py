import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"

# Proper decade table
q2 = f"""
SELECT
  (publication_year // 10) * 10 AS decade,
  COUNT(*) AS n,
  100.0*SUM(CASE WHEN doi IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*) AS doi_pct,
  100.0*SUM(CASE WHEN abstract IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*) AS abs_pct,
  100.0*SUM(CASE WHEN journal IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*) AS jrnl_pct,
  100.0*SUM(CASE WHEN language IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*) AS lang_pct
FROM read_parquet('{P}')
WHERE publication_year >= 1900
GROUP BY 1 ORDER BY 1
"""
print("=== PART 2 (redo): % NON-NULL BY DECADE ===")
print("decade | n | doi% | abstract% | journal% | language%")
for row in duckdb.sql(q2).fetchall():
    print(f"{int(row[0])}s | {row[1]} | {row[2]:.2f} | {row[3]:.2f} | {row[4]:.2f} | {row[5]:.2f}")

# pre-1900 count for context
r = duckdb.sql(f"SELECT COUNT(*), 100.0*SUM(CASE WHEN doi IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*), 100.0*SUM(CASE WHEN abstract IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*) FROM read_parquet('{P}') WHERE publication_year < 1900").fetchall()[0]
print(f"\npre-1900: n={r[0]} doi%={r[1]:.2f} abs%={r[2]:.2f}")

# Surprise chase 1: language nulls by year 2019-2025, and by type in 2024-2025
q_lang = f"""
SELECT publication_year, COUNT(*) n,
  SUM(CASE WHEN language IS NULL THEN 1 ELSE 0 END) lang_null
FROM read_parquet('{P}')
WHERE publication_year BETWEEN 2019 AND 2025
GROUP BY 1 ORDER BY 1
"""
print("\n=== language nulls by year 2019-2025 ===")
for row in duckdb.sql(q_lang).fetchall():
    print(f"{row[0]}: n={row[1]} lang_null={row[2]} ({100.0*row[2]/row[1]:.2f}%)")

q_lang_type = f"""
SELECT type, COUNT(*) n,
  SUM(CASE WHEN language IS NULL THEN 1 ELSE 0 END) lang_null
FROM read_parquet('{P}')
WHERE publication_year BETWEEN 2023 AND 2025
GROUP BY 1 ORDER BY lang_null DESC LIMIT 10
"""
print("\n=== language nulls by type, 2023-2025 ===")
for row in duckdb.sql(q_lang_type).fetchall():
    print(f"{row[0]}: n={row[1]} lang_null={row[2]} ({100.0*row[2]/row[1]:.2f}%)")

# Surprise chase 2: first_author null vs author_count=0 identity
q_fa = f"""
SELECT
  SUM(CASE WHEN first_author IS NULL AND author_count = 0 THEN 1 ELSE 0 END) AS both,
  SUM(CASE WHEN first_author IS NULL AND author_count > 0 THEN 1 ELSE 0 END) AS fa_null_only,
  SUM(CASE WHEN first_author IS NOT NULL AND author_count = 0 THEN 1 ELSE 0 END) AS ac0_only
FROM read_parquet('{P}')
"""
print("\n=== first_author null vs author_count=0 ===")
print(duckdb.sql(q_fa).fetchall()[0])

# zero-citation and zero-references breakdown by type (top types)
q_z = f"""
SELECT type, COUNT(*) n,
  100.0*SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END)/COUNT(*) cbc0_pct,
  100.0*SUM(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END)/COUNT(*) rwc0_pct,
  100.0*SUM(CASE WHEN author_count=0 THEN 1 ELSE 0 END)/COUNT(*) ac0_pct
FROM read_parquet('{P}')
GROUP BY 1 ORDER BY n DESC LIMIT 8
"""
print("\n=== zero-value shares by type (top 8 types) ===")
for row in duckdb.sql(q_z).fetchall():
    print(f"{row[0]}: n={row[1]} cbc0={row[2]:.1f}% rwc0={row[3]:.1f}% ac0={row[4]:.1f}%")
