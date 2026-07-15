import duckdb
import matplotlib
print("duckdb", duckdb.__version__, "| matplotlib", matplotlib.__version__)

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"
con = duckdb.connect()

print("TOTAL:", con.sql(f"SELECT COUNT(*), MIN(publication_year), MAX(publication_year) FROM read_parquet('{P}')").fetchall())

print("TYPES:", con.sql(f"SELECT type, COUNT(*) n FROM read_parquet('{P}') GROUP BY 1 ORDER BY n DESC LIMIT 8").fetchall())

print("SUBFIELDS:", con.sql(f"SELECT subfield, COUNT(*) n FROM read_parquet('{P}') GROUP BY 1 ORDER BY n DESC LIMIT 12").fetchall())

print("LANGS:", con.sql(f"SELECT language, COUNT(*) n FROM read_parquet('{P}') GROUP BY 1 ORDER BY n DESC LIMIT 10").fetchall())

print("NULLS:", con.sql(f"""SELECT
  SUM(CASE WHEN doi IS NULL THEN 1 ELSE 0 END) doi_null,
  SUM(CASE WHEN abstract IS NULL THEN 1 ELSE 0 END) abs_null,
  SUM(CASE WHEN journal IS NULL THEN 1 ELSE 0 END) j_null,
  SUM(CASE WHEN language IS NULL THEN 1 ELSE 0 END) lang_null,
  SUM(CASE WHEN is_oa IS NULL THEN 1 ELSE 0 END) oa_null,
  SUM(CASE WHEN author_count IS NULL THEN 1 ELSE 0 END) ac_null,
  SUM(CASE WHEN cited_by_count IS NULL THEN 1 ELSE 0 END) cc_null
FROM read_parquet('{P}')""").fetchall())
