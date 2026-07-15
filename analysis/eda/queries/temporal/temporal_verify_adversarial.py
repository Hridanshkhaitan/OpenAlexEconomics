import duckdb

P = "read_parquet('/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet')"

def run(i, sql):
    try:
        rows = duckdb.sql(sql).fetchall()
        print(f"=== CLAIM {i} ===")
        for r in rows:
            print(r)
    except Exception as e:
        print(f"=== CLAIM {i} ERROR: {e}")
    print()

# Claim 1
run(1, f"SELECT publication_year, COUNT(*) AS n FROM {P} GROUP BY publication_year ORDER BY n DESC LIMIT 3")

# Claim 2
run(2, f"SELECT ROUND(100*(POWER(SUM(CASE WHEN publication_year=2019 THEN 1 ELSE 0 END)*1.0/SUM(CASE WHEN publication_year=1950 THEN 1 ELSE 0 END), 1.0/69)-1),3) AS cagr_1950_2019_pct, ROUND(100*(POWER(SUM(CASE WHEN publication_year=2019 THEN 1 ELSE 0 END)*1.0/SUM(CASE WHEN publication_year=2000 THEN 1 ELSE 0 END), 1.0/19)-1),3) AS cagr_2000_2019_pct FROM {P}")
run("2-ctx", f"SELECT publication_year, COUNT(*) n FROM {P} WHERE publication_year IN (1950,2000,2019) GROUP BY 1 ORDER BY 1")

# Claim 3
run(3, f"SELECT ROUND(100.0*SUM(CASE WHEN publication_year>=1990 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_ge_1990, ROUND(100.0*SUM(CASE WHEN publication_year>=2000 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_ge_2000, ROUND(100.0*SUM(CASE WHEN publication_year>=2010 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_ge_2010 FROM {P}")

# Claim 4
run(4, f"SELECT publication_year, COUNT(*) AS n, SUM(CASE WHEN type='book-chapter' THEN 1 ELSE 0 END) AS chapters FROM {P} WHERE publication_year BETWEEN 2019 AND 2025 GROUP BY publication_year ORDER BY publication_year")

# Claim 5
run(5, f"SELECT publication_year, COUNT(*) AS n FROM {P} WHERE publication_year IN (1913,1918,1938,1944) GROUP BY publication_year ORDER BY publication_year")

# Claim 6
run(6, f"SELECT (publication_year//10)*10 AS decade, ROUND(AVG(author_count),3) AS avg_authors, MEDIAN(author_count) AS med_authors FROM {P} WHERE publication_year>=1900 AND author_count>0 GROUP BY 1 ORDER BY 1")

# Claim 7
run(7, f"SELECT (publication_year//5)*5 AS bucket, COUNT(*) AS n, ROUND(100.0*SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero_cited FROM {P} WHERE publication_year>=1980 GROUP BY 1 ORDER BY 1")
run("7-median", f"SELECT publication_year, MEDIAN(cited_by_count) AS med FROM {P} WHERE publication_year BETWEEN 1980 AND 2025 GROUP BY publication_year HAVING MEDIAN(cited_by_count) <> 0 ORDER BY publication_year")

# Claim 8
run(8, f"SELECT COALESCE(journal,'(null)') AS journal, COUNT(*) AS n FROM {P} WHERE publication_year < 1800 GROUP BY 1 ORDER BY n DESC LIMIT 3")
run("8-ctx", f"SELECT COUNT(*) AS total_pre1800, SUM(CASE WHEN type='book-chapter' THEN 1 ELSE 0 END) AS bc, ROUND(100.0*SUM(CASE WHEN type='book-chapter' THEN 1 ELSE 0 END)/COUNT(*),2) AS bc_pct FROM {P} WHERE publication_year<1800")
run("8-nq", f"SELECT COUNT(*) AS total_19c, SUM(CASE WHEN journal='Notes and Queries' THEN 1 ELSE 0 END) AS nq, ROUND(100.0*SUM(CASE WHEN journal='Notes and Queries' THEN 1 ELSE 0 END)/COUNT(*),2) AS nq_pct FROM {P} WHERE publication_year BETWEEN 1800 AND 1899")
