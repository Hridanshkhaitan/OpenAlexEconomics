import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"

queries = {
1: f"SELECT count(*) AS n_works, sum(CASE WHEN journal IS NULL THEN 1 ELSE 0 END) AS n_null, round(100.0*sum(CASE WHEN journal IS NULL THEN 1 ELSE 0 END)/count(*),2) AS pct_null FROM read_parquet('{P}')",
2: f"SELECT count(*) AS distinct_journals, sum(CASE WHEN n=1 THEN 1 ELSE 0 END) AS singleton_journals FROM (SELECT journal, count(*) AS n FROM read_parquet('{P}') WHERE journal IS NOT NULL GROUP BY journal)",
3: f"SELECT journal, count(*) AS n_works, round(100.0*count(*)/8646207,2) AS pct_corpus, sum(cited_by_count) AS total_citations FROM read_parquet('{P}') WHERE journal = 'SSRN Electronic Journal' GROUP BY journal",
4: f"SELECT sum(n) AS works_top100, round(100.0*sum(n)/8646207,2) AS pct_corpus FROM (SELECT journal, count(*) AS n FROM read_parquet('{P}') WHERE journal IS NOT NULL GROUP BY journal ORDER BY n DESC LIMIT 100)",
5: f"SELECT sum(CASE WHEN journal ILIKE '%ebook%' THEN 1 ELSE 0 END) AS ebook, sum(CASE WHEN journal ILIKE '%ssrn%' THEN 1 ELSE 0 END) AS ssrn, sum(CASE WHEN journal ILIKE '%repository%' THEN 1 ELSE 0 END) AS repository, sum(CASE WHEN journal ILIKE '%proceedings%' THEN 1 ELSE 0 END) AS proceedings, sum(CASE WHEN journal ILIKE '%conference%' THEN 1 ELSE 0 END) AS conference, sum(CASE WHEN journal ILIKE '%working paper%' THEN 1 ELSE 0 END) AS working_paper, sum(CASE WHEN journal ILIKE '%dissertation%' THEN 1 ELSE 0 END) AS dissertation, sum(CASE WHEN journal ILIKE '%thesis%' THEN 1 ELSE 0 END) AS thesis FROM read_parquet('{P}')",
6: f"SELECT count(*) AS n_works, min(publication_year) AS min_yr, max(publication_year) AS max_yr, round(avg(cited_by_count),2) AS avg_cites FROM read_parquet('{P}') WHERE journal = 'Medical Entomology and Zoology'",
7: f"SELECT count(*) AS n, round(100.0*count(*)/8646207,2) AS pct FROM read_parquet('{P}') WHERE journal IN ('PubMed','BMJ','JAMA','The Lancet','Science','Nature','New England Journal of Medicine','Journal of the American Medical Association','The Journal of Urology','AJN American Journal of Nursing','Value in Health','Medical Entomology and Zoology','Scientific American')",
8: f"SELECT count(*) AS n_pairs, sum(a.n + b.n) AS works_involved FROM (SELECT journal, count(*) AS n FROM read_parquet('{P}') WHERE journal IS NOT NULL GROUP BY journal) a JOIN (SELECT journal, count(*) AS n FROM read_parquet('{P}') WHERE journal IS NOT NULL GROUP BY journal) b ON b.journal = 'The ' || a.journal",
}

for idx in sorted(queries):
    try:
        rows = duckdb.sql(queries[idx]).fetchall()
        cols = duckdb.sql(queries[idx]).columns
        print(f"CLAIM {idx}: cols={cols} rows={rows}")
    except Exception as e:
        print(f"CLAIM {idx}: ERROR {type(e).__name__}: {e}")

# Sub-claims needing extra checks:
# Claim 1 sub: NULL rate by decade (peak 22.88% in 2010s) and per-year peak 25.3% in 2013
try:
    q_dec = f"""
    SELECT (publication_year/10)*10 AS decade,
           round(100.0*sum(CASE WHEN journal IS NULL THEN 1 ELSE 0 END)/count(*),2) AS pct_null,
           count(*) AS n
    FROM read_parquet('{P}')
    GROUP BY 1 ORDER BY pct_null DESC LIMIT 5
    """
    print("CLAIM 1b (decade null peak):", duckdb.sql(q_dec).fetchall())
    q_yr = f"""
    SELECT publication_year,
           round(100.0*sum(CASE WHEN journal IS NULL THEN 1 ELSE 0 END)/count(*),1) AS pct_null
    FROM read_parquet('{P}')
    GROUP BY 1 ORDER BY pct_null DESC LIMIT 5
    """
    print("CLAIM 1c (year null peak):", duckdb.sql(q_yr).fetchall())
except Exception as e:
    print("CLAIM 1b/1c: ERROR", e)

# Claim 3 sub: Journal of Finance and AER citation totals
try:
    q_cit = f"""
    SELECT journal, sum(cited_by_count) AS total_citations, count(*) AS n
    FROM read_parquet('{P}')
    WHERE journal IN ('The Journal of Finance','American Economic Review')
    GROUP BY journal
    """
    print("CLAIM 3b (JF/AER citations):", duckdb.sql(q_cit).fetchall())
    q_top = f"""
    SELECT journal, sum(cited_by_count) AS total_citations
    FROM read_parquet('{P}')
    WHERE journal IS NOT NULL
    GROUP BY journal ORDER BY total_citations DESC LIMIT 5
    """
    print("CLAIM 3c (top cited venues):", duckdb.sql(q_top).fetchall())
    q_topn = f"""
    SELECT journal, count(*) AS n
    FROM read_parquet('{P}')
    WHERE journal IS NOT NULL
    GROUP BY journal ORDER BY n DESC LIMIT 8
    """
    print("CLAIM 3d/6b (top venues by works, check SSRN #1 and MedEntZool rank):", duckdb.sql(q_topn).fetchall())
except Exception as e:
    print("CLAIM 3b/c/d: ERROR", e)

# Claim 4 sub: 28.10% of non-null works
try:
    q_nn = f"""
    SELECT round(100.0*(SELECT sum(n) FROM (SELECT journal, count(*) AS n FROM read_parquet('{P}') WHERE journal IS NOT NULL GROUP BY journal ORDER BY n DESC LIMIT 100))
           / count(*),2) AS pct_nonnull
    FROM read_parquet('{P}') WHERE journal IS NOT NULL
    """
    print("CLAIM 4b (pct of non-null):", duckdb.sql(q_nn).fetchall())
except Exception as e:
    print("CLAIM 4b: ERROR", e)
