import duckdb

P = "read_parquet('/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet')"

def run(i, sql, label=""):
    print("="*70)
    print(f"CLAIM {i} {label}")
    try:
        rows = duckdb.sql(sql).fetchall()
        cols = duckdb.sql(sql).columns
        print("cols:", cols)
        for r in rows:
            print(r)
    except Exception as e:
        print("ERROR:", repr(e))

# Claim 1
run(1, f"SELECT (publication_year/10)::INT*10 AS decade, round(100.0*count(*) FILTER (author_count=1)/count(*),2) AS pct_solo_of_authored, round(avg(author_count),3) AS mean_authors FROM {P} WHERE publication_year >= 1900 AND author_count >= 1 GROUP BY 1 ORDER BY 1")

# Claim 2
run(2, f"SELECT count(*) AS n_zero, round(100.0*count(*)/(SELECT count(*) FROM {P}),2) AS pct, median(publication_year) AS med_year, count(*) FILTER (publication_year < 1950) AS pre1950, count(*) FILTER (publication_year >= 2000) AS post2000 FROM {P} WHERE author_count = 0")

# Claim 3
run(3, f"SELECT median(author_count) AS med, round(avg(author_count),3) AS mean, quantile_cont(author_count,0.95) AS p95, quantile_cont(author_count,0.99) AS p99, max(author_count) AS mx, count(*) FILTER (author_count = 100) AS n_at_100, count(*) FILTER (author_count BETWEEN 90 AND 99) AS n_90_99, count(*) FILTER (author_count IS NULL) AS n_null FROM {P}")

# Claim 4
run(4, f"SELECT CASE WHEN author_count = 0 THEN '0' WHEN author_count = 1 THEN '1' WHEN author_count = 2 THEN '2' WHEN author_count BETWEEN 3 AND 5 THEN '3-5' WHEN author_count BETWEEN 6 AND 10 THEN '6-10' WHEN author_count BETWEEN 11 AND 50 THEN '11-50' ELSE '>50' END AS bucket, count(*) AS n FROM {P} GROUP BY 1 ORDER BY 1")

# Claim 5
run(5, f"SELECT (publication_year/10)::INT*10 AS decade, count(*) AS n_named, round(100.0*count(*) FILTER (first_author LIKE '%,%')/count(*),2) AS pct_comma FROM {P} WHERE publication_year >= 1950 AND first_author IS NOT NULL AND trim(first_author) <> '' GROUP BY 1 ORDER BY 1")

# Claim 5 overall pct comma
run("5b", f"SELECT round(100.0*count(*) FILTER (first_author LIKE '%,%')/count(*),2) AS pct_comma_overall FROM {P} WHERE first_author IS NOT NULL AND trim(first_author) <> ''")

# Claim 6
run(6, f"SELECT first_author, count(*) AS n FROM {P} WHERE first_author IS NOT NULL AND trim(first_author) <> '' GROUP BY 1 ORDER BY n DESC LIMIT 15")

# Claim 6 placeholders total
run("6b", f"SELECT count(*) AS placeholder_total FROM {P} WHERE first_author IN (':unav','&NA;','none')")

# Claim 7
run(7, f"SELECT count(*) AS n, min(publication_year) AS y0, max(publication_year) AS y1, count(*) FILTER (type = 'dataset') AS n_dataset, count(*) FILTER (journal = 'Harvard Dataverse') AS n_dataverse FROM {P} WHERE first_author = 'Master, Daniel M.'")

# Claim 8
run(8, f"SELECT count(*) FILTER ((first_author IS NULL OR trim(first_author) = '') AND author_count > 0) AS n_inconsistent, count(*) FILTER (first_author IS NULL) AS n_fa_null, count(*) FILTER (author_count = 0) AS n_zero_author FROM {P}")

print("="*70)
print("DONE")
