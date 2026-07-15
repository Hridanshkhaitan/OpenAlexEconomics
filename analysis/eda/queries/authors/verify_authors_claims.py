import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"

queries = {
1: "SELECT (publication_year/10)::INT*10 AS decade, round(100.0*count(*) FILTER (author_count=1)/count(*),2) AS pct_solo_of_authored, round(avg(author_count),3) AS mean_authors FROM read_parquet('%s') WHERE publication_year >= 1900 AND author_count >= 1 GROUP BY 1 ORDER BY 1" % P,
2: "SELECT count(*) AS n_zero, round(100.0*count(*)/(SELECT count(*) FROM read_parquet('%s')),2) AS pct, median(publication_year) AS med_year, count(*) FILTER (publication_year < 1950) AS pre1950, count(*) FILTER (publication_year >= 2000) AS post2000 FROM read_parquet('%s') WHERE author_count = 0" % (P, P),
3: "SELECT median(author_count) AS med, round(avg(author_count),3) AS mean, quantile_cont(author_count,0.95) AS p95, quantile_cont(author_count,0.99) AS p99, max(author_count) AS mx, count(*) FILTER (author_count = 100) AS n_at_100, count(*) FILTER (author_count BETWEEN 90 AND 99) AS n_90_99, count(*) FILTER (author_count IS NULL) AS n_null FROM read_parquet('%s')" % P,
4: "SELECT CASE WHEN author_count = 0 THEN '0' WHEN author_count = 1 THEN '1' WHEN author_count = 2 THEN '2' WHEN author_count BETWEEN 3 AND 5 THEN '3-5' WHEN author_count BETWEEN 6 AND 10 THEN '6-10' WHEN author_count BETWEEN 11 AND 50 THEN '11-50' ELSE '>50' END AS bucket, count(*) AS n FROM read_parquet('%s') GROUP BY 1 ORDER BY 1" % P,
5: "SELECT (publication_year/10)::INT*10 AS decade, count(*) AS n_named, round(100.0*count(*) FILTER (first_author LIKE '%%,%%')/count(*),2) AS pct_comma FROM read_parquet('%s') WHERE publication_year >= 1950 AND first_author IS NOT NULL AND trim(first_author) <> '' GROUP BY 1 ORDER BY 1" % P,
6: "SELECT first_author, count(*) AS n FROM read_parquet('%s') WHERE first_author IS NOT NULL AND trim(first_author) <> '' GROUP BY 1 ORDER BY n DESC LIMIT 15" % P,
7: "SELECT count(*) AS n, min(publication_year) AS y0, max(publication_year) AS y1, count(*) FILTER (type = 'dataset') AS n_dataset, count(*) FILTER (journal = 'Harvard Dataverse') AS n_dataverse FROM read_parquet('%s') WHERE first_author = 'Master, Daniel M.'" % P,
8: "SELECT count(*) FILTER ((first_author IS NULL OR trim(first_author) = '') AND author_count > 0) AS n_inconsistent, count(*) FILTER (first_author IS NULL) AS n_fa_null, count(*) FILTER (author_count = 0) AS n_zero_author FROM read_parquet('%s')" % P,
}

for idx in sorted(queries):
    print("=" * 20, "CLAIM", idx, "=" * 20)
    try:
        df = duckdb.sql(queries[idx]).df()
        print(df.to_string(index=False))
    except Exception as e:
        print("ERROR:", repr(e))

# extras needed for sub-claims
print("=" * 20, "EXTRA A (claim 5 overall pct comma)", "=" * 20)
try:
    df = duckdb.sql("SELECT round(100.0*count(*) FILTER (first_author LIKE '%%,%%')/count(*),3) AS pct_comma_overall FROM read_parquet('%s') WHERE first_author IS NOT NULL AND trim(first_author) <> ''" % P).df()
    print(df.to_string(index=False))
except Exception as e:
    print("ERROR:", repr(e))

print("=" * 20, "EXTRA B (claim 6 placeholder total)", "=" * 20)
try:
    df = duckdb.sql("SELECT sum(CASE WHEN first_author IN (':unav','&NA;','none') THEN 1 ELSE 0 END) AS placeholder_total FROM read_parquet('%s')" % P).df()
    print(df.to_string(index=False))
except Exception as e:
    print("ERROR:", repr(e))
