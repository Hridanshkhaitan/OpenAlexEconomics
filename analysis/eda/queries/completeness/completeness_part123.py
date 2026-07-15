import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"

# ---------- Part 1: null/empty audit ----------
q1 = f"""
SELECT
  COUNT(*) AS n,
  SUM(CASE WHEN doi IS NULL THEN 1 ELSE 0 END) AS doi_null,
  SUM(CASE WHEN doi = '' THEN 1 ELSE 0 END) AS doi_empty,
  SUM(CASE WHEN title IS NULL THEN 1 ELSE 0 END) AS title_null,
  SUM(CASE WHEN title = '' THEN 1 ELSE 0 END) AS title_empty,
  SUM(CASE WHEN publication_date IS NULL THEN 1 ELSE 0 END) AS pubdate_null,
  SUM(CASE WHEN publication_date = '' THEN 1 ELSE 0 END) AS pubdate_empty,
  SUM(CASE WHEN type IS NULL THEN 1 ELSE 0 END) AS type_null,
  SUM(CASE WHEN type = '' THEN 1 ELSE 0 END) AS type_empty,
  SUM(CASE WHEN language IS NULL THEN 1 ELSE 0 END) AS lang_null,
  SUM(CASE WHEN language = '' THEN 1 ELSE 0 END) AS lang_empty,
  SUM(CASE WHEN journal IS NULL THEN 1 ELSE 0 END) AS journal_null,
  SUM(CASE WHEN journal = '' THEN 1 ELSE 0 END) AS journal_empty,
  SUM(CASE WHEN first_author IS NULL THEN 1 ELSE 0 END) AS fa_null,
  SUM(CASE WHEN first_author = '' THEN 1 ELSE 0 END) AS fa_empty,
  SUM(CASE WHEN abstract IS NULL THEN 1 ELSE 0 END) AS abs_null,
  SUM(CASE WHEN abstract = '' THEN 1 ELSE 0 END) AS abs_empty,
  SUM(CASE WHEN is_oa IS NULL THEN 1 ELSE 0 END) AS isoa_null,
  SUM(CASE WHEN cited_by_count IS NULL THEN 1 ELSE 0 END) AS cbc_null,
  SUM(CASE WHEN cited_by_count = 0 THEN 1 ELSE 0 END) AS cbc_zero,
  SUM(CASE WHEN referenced_works_count IS NULL THEN 1 ELSE 0 END) AS rwc_null,
  SUM(CASE WHEN referenced_works_count = 0 THEN 1 ELSE 0 END) AS rwc_zero,
  SUM(CASE WHEN author_count IS NULL THEN 1 ELSE 0 END) AS ac_null,
  SUM(CASE WHEN author_count = 0 THEN 1 ELSE 0 END) AS ac_zero,
  SUM(CASE WHEN id IS NULL THEN 1 ELSE 0 END) AS id_null,
  SUM(CASE WHEN field IS NULL THEN 1 ELSE 0 END) AS field_null,
  SUM(CASE WHEN subfield IS NULL THEN 1 ELSE 0 END) AS subfield_null,
  SUM(CASE WHEN primary_topic IS NULL THEN 1 ELSE 0 END) AS ptopic_null,
  SUM(CASE WHEN publication_year IS NULL THEN 1 ELSE 0 END) AS pubyear_null
FROM read_parquet('{P}')
"""
r = duckdb.sql(q1).fetchall()[0]
cols = [d[0] for d in duckdb.sql(q1).description]
n = r[0]
print("=== PART 1: NULL/EMPTY AUDIT (total rows = %d) ===" % n)
for c, v in zip(cols, r):
    if c == 'n':
        continue
    print(f"{c}: {v} ({100.0*v/n:.3f}%)")

# ---------- Part 2: coverage by decade since 1900 ----------
q2 = f"""
SELECT
  (publication_year/10)*10 AS decade,
  COUNT(*) AS n,
  100.0*SUM(CASE WHEN doi IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*) AS doi_pct,
  100.0*SUM(CASE WHEN abstract IS NOT NULL AND abstract <> '' THEN 1 ELSE 0 END)/COUNT(*) AS abs_pct,
  100.0*SUM(CASE WHEN journal IS NOT NULL AND journal <> '' THEN 1 ELSE 0 END)/COUNT(*) AS jrnl_pct,
  100.0*SUM(CASE WHEN language IS NOT NULL AND language <> '' THEN 1 ELSE 0 END)/COUNT(*) AS lang_pct
FROM read_parquet('{P}')
WHERE publication_year >= 1900
GROUP BY 1 ORDER BY 1
"""
print("\n=== PART 2: % NON-NULL BY DECADE (>=1900) ===")
print("decade | n | doi% | abstract% | journal% | language%")
for row in duckdb.sql(q2).fetchall():
    print(f"{int(row[0])} | {row[1]} | {row[2]:.2f} | {row[3]:.2f} | {row[4]:.2f} | {row[5]:.2f}")

# ---------- Part 3: consistency publication_date vs publication_year ----------
q3 = f"""
SELECT
  COUNT(*) AS n,
  SUM(CASE WHEN publication_date IS NULL THEN 1 ELSE 0 END) AS pd_null,
  SUM(CASE WHEN publication_date IS NOT NULL AND TRY_CAST(publication_date AS DATE) IS NULL THEN 1 ELSE 0 END) AS pd_bad,
  SUM(CASE WHEN TRY_CAST(publication_date AS DATE) IS NOT NULL
            AND year(TRY_CAST(publication_date AS DATE)) <> publication_year THEN 1 ELSE 0 END) AS yr_mismatch
FROM read_parquet('{P}')
"""
r3 = duckdb.sql(q3).fetchall()[0]
print("\n=== PART 3: DATE CONSISTENCY ===")
print(f"total={r3[0]} pubdate_null={r3[1]} pubdate_unparseable={r3[2]} year_mismatch={r3[3]} ({100.0*r3[3]/r3[0]:.4f}%)")

# sample of mismatches if any
if r3[3] and r3[3] > 0:
    q3b = f"""
    SELECT publication_date, publication_year, COUNT(*) c
    FROM read_parquet('{P}')
    WHERE TRY_CAST(publication_date AS DATE) IS NOT NULL
      AND year(TRY_CAST(publication_date AS DATE)) <> publication_year
    GROUP BY 1,2 ORDER BY c DESC LIMIT 15
    """
    print("top mismatch patterns (date, year, count):")
    for row in duckdb.sql(q3b).fetchall():
        print(row)
