import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"

# Proper decade NULL-journal rates (integer floor to decade), show 1900s-2020s
q_dec = f"""
SELECT CAST(floor(publication_year/10.0)*10 AS INT) AS decade,
       count(*) AS n,
       round(100.0*sum(CASE WHEN journal IS NULL THEN 1 ELSE 0 END)/count(*),2) AS pct_null
FROM read_parquet('{P}')
WHERE publication_year >= 1900
GROUP BY 1 ORDER BY 1
"""
print("Decade null rates 1900+:")
for r in duckdb.sql(q_dec).fetchall():
    print(r)

# 2013 specifically and nearby years
q_yr = f"""
SELECT publication_year, count(*) AS n,
       round(100.0*sum(CASE WHEN journal IS NULL THEN 1 ELSE 0 END)/count(*),1) AS pct_null
FROM read_parquet('{P}')
WHERE publication_year BETWEEN 2005 AND 2025
GROUP BY 1 ORDER BY 1
"""
print("Yearly null rates 2005-2025:")
for r in duckdb.sql(q_yr).fetchall():
    print(r)

# Claim 8 example pair counts
q_pairs = f"""
SELECT journal, count(*) AS n
FROM read_parquet('{P}')
WHERE journal IN ('The World Bank eBooks','World Bank eBooks','The Journal of Law and Economics','Journal of Law and Economics')
GROUP BY journal ORDER BY journal
"""
print("Claim 8 example pairs:", duckdb.sql(q_pairs).fetchall())
