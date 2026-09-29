"""Citation audit (Blocker 5): every citation in main.tex must resolve
against references.bib; list unused entries."""
import re
import sys

tex = open("paper/arr2026/main.tex", encoding="utf-8").read()
cited = set()
for m in re.finditer(r"\\cite[tp]?\*?\{([^}]+)\}", tex):
    cited.update(k.strip() for k in m.group(1).split(","))
bib = open("paper/arr2026/references.bib", encoding="utf-8").read()
keys = set(re.findall(r"@\w+\{([^,]+),", bib))
missing = cited - keys
unused = keys - cited
print("cited:", len(cited), "in bib:", len(keys))
print("MISSING:", sorted(missing))
print("unused:", sorted(unused))
sys.exit(1 if missing else 0)
