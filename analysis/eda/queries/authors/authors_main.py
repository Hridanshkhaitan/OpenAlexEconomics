import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"

def q(sql):
    return duckdb.sql(sql).fetchall()

print("=== 1. author_count distribution ===")
r = q(f"""
SELECT
  count(*) AS n,
  median(author_count) AS med,
  round(avg(author_count),3) AS mean,
  quantile_cont(author_count, 0.95) AS p95,
  quantile_cont(author_count, 0.99) AS p99,
  max(author_count) AS mx,
  count(*) FILTER (author_count IS NULL) AS n_null
FROM read_parquet('{P}')
""")
print(r)

print("=== 1b. buckets ===")
r = q(f"""
SELECT
  CASE
    WHEN author_count IS NULL THEN 'NULL'
    WHEN author_count = 0 THEN '0'
    WHEN author_count = 1 THEN '1'
    WHEN author_count = 2 THEN '2'
    WHEN author_count BETWEEN 3 AND 5 THEN '3-5'
    WHEN author_count BETWEEN 6 AND 10 THEN '6-10'
    WHEN author_count BETWEEN 11 AND 50 THEN '11-50'
    ELSE '>50'
  END AS bucket,
  count(*) AS n
FROM read_parquet('{P}')
GROUP BY 1 ORDER BY 1
""")
for row in r: print(row)

print("=== 2. author_count = 0 ===")
r = q(f"""
SELECT count(*), round(100.0*count(*)/8646207, 3)
FROM read_parquet('{P}') WHERE author_count = 0
""")
print(r)
print("-- examples --")
r = q(f"""
SELECT title, publication_year, journal, type
FROM read_parquet('{P}')
WHERE author_count = 0
ORDER BY publication_year
LIMIT 5
""")
for row in r: print(row)
print("-- zero-author year distribution summary --")
r = q(f"""
SELECT min(publication_year), median(publication_year), max(publication_year),
       count(*) FILTER (publication_year < 1950) AS pre1950,
       count(*) FILTER (publication_year >= 2000) AS post2000
FROM read_parquet('{P}') WHERE author_count = 0
""")
print(r)
print("-- zero-author by type top 8 --")
r = q(f"""
SELECT type, count(*) AS n FROM read_parquet('{P}')
WHERE author_count = 0 GROUP BY 1 ORDER BY n DESC LIMIT 8
""")
for row in r: print(row)

print("=== 3. solo share by decade since 1900 ===")
r = q(f"""
SELECT (publication_year/10)::INT*10 AS decade,
  count(*) AS n_total,
  count(*) FILTER (author_count = 1) AS n_solo,
  round(100.0*count(*) FILTER (author_count = 1)/count(*) ,2) AS pct_solo,
  round(avg(author_count) FILTER (author_count >= 1),3) AS mean_ac_nonzero
FROM read_parquet('{P}')
WHERE publication_year >= 1900
GROUP BY 1 ORDER BY 1
""")
for row in r: print(row)

print("=== 4. largest teams top 5 ===")
r = q(f"""
SELECT author_count, left(title, 90) AS title, publication_year, journal
FROM read_parquet('{P}')
ORDER BY author_count DESC NULLS LAST
LIMIT 5
""")
for row in r: print(row)

print("=== 5. first_author comma format by decade since 1950 ===")
r = q(f"""
SELECT (publication_year/10)::INT*10 AS decade,
  count(*) FILTER (first_author IS NOT NULL AND trim(first_author) <> '') AS n_named,
  round(100.0*count(*) FILTER (first_author LIKE '%,%') /
    nullif(count(*) FILTER (first_author IS NOT NULL AND trim(first_author) <> ''),0), 2) AS pct_comma
FROM read_parquet('{P}')
WHERE publication_year >= 1950
GROUP BY 1 ORDER BY 1
""")
for row in r: print(row)

print("-- overall comma share (all years, non-null non-empty) --")
r = q(f"""
SELECT count(*) AS n_named,
  count(*) FILTER (first_author LIKE '%,%') AS n_comma,
  round(100.0*count(*) FILTER (first_author LIKE '%,%')/count(*),2) AS pct_comma
FROM read_parquet('{P}')
WHERE first_author IS NOT NULL AND trim(first_author) <> ''
""")
print(r)

print("=== 6. top 15 first_author values ===")
r = q(f"""
SELECT first_author, count(*) AS n
FROM read_parquet('{P}')
WHERE first_author IS NOT NULL AND trim(first_author) <> ''
GROUP BY 1 ORDER BY n DESC LIMIT 15
""")
for row in r: print(row)

print("=== 7. first_author NULL/empty but author_count > 0 ===")
r = q(f"""
SELECT
  count(*) FILTER (first_author IS NULL) AS fa_null,
  count(*) FILTER (first_author IS NOT NULL AND trim(first_author) = '') AS fa_empty,
  count(*) FILTER ((first_author IS NULL OR trim(first_author)='') AND author_count > 0) AS null_but_ac_pos,
  round(100.0*count(*) FILTER ((first_author IS NULL OR trim(first_author)='') AND author_count > 0)/8646207,3) AS pct_of_all
FROM read_parquet('{P}')
""")
print(r)
