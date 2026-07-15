import duckdb

P = "read_parquet('/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet')"

# Claim 1: subfield split
print("=== CLAIM 1: subfield split ===")
q1 = f"""SELECT subfield, COUNT(*) n, ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),2) pct
FROM {P} GROUP BY 1 ORDER BY n DESC"""
for r in duckdb.sql(q1).fetchall():
    print(r)

# Claim 2: distinct primary_topics
print("=== CLAIM 2: distinct primary_topics ===")
q2 = f"SELECT COUNT(DISTINCT primary_topic) AS n_topics FROM {P}"
print(duckdb.sql(q2).fetchall())

# Claim 3: catch-all topic
print("=== CLAIM 3: top topic ===")
q3 = f"""SELECT primary_topic, COUNT(*) n,
ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM {P}),2) pct
FROM {P} GROUP BY 1 ORDER BY n DESC LIMIT 1"""
print(duckdb.sql(q3).fetchall())

# Claim 4: Finance decade shares
print("=== CLAIM 4: finance decade shares ===")
q4 = f"""SELECT (publication_year/10)::INT*10 AS decade,
ROUND(100.0*COUNT(*) FILTER (WHERE subfield='Finance')/COUNT(*),2) fin_pct
FROM {P} WHERE publication_year>=1950 GROUP BY 1 ORDER BY 1"""
for r in duckdb.sql(q4).fetchall():
    print(r)

# Claim 5: suspect venues
print("=== CLAIM 5: suspect venues ===")
q5 = f"""SELECT COUNT(*) n, ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM {P}),2) pct
FROM {P} WHERE journal IS NOT NULL AND (journal ILIKE '%cancer%' OR journal ILIKE '%medic%' OR journal ILIKE '%health%' OR journal ILIKE '%surg%' OR journal ILIKE '%energy%' OR journal ILIKE '%tourism%' OR journal ILIKE '%environment%' OR journal ILIKE '%nurs%' OR journal ILIKE '%clinic%' OR journal ILIKE '%oncol%' OR journal ILIKE '%epidemi%' OR journal ILIKE '%hospital%' OR journal ILIKE '%disease%' OR journal ILIKE '%pediatr%' OR journal ILIKE '%psychiatr%' OR journal ILIKE '%pharma%' OR journal ILIKE '%veterinar%' OR journal ILIKE '%agricult%' OR journal ILIKE '%sustainab%')"""
print(duckdb.sql(q5).fetchall())

# Claim 6: Medical Entomology and Zoology
print("=== CLAIM 6: Medical Entomology and Zoology ===")
q6 = f"""SELECT journal, COUNT(*) n FROM {P} WHERE journal='Medical Entomology and Zoology' GROUP BY 1"""
print(duckdb.sql(q6).fetchall())

# Claim 7: clinical topics
print("=== CLAIM 7: clinical primary_topics ===")
q7 = f"""SELECT COUNT(*) n, ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM {P}),2) pct
FROM {P} WHERE primary_topic IN ('Healthcare Policy and Management','Health Systems, Economic Evaluations, Quality of Life','Economic and Financial Impacts of Cancer','Pharmaceutical Economics and Policy','Healthcare Systems and Reforms','HIV/AIDS Impact and Responses','COVID-19 Pandemic Impacts')"""
print(duckdb.sql(q7).fetchall())

# Claim 8: combined leakage
print("=== CLAIM 8: combined leakage ===")
q8 = f"""SELECT COUNT(*) n, ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM {P}),2) pct
FROM {P} WHERE (journal IS NOT NULL AND (journal ILIKE '%cancer%' OR journal ILIKE '%medic%' OR journal ILIKE '%health%' OR journal ILIKE '%surg%' OR journal ILIKE '%energy%' OR journal ILIKE '%tourism%' OR journal ILIKE '%environment%' OR journal ILIKE '%nurs%' OR journal ILIKE '%clinic%' OR journal ILIKE '%oncol%' OR journal ILIKE '%epidemi%' OR journal ILIKE '%hospital%' OR journal ILIKE '%disease%' OR journal ILIKE '%pediatr%' OR journal ILIKE '%psychiatr%' OR journal ILIKE '%pharma%' OR journal ILIKE '%veterinar%' OR journal ILIKE '%agricult%' OR journal ILIKE '%sustainab%')) OR primary_topic IN ('Healthcare Policy and Management','Health Systems, Economic Evaluations, Quality of Life','Economic and Financial Impacts of Cancer','Pharmaceutical Economics and Policy','Healthcare Systems and Reforms','HIV/AIDS Impact and Responses','COVID-19 Pandemic Impacts')"""
print(duckdb.sql(q8).fetchall())

print("=== DONE ===")
