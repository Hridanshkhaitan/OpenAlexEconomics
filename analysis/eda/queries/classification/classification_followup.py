import duckdb
P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"
con = duckdb.connect()
def q(sql): return con.sql(sql).df()

# SURPRISE 1: the catch-all "Diverse Scientific and Economic Studies" (25% of corpus)
print("=== TOP JOURNALS IN 'Diverse Scientific and Economic Studies' ===")
df = q(f"""
SELECT journal, COUNT(*) n
FROM read_parquet('{P}')
WHERE primary_topic='Diverse Scientific and Economic Studies'
GROUP BY 1 ORDER BY n DESC LIMIT 20
""")
print(df.to_string(index=False))

print("\n=== NULL-journal share within that catch-all topic ===")
df = q(f"""
SELECT COUNT(*) FILTER (WHERE journal IS NULL) n_null, COUNT(*) tot,
 ROUND(100.0*COUNT(*) FILTER (WHERE journal IS NULL)/COUNT(*),1) pct_null
FROM read_parquet('{P}') WHERE primary_topic='Diverse Scientific and Economic Studies'
""")
print(df.to_string(index=False))

print("\n=== 8 sample titles in catch-all topic (highest cited) ===")
df = q(f"""
SELECT title, journal, publication_year FROM read_parquet('{P}')
WHERE primary_topic='Diverse Scientific and Economic Studies' AND title IS NOT NULL
ORDER BY cited_by_count DESC LIMIT 8
""")
print(df.to_string(index=False))

# SURPRISE 2: Medical Entomology and Zoology - 47k works
print("\n=== 'Medical Entomology and Zoology' journal: topic breakdown ===")
df = q(f"""
SELECT primary_topic, subfield, COUNT(*) n, MIN(publication_year) mn, MAX(publication_year) mx
FROM read_parquet('{P}') WHERE journal='Medical Entomology and Zoology'
GROUP BY 1,2 ORDER BY n DESC LIMIT 5
""")
print(df.to_string(index=False))
df = q(f"""
SELECT title, publication_year FROM read_parquet('{P}')
WHERE journal='Medical Entomology and Zoology' ORDER BY cited_by_count DESC LIMIT 4
""")
print(df.to_string(index=False))

# TOPIC-BASED LEAKAGE ESTIMATE: sum of clearly health/medical topics
print("\n=== CLEARLY HEALTH/MEDICAL TOPICS (topic-based leakage) ===")
HEALTH_TOPICS = """primary_topic IN (
 'Healthcare Policy and Management','Health Systems, Economic Evaluations, Quality of Life',
 'Economic and Financial Impacts of Cancer','Pharmaceutical Economics and Policy',
 'Healthcare Systems and Reforms','HIV/AIDS Impact and Responses','COVID-19 Pandemic Impacts',
 'Global Health and Disease Prevention','Mental Health and Well-being','Health disparities and outcomes')"""
df = q(f"""
SELECT primary_topic, subfield, COUNT(*) n, ROUND(100.0*COUNT(*)/8646207,2) pct
FROM read_parquet('{P}') WHERE {HEALTH_TOPICS}
GROUP BY 1,2 ORDER BY n DESC
""")
print(df.to_string(index=False))
df = q(f"SELECT COUNT(*) n, ROUND(100.0*COUNT(*)/8646207,2) pct FROM read_parquet('{P}') WHERE {HEALTH_TOPICS}")
print("HEALTH TOPIC TOTAL:", df.to_string(index=False))

# Straddle topics quantified (from top 30): media, cultural, area-studies
print("\n=== STRADDLE / NON-CORE-ECON TOPICS in top 30 ===")
df = q(f"""
SELECT primary_topic, COUNT(*) n, ROUND(100.0*COUNT(*)/8646207,2) pct
FROM read_parquet('{P}')
WHERE primary_topic IN ('Cinema and Media Studies','Diverse academic and cultural studies',
 'Balkan and Eastern European Studies','Historical and socio-economic studies of Spain and related regions',
 'Regional Development and Management Studies','Climate Change Policy and Economics')
GROUP BY 1 ORDER BY n DESC
""")
print(df.to_string(index=False))

# Combined leakage estimate: suspect venues OR clearly-health topics OR catch-all-with-suspect
print("\n=== COMBINED CONSERVATIVE LEAKAGE: suspect venue OR clear-health topic ===")
SUSPECT = """(journal ILIKE '%cancer%' OR journal ILIKE '%medic%' OR journal ILIKE '%health%'
 OR journal ILIKE '%surg%' OR journal ILIKE '%energy%' OR journal ILIKE '%tourism%'
 OR journal ILIKE '%environment%' OR journal ILIKE '%nurs%' OR journal ILIKE '%clinic%'
 OR journal ILIKE '%oncol%' OR journal ILIKE '%epidemi%' OR journal ILIKE '%hospital%'
 OR journal ILIKE '%disease%' OR journal ILIKE '%pediatr%' OR journal ILIKE '%psychiatr%'
 OR journal ILIKE '%pharma%' OR journal ILIKE '%veterinar%' OR journal ILIKE '%agricult%'
 OR journal ILIKE '%sustainab%')"""
df = q(f"""
SELECT COUNT(*) n, ROUND(100.0*COUNT(*)/8646207,2) pct FROM read_parquet('{P}')
WHERE ({SUSPECT}) OR {HEALTH_TOPICS}
""")
print(df.to_string(index=False))
