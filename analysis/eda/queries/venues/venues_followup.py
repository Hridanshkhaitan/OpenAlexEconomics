import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"
con = duckdb.connect()
def q(sql): return con.sql(sql).fetchall()

# A. Known name-variant candidates: "The X" vs "X"
cands = [
  'American Economic Review', 'Quarterly Journal of Economics', 'Journal of Finance',
  'Review of Economics and Statistics', 'Economic Journal', 'Journal of Political Economy',
  'Review of Economic Studies', 'Journal of Economic Literature', 'Journal of Economic Perspectives',
  'Economic History Review', 'Journal of Economic History'
]
print("== 'The X' vs 'X' variant counts ==")
for c in cands:
    r = q(f"""
    SELECT journal, count(*) FROM read_parquet('{P}')
    WHERE journal IN ('{c}', 'The {c}')
    GROUP BY 1 ORDER BY 1
    """)
    print(c, "->", r)

# JAMA variants
r = q(f"""
SELECT journal, count(*) FROM read_parquet('{P}')
WHERE journal IN ('JAMA','Journal of the American Medical Association','JAMA Network Open')
GROUP BY 1 ORDER BY 2 DESC
""")
print("== JAMA variants ==", r)

# B. Substring pairs among top-200 journals
r = q(f"""
WITH top200 AS (
  SELECT journal, count(*) AS n
  FROM read_parquet('{P}')
  WHERE journal IS NOT NULL
  GROUP BY 1 ORDER BY n DESC LIMIT 200
)
SELECT a.journal, a.n, b.journal, b.n
FROM top200 a JOIN top200 b
  ON a.journal <> b.journal
 AND len(a.journal) < len(b.journal)
 AND position(lower(a.journal) IN lower(b.journal)) > 0
ORDER BY a.n DESC
""")
print("== substring pairs among top-200 (shorter contained in longer) ==")
for row in r: print(row)

# C. Chase surprise: Medical Entomology and Zoology
r = q(f"""
SELECT min(publication_year), max(publication_year), count(*),
       round(avg(cited_by_count),2)
FROM read_parquet('{P}') WHERE journal = 'Medical Entomology and Zoology'
""")
print("== Medical Entomology and Zoology: yr range, n, avg cites ==", r)
r = q(f"""
SELECT primary_topic, subfield, count(*) AS n
FROM read_parquet('{P}') WHERE journal = 'Medical Entomology and Zoology'
GROUP BY 1,2 ORDER BY n DESC LIMIT 5
""")
print("== MEZ top primary_topics ==")
for row in r: print(row)
r = q(f"""
SELECT language, count(*) FROM read_parquet('{P}')
WHERE journal = 'Medical Entomology and Zoology' GROUP BY 1 ORDER BY 2 DESC LIMIT 3
""")
print("== MEZ languages ==", r)
r = q(f"""
SELECT title FROM read_parquet('{P}')
WHERE journal = 'Medical Entomology and Zoology' AND title IS NOT NULL LIMIT 5
""")
print("== MEZ sample titles ==")
for row in r: print(row[0][:100])

# D. Chase 'Time to knit' and 'Warfare in North America'
for j in ['Time to knit', 'Warfare in North America, c. 1756-1815', 'Notes and Queries']:
    r = q(f"""
    SELECT min(publication_year), max(publication_year), count(*), count(DISTINCT type),
           arg_max(type, cnt) FROM (
      SELECT publication_year, type, count(*) OVER (PARTITION BY type) AS cnt
      FROM read_parquet('{P}') WHERE journal = '{j}'
    )
    """)
    print(f"== {j}: yr range, n, ntypes, modal type ==", r)
    r2 = q(f"""
    SELECT primary_topic, count(*) FROM read_parquet('{P}')
    WHERE journal = '{j}' GROUP BY 1 ORDER BY 2 DESC LIMIT 3
    """)
    print("   topics:", r2)
    r3 = q(f"""
    SELECT title FROM read_parquet('{P}') WHERE journal='{j}' AND title IS NOT NULL LIMIT 3
    """)
    for row in r3: print("   title:", (row[0] or '')[:90])

# E. medical/science journal presence quantification (misclassification signal)
r = q(f"""
SELECT count(*) FROM read_parquet('{P}')
WHERE journal IN ('PubMed','BMJ','JAMA','The Lancet','Science','Nature',
 'New England Journal of Medicine','Journal of the American Medical Association',
 'The Journal of Urology','AJN American Journal of Nursing','Value in Health',
 'Medical Entomology and Zoology','Scientific American')
""")
print("== works in 13 clearly non-econ medical/science venues in top-100 ==", r)
