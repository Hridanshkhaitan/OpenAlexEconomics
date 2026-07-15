import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"
con = duckdb.connect()
def q(sql): return con.sql(sql).fetchall()

# Corpus-wide: journal names where BOTH 'X' and 'The X' exist (min 50 works each side)
r = q(f"""
WITH j AS (
  SELECT journal, count(*) AS n
  FROM read_parquet('{P}')
  WHERE journal IS NOT NULL
  GROUP BY 1
)
SELECT a.journal AS short_name, a.n AS n_short, b.journal AS the_name, b.n AS n_the
FROM j a JOIN j b ON b.journal = 'The ' || a.journal
WHERE a.n >= 50 AND b.n >= 50
ORDER BY (a.n + b.n) DESC
LIMIT 25
""")
print("== 'X' and 'The X' both exist (>=50 works each) ==")
for row in r: print(row)

# total count of such pairs (any size)
r = q(f"""
WITH j AS (
  SELECT journal, count(*) AS n
  FROM read_parquet('{P}')
  WHERE journal IS NOT NULL GROUP BY 1
)
SELECT count(*), sum(a.n + b.n)
FROM j a JOIN j b ON b.journal = 'The ' || a.journal
""")
print("== total 'X'/'The X' coexisting pairs (any size), works involved ==", r)

# case-insensitive duplicates: same lower(journal) but multiple distinct spellings
r = q(f"""
WITH j AS (
  SELECT journal, count(*) AS n
  FROM read_parquet('{P}')
  WHERE journal IS NOT NULL GROUP BY 1
)
SELECT lower(journal) AS lj, count(*) AS n_variants, sum(n) AS works
FROM j GROUP BY 1 HAVING count(*) > 1
ORDER BY works DESC LIMIT 10
""")
print("== case-variant duplicate names (same lowercase, multiple spellings) ==")
for row in r: print(row)
