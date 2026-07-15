import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"
con = duckdb.connect()
N = 8646207

def q(sql):
    return con.sql(sql).df()

print("=== ENGLISH SHARE BY PROPER DECADE SINCE 1900 ===")
print(q(f"""
SELECT (publication_year//10)*10 AS decade,
       COUNT(*) AS n,
       ROUND(100.0*SUM(CASE WHEN language='en' THEN 1 ELSE 0 END)/COUNT(*),2) AS en_pct,
       ROUND(100.0*SUM(CASE WHEN language IS NOT NULL AND language!='en' THEN 1 ELSE 0 END)/COUNT(*),2) AS nonen_pct,
       ROUND(100.0*SUM(CASE WHEN language IS NULL THEN 1 ELSE 0 END)/COUNT(*),2) AS null_pct
FROM read_parquet('{P}')
WHERE publication_year>=1900
GROUP BY 1 ORDER BY 1
""").to_string(index=False))

print("\n=== ABSTRACT COVERAGE BY PROPER DECADE SINCE 1950 ===")
print(q(f"""
SELECT (publication_year//10)*10 AS decade, COUNT(*) AS n,
       ROUND(100.0*SUM(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN 1 ELSE 0 END)/COUNT(*),2) AS abs_pct
FROM read_parquet('{P}')
WHERE publication_year>=1950
GROUP BY 1 ORDER BY 1
""").to_string(index=False))

print("\n=== 2016 NON-ENGLISH SPIKE: top languages 2015-2017 ===")
print(q(f"""
SELECT publication_year, language, COUNT(*) AS n
FROM read_parquet('{P}')
WHERE publication_year IN (2015,2016,2017) AND language IS NOT NULL AND language!='en'
GROUP BY 1,2
QUALIFY ROW_NUMBER() OVER (PARTITION BY publication_year ORDER BY n DESC) <= 6
ORDER BY publication_year, n DESC
""").to_string(index=False))

print("\n=== TYPE OF 'Editorial Board' TITLED WORKS ===")
print(q(f"""
SELECT type, COUNT(*) AS n
FROM read_parquet('{P}')
WHERE title ILIKE '%editorial board%'
GROUP BY 1 ORDER BY n DESC LIMIT 8
""").to_string(index=False))

print("\n=== PARATEXT vs FURNITURE OVERLAP ===")
print(q(f"""
SELECT
  SUM(CASE WHEN type='paratext' THEN 1 ELSE 0 END) AS paratext_n,
  SUM(CASE WHEN furn THEN 1 ELSE 0 END) AS furn_n,
  SUM(CASE WHEN type='paratext' AND furn THEN 1 ELSE 0 END) AS both_n,
  SUM(CASE WHEN type!='paratext' AND furn THEN 1 ELSE 0 END) AS furn_not_paratext
FROM (
  SELECT type,
    (title ILIKE 'book review%' OR title ILIKE 'front matter%' OR title ILIKE 'back matter%'
     OR title ILIKE '%editorial board%' OR title ILIKE 'index%' OR title ILIKE 'erratum%'
     OR title ILIKE 'corrigendum%') AS furn
  FROM read_parquet('{P}')
)
""").to_string(index=False))

print("\n=== EXTENDED FURNITURE (incl. ToC, Issue Info, etc.) ===")
print(q(f"""
SELECT COUNT(*) AS n, ROUND(100.0*COUNT(*)/{N},3) AS pct
FROM read_parquet('{P}')
WHERE title ILIKE 'book review%' OR title ILIKE 'front matter%' OR title ILIKE 'back matter%'
   OR title ILIKE '%editorial board%' OR title ILIKE 'index%' OR title ILIKE 'erratum%'
   OR title ILIKE 'corrigendum%' OR title ILIKE 'table of contents%' OR title ILIKE 'titelei%'
   OR title ILIKE 'issue information%' OR title ILIKE 'acknowledgment%' OR title ILIKE 'acknowledgement%'
   OR title ILIKE 'list of contributors%' OR title ILIKE 'list of illustrations%'
   OR title ILIKE 'list of abbreviations%' OR title ILIKE 'inside front cover%'
   OR title ILIKE 'inside back cover%' OR title ILIKE 'copyright%' OR title ILIKE 'masthead%'
   OR title ILIKE 'contents%' OR title ILIKE 'subject index%' OR title ILIKE 'author index%'
   OR type='paratext'
""").to_string(index=False))

print("\n=== 'index%' MATCHES: top titles (false positive check) ===")
print(q(f"""
SELECT title, COUNT(*) AS n
FROM read_parquet('{P}')
WHERE title ILIKE 'index%'
GROUP BY 1 ORDER BY n DESC LIMIT 12
""").to_string(index=False))
print(q(f"""
SELECT
 SUM(CASE WHEN LOWER(TRIM(title))='index' THEN 1 ELSE 0 END) AS exact_index,
 SUM(CASE WHEN title ILIKE 'index of%' OR title ILIKE 'index to%' OR LOWER(TRIM(title))='index' OR title ILIKE 'indexes%' OR title ILIKE 'index.%' THEN 1 ELSE 0 END) AS furniture_like
FROM read_parquet('{P}') WHERE title ILIKE 'index%'
""").to_string(index=False))

print("\n=== NULL LANGUAGE BY RECENT YEAR (2020-2025) ===")
print(q(f"""
SELECT publication_year, COUNT(*) AS n,
       ROUND(100.0*SUM(CASE WHEN language IS NULL THEN 1 ELSE 0 END)/COUNT(*),2) AS null_lang_pct,
       ROUND(100.0*SUM(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN 1 ELSE 0 END)/COUNT(*),2) AS abs_pct
FROM read_parquet('{P}')
WHERE publication_year>=2020
GROUP BY 1 ORDER BY 1
""").to_string(index=False))
