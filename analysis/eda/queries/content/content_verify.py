import duckdb

P = "read_parquet('/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet')"

def run(i, sql):
    print(f"===== CLAIM {i} =====")
    try:
        rows = duckdb.sql(sql).fetchall()
        for r in rows:
            print(r)
    except Exception as e:
        print("ERROR:", repr(e))
    print()

# Claim 1
run(1, f"""SELECT COALESCE(language,'<NULL>') AS lang, COUNT(*) AS n, ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),2) AS pct FROM {P} GROUP BY 1 ORDER BY n DESC LIMIT 16""")

# Claim 2
run(2, f"""SELECT (publication_year//10)*10 AS decade, ROUND(100.0*SUM(CASE WHEN language IS NOT NULL AND language!='en' THEN 1 ELSE 0 END)/COUNT(*),2) AS nonen_pct FROM {P} WHERE publication_year BETWEEN 1990 AND 2019 GROUP BY 1 ORDER BY 1""")

# Claim 3
run(3, f"""SELECT COUNT(*) AS n, ROUND(100.0*COUNT(*)/8646207,3) AS pct FROM {P} WHERE title ILIKE 'book review%' OR title ILIKE 'front matter%' OR title ILIKE 'back matter%' OR title ILIKE '%editorial board%' OR title ILIKE 'index%' OR title ILIKE 'erratum%' OR title ILIKE 'corrigendum%'""")

# Claim 3b - breakdown of editorial board
run("3b", f"""SELECT COUNT(*) AS n, ROUND(100.0*COUNT(*)/8646207,3) AS pct FROM {P} WHERE title ILIKE '%editorial board%'""")

# Claim 4
run(4, f"""SELECT title, COUNT(*) AS n FROM {P} WHERE title IS NOT NULL AND TRIM(title)!='' GROUP BY title ORDER BY n DESC LIMIT 10""")

# Claim 5
run(5, f"""SELECT SUM(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN 1 ELSE 0 END) AS with_abs, ROUND(100.0*SUM(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN 1 ELSE 0 END)/COUNT(*),2) AS abs_pct, ROUND(AVG(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN array_length(string_split_regex(TRIM(abstract),'\\\\s+')) END),1) AS avg_abs_words FROM {P}""")

# Claim 6
run(6, f"""SELECT journal, COUNT(*) AS n, ROUND(100.0*SUM(CASE WHEN abstract IS NOT NULL AND TRIM(abstract)!='' THEN 1 ELSE 0 END)/COUNT(*),2) AS abs_pct FROM {P} WHERE journal IN ('Economics Letters','Journal of Banking & Finance','Journal of Econometrics','The Quarterly Journal of Economics','Applied Economics') GROUP BY 1 ORDER BY abs_pct""")

# Claim 7
run(7, f"""SELECT type, COUNT(*) AS n, ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),3) AS pct FROM {P} GROUP BY 1 ORDER BY n DESC""")

# Claim 8
run(8, f"""SELECT publication_year, ROUND(100.0*SUM(CASE WHEN language IS NULL THEN 1 ELSE 0 END)/COUNT(*),2) AS null_lang_pct FROM {P} WHERE publication_year BETWEEN 2020 AND 2025 GROUP BY 1 ORDER BY 1""")
