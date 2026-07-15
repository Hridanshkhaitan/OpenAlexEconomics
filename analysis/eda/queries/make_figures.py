"""EDA figures for OpenAlex Economics corpus (field 20), 1647-2025.

Reads parquet via DuckDB, writes 11 PNGs to analysis/eda/figures/ and
works_per_year.txt to analysis/eda/. Prints compact summary stats.
"""
import os
import duckdb
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"
BASE = "/project/def-kmcel/hridansh/openalex_econ/analysis/eda"
FIGDIR = os.path.join(BASE, "figures")
os.makedirs(FIGDIR, exist_ok=True)

plt.rcParams.update({
    "font.size": 11, "axes.titlesize": 13, "axes.labelsize": 12,
    "figure.dpi": 150, "savefig.dpi": 150,
})
kfmt = FuncFormatter(lambda x, p: f"{int(x):,}")
COLORS = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e",
          "#8c564b", "#17becf", "#7f7f7f", "#bcbd22", "#e377c2"]

con = duckdb.connect()

def q(sql):
    return con.sql(sql).df()

def save(fig, name):
    fig.tight_layout()
    path = os.path.join(FIGDIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"SAVED {name}")

# ---------------------------------------------------------------- per-year counts
wy = q(f"""SELECT publication_year AS y, COUNT(*) AS n
           FROM read_parquet('{P}') GROUP BY 1 ORDER BY 1""")
with open(os.path.join(BASE, "works_per_year.txt"), "w") as f:
    for _, r in wy.iterrows():
        f.write(f"{int(r.y)}\t{int(r.n)}\n")
print(f"works_per_year.txt rows: {len(wy)}  total works: {int(wy.n.sum()):,}")
peak = wy.loc[wy.n.idxmax()]
print(f"PEAK year: {int(peak.y)} with {int(peak.n):,} works")
for yy in (1900, 1950, 2000, 2020, 2023, 2024, 2025):
    v = wy.loc[wy.y == yy, "n"]
    if len(v):
        print(f"  works in {yy}: {int(v.iloc[0]):,}")

# 1. full-range, log y
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(wy.y, wy.n, lw=1.2, color=COLORS[0])
ax.set_yscale("log")
ax.set_title("Economics works per year, 1647–2025 (log scale)")
ax.set_xlabel("Publication year"); ax.set_ylabel("Works (log scale)")
ax.yaxis.set_major_formatter(kfmt)
ax.grid(True, which="both", alpha=0.3)
save(fig, "works_per_year_full.png")

# 2. modern era, linear
m = wy[wy.y >= 1900]
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(m.y, m.n, lw=1.5, color=COLORS[0])
ax.fill_between(m.y, m.n, alpha=0.15, color=COLORS[0])
ax.set_title("Economics works per year, 1900–2025")
ax.set_xlabel("Publication year"); ax.set_ylabel("Works")
ax.yaxis.set_major_formatter(kfmt)
ax.grid(True, alpha=0.3)
save(fig, "works_per_year_modern.png")

# ---------------------------------------------------------------- 3. metadata coverage by decade
cov = q(f"""SELECT (publication_year//10)*10 AS dec,
        100.0*AVG(CASE WHEN doi      IS NOT NULL THEN 1 ELSE 0 END) AS doi,
        100.0*AVG(CASE WHEN abstract IS NOT NULL THEN 1 ELSE 0 END) AS abstract,
        100.0*AVG(CASE WHEN journal  IS NOT NULL THEN 1 ELSE 0 END) AS journal,
        100.0*AVG(CASE WHEN language IS NOT NULL THEN 1 ELSE 0 END) AS language
        FROM read_parquet('{P}')
        WHERE publication_year BETWEEN 1900 AND 2029
        GROUP BY 1 ORDER BY 1""")
fig, ax = plt.subplots(figsize=(10, 5.5))
for i, c in enumerate(["doi", "abstract", "journal", "language"]):
    ax.plot(cov.dec, cov[c], marker="o", lw=1.8, color=COLORS[i], label=c)
ax.set_title("Metadata coverage by decade (% of works with field non-null)")
ax.set_xlabel("Decade"); ax.set_ylabel("% non-null")
ax.set_ylim(0, 102)
ax.set_xticks(cov.dec)
ax.set_xticklabels([f"{int(d)}s" for d in cov.dec], rotation=45)
ax.legend(); ax.grid(True, alpha=0.3)
save(fig, "coverage_by_decade.png")
print("COVERAGE 2020s (doi, abstract, journal, language %):",
      [round(x, 1) for x in cov[cov.dec == 2020][["doi", "abstract", "journal", "language"]].iloc[0]])
print("COVERAGE 1900s:",
      [round(x, 1) for x in cov[cov.dec == 1900][["doi", "abstract", "journal", "language"]].iloc[0]])

# ---------------------------------------------------------------- 4. citation distribution (2000+)
cd = q(f"""SELECT cited_by_count AS c, COUNT(*) AS n
           FROM read_parquet('{P}') WHERE publication_year >= 2000
           GROUP BY 1 ORDER BY 1""")
tot2000 = int(cd.n.sum())
zero = int(cd.loc[cd.c == 0, "n"].iloc[0]) if (cd.c == 0).any() else 0
pos = cd[cd.c >= 1]
fig, ax = plt.subplots(figsize=(9, 6))
ax.scatter(pos.c, pos.n, s=8, alpha=0.5, color=COLORS[0])
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_title("Citation distribution, works published 2000–2025 (log–log)")
ax.set_xlabel("Citations received (cited_by_count)")
ax.set_ylabel("Number of works with that citation count")
ax.grid(True, which="both", alpha=0.3)
ax.text(0.02, 0.06,
        f"n = {tot2000:,} works\nzero-cited: {zero:,} ({100*zero/tot2000:.1f}%)\n"
        f"max citations: {int(cd.c.max()):,}",
        transform=ax.transAxes, fontsize=10,
        bbox=dict(boxstyle="round", fc="white", ec="gray", alpha=0.9))
save(fig, "citation_distribution.png")
print(f"CITATIONS 2000+: n={tot2000:,}, zero-cited={zero:,} ({100*zero/tot2000:.2f}%), max={int(cd.c.max()):,}")

# ---------------------------------------------------------------- 5. citations by year
cy = q(f"""SELECT publication_year AS y, AVG(cited_by_count) AS mean_c,
           100.0*AVG(CASE WHEN cited_by_count=0 THEN 1 ELSE 0 END) AS zero_share
           FROM read_parquet('{P}')
           WHERE publication_year BETWEEN 1980 AND 2025
           GROUP BY 1 ORDER BY 1""")
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.plot(cy.y, cy.mean_c, lw=2, color=COLORS[0], label="Mean citations")
ax.set_xlabel("Publication year"); ax.set_ylabel("Mean cited_by_count", color=COLORS[0])
ax.tick_params(axis="y", labelcolor=COLORS[0])
ax2 = ax.twinx()
ax2.plot(cy.y, cy.zero_share, lw=2, color=COLORS[1], ls="--", label="% zero-cited")
ax2.set_ylabel("% of works with zero citations", color=COLORS[1])
ax2.tick_params(axis="y", labelcolor=COLORS[1])
ax2.set_ylim(0, 100)
ax.set_title("Mean citations and zero-cited share by publication year, 1980–2025")
l1, lb1 = ax.get_legend_handles_labels(); l2, lb2 = ax2.get_legend_handles_labels()
ax.legend(l1 + l2, lb1 + lb2, loc="upper right")
ax.grid(True, alpha=0.3)
save(fig, "citations_by_year.png")
pk = cy.loc[cy.mean_c.idxmax()]
print(f"MEAN CITATIONS peak: {pk.mean_c:.2f} in {int(pk.y)}; "
      f"1990={float(cy.loc[cy.y==1990,'mean_c'].iloc[0]):.2f}, 2025={float(cy.loc[cy.y==2025,'mean_c'].iloc[0]):.2f}; "
      f"zero-share 2025={float(cy.loc[cy.y==2025,'zero_share'].iloc[0]):.1f}%")

# ---------------------------------------------------------------- 6. team size
ts = q(f"""SELECT publication_year AS y, AVG(author_count) AS mean_a,
           MEDIAN(author_count) AS med_a
           FROM read_parquet('{P}')
           WHERE publication_year BETWEEN 1900 AND 2025
           GROUP BY 1 ORDER BY 1""")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(ts.y, ts.mean_a, lw=2, color=COLORS[0], label="Mean authors per work")
ax.plot(ts.y, ts.med_a, lw=2, color=COLORS[1], ls="--", label="Median authors per work")
ax.set_title("Team size (author_count) by year, 1900–2025")
ax.set_xlabel("Publication year"); ax.set_ylabel("Authors per work")
ax.legend(); ax.grid(True, alpha=0.3)
save(fig, "team_size_trend.png")
print(f"TEAM SIZE mean: 1950={float(ts.loc[ts.y==1950,'mean_a'].iloc[0]):.2f}, "
      f"1980={float(ts.loc[ts.y==1980,'mean_a'].iloc[0]):.2f}, "
      f"2000={float(ts.loc[ts.y==2000,'mean_a'].iloc[0]):.2f}, "
      f"2025={float(ts.loc[ts.y==2025,'mean_a'].iloc[0]):.2f}; "
      f"median 2025={float(ts.loc[ts.y==2025,'med_a'].iloc[0]):.1f}")

# ---------------------------------------------------------------- 7. top journals
tj = q(f"""SELECT journal, COUNT(*) AS n FROM read_parquet('{P}')
           WHERE journal IS NOT NULL GROUP BY 1 ORDER BY n DESC LIMIT 20""")
labels = [j if len(j) <= 55 else j[:52] + "..." for j in tj.journal]
fig, ax = plt.subplots(figsize=(10, 8))
ypos = np.arange(len(tj))[::-1]
ax.barh(ypos, tj.n, color=COLORS[0], alpha=0.85)
ax.set_yticks(ypos); ax.set_yticklabels(labels, fontsize=9)
ax.set_title("Top 20 journals / sources by number of works")
ax.set_xlabel("Works")
ax.xaxis.set_major_formatter(kfmt)
for yp, v in zip(ypos, tj.n):
    ax.text(v, yp, f" {int(v):,}", va="center", fontsize=8)
ax.grid(True, axis="x", alpha=0.3)
save(fig, "top_journals.png")
print("TOP JOURNALS:", [(r.journal[:40], int(r.n)) for r in tj.head(5).itertuples()])

# ---------------------------------------------------------------- 8. subfield trends
sf = q(f"""SELECT (publication_year//10)*10 AS dec, subfield, COUNT(*) AS n
           FROM read_parquet('{P}')
           WHERE publication_year BETWEEN 1950 AND 2029 AND subfield IS NOT NULL
           GROUP BY 1, 2 ORDER BY 1""")
piv = sf.pivot(index="dec", columns="subfield", values="n").fillna(0)
share = piv.div(piv.sum(axis=1), axis=0) * 100
order = piv.sum().sort_values(ascending=False).index
fig, ax = plt.subplots(figsize=(10, 5.5))
for i, c in enumerate(order):
    ax.plot(share.index, share[c], marker="o", lw=2, color=COLORS[i], label=c)
ax.set_title("Subfield share of economics works by decade, 1950s–2020s")
ax.set_xlabel("Decade"); ax.set_ylabel("% of works")
ax.set_xticks(share.index)
ax.set_xticklabels([f"{int(d)}s" for d in share.index], rotation=45)
ax.set_ylim(0, 100)
ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
save(fig, "subfield_trends.png")
print("SUBFIELD SHARE 2020s (%):", {c: round(share.loc[2020, c], 1) for c in order})

# ---------------------------------------------------------------- 9. type mix
top_types = q(f"""SELECT type FROM read_parquet('{P}') WHERE type IS NOT NULL
                  GROUP BY 1 ORDER BY COUNT(*) DESC LIMIT 6""").type.tolist()
tl = ",".join(f"'{t}'" for t in top_types)
tm = q(f"""SELECT (publication_year//10)*10 AS dec,
           CASE WHEN type IN ({tl}) THEN type ELSE 'other types' END AS t,
           COUNT(*) AS n
           FROM read_parquet('{P}')
           WHERE publication_year BETWEEN 1950 AND 2029
           GROUP BY 1, 2 ORDER BY 1""")
pivt = tm.pivot(index="dec", columns="t", values="n").fillna(0)
cols = [t for t in top_types if t in pivt.columns] + \
       ([c for c in pivt.columns if c == "other types"])
pivt = pivt[cols]
sharet = pivt.div(pivt.sum(axis=1), axis=0) * 100
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.stackplot(sharet.index, [sharet[c] for c in cols], labels=cols,
             colors=COLORS[:len(cols)], alpha=0.85)
ax.set_title("Work-type composition by decade since 1950 (top 6 types + other)")
ax.set_xlabel("Decade"); ax.set_ylabel("% of works")
ax.set_xticks(sharet.index)
ax.set_xticklabels([f"{int(d)}s" for d in sharet.index], rotation=45)
ax.set_ylim(0, 100)
ax.legend(loc="lower left", fontsize=9, framealpha=0.9)
ax.grid(True, alpha=0.2)
save(fig, "type_mix.png")
print("TYPE SHARE 2020s (%):", {c: round(sharet.loc[2020, c], 1) for c in cols})

# ---------------------------------------------------------------- 10. language share
ld = q(f"""SELECT (publication_year//10)*10 AS dec,
           100.0*SUM(CASE WHEN language='en' THEN 1 ELSE 0 END)/COUNT(*) AS en,
           100.0*SUM(CASE WHEN language IS NOT NULL AND language<>'en' THEN 1 ELSE 0 END)/COUNT(*) AS non_en
           FROM read_parquet('{P}')
           WHERE publication_year BETWEEN 1900 AND 2029 AND language IS NOT NULL
           GROUP BY 1 ORDER BY 1""")
nl = q(f"""SELECT language, COUNT(*) AS n FROM read_parquet('{P}')
           WHERE language IS NOT NULL AND language<>'en'
           GROUP BY 1 ORDER BY n DESC LIMIT 8""")
LANG = {"es": "Spanish", "de": "German", "fr": "French", "it": "Italian",
        "hr": "Croatian", "pl": "Polish", "id": "Indonesian", "pt": "Portuguese",
        "ru": "Russian", "uk": "Ukrainian", "ja": "Japanese", "zh": "Chinese",
        "tr": "Turkish", "nl": "Dutch", "cs": "Czech", "sv": "Swedish"}
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
ax1.plot(ld.dec, ld.en, marker="o", lw=2, color=COLORS[0], label="English")
ax1.plot(ld.dec, ld.non_en, marker="o", lw=2, color=COLORS[1], label="Non-English")
ax1.set_title("English vs non-English share by decade\n(among works with language tagged)")
ax1.set_xlabel("Decade"); ax1.set_ylabel("% of works")
ax1.set_xticks(ld.dec)
ax1.set_xticklabels([f"{int(d)}s" for d in ld.dec], rotation=45)
ax1.set_ylim(0, 100); ax1.legend(); ax1.grid(True, alpha=0.3)
names = [LANG.get(l, l) for l in nl.language]
yp = np.arange(len(nl))[::-1]
ax2.barh(yp, nl.n, color=COLORS[1], alpha=0.85)
ax2.set_yticks(yp); ax2.set_yticklabels(names)
ax2.set_title("Top 8 non-English languages (all years)")
ax2.set_xlabel("Works")
ax2.xaxis.set_major_formatter(kfmt)
for y_, v in zip(yp, nl.n):
    ax2.text(v, y_, f" {int(v):,}", va="center", fontsize=9)
ax2.grid(True, axis="x", alpha=0.3)
save(fig, "language_share.png")
print("ENGLISH SHARE by decade (tagged works): 1900s="
      f"{float(ld.loc[ld.dec==1900,'en'].iloc[0]):.1f}%, "
      f"1980s={float(ld.loc[ld.dec==1980,'en'].iloc[0]):.1f}%, "
      f"2020s={float(ld.loc[ld.dec==2020,'en'].iloc[0]):.1f}%")
print("TOP NON-EN:", [(LANG.get(r.language, r.language), int(r.n)) for r in nl.itertuples()])

# ---------------------------------------------------------------- 11. OA share
oa = q(f"""SELECT publication_year AS y,
           100.0*AVG(CASE WHEN is_oa THEN 1 ELSE 0 END) AS oa
           FROM read_parquet('{P}')
           WHERE publication_year BETWEEN 1990 AND 2025
           GROUP BY 1 ORDER BY 1""")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(oa.y, oa.oa, lw=2, marker="o", ms=4, color=COLORS[2])
ax.set_title("Open-access share (is_oa = true) by publication year, 1990–2025")
ax.set_xlabel("Publication year"); ax.set_ylabel("% open access")
ax.set_ylim(0, max(60, oa.oa.max() * 1.15))
ax.grid(True, alpha=0.3)
save(fig, "oa_share_by_year.png")
print(f"OA SHARE: 1990={float(oa.loc[oa.y==1990,'oa'].iloc[0]):.1f}%, "
      f"2000={float(oa.loc[oa.y==2000,'oa'].iloc[0]):.1f}%, "
      f"2010={float(oa.loc[oa.y==2010,'oa'].iloc[0]):.1f}%, "
      f"2020={float(oa.loc[oa.y==2020,'oa'].iloc[0]):.1f}%, "
      f"2025={float(oa.loc[oa.y==2025,'oa'].iloc[0]):.1f}%")

print("ALL DONE")
