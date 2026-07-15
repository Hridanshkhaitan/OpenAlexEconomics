import duckdb

P = "read_parquet('/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet')"

def run(i, sql):
    try:
        rows = duckdb.sql(sql).fetchall()
        cols = duckdb.sql(sql).columns
        print(f"=== CLAIM {i} ===")
        print("COLS:", cols)
        for r in rows:
            print("ROW:", r)
    except Exception as e:
        print(f"=== CLAIM {i} ERROR ===")
        print("ERR:", repr(e))

# Claim 1
run(1, f"SELECT count(*) AS n_works, sum(CASE WHEN journal IS NULL THEN 1 ELSE 0 END) AS n_null, round(100.0*sum(CASE WHEN journal IS NULL THEN 1 ELSE 0 END)/count(*),2) AS pct_null FROM {P}")

# Claim 1 extra: decade peak and per-year peak
run("1b_decade", f"SELECT (publication_year/10)*10 AS decade, round(100.0*sum(CASE WHEN journal IS NULL THEN 1 ELSE 0 END)/count(*),2) AS pct_null, count(*) AS n FROM {P} GROUP BY decade ORDER BY pct_null DESC LIMIT 5")
run("1c_year", f"SELECT publication_year AS yr, round(100.0*sum(CASE WHEN journal IS NULL THEN 1 ELSE 0 END)/count(*),2) AS pct_null, count(*) AS n FROM {P} WHERE publication_year>=1990 GROUP BY yr ORDER BY pct_null DESC LIMIT 5")

# Claim 2
run(2, f"SELECT count(*) AS distinct_journals, sum(CASE WHEN n=1 THEN 1 ELSE 0 END) AS singleton_journals FROM (SELECT journal, count(*) AS n FROM {P} WHERE journal IS NOT NULL GROUP BY journal)")

# Claim 3
run(3, f"SELECT journal, count(*) AS n_works, round(100.0*count(*)/8646207,2) AS pct_corpus, sum(cited_by_count) AS total_citations FROM {P} WHERE journal = 'SSRN Electronic Journal' GROUP BY journal")
# Claim 3 extra: verify SSRN is largest venue and most-cited; check Journal of Finance and AER citations
run("3b_topcited", f"SELECT journal, sum(cited_by_count) AS total_citations FROM {P} WHERE journal IS NOT NULL GROUP BY journal ORDER BY total_citations DESC LIMIT 5")
run("3c_topworks", f"SELECT journal, count(*) AS n FROM {P} WHERE journal IS NOT NULL GROUP BY journal ORDER BY n DESC LIMIT 3")

# Claim 4
run(4, f"SELECT sum(n) AS works_top100, round(100.0*sum(n)/8646207,2) AS pct_corpus FROM (SELECT journal, count(*) AS n FROM {P} WHERE journal IS NOT NULL GROUP BY journal ORDER BY n DESC LIMIT 100)")
# Claim 4 extra: pct of non-null works
run("4b", f"SELECT count(*) AS nonnull FROM {P} WHERE journal IS NOT NULL")

# Claim 5
run(5, f"SELECT sum(CASE WHEN journal ILIKE '%ebook%' THEN 1 ELSE 0 END) AS ebook, sum(CASE WHEN journal ILIKE '%ssrn%' THEN 1 ELSE 0 END) AS ssrn, sum(CASE WHEN journal ILIKE '%repository%' THEN 1 ELSE 0 END) AS repository, sum(CASE WHEN journal ILIKE '%proceedings%' THEN 1 ELSE 0 END) AS proceedings, sum(CASE WHEN journal ILIKE '%conference%' THEN 1 ELSE 0 END) AS conference, sum(CASE WHEN journal ILIKE '%working paper%' THEN 1 ELSE 0 END) AS working_paper, sum(CASE WHEN journal ILIKE '%dissertation%' THEN 1 ELSE 0 END) AS dissertation, sum(CASE WHEN journal ILIKE '%thesis%' THEN 1 ELSE 0 END) AS thesis FROM {P}")
run("5b_ebookpct", f"SELECT round(100.0*sum(CASE WHEN journal ILIKE '%ebook%' THEN 1 ELSE 0 END)/8646207,2) AS ebook_pct FROM {P}")

# Claim 6
run(6, f"SELECT count(*) AS n_works, min(publication_year) AS min_yr, max(publication_year) AS max_yr, round(avg(cited_by_count),2) AS avg_cites FROM {P} WHERE journal = 'Medical Entomology and Zoology'")
# Claim 6 extra: rank of this venue
run("6b_rank", f"SELECT journal, n FROM (SELECT journal, count(*) AS n, row_number() OVER (ORDER BY count(*) DESC) AS rk FROM {P} WHERE journal IS NOT NULL GROUP BY journal) WHERE rk<=10 ORDER BY n DESC")

# Claim 7
run(7, f"SELECT count(*) AS n, round(100.0*count(*)/8646207,2) AS pct FROM {P} WHERE journal IN ('PubMed','BMJ','JAMA','The Lancet','Science','Nature','New England Journal of Medicine','Journal of the American Medical Association','The Journal of Urology','AJN American Journal of Nursing','Value in Health','Medical Entomology and Zoology','Scientific American')")

# Claim 8
run(8, f"SELECT count(*) AS n_pairs, sum(a.n + b.n) AS works_involved FROM (SELECT journal, count(*) AS n FROM {P} WHERE journal IS NOT NULL GROUP BY journal) a JOIN (SELECT journal, count(*) AS n FROM {P} WHERE journal IS NOT NULL GROUP BY journal) b ON b.journal = 'The ' || a.journal")

print("=== DONE ===")
