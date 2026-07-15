import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"
con = duckdb.connect()

def q(sql):
    return con.sql(sql).df()

print("=== TOTAL ===")
tot = q(f"SELECT COUNT(*) AS n FROM read_parquet('{P}')")
N = int(tot.n[0])
print(N)

print("\n=== LANGUAGE TOP 15 + NULL ===")
print(q(f"""
SELECT COALESCE(language,'<NULL>') AS lang, COUNT(*) AS n,
       ROUND(100.0*COUNT(*)/{N},3) AS pct
FROM read_parquet('{P}')
GROUP BY 1 ORDER BY n DESC LIMIT 16
""").to_string(index=False))

print("\n=== ENGLISH SHARE BY DECADE SINCE 1900 ===")
print(q(f"""
SELECT (publication_year/10)*10 AS decade,
       COUNT(*) AS n,
       ROUND(100.0*SUM(CASE WHEN language='en' THEN 1 ELSE 0 END)/COUNT(*),2) AS en_pct,
       ROUND(100.0*SUM(CASE WHEN language IS NOT NULL AND language!='en' THEN 1 ELSE 0 END)/COUNT(*),2) AS nonen_pct,
       ROUND(100.0*SUM(CASE WHEN language IS NULL THEN 1 ELSE 0 END)/COUNT(*),2) AS null_pct
FROM read_parquet('{P}')
WHERE publication_year>=1900
GROUP BY 1 ORDER BY 1
""").to_string(index=False))

print("\n=== TYPE DISTRIBUTION (ALL) ===")
print(q(f"""
SELECT COALESCE(type,'<NULL>') AS type, COUNT(*) AS n,
       ROUND(100.0*COUNT(*)/{N},3) AS pct
FROM read_parquet('{P}')
GROUP BY 1 ORDER BY n DESC
""").to_string(index=False))

print("\n=== TITLE AUDIT ===")
print(q(f"""
SELECT
  SUM(CASE WHEN title IS NULL THEN 1 ELSE 0 END) AS null_titles,
  SUM(CASE WHEN title IS NOT NULL AND TRIM(title)='' THEN 1 ELSE 0 END) AS empty_titles,
  ROUND(AVG(CASE WHEN title IS NOT NULL AND TRIM(title)!='' THEN array_length(string_split_regex(TRIM(title),'\\s+')) END),2) AS avg_title_words,
  MEDIAN(CASE WHEN title IS NOT NULL AND TRIM(title)!='' THEN array_length(string_split_regex(TRIM(title),'\\s+')) END) AS med_title_words
FROM read_parquet('{P}')
""").to_string(index=False))

print("\n=== TOP 10 DUPLICATE TITLES ===")
print(q(f"""
SELECT title, COUNT(*) AS n
FROM read_parquet('{P}')
WHERE title IS NOT NULL AND TRIM(title)!=''
GROUP BY title ORDER BY n DESC LIMIT 10
""").to_string(index=False))

print("\n=== JOURNAL FURNITURE PATTERNS ===")
pats = ['book review%','front matter%','back matter%','%editorial board%','index%','erratum%','corrigendum%']
for p in pats:
    r = q(f"SELECT COUNT(*) AS n FROM read_parquet('{P}') WHERE title ILIKE '{p}'")
    n = int(r.n[0])
    print(f"{p!r}: {n}  ({100.0*n/N:.3f}%)")
r = q(f"""
SELECT COUNT(*) AS n FROM read_parquet('{P}')
WHERE title ILIKE 'book review%' OR title ILIKE 'front matter%' OR title ILIKE 'back matter%'
   OR title ILIKE '%editorial board%' OR title ILIKE 'index%' OR title ILIKE 'erratum%'
   OR title ILIKE 'corrigendum%'
""")
n = int(r.n[0])
print(f"COMBINED (any pattern): {n}  ({100.0*n/N:.3f}%)")

print("\n=== ABSTRACT AUDIT: OVERALL ===")
print(q(f"""
SELECT
  SUM(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN 1 ELSE 0 END) AS with_abs,
  ROUND(100.0*SUM(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN 1 ELSE 0 END)/COUNT(*),2) AS abs_pct,
  ROUND(AVG(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN array_length(string_split_regex(TRIM(abstract),'\\s+')) END),1) AS avg_abs_words,
  MEDIAN(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN array_length(string_split_regex(TRIM(abstract),'\\s+')) END) AS med_abs_words
FROM read_parquet('{P}')
""").to_string(index=False))

print("\n=== ABSTRACT COVERAGE BY DECADE SINCE 1950 ===")
print(q(f"""
SELECT (publication_year/10)*10 AS decade, COUNT(*) AS n,
       ROUND(100.0*SUM(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN 1 ELSE 0 END)/COUNT(*),2) AS abs_pct
FROM read_parquet('{P}')
WHERE publication_year>=1950
GROUP BY 1 ORDER BY 1
""").to_string(index=False))

print("\n=== TOP 10 JOURNALS BY SIZE + ABSTRACT COVERAGE ===")
print(q(f"""
SELECT journal, COUNT(*) AS n,
       ROUND(100.0*SUM(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN 1 ELSE 0 END)/COUNT(*),2) AS abs_pct
FROM read_parquet('{P}')
WHERE journal IS NOT NULL
GROUP BY 1 ORDER BY n DESC LIMIT 10
""").to_string(index=False))

print("\n=== NAMED JOURNALS ABSTRACT COVERAGE ===")
named = ['American Economic Review','Econometrica','The Journal of Finance','Economics Letters',
         'Journal of Banking & Finance','The Quarterly Journal of Economics','Energy Economics',
         'World Development','Applied Economics','Journal of Econometrics','The Economic Journal',
         'Journal of Political Economy']
lst = ",".join("'"+x.replace("'","''")+"'" for x in named)
print(q(f"""
SELECT journal, COUNT(*) AS n,
       ROUND(100.0*SUM(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN 1 ELSE 0 END)/COUNT(*),2) AS abs_pct
FROM read_parquet('{P}')
WHERE journal IN ({lst})
GROUP BY 1 ORDER BY n DESC
""").to_string(index=False))
