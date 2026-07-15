import duckdb
from collections import defaultdict

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"

def q(sql):
    return duckdb.sql(sql).fetchall()

# 1. Proper decade counts
print("=== DECADE COUNTS (proper) ===")
rows = q(f"""
SELECT (publication_year//10)*10 AS decade, COUNT(*) AS n
FROM read_parquet('{P}') GROUP BY 1 ORDER BY 1
""")
for r in rows:
    print(f"{int(r[0])}s\t{r[1]}")

# 2. Type mix by proper decade since 1900
print("=== TYPE MIX BY DECADE (proper, pct) ===")
rows = q(f"""
WITH t6 AS (
  SELECT type FROM read_parquet('{P}') WHERE publication_year>=1900
  GROUP BY 1 ORDER BY COUNT(*) DESC LIMIT 6
)
SELECT (publication_year//10)*10 AS dec,
  CASE WHEN type IN (SELECT type FROM t6) THEN type ELSE 'other*' END AS ty,
  COUNT(*) AS n
FROM read_parquet('{P}') WHERE publication_year >= 1900
GROUP BY 1,2 ORDER BY 1,3 DESC
""")
dec_tot = defaultdict(int)
for r in rows:
    dec_tot[int(r[0])] += r[2]
cur = None
for r in rows:
    dec = int(r[0])
    if dec != cur:
        print(f"-- {dec}s (total {dec_tot[dec]})")
        cur = dec
    print(f"   {r[1]}: {r[2]} ({100*r[2]/dec_tot[dec]:.1f}%)")

# 3. Author count by proper decade
print("=== AUTHOR COUNT BY DECADE (proper) ===")
rows = q(f"""
SELECT (publication_year//10)*10 AS dec,
  ROUND(AVG(author_count),3), MEDIAN(author_count), COUNT(*)
FROM read_parquet('{P}')
WHERE publication_year >= 1900 AND author_count IS NOT NULL AND author_count > 0
GROUP BY 1 ORDER BY 1
""")
for r in rows:
    print(f"{int(r[0])}s\tavg={r[1]}\tmed={r[2]}\tn={r[3]}")

# 4. Zero-cited share by proper 5y bucket
print("=== ZERO-CITED SHARE BY PROPER 5Y BUCKET ===")
rows = q(f"""
SELECT (publication_year//5)*5 AS b, COUNT(*) AS n,
  SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END) AS z
FROM read_parquet('{P}') WHERE publication_year >= 1980
GROUP BY 1 ORDER BY 1
""")
for r in rows:
    print(f"{int(r[0])}-{int(r[0])+4}\tn={r[1]}\tzero={r[2]} ({100*r[2]/r[1]:.2f}%)")

# 5. Type-by-year 2014-2025 to explain the 2016 peak / 2021-22 dip / 2023 rebound
print("=== TYPE BY YEAR 2014-2025 ===")
rows = q(f"""
SELECT publication_year, type, COUNT(*) FROM read_parquet('{P}')
WHERE publication_year BETWEEN 2014 AND 2025
  AND type IN ('article','book-chapter','paratext','preprint','dissertation','book','dataset')
GROUP BY 1,2 ORDER BY 1,3 DESC
""")
cur = None
for r in rows:
    if r[0] != cur:
        print(f"-- {r[0]}")
        cur = r[0]
    print(f"   {r[1]}: {r[2]}")

# 6. 1969-1972 type counts (explain 1971 dip)
print("=== TYPE BY YEAR 1969-1972 ===")
rows = q(f"""
SELECT publication_year, type, COUNT(*) FROM read_parquet('{P}')
WHERE publication_year BETWEEN 1969 AND 1972
GROUP BY 1,2 HAVING COUNT(*) > 100 ORDER BY 1,3 DESC
""")
for r in rows:
    print(f"{r[0]}\t{r[1]}\t{r[2]}")

# 6b. top journals 1970 vs 1971 to find source of dip
print("=== TOP JOURNALS 1970 vs 1971 ===")
rows = q(f"""
SELECT publication_year, COALESCE(journal,'(null)'), COUNT(*) AS n
FROM read_parquet('{P}') WHERE publication_year IN (1970,1971)
GROUP BY 1,2 QUALIFY ROW_NUMBER() OVER (PARTITION BY publication_year ORDER BY n DESC) <= 8
ORDER BY 1, n DESC
""")
for r in rows:
    print(f"{r[0]}\t{r[1][:60]}\t{r[2]}")

# 7. 2008-2009 author-count spike: avg by type
print("=== 2007-2010 AVG AUTHOR COUNT BY TYPE (n>1000) ===")
rows = q(f"""
SELECT publication_year, type, ROUND(AVG(author_count),2), COUNT(*)
FROM read_parquet('{P}')
WHERE publication_year BETWEEN 2007 AND 2010 AND author_count > 0
GROUP BY 1,2 HAVING COUNT(*) > 1000 ORDER BY 1,3 DESC
""")
for r in rows:
    print(f"{r[0]}\t{r[1]}\tavg={r[2]}\tn={r[3]}")

# 8. Pre-1800: type mix and 1727 spike detail
print("=== PRE-1800 TYPE MIX ===")
rows = q(f"""
SELECT type, COUNT(*) FROM read_parquet('{P}')
WHERE publication_year < 1800 GROUP BY 1 ORDER BY 2 DESC
""")
for r in rows:
    print(f"{r[0]}\t{r[1]}")

print("=== 1727 SPIKE: journals/titles ===")
rows = q(f"""
SELECT COALESCE(journal,'(null)'), COUNT(*) FROM read_parquet('{P}')
WHERE publication_year = 1727 GROUP BY 1 ORDER BY 2 DESC LIMIT 5
""")
for r in rows:
    print(f"{r[0]}\t{r[1]}")
rows = q(f"""
SELECT LEFT(title,90) FROM read_parquet('{P}') WHERE publication_year = 1727 LIMIT 6
""")
for r in rows:
    print(f"  T: {r[0]}")

# 9. Diverse 1700s sample (excluding OUP eBooks)
print("=== 1700s SAMPLE excl OUP eBooks ===")
rows = q(f"""
SELECT publication_year, LEFT(title,100), COALESCE(journal,'(null)')
FROM read_parquet('{P}')
WHERE publication_year BETWEEN 1700 AND 1799
  AND (journal IS NULL OR journal <> 'Oxford University Press eBooks')
USING SAMPLE 8 ROWS
""")
for r in rows:
    print(f"{r[0]} | {r[1]} | J: {r[2]}")

# 10. Pre-1900 counts by 50y (proper)
print("=== PRE-1900 BY 50Y (proper) ===")
rows = q(f"""
SELECT (publication_year//50)*50, COUNT(*) FROM read_parquet('{P}')
WHERE publication_year < 1900 GROUP BY 1 ORDER BY 1
""")
for r in rows:
    print(f"{int(r[0])}-{int(r[0])+49}\t{r[1]}")

# 11. WWI/WWII trough-to-peak stats
print("=== WAR ERA EXTREMA ===")
rows = q(f"""
SELECT publication_year, COUNT(*) FROM read_parquet('{P}')
WHERE publication_year IN (1913,1918,1938,1944,1946)
GROUP BY 1 ORDER BY 1
""")
for r in rows:
    print(f"{r[0]}\t{r[1]}")
