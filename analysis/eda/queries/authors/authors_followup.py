import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"

def q(sql):
    return duckdb.sql(sql).fetchall()

print("=== A. author_count == 100 exactly (cap?) and 90-100 tail ===")
r = q(f"""
SELECT count(*) FILTER (author_count = 100) AS n_100,
       count(*) FILTER (author_count BETWEEN 90 AND 99) AS n_90_99,
       count(*) FILTER (author_count BETWEEN 51 AND 89) AS n_51_89
FROM read_parquet('{P}')
""")
print(r)

print("=== A2. largest teams, type='article' only ===")
r = q(f"""
SELECT author_count, left(title,80), publication_year, journal
FROM read_parquet('{P}')
WHERE type = 'article'
ORDER BY author_count DESC LIMIT 5
""")
for row in r: print(row)

print("=== B. modern zero-author works: top journals post-2000 ===")
r = q(f"""
SELECT journal, count(*) AS n
FROM read_parquet('{P}')
WHERE author_count = 0 AND publication_year >= 2000
GROUP BY 1 ORDER BY n DESC LIMIT 10
""")
for row in r: print(row)

print("=== B2. modern zero-author examples (articles post-2010) ===")
r = q(f"""
SELECT left(title,70), publication_year, journal, type
FROM read_parquet('{P}')
WHERE author_count = 0 AND publication_year >= 2010 AND type='article'
USING SAMPLE 5 ROWS (reservoir, 42)
""")
for row in r: print(row)

print("=== C. Carey Hand Funeral Home works ===")
r = q(f"""
SELECT min(publication_year), max(publication_year),
       arg_max(type, cnt) FROM (
  SELECT publication_year, type, count(*) AS cnt
  FROM read_parquet('{P}')
  WHERE first_author = 'Carey Hand Funeral Home'
  GROUP BY 1,2)
""")
print(r)
r = q(f"""
SELECT left(title,80), publication_year, journal, type, primary_topic
FROM read_parquet('{P}')
WHERE first_author = 'Carey Hand Funeral Home' LIMIT 3
""")
for row in r: print(row)

print("=== C2. Master, Daniel M. works ===")
r = q(f"""
SELECT left(title,80), publication_year, journal, type, primary_topic
FROM read_parquet('{P}')
WHERE first_author = 'Master, Daniel M.' LIMIT 3
""")
for row in r: print(row)
r = q(f"""
SELECT min(publication_year), max(publication_year), count(DISTINCT journal)
FROM read_parquet('{P}') WHERE first_author = 'Master, Daniel M.'
""")
print(r)

print("=== C3. :unav works ===")
r = q(f"""
SELECT type, count(*) FROM read_parquet('{P}')
WHERE first_author = ':unav' GROUP BY 1 ORDER BY 2 DESC LIMIT 5
""")
for row in r: print(row)
r = q(f"""
SELECT min(publication_year), median(publication_year), max(publication_year)
FROM read_parquet('{P}') WHERE first_author = ':unav'
""")
print(r)

print("=== D. comma-share U-shape: what drives 2020s rebound? top comma first_authors 2020s ===")
r = q(f"""
SELECT journal, count(*) AS n
FROM read_parquet('{P}')
WHERE publication_year >= 2020 AND first_author LIKE '%,%'
GROUP BY 1 ORDER BY n DESC LIMIT 8
""")
for row in r: print(row)

print("=== D2. comma share 2020s excluding SSRN/RePEc/preprint repositories ===")
r = q(f"""
SELECT
  round(100.0*count(*) FILTER (first_author LIKE '%,%')/count(*),2) AS pct_comma_articles_only
FROM read_parquet('{P}')
WHERE publication_year >= 2020 AND type='article'
  AND first_author IS NOT NULL AND trim(first_author) <> ''
""")
print(r)

print("=== E. zero-author share by decade (are they inflating recent decades?) ===")
r = q(f"""
SELECT (publication_year/10)::INT*10 AS decade,
  count(*) AS n,
  round(100.0*count(*) FILTER (author_count=0)/count(*),2) AS pct_zero
FROM read_parquet('{P}')
WHERE publication_year >= 1900
GROUP BY 1 ORDER BY 1
""")
for row in r: print(row)

print("=== F. solo share by decade among works WITH authors (ac>=1) ===")
r = q(f"""
SELECT (publication_year/10)::INT*10 AS decade,
  round(100.0*count(*) FILTER (author_count=1)/count(*),2) AS pct_solo_of_authored
FROM read_parquet('{P}')
WHERE publication_year >= 1900 AND author_count >= 1
GROUP BY 1 ORDER BY 1
""")
for row in r: print(row)
