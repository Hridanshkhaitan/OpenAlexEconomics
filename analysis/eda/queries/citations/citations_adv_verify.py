import duckdb

P = "read_parquet('/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet')"

def run(i, sql):
    try:
        res = duckdb.sql(sql)
        cols = [d[0] for d in res.description]
        rows = res.fetchall()
        print(f"=== CLAIM {i} ===")
        print("COLS:", cols)
        for r in rows:
            print(r)
    except Exception as e:
        print(f"=== CLAIM {i} ERROR ===")
        print(repr(e))
    print()

# Claim 1
run(1, f"SELECT COUNT(*) AS n, SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END) AS zeros, ROUND(100.0*SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero, median(cited_by_count) AS med FROM {P}")

# Claim 2
run(2, f"WITH ranked AS (SELECT cited_by_count, ROW_NUMBER() OVER (ORDER BY cited_by_count DESC) AS rk, COUNT(*) OVER () AS n, SUM(cited_by_count) OVER () AS total FROM {P}) SELECT ROUND(100.0*SUM(CASE WHEN rk <= n*0.01 THEN cited_by_count ELSE 0 END)/MAX(total),2) AS top1_pct, ROUND(100.0*SUM(CASE WHEN rk <= n*0.001 THEN cited_by_count ELSE 0 END)/MAX(total),2) AS top01_pct FROM ranked")

# Claim 3
run(3, f"SELECT COUNT(*) AS n, AVG(cited_by_count) AS mean, median(cited_by_count) AS med, quantile_cont(cited_by_count,0.75) AS p75, quantile_cont(cited_by_count,0.90) AS p90, quantile_cont(cited_by_count,0.99) AS p99, MAX(cited_by_count) AS mx FROM {P}")
run("3b_total", f"SELECT SUM(cited_by_count) AS total_cites FROM {P}")
run("3c_maxwork", f"SELECT cited_by_count, publication_year, LEFT(title,60) AS title, first_author FROM {P} ORDER BY cited_by_count DESC LIMIT 1")

# Claim 4
run(4, f"SELECT COUNT(*) AS n, ROUND(100.0*SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero FROM {P} WHERE publication_year <= 2015")
run("4b_matureart", f"SELECT COUNT(*) AS n, ROUND(100.0*SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero FROM {P} WHERE publication_year <= 2015 AND type='article'")

# Claim 5
run(5, f"SELECT SUM(CASE WHEN cited_by_count >= 10000 THEN 1 ELSE 0 END) AS ge10k, SUM(CASE WHEN cited_by_count >= 1000 THEN 1 ELSE 0 END) AS ge1k FROM {P}")
run("5b_pct", f"SELECT ROUND(100.0*SUM(CASE WHEN cited_by_count >= 1000 THEN 1 ELSE 0 END)/COUNT(*),4) AS pct_ge1k FROM {P}")

# Claim 6
run(6, f"SELECT COUNT(*) AS n, AVG(referenced_works_count) AS mean, median(referenced_works_count) AS med, ROUND(100.0*SUM(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero FROM {P}")
run("6b_2020art", f"SELECT ROUND(100.0*SUM(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero FROM {P} WHERE publication_year >= 2020 AND type='article'")
run("6c_nonzero", f"SELECT ROUND(AVG(referenced_works_count),2) AS mean_nonzero FROM {P} WHERE referenced_works_count > 0")

# Claim 7
run(7, f"SELECT CASE WHEN author_count = 0 THEN '0_missing' WHEN author_count = 1 THEN '1_solo' WHEN author_count <= 3 THEN '2-3' ELSE '4plus' END AS grp, COUNT(*) AS n, ROUND(AVG(cited_by_count),2) AS mean_cites FROM {P} WHERE publication_year BETWEEN 2000 AND 2015 GROUP BY 1 ORDER BY 1")

# Claim 8
run(8, f"SELECT cited_by_count, publication_year, journal, LEFT(title,90) AS title FROM {P} ORDER BY cited_by_count DESC LIMIT 15")
