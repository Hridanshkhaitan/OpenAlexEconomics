import duckdb

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"
con = duckdb.connect()

print("=== GERMAN 2016 SPIKE: top journals ===")
print(con.sql(f"""
SELECT COALESCE(journal,'<NULL>') AS journal, type, COUNT(*) AS n
FROM read_parquet('{P}')
WHERE publication_year=2016 AND language='de'
GROUP BY 1,2 ORDER BY n DESC LIMIT 10
""").df().to_string(index=False))

print("\n=== same journals in 2015/2017 for comparison ===")
print(con.sql(f"""
SELECT publication_year, COUNT(*) AS n
FROM read_parquet('{P}')
WHERE language='de' AND journal='Duncker & Humblot eBooks'
GROUP BY 1 ORDER BY 1 DESC LIMIT 6
""").df().to_string(index=False))
