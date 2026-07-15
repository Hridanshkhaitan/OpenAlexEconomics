import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"

sqls = {
1: "SELECT COUNT(*) AS n, SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END) AS zeros, ROUND(100.0*SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero, median(cited_by_count) AS med FROM read_parquet('%s')" % P,
2: "WITH ranked AS (SELECT cited_by_count, ROW_NUMBER() OVER (ORDER BY cited_by_count DESC) AS rk, COUNT(*) OVER () AS n, SUM(cited_by_count) OVER () AS total FROM read_parquet('%s')) SELECT ROUND(100.0*SUM(CASE WHEN rk <= n*0.01 THEN cited_by_count ELSE 0 END)/MAX(total),2) AS top1_pct, ROUND(100.0*SUM(CASE WHEN rk <= n*0.001 THEN cited_by_count ELSE 0 END)/MAX(total),2) AS top01_pct, MAX(total) AS total_cites FROM ranked" % P,
3: "SELECT COUNT(*) AS n, AVG(cited_by_count) AS mean, median(cited_by_count) AS med, quantile_cont(cited_by_count,0.75) AS p75, quantile_cont(cited_by_count,0.90) AS p90, quantile_cont(cited_by_count,0.99) AS p99, MAX(cited_by_count) AS mx FROM read_parquet('%s')" % P,
4: "SELECT COUNT(*) AS n, ROUND(100.0*SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero FROM read_parquet('%s') WHERE publication_year <= 2015" % P,
5: "SELECT SUM(CASE WHEN cited_by_count >= 10000 THEN 1 ELSE 0 END) AS ge10k, SUM(CASE WHEN cited_by_count >= 1000 THEN 1 ELSE 0 END) AS ge1k FROM read_parquet('%s')" % P,
6: "SELECT COUNT(*) AS n, AVG(referenced_works_count) AS mean, median(referenced_works_count) AS med, ROUND(100.0*SUM(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero FROM read_parquet('%s')" % P,
7: "SELECT CASE WHEN author_count = 0 THEN '0_missing' WHEN author_count = 1 THEN '1_solo' WHEN author_count <= 3 THEN '2-3' ELSE '4plus' END AS grp, COUNT(*) AS n, ROUND(AVG(cited_by_count),2) AS mean_cites FROM read_parquet('%s') WHERE publication_year BETWEEN 2000 AND 2015 GROUP BY 1 ORDER BY 1" % P,
8: "SELECT cited_by_count, publication_year, journal, LEFT(title,90) AS title FROM read_parquet('%s') ORDER BY cited_by_count DESC LIMIT 15" % P,
}

for i in sorted(sqls):
    print("=== CLAIM %d ===" % i)
    try:
        df = duckdb.sql(sqls[i]).df()
        print(df.to_string(index=False))
    except Exception as e:
        print("ERROR:", repr(e))
    print()

# Extra checks for sub-parts of claims
extras = {
"4b_mature_journal_articles_pct_zero": "SELECT ROUND(100.0*SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero FROM read_parquet('%s') WHERE publication_year <= 2015 AND type='article' AND journal IS NOT NULL" % P,
"5b_ge1k_pct": "SELECT ROUND(100.0*SUM(CASE WHEN cited_by_count >= 1000 THEN 1 ELSE 0 END)/COUNT(*),4) AS pct_ge1k FROM read_parquet('%s')" % P,
"6b_2020s_articles_zero_refs": "SELECT ROUND(100.0*SUM(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero, COUNT(*) AS n FROM read_parquet('%s') WHERE publication_year >= 2020 AND type='article'" % P,
"6c_mean_refs_nonzero": "SELECT ROUND(AVG(referenced_works_count),2) AS mean_refs FROM read_parquet('%s') WHERE referenced_works_count > 0" % P,
}
for k in sorted(extras):
    print("=== EXTRA %s ===" % k)
    try:
        df = duckdb.sql(extras[k]).df()
        print(df.to_string(index=False))
    except Exception as e:
        print("ERROR:", repr(e))
    print()
