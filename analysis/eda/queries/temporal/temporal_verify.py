import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"

queries = [
    # 1 peak years
    f"SELECT publication_year, COUNT(*) AS n FROM read_parquet('{P}') GROUP BY publication_year ORDER BY n DESC LIMIT 3",
    # 2 CAGR
    f"SELECT ROUND(100*(POWER(SUM(CASE WHEN publication_year=2019 THEN 1 ELSE 0 END)*1.0/SUM(CASE WHEN publication_year=1950 THEN 1 ELSE 0 END), 1.0/69)-1),3) AS cagr_1950_2019_pct, ROUND(100*(POWER(SUM(CASE WHEN publication_year=2019 THEN 1 ELSE 0 END)*1.0/SUM(CASE WHEN publication_year=2000 THEN 1 ELSE 0 END), 1.0/19)-1),3) AS cagr_2000_2019_pct FROM read_parquet('{P}')",
    # 2b supporting counts for 1950/2019
    f"SELECT SUM(CASE WHEN publication_year=1950 THEN 1 ELSE 0 END) AS n1950, SUM(CASE WHEN publication_year=2019 THEN 1 ELSE 0 END) AS n2019 FROM read_parquet('{P}')",
    # 3 recency shares
    f"SELECT ROUND(100.0*SUM(CASE WHEN publication_year>=1990 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_ge_1990, ROUND(100.0*SUM(CASE WHEN publication_year>=2000 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_ge_2000, ROUND(100.0*SUM(CASE WHEN publication_year>=2010 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_ge_2010 FROM read_parquet('{P}')",
    # 4 2019-2025 counts + chapters
    f"SELECT publication_year, COUNT(*) AS n, SUM(CASE WHEN type='book-chapter' THEN 1 ELSE 0 END) AS chapters FROM read_parquet('{P}') WHERE publication_year BETWEEN 2019 AND 2025 GROUP BY publication_year ORDER BY publication_year",
    # 4b lowest-since-2012 check
    f"SELECT publication_year, COUNT(*) AS n FROM read_parquet('{P}') WHERE publication_year BETWEEN 2012 AND 2022 GROUP BY publication_year ORDER BY publication_year",
    # 5 war years
    f"SELECT publication_year, COUNT(*) AS n FROM read_parquet('{P}') WHERE publication_year IN (1913,1918,1938,1944) GROUP BY publication_year ORDER BY publication_year",
    # 5b decade counts since 1800 (only-decade-smaller check)
    f"SELECT (publication_year//10)*10 AS decade, COUNT(*) AS n FROM read_parquet('{P}') WHERE publication_year>=1800 GROUP BY 1 ORDER BY 1",
    # 6 team size by decade
    f"SELECT (publication_year//10)*10 AS decade, ROUND(AVG(author_count),3) AS avg_authors, MEDIAN(author_count) AS med_authors FROM read_parquet('{P}') WHERE publication_year>=1900 AND author_count>0 GROUP BY 1 ORDER BY 1",
    # 7 zero-cited by 5y bucket
    f"SELECT (publication_year//5)*5 AS bucket, COUNT(*) AS n, ROUND(100.0*SUM(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_zero_cited FROM read_parquet('{P}') WHERE publication_year>=1980 GROUP BY 1 ORDER BY 1",
    # 7b median cited_by_count per year 1980-2025 (count of years where median != 0)
    f"SELECT SUM(CASE WHEN med<>0 THEN 1 ELSE 0 END) AS years_median_nonzero, COUNT(*) AS years FROM (SELECT publication_year, MEDIAN(cited_by_count) AS med FROM read_parquet('{P}') WHERE publication_year BETWEEN 1980 AND 2025 GROUP BY publication_year)",
    # 8 pre-1800 top journals
    f"SELECT COALESCE(journal,'(null)') AS journal, COUNT(*) AS n FROM read_parquet('{P}') WHERE publication_year < 1800 GROUP BY 1 ORDER BY n DESC LIMIT 3",
    # 8b pre-1800 totals, book-chapter share, and 19th c Notes and Queries
    f"SELECT COUNT(*) AS pre1800_total, ROUND(100.0*SUM(CASE WHEN type='book-chapter' THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_chapter FROM read_parquet('{P}') WHERE publication_year < 1800",
    f"SELECT SUM(CASE WHEN journal='Notes and Queries' THEN 1 ELSE 0 END) AS nq, COUNT(*) AS total_1800s, ROUND(100.0*SUM(CASE WHEN journal='Notes and Queries' THEN 1 ELSE 0 END)/COUNT(*),2) AS pct FROM read_parquet('{P}') WHERE publication_year BETWEEN 1800 AND 1899",
]

for i, q in enumerate(queries, 1):
    try:
        df = duckdb.sql(q).df()
        print(f"--- Q{i} ---")
        print(df.to_string(index=False))
    except Exception as e:
        print(f"--- Q{i} ERROR ---")
        print(repr(e))
