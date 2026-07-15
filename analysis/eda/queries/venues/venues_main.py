import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"
con = duckdb.connect()

def q(sql):
    return con.sql(sql).fetchall()

# 1. NULL journal overall
r = q(f"""
SELECT count(*) AS n,
       sum(CASE WHEN journal IS NULL THEN 1 ELSE 0 END) AS n_null,
       round(100.0*sum(CASE WHEN journal IS NULL THEN 1 ELSE 0 END)/count(*),2) AS pct_null
FROM read_parquet('{P}')
""")
print("== NULL journal overall ==")
print(r)

# 2. NULL journal by decade since 1900
r = q(f"""
SELECT (publication_year/10)*10 AS decade,
       count(*) AS n,
       sum(CASE WHEN journal IS NULL THEN 1 ELSE 0 END) AS n_null,
       round(100.0*sum(CASE WHEN journal IS NULL THEN 1 ELSE 0 END)/count(*),2) AS pct_null
FROM read_parquet('{P}')
WHERE publication_year >= 1900
GROUP BY 1 ORDER BY 1
""")
print("== NULL journal by decade (>=1900) ==")
for row in r: print(row)

# 3. distinct journal names
r = q(f"SELECT count(DISTINCT journal) FROM read_parquet('{P}') WHERE journal IS NOT NULL")
print("== distinct journal names ==", r)

# 4. top 25 journals by work count
r = q(f"""
SELECT journal, count(*) AS n,
       round(100.0*count(*)/8646207,3) AS pct_corpus
FROM read_parquet('{P}')
WHERE journal IS NOT NULL
GROUP BY 1 ORDER BY n DESC LIMIT 25
""")
print("== top 25 journals by work count ==")
for row in r: print(row)

# 5. top 10 journals by SUM citations
r = q(f"""
SELECT journal, sum(cited_by_count) AS total_cites, count(*) AS n_works
FROM read_parquet('{P}')
WHERE journal IS NOT NULL
GROUP BY 1 ORDER BY total_cites DESC LIMIT 10
""")
print("== top 10 journals by SUM cited_by_count ==")
for row in r: print(row)

# 6. concentration: share of all works in top 100 journals
r = q(f"""
WITH t AS (
  SELECT journal, count(*) AS n
  FROM read_parquet('{P}')
  WHERE journal IS NOT NULL
  GROUP BY 1 ORDER BY n DESC LIMIT 100
)
SELECT sum(n) AS works_top100,
       round(100.0*sum(n)/8646207,2) AS pct_of_corpus
FROM t
""")
print("== top-100 journal concentration ==", r)

# also share of non-null works
r = q(f"""
WITH nn AS (SELECT count(*) AS n_nonnull FROM read_parquet('{P}') WHERE journal IS NOT NULL),
t AS (
  SELECT journal, count(*) AS n
  FROM read_parquet('{P}')
  WHERE journal IS NOT NULL
  GROUP BY 1 ORDER BY n DESC LIMIT 100
)
SELECT sum(t.n), round(100.0*sum(t.n)/max(nn.n_nonnull),2) FROM t, nn
""")
print("== top-100 share of NON-NULL-journal works ==", r)

# 7. long tail: journals with exactly 1 work
r = q(f"""
WITH t AS (
  SELECT journal, count(*) AS n
  FROM read_parquet('{P}')
  WHERE journal IS NOT NULL
  GROUP BY 1
)
SELECT count(*) FROM t WHERE n = 1
""")
print("== journals with exactly 1 work ==", r)

# 8. venue-quality heuristic patterns
patterns = ['%ebook%','%repository%','%ssrn%','%working paper%','%proceedings%','%conference%','%thesis%','%dissertation%']
print("== pattern counts (works whose journal ILIKE pattern) ==")
for pat in patterns:
    r = q(f"""
    SELECT count(*), round(100.0*count(*)/8646207,3)
    FROM read_parquet('{P}')
    WHERE journal ILIKE '{pat}'
    """)
    print(pat, r)

# 9. top-100 journal list (for identifying non-peer-reviewed venues)
r = q(f"""
SELECT journal, count(*) AS n
FROM read_parquet('{P}')
WHERE journal IS NOT NULL
GROUP BY 1 ORDER BY n DESC LIMIT 100
""")
print("== top 100 journals ==")
for i,row in enumerate(r,1): print(i, row)
