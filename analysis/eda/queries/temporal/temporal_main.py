import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"

def q(sql):
    return duckdb.sql(sql).fetchall()

# 1. Works per decade (full)
print("=== DECADE COUNTS ===")
rows = q(f"""
SELECT (publication_year/10)*10 AS decade, COUNT(*) AS n
FROM read_parquet('{P}') GROUP BY 1 ORDER BY 1
""")
for r in rows:
    print(f"{int(r[0])}s\t{r[1]}")

# 2. Annual counts for notable eras
print("=== ANNUAL COUNTS: eras ===")
rows = q(f"""
SELECT publication_year, COUNT(*) FROM read_parquet('{P}')
WHERE publication_year BETWEEN 1910 AND 1925
   OR publication_year BETWEEN 1935 AND 1950
   OR publication_year BETWEEN 1965 AND 1975
   OR publication_year BETWEEN 2010 AND 2025
GROUP BY 1 ORDER BY 1
""")
for r in rows:
    print(f"{r[0]}\t{r[1]}")

# 3. CAGR anchor years + peak year
print("=== CAGR ANCHORS ===")
rows = q(f"""
SELECT publication_year, COUNT(*) FROM read_parquet('{P}')
WHERE publication_year IN (1950, 2000, 2019)
GROUP BY 1 ORDER BY 1
""")
d = {r[0]: r[1] for r in rows}
print(d)
c1950, c2000, c2019 = d[1950], d[2000], d[2019]
print(f"CAGR 1950-2019: {((c2019/c1950)**(1/69)-1)*100:.3f}%")
print(f"CAGR 2000-2019: {((c2019/c2000)**(1/19)-1)*100:.3f}%")

print("=== PEAK YEAR (top 8) ===")
rows = q(f"""
SELECT publication_year, COUNT(*) AS n FROM read_parquet('{P}')
GROUP BY 1 ORDER BY n DESC LIMIT 8
""")
for r in rows:
    print(f"{r[0]}\t{r[1]}")

# 4. Non-monotonic dips: year-over-year declines since 1900
print("=== YoY DECLINES since 1900 ===")
rows = q(f"""
WITH a AS (SELECT publication_year y, COUNT(*) n FROM read_parquet('{P}')
           WHERE publication_year >= 1900 GROUP BY 1)
SELECT y, n, n - LAG(n) OVER (ORDER BY y) AS delta,
       ROUND(100.0*(n - LAG(n) OVER (ORDER BY y))/LAG(n) OVER (ORDER BY y),2) AS pct
FROM a QUALIFY delta < 0 ORDER BY y
""")
for r in rows:
    print(f"{r[0]}\tn={r[1]}\tdelta={r[2]}\t{r[3]}%")

# 5. Shares of corpus
print("=== SHARES ===")
rows = q(f"""
SELECT COUNT(*) AS total,
  SUM(CASE WHEN publication_year>=1990 THEN 1 ELSE 0 END) AS ge1990,
  SUM(CASE WHEN publication_year>=2000 THEN 1 ELSE 0 END) AS ge2000,
  SUM(CASE WHEN publication_year>=2010 THEN 1 ELSE 0 END) AS ge2010
FROM read_parquet('{P}')
""")
t, a, b, c = rows[0]
print(f"total={t} >=1990={a} ({100*a/t:.2f}%) >=2000={b} ({100*b/t:.2f}%) >=2010={c} ({100*c/t:.2f}%)")

# 6. Type mix by decade since 1900 (top 6 types overall)
print("=== TOP TYPES OVERALL (since 1900) ===")
rows = q(f"""
SELECT type, COUNT(*) FROM read_parquet('{P}')
WHERE publication_year >= 1900 GROUP BY 1 ORDER BY 2 DESC LIMIT 10
""")
for r in rows:
    print(f"{r[0]}\t{r[1]}")

print("=== TYPE MIX BY DECADE (pct) ===")
rows = q(f"""
WITH t6 AS (
  SELECT type FROM read_parquet('{P}') WHERE publication_year>=1900
  GROUP BY 1 ORDER BY COUNT(*) DESC LIMIT 6
)
SELECT (publication_year/10)*10 AS dec,
  CASE WHEN type IN (SELECT type FROM t6) THEN type ELSE 'other' END AS ty,
  COUNT(*) AS n
FROM read_parquet('{P}') WHERE publication_year >= 1900
GROUP BY 1,2 ORDER BY 1,3 DESC
""")
from collections import defaultdict
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

# 7. Author count by decade since 1900
print("=== AUTHOR COUNT BY DECADE ===")
rows = q(f"""
SELECT (publication_year/10)*10 AS dec,
  ROUND(AVG(author_count),3), MEDIAN(author_count), COUNT(*)
FROM read_parquet('{P}')
WHERE publication_year >= 1900 AND author_count IS NOT NULL AND author_count > 0
GROUP BY 1 ORDER BY 1
""")
for r in rows:
    print(f"{int(r[0])}s\tavg={r[1]}\tmed={r[2]}\tn={r[3]}")

# 8. Citation aging curve 1980-2025
print("=== AVG CITED_BY_COUNT BY YEAR 1980-2025 ===")
rows = q(f"""
SELECT publication_year, ROUND(AVG(cited_by_count),2), MEDIAN(cited_by_count), COUNT(*)
FROM read_parquet('{P}') WHERE publication_year BETWEEN 1980 AND 2025
GROUP BY 1 ORDER BY 1
""")
for r in rows:
    print(f"{r[0]}\tavg={r[1]}\tmed={r[2]}\tn={r[3]}")

# 9. Zero-cited share by 5-year bucket since 1980
print("=== ZERO-CITED SHARE BY 5Y BUCKET ===")
rows = q(f"""
SELECT (publication_year/5)*5 AS b, COUNT(*) AS n,
  SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END) AS z
FROM read_parquet('{P}') WHERE publication_year >= 1980
GROUP BY 1 ORDER BY 1
""")
for r in rows:
    print(f"{int(r[0])}-{int(r[0])+4}\tn={r[1]}\tzero={r[2]} ({100*r[2]/r[1]:.2f}%)")

# 10. Pre-1900 characterization
print("=== PRE-1900 COUNTS BY 50Y ===")
rows = q(f"""
SELECT (publication_year/50)*50, COUNT(*) FROM read_parquet('{P}')
WHERE publication_year < 1900 GROUP BY 1 ORDER BY 1
""")
for r in rows:
    print(f"{int(r[0])}\t{r[1]}")

print("=== SAMPLE 1647 TITLES ===")
rows = q(f"""
SELECT publication_year, LEFT(title, 110), journal FROM read_parquet('{P}')
WHERE publication_year = 1647 LIMIT 5
""")
for r in rows:
    print(f"{r[0]} | {r[1]} | J: {r[2]}")

print("=== SAMPLE 1700s TITLES ===")
rows = q(f"""
SELECT publication_year, LEFT(title, 110), journal FROM read_parquet('{P}')
WHERE publication_year BETWEEN 1700 AND 1799
USING SAMPLE 5 ROWS
""")
for r in rows:
    print(f"{r[0]} | {r[1]} | J: {r[2]}")

print("=== PRE-1800 TOP JOURNALS ===")
rows = q(f"""
SELECT COALESCE(journal,'(null)') AS j, COUNT(*) FROM read_parquet('{P}')
WHERE publication_year < 1800 GROUP BY 1 ORDER BY 2 DESC LIMIT 10
""")
for r in rows:
    print(f"{r[0]}\t{r[1]}")

print("=== 1800-1899 TOP JOURNALS ===")
rows = q(f"""
SELECT COALESCE(journal,'(null)') AS j, COUNT(*) FROM read_parquet('{P}')
WHERE publication_year BETWEEN 1800 AND 1899 GROUP BY 1 ORDER BY 2 DESC LIMIT 8
""")
for r in rows:
    print(f"{r[0]}\t{r[1]}")
