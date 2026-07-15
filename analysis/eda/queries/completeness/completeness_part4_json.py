import gzip, json, collections

FP = "/project/def-kmcel/hridansh/openalex_econ/data/archive/2000s/econ_2020.jsonl.gz"
N = 2000

top = collections.Counter()          # key -> count present (non-null)
top_seen = collections.Counter()     # key -> count key exists at all
auth0 = collections.Counter()
auth0_n = 0
ploc = collections.Counter()
ploc_n = 0
ploc_src = collections.Counter()
ploc_src_n = 0
n = 0

def nonempty(v):
    return v is not None and v != [] and v != {} and v != ""

with gzip.open(FP, "rt") as f:
    for line in f:
        if n >= N:
            break
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        n += 1
        for k, v in rec.items():
            top_seen[k] += 1
            if nonempty(v):
                top[k] += 1
        a = rec.get("authorships")
        if isinstance(a, list) and a:
            auth0_n += 1
            for k, v in a[0].items():
                if nonempty(v):
                    auth0[k] += 1
        pl = rec.get("primary_location")
        if isinstance(pl, dict):
            ploc_n += 1
            for k, v in pl.items():
                if nonempty(v):
                    ploc[k] += 1
            src = pl.get("source")
            if isinstance(src, dict):
                ploc_src_n += 1
                for k, v in src.items():
                    if nonempty(v):
                        ploc_src[k] += 1

print(f"records parsed: {n}")
print(f"\n=== TOP-LEVEL KEYS ({len(top_seen)} distinct): key | present_nonempty% ===")
for k in sorted(top_seen, key=lambda x: -top[x]):
    print(f"{k}: {100.0*top[k]/n:.1f}%")

print(f"\n=== authorships[0] keys (over {auth0_n} recs with >=1 authorship) ===")
for k, c in auth0.most_common():
    print(f"{k}: {100.0*c/auth0_n:.1f}%")

print(f"\n=== primary_location keys (over {ploc_n} recs) ===")
for k, c in ploc.most_common():
    print(f"{k}: {100.0*c/ploc_n:.1f}%")

print(f"\n=== primary_location.source keys (over {ploc_src_n} recs) ===")
for k, c in ploc_src.most_common():
    print(f"{k}: {100.0*c/ploc_src_n:.1f}%")

# small peek at a couple of rich nested fields' shapes
with gzip.open(FP, "rt") as f:
    rec = json.loads(f.readline())
kshow = ["topics", "grants", "biblio", "open_access", "counts_by_year", "referenced_works",
         "keywords", "sustainable_development_goals", "apc_list", "apc_paid", "indexed_in",
         "corresponding_author_ids", "corresponding_institution_ids", "locations_count", "fwci",
         "citation_normalized_percentile", "cited_by_percentile_year"]
print("\n=== EXAMPLE SHAPES (record 1) ===")
for k in kshow:
    if k in rec:
        v = rec[k]
        s = json.dumps(v)[:220]
        print(f"{k}: {s}")
