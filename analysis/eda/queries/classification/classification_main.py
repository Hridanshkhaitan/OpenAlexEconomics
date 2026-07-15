import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"

con = duckdb.connect()

def q(sql):
    return con.sql(sql).df()

# 1) Subfield distribution
print("=== SUBFIELD DISTRIBUTION ===")
df = q(f"""
SELECT subfield, COUNT(*) n, ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),3) pct
FROM read_parquet('{P}')
GROUP BY 1 ORDER BY n DESC
""")
print(df.to_string(index=False))

# 2) Distinct topics + top 30 topics (need top 30 for straddle assessment, report top 20)
print("\n=== DISTINCT PRIMARY_TOPIC COUNT ===")
df = q(f"SELECT COUNT(DISTINCT primary_topic) n_topics, COUNT(*) n_rows FROM read_parquet('{P}')")
print(df.to_string(index=False))

print("\n=== TOP 30 TOPICS ===")
df = q(f"""
SELECT primary_topic, subfield, COUNT(*) n, ROUND(100.0*COUNT(*)/8646207,2) pct
FROM read_parquet('{P}')
GROUP BY 1,2 ORDER BY n DESC LIMIT 30
""")
print(df.to_string(index=False))

# 3) Subfield share by decade since 1950
print("\n=== SUBFIELD SHARE BY DECADE (>=1950) ===")
df = q(f"""
WITH d AS (
  SELECT (publication_year/10)::INT*10 AS decade, subfield, COUNT(*) n
  FROM read_parquet('{P}')
  WHERE publication_year >= 1950
  GROUP BY 1,2
)
SELECT decade, subfield, n, ROUND(100.0*n/SUM(n) OVER (PARTITION BY decade),2) pct
FROM d ORDER BY decade, n DESC
""")
print(df.to_string(index=False))

# 4) Misclassification probe: suspect journals
print("\n=== TOP 20 SUSPECT JOURNALS ===")
SUSPECT = """(journal ILIKE '%cancer%' OR journal ILIKE '%medic%' OR journal ILIKE '%health%'
 OR journal ILIKE '%surg%' OR journal ILIKE '%energy%' OR journal ILIKE '%tourism%'
 OR journal ILIKE '%environment%' OR journal ILIKE '%nurs%' OR journal ILIKE '%clinic%'
 OR journal ILIKE '%oncol%' OR journal ILIKE '%epidemi%' OR journal ILIKE '%hospital%'
 OR journal ILIKE '%disease%' OR journal ILIKE '%pediatr%' OR journal ILIKE '%psychiatr%'
 OR journal ILIKE '%pharma%' OR journal ILIKE '%veterinar%' OR journal ILIKE '%agricult%'
 OR journal ILIKE '%sustainab%')"""
df = q(f"""
SELECT journal, COUNT(*) n
FROM read_parquet('{P}')
WHERE journal IS NOT NULL AND {SUSPECT}
GROUP BY 1 ORDER BY n DESC LIMIT 20
""")
print(df.to_string(index=False))

# share of corpus in suspect venues
print("\n=== SUSPECT VENUE SHARE ===")
df = q(f"""
SELECT COUNT(*) n_suspect, ROUND(100.0*COUNT(*)/8646207,3) pct_of_corpus
FROM read_parquet('{P}')
WHERE journal IS NOT NULL AND {SUSPECT}
""")
print(df.to_string(index=False))

# narrower core-medical-only share (exclude energy/environment/sustain/agri/tourism which can be econ-adjacent)
print("\n=== MEDICAL-ONLY SUSPECT SHARE ===")
MED = """(journal ILIKE '%cancer%' OR journal ILIKE '%medic%' OR journal ILIKE '%health%'
 OR journal ILIKE '%surg%' OR journal ILIKE '%nurs%' OR journal ILIKE '%clinic%'
 OR journal ILIKE '%oncol%' OR journal ILIKE '%epidemi%' OR journal ILIKE '%hospital%'
 OR journal ILIKE '%disease%' OR journal ILIKE '%pediatr%' OR journal ILIKE '%psychiatr%'
 OR journal ILIKE '%pharma%' OR journal ILIKE '%veterinar%')"""
df = q(f"""
SELECT COUNT(*) n, ROUND(100.0*COUNT(*)/8646207,3) pct FROM read_parquet('{P}')
WHERE journal IS NOT NULL AND {MED}
""")
print(df.to_string(index=False))

# 5) Example clearly-non-econ works
print("\n=== EXAMPLE NON-ECON WORKS ===")
df = q(f"""
SELECT title, journal, publication_year, primary_topic, subfield, cited_by_count
FROM read_parquet('{P}')
WHERE journal IS NOT NULL
  AND (journal ILIKE '%cancer%' OR journal ILIKE '%surg%' OR journal ILIKE '%oncol%'
       OR journal ILIKE '%nurs%' OR journal ILIKE '%pediatr%')
ORDER BY cited_by_count DESC LIMIT 10
""")
print(df.to_string(index=False))

# what topics are the suspect-journal works assigned to?
print("\n=== TOP TOPICS WITHIN SUSPECT VENUES ===")
df = q(f"""
SELECT primary_topic, subfield, COUNT(*) n
FROM read_parquet('{P}')
WHERE journal IS NOT NULL AND {SUSPECT}
GROUP BY 1,2 ORDER BY n DESC LIMIT 15
""")
print(df.to_string(index=False))

# journal null share (context for venue-based filtering)
print("\n=== JOURNAL NULL SHARE ===")
df = q(f"""
SELECT COUNT(*) FILTER (WHERE journal IS NULL) n_null,
       ROUND(100.0*COUNT(*) FILTER (WHERE journal IS NULL)/COUNT(*),2) pct_null
FROM read_parquet('{P}')
""")
print(df.to_string(index=False))
