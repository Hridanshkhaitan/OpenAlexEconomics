import duckdb

P = "read_parquet('/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet')"

# Corrected regex: single backslash so DuckDB/RE2 sees \s+
sql5 = r"""
SELECT
  SUM(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN 1 ELSE 0 END) AS with_abs,
  ROUND(100.0*SUM(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN 1 ELSE 0 END)/COUNT(*),2) AS abs_pct,
  ROUND(AVG(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN array_length(string_split_regex(TRIM(abstract),'\s+')) END),1) AS avg_abs_words,
  ROUND(MEDIAN(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN array_length(string_split_regex(TRIM(abstract),'\s+')) END),1) AS median_abs_words
FROM """ + P
print("CLAIM 5 corrected:")
print(duckdb.sql(sql5).fetchall())

# Decade coverage sub-claim: 29.6% 1960s -> 54.6% 2020s monotonic
sql5b = f"""
SELECT (publication_year//10)*10 AS decade,
  ROUND(100.0*SUM(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN 1 ELSE 0 END)/COUNT(*),2) AS abs_pct
FROM {P}
WHERE publication_year BETWEEN 1960 AND 2029
GROUP BY 1 ORDER BY 1
"""
print("\nDecade abstract coverage:")
for r in duckdb.sql(sql5b).fetchall():
    print(r)
