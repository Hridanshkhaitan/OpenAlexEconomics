import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"

sqls = {
1: f"SELECT COALESCE(language,'<NULL>') AS lang, COUNT(*) AS n, ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),2) AS pct FROM read_parquet('{P}') GROUP BY 1 ORDER BY n DESC LIMIT 16",
2: f"SELECT (publication_year//10)*10 AS decade, ROUND(100.0*SUM(CASE WHEN language IS NOT NULL AND language!='en' THEN 1 ELSE 0 END)/COUNT(*),2) AS nonen_pct FROM read_parquet('{P}') WHERE publication_year BETWEEN 1990 AND 2019 GROUP BY 1 ORDER BY 1",
3: f"SELECT COUNT(*) AS n, ROUND(100.0*COUNT(*)/8646207,3) AS pct FROM read_parquet('{P}') WHERE title ILIKE 'book review%' OR title ILIKE 'front matter%' OR title ILIKE 'back matter%' OR title ILIKE '%editorial board%' OR title ILIKE 'index%' OR title ILIKE 'erratum%' OR title ILIKE 'corrigendum%'",
4: f"SELECT title, COUNT(*) AS n FROM read_parquet('{P}') WHERE title IS NOT NULL AND TRIM(title)!='' GROUP BY title ORDER BY n DESC LIMIT 10",
5: f"SELECT SUM(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN 1 ELSE 0 END) AS with_abs, ROUND(100.0*SUM(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN 1 ELSE 0 END)/COUNT(*),2) AS abs_pct, ROUND(AVG(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN array_length(string_split_regex(TRIM(abstract),'\\s+')) END),1) AS avg_abs_words FROM read_parquet('{P}')",
6: f"SELECT journal, COUNT(*) AS n, ROUND(100.0*SUM(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN 1 ELSE 0 END)/COUNT(*),2) AS abs_pct FROM read_parquet('{P}') WHERE journal IN ('Economics Letters','Journal of Banking & Finance','Journal of Econometrics','The Quarterly Journal of Economics','Applied Economics') GROUP BY 1 ORDER BY abs_pct",
7: f"SELECT type, COUNT(*) AS n, ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),3) AS pct FROM read_parquet('{P}') GROUP BY 1 ORDER BY n DESC",
8: f"SELECT publication_year, ROUND(100.0*SUM(CASE WHEN language IS NULL THEN 1 ELSE 0 END)/COUNT(*),2) AS null_lang_pct FROM read_parquet('{P}') WHERE publication_year BETWEEN 2020 AND 2025 GROUP BY 1 ORDER BY 1",
}

for i in sorted(sqls):
    print(f"===== CLAIM {i} =====")
    try:
        df = duckdb.sql(sqls[i]).df()
        print(df.to_string(index=False))
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
    print()

# Extra sub-checks embedded in claims that the headline SQLs don't fully cover
print("===== EXTRA A: claim3 breakdown editorial board =====")
try:
    df = duckdb.sql(f"SELECT COUNT(*) n, ROUND(100.0*COUNT(*)/8646207,3) pct FROM read_parquet('{P}') WHERE title ILIKE '%editorial board%'").df()
    print(df.to_string(index=False))
except Exception as e:
    print("ERROR:", e)

print("===== EXTRA B: claim5 median abstract words + decade coverage =====")
try:
    df = duckdb.sql(f"SELECT MEDIAN(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN array_length(string_split_regex(TRIM(abstract),'\\s+')) END) med FROM read_parquet('{P}')").df()
    print(df.to_string(index=False))
    df = duckdb.sql(f"SELECT (publication_year//10)*10 dec, ROUND(100.0*SUM(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN 1 ELSE 0 END)/COUNT(*),2) pct FROM read_parquet('{P}') WHERE publication_year BETWEEN 1960 AND 2025 GROUP BY 1 ORDER BY 1").df()
    print(df.to_string(index=False))
except Exception as e:
    print("ERROR:", e)

print("===== EXTRA C: claim7 furniture not paratext =====")
try:
    df = duckdb.sql(f"SELECT COUNT(*) n FROM read_parquet('{P}') WHERE (title ILIKE 'book review%' OR title ILIKE 'front matter%' OR title ILIKE 'back matter%' OR title ILIKE '%editorial board%' OR title ILIKE 'index%' OR title ILIKE 'erratum%' OR title ILIKE 'corrigendum%') AND (type IS NULL OR type!='paratext')").df()
    print(df.to_string(index=False))
    df = duckdb.sql(f"SELECT COUNT(*) n FROM read_parquet('{P}') WHERE title='Editorial Board' AND type='article'").df()
    print(df.to_string(index=False))
except Exception as e:
    print("ERROR:", e)

print("===== EXTRA D: claim8 2016 german inactive dois =====")
try:
    df = duckdb.sql(f"SELECT COUNT(*) n FROM read_parquet('{P}') WHERE publication_year=2016 AND language='de' AND type='book-chapter' AND journal='Inactive DOIs'").df()
    print(df.to_string(index=False))
except Exception as e:
    print("ERROR:", e)
