import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"

def q(sql):
    return duckdb.sql(sql).fetchall()

print("=== 1. cited_by_count distribution: overall and 2000+ ===")
sql = f"""
SELECT 'overall' AS grp, COUNT(*) AS n, AVG(cited_by_count) AS mean,
       median(cited_by_count) AS med,
       quantile_cont(cited_by_count, 0.75) AS p75,
       quantile_cont(cited_by_count, 0.90) AS p90,
       quantile_cont(cited_by_count, 0.99) AS p99,
       MAX(cited_by_count) AS mx
FROM read_parquet('{P}')
UNION ALL
SELECT '2000plus', COUNT(*), AVG(cited_by_count), median(cited_by_count),
       quantile_cont(cited_by_count, 0.75), quantile_cont(cited_by_count, 0.90),
       quantile_cont(cited_by_count, 0.99), MAX(cited_by_count)
FROM read_parquet('{P}') WHERE publication_year >= 2000
"""
for r in q(sql):
    print(r)

print("=== 2. zero-citation share: overall and <=2015 ===")
sql = f"""
SELECT 'overall' AS grp, COUNT(*) AS n,
       SUM(CASE WHEN cited_by_count = 0 THEN 1 ELSE 0 END) AS zeros,
       ROUND(100.0*SUM(CASE WHEN cited_by_count = 0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero
FROM read_parquet('{P}')
UNION ALL
SELECT 'le2015', COUNT(*),
       SUM(CASE WHEN cited_by_count = 0 THEN 1 ELSE 0 END),
       ROUND(100.0*SUM(CASE WHEN cited_by_count = 0 THEN 1 ELSE 0 END)/COUNT(*),2)
FROM read_parquet('{P}') WHERE publication_year <= 2015
"""
for r in q(sql):
    print(r)

print("=== 3. concentration: top 1% and top 0.1% share of all citations ===")
sql = f"""
WITH ranked AS (
  SELECT cited_by_count,
         ROW_NUMBER() OVER (ORDER BY cited_by_count DESC) AS rk,
         COUNT(*) OVER () AS n,
         SUM(cited_by_count) OVER () AS total
  FROM read_parquet('{P}')
)
SELECT
  MAX(total) AS total_citations,
  MAX(n) AS n_works,
  SUM(CASE WHEN rk <= n*0.01 THEN cited_by_count ELSE 0 END) AS top1_cites,
  ROUND(100.0*SUM(CASE WHEN rk <= n*0.01 THEN cited_by_count ELSE 0 END)/MAX(total),2) AS top1_pct,
  SUM(CASE WHEN rk <= n*0.001 THEN cited_by_count ELSE 0 END) AS top01_cites,
  ROUND(100.0*SUM(CASE WHEN rk <= n*0.001 THEN cited_by_count ELSE 0 END)/MAX(total),2) AS top01_pct
FROM ranked
"""
for r in q(sql):
    print(r)

print("=== 4. top 15 most cited works ===")
sql = f"""
SELECT cited_by_count, publication_year, COALESCE(journal,'<none>') AS journal,
       COALESCE(primary_topic,'<none>') AS topic, LEFT(title, 90) AS title
FROM read_parquet('{P}')
ORDER BY cited_by_count DESC LIMIT 15
"""
for r in q(sql):
    print(r)

print("=== 5. counts >= 10000 and >= 1000 ===")
sql = f"""
SELECT SUM(CASE WHEN cited_by_count >= 10000 THEN 1 ELSE 0 END) AS ge10k,
       SUM(CASE WHEN cited_by_count >= 1000 THEN 1 ELSE 0 END) AS ge1k
FROM read_parquet('{P}')
"""
print(q(sql))

print("=== 6. referenced_works_count: overall ===")
sql = f"""
SELECT COUNT(*) AS n, AVG(referenced_works_count) AS mean,
       median(referenced_works_count) AS med,
       ROUND(100.0*SUM(CASE WHEN referenced_works_count = 0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero
FROM read_parquet('{P}')
"""
print(q(sql))

print("=== 6b. referenced_works_count by decade since 1950 ===")
sql = f"""
SELECT (publication_year/10)::INT*10 AS decade, COUNT(*) AS n,
       ROUND(AVG(referenced_works_count),2) AS mean,
       median(referenced_works_count) AS med,
       ROUND(100.0*SUM(CASE WHEN referenced_works_count = 0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero
FROM read_parquet('{P}')
WHERE publication_year >= 1950
GROUP BY 1 ORDER BY 1
"""
for r in q(sql):
    print(r)

print("=== 7. author_count vs citations, 2000-2015 ===")
sql = f"""
SELECT CASE WHEN author_count <= 1 THEN '1_solo'
            WHEN author_count <= 3 THEN '2-3'
            ELSE '4plus' END AS grp,
       COUNT(*) AS n,
       ROUND(AVG(cited_by_count),2) AS mean_cites,
       median(cited_by_count) AS med_cites,
       ROUND(100.0*SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero
FROM read_parquet('{P}')
WHERE publication_year BETWEEN 2000 AND 2015
GROUP BY 1 ORDER BY 1
"""
for r in q(sql):
    print(r)

print("=== extra: author_count anomalies (0 or null) 2000-2015 ===")
sql = f"""
SELECT SUM(CASE WHEN author_count IS NULL THEN 1 ELSE 0 END) AS null_ac,
       SUM(CASE WHEN author_count = 0 THEN 1 ELSE 0 END) AS zero_ac
FROM read_parquet('{P}') WHERE publication_year BETWEEN 2000 AND 2015
"""
print(q(sql))
