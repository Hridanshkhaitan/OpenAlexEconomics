import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"

def q(sql):
    return duckdb.sql(sql).fetchall()

print("=== A. author_count exact split, 2000-2015 (fixing the 0-author lump) ===")
sql = f"""
SELECT CASE WHEN author_count = 0 THEN '0_missing'
            WHEN author_count = 1 THEN '1_solo'
            WHEN author_count <= 3 THEN '2-3'
            ELSE '4plus' END AS grp,
       COUNT(*) AS n,
       ROUND(AVG(cited_by_count),2) AS mean_cites,
       median(cited_by_count) AS med_cites,
       ROUND(100.0*SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero_cites
FROM read_parquet('{P}')
WHERE publication_year BETWEEN 2000 AND 2015
GROUP BY 1 ORDER BY 1
"""
for r in q(sql):
    print(r)

print("=== A2. what types are the 0-author works (2000-2015)? top 8 ===")
sql = f"""
SELECT type, COUNT(*) AS n
FROM read_parquet('{P}')
WHERE publication_year BETWEEN 2000 AND 2015 AND author_count = 0
GROUP BY 1 ORDER BY n DESC LIMIT 8
"""
for r in q(sql):
    print(r)

print("=== B. zero-citation and zero-reference share by type (all years, top 12 types) ===")
sql = f"""
SELECT type, COUNT(*) AS n,
       ROUND(100.0*SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero_cites,
       ROUND(100.0*SUM(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero_refs,
       ROUND(AVG(cited_by_count),2) AS mean_cites,
       ROUND(AVG(referenced_works_count),2) AS mean_refs
FROM read_parquet('{P}')
GROUP BY 1 ORDER BY n DESC LIMIT 12
"""
for r in q(sql):
    print(r)

print("=== C. articles only: zero-ref share by decade since 1950 + mean refs when >0 ===")
sql = f"""
SELECT (publication_year/10)::INT*10 AS decade, COUNT(*) AS n,
       ROUND(100.0*SUM(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero_refs,
       ROUND(AVG(CASE WHEN referenced_works_count>0 THEN referenced_works_count END),2) AS mean_refs_nonzero
FROM read_parquet('{P}')
WHERE publication_year >= 1950 AND type = 'article'
GROUP BY 1 ORDER BY 1
"""
for r in q(sql):
    print(r)

print("=== D. duplicate check: North 'Institutions, Institutional Change' variants ===")
sql = f"""
SELECT id, publication_year, type, journal, cited_by_count, LEFT(title,70)
FROM read_parquet('{P}')
WHERE title ILIKE 'Institutions, Institutional Change%'
ORDER BY cited_by_count DESC LIMIT 6
"""
for r in q(sql):
    print(r)

print("=== E. overall refs conditional on nonzero; and share of works that are articles ===")
sql = f"""
SELECT ROUND(AVG(CASE WHEN referenced_works_count>0 THEN referenced_works_count END),2) AS mean_refs_nonzero,
       median(CASE WHEN referenced_works_count>0 THEN referenced_works_count END) AS med_refs_nonzero
FROM read_parquet('{P}')
"""
print(q(sql))

print("=== F. zero-cite share for mature ARTICLES (<=2015) as robustness ===")
sql = f"""
SELECT COUNT(*) AS n,
       ROUND(100.0*SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero
FROM read_parquet('{P}')
WHERE publication_year <= 2015 AND type = 'article'
"""
print(q(sql))
