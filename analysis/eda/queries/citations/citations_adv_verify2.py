import duckdb
P = "read_parquet('/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet')"

def run(i, sql):
    res = duckdb.sql(sql)
    cols = [d[0] for d in res.description]
    rows = res.fetchall()
    print(f"=== {i} ===")
    print("COLS:", cols)
    for r in rows:
        print(r)
    print()

# distinct types
run("types", f"SELECT type, COUNT(*) n FROM {P} WHERE publication_year>=2020 GROUP BY 1 ORDER BY 2 DESC LIMIT 12")

# variants for 2020s journal-article zero-refs
run("A year>=2020 type=article", f"SELECT ROUND(100.0*SUM(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) pct, COUNT(*) n FROM {P} WHERE publication_year>=2020 AND type='article'")
run("B year 2020-2029 type=article", f"SELECT ROUND(100.0*SUM(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) pct, COUNT(*) n FROM {P} WHERE publication_year BETWEEN 2020 AND 2029 AND type='article'")
run("C year>=2020 all types", f"SELECT ROUND(100.0*SUM(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) pct, COUNT(*) n FROM {P} WHERE publication_year>=2020")
run("D year>=2020 type=article AND journal NOT NULL", f"SELECT ROUND(100.0*SUM(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) pct, COUNT(*) n FROM {P} WHERE publication_year>=2020 AND type='article' AND journal IS NOT NULL")
run("E year>=2020 type in article,journal-article", f"SELECT ROUND(100.0*SUM(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) pct, COUNT(*) n FROM {P} WHERE publication_year>=2020 AND type IN ('article','journal-article')")
