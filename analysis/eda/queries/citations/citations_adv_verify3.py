import duckdb
P = "read_parquet('/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet')"
def run(i, sql):
    r = duckdb.sql(sql).fetchall()
    print(i, "->", r)
run("2020-2024 article", f"SELECT ROUND(100.0*AVG(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END),2) FROM {P} WHERE publication_year BETWEEN 2020 AND 2024 AND type='article'")
run("2020+ article+preprint", f"SELECT ROUND(100.0*AVG(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END),2) FROM {P} WHERE publication_year>=2020 AND type IN ('article','preprint')")
run("2020+ article+chapter", f"SELECT ROUND(100.0*AVG(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END),2) FROM {P} WHERE publication_year>=2020 AND type IN ('article','book-chapter')")
run("2020+ article+preprint+chapter+review", f"SELECT ROUND(100.0*AVG(CASE WHEN referenced_works_count=0 THEN 1 ELSE 0 END),2) FROM {P} WHERE publication_year>=2020 AND type IN ('article','preprint','book-chapter','review')")
