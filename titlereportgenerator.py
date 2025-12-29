import re
import sys
import csv
from urllib.parse import urljoin

import requests
import pandas as pd
from bs4 import BeautifulSoup

URL = "https://www.bg-wiki.com/ffxi/Titles"
BASE = "https://www.bg-wiki.com"

# Paste your title list exactly as you provided it (one per line)
# The missing titles I included here are just an EXAMPLE.
# Please:
# 1.) Delete the 5 lines of missing titles that I included on lines 21-25
# 2.) Copy/paste your missing titles in their place.
# 3.) Run python titlereportgenerator.py

RAW_TITLES = r"""
A Friend Indeed
Accomplished Alchemist
Visitor to Abyssea
Warrior of Abyssea
Waterway Exemplar
""".strip()


def normalize_title(s: str) -> str:
    """
    Normalizes user input + BG-wiki title text so mojibake/star glyph differences match.
    We REMOVE star glyphs (☆/★/etc) and known mojibake sequences, then normalize whitespace.
    """
    s = str(s).replace("\u2019", "'")  # curly apostrophe -> straight
    s = s.replace("A?â,¢", "")
    s = s.replace("A?Å¡", "")
    s = s.replace("™", "")
    s = s.replace("š", "")
    # remove common star glyphs
    s = re.sub(r"[★☆✦✩✪✫✬✭✮✯]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def cell_links(td) -> list[str]:
    links = []
    for a in td.find_all("a", href=True):
        href = urljoin(BASE, a["href"])
        links.append(href)
    # de-dup while preserving order
    seen = set()
    out = []
    for h in links:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def sanitize_td_keep_anchors(td) -> str:
    """
    Return TD inner HTML, but keep only <a> and <br> tags (unwrap everything else).
    Also convert hrefs to absolute URLs.
    """
    soup = BeautifulSoup(str(td), "lxml")
    td2 = soup.find("td") or soup

    # absolute hrefs
    for a in td2.find_all("a", href=True):
        a["href"] = urljoin(BASE, a["href"])

    # unwrap all tags except a/br
    for tag in list(td2.find_all(True)):
        if tag.name not in ("a", "br"):
            tag.unwrap()

    html = td2.decode_contents()
    html = html.replace("\n", " ").strip()
    html = re.sub(r"\s{2,}", " ", html)
    return html


def load_titles_table_with_links() -> pd.DataFrame:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; titles-extractor/1.0)"
    }
    resp = requests.get(URL, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    target_table = None
    for table in soup.find_all("table"):
        ths = [th.get_text(" ", strip=True) for th in table.find_all("th")]
        if len(ths) >= 3 and ths[0] == "Titles" and ths[1] == "How to obtain" and ths[2] == "Title NPC":
            target_table = table
            break

    if target_table is None:
        raise RuntimeError("Could not locate the Titles / How to obtain / Title NPC table.")

    rows = []
    for tr in target_table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) != 3:
            continue

        title = tds[0].get_text(" ", strip=True)
        how_text = tds[1].get_text(" ", strip=True)
        how_html = sanitize_td_keep_anchors(tds[1])
        how_links = " | ".join(cell_links(tds[1]))
        npc = tds[2].get_text(" ", strip=True)

        rows.append({
            "Title": title,
            "HowToObtain": how_text,
            "HowToObtainHTML": how_html,
            "HowToObtainLinks": how_links,
            "TitleNPC": npc,
        })

    return pd.DataFrame(rows)


def add_enemy_tag(df: pd.DataFrame) -> pd.DataFrame:
    def tag(row):
        how = str(row["HowToObtain"])
        npc = str(row["TitleNPC"]).strip()
        if how.startswith("Enemy"):
            return "Abyssea Enemy" if npc == "Zuah Lepahnyu" else "Non-Abyssea Enemy"
        return ""
    df["EnemyTag"] = df.apply(tag, axis=1)
    return df


def escape(s: str) -> str:
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def make_sortable_html(df: pd.DataFrame, out_path: str):
    # IMPORTANT: HowToObtainHTML is inserted RAW (do not escape) so links remain clickable.
    html_rows = "\n".join(
        "<tr>"
        f"<td>{escape(r.Title)}</td>"
        f"<td>{r.HowToObtainHTML}</td>"
        f"<td>{escape(r.TitleNPC)}</td>"
        f"<td>{escape(r.EnemyTag)}</td>"
        "</tr>"
        for r in df.itertuples(index=False)
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>FFXI Titles (Filtered)</title>
<style>
table {{ border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; }}
th, td {{ border: 1px solid #aaa; padding: 6px 10px; vertical-align: top; }}
th {{ cursor: pointer; background: #f0f0f0; user-select: none; }}
th:hover {{ background: #e0e0e0; }}
#rowCount {{ margin-bottom: 8px; font-weight: bold; }}
</style>
</head>
<body>

<div id="rowCount">Rows: 0</div>

<table id="titlesTable">
  <thead>
    <tr>
      <th onclick="sortTable(0)">Title</th>
      <th onclick="sortTable(1)">How to Obtain</th>
      <th onclick="sortTable(2)">Title NPC</th>
      <th onclick="sortTable(3)">Enemy Tag</th>
    </tr>
  </thead>
  <tbody>
{html_rows}
  </tbody>
</table>

<script>
function updateRowCount() {{
  const table = document.getElementById("titlesTable");
  const count = table.tBodies[0].rows.length;
  document.getElementById("rowCount").innerText = "Rows: " + count;
}}

function sortTable(col) {{
  const table = document.getElementById("titlesTable");
  let rows = Array.from(table.tBodies[0].rows);

  const asc =
    table.getAttribute("data-sort-col") != col ||
    table.getAttribute("data-sort-dir") !== "asc";

  table.setAttribute("data-sort-col", col);
  table.setAttribute("data-sort-dir", asc ? "asc" : "desc");

  rows.sort((a, b) => {{
    const x = a.cells[col].innerText.toLowerCase();
    const y = b.cells[col].innerText.toLowerCase();
    return asc ? x.localeCompare(y) : y.localeCompare(x);
  }});

  rows.forEach(r => table.tBodies[0].appendChild(r));
  updateRowCount();
}}

updateRowCount();
</script>

</body>
</html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    wanted_raw = [x.strip() for x in RAW_TITLES.splitlines() if x.strip()]
    wanted_norm = [normalize_title(x) for x in wanted_raw]
    wanted_set = set(wanted_norm)

    df = load_titles_table_with_links()
    df["_TitleNorm"] = df["Title"].map(normalize_title)

    filtered = df[df["_TitleNorm"].isin(wanted_set)].copy()
    filtered.drop(columns=["_TitleNorm"], inplace=True)

    # preserve your input order
    order_index = {t: i for i, t in enumerate(wanted_norm)}
    filtered["_order"] = filtered["Title"].map(lambda t: order_index.get(normalize_title(t), 10**9))
    filtered.sort_values("_order", inplace=True)
    filtered.drop(columns=["_order"], inplace=True)

    filtered = add_enemy_tag(filtered)

    # CSV: keep readable text + also include link URLs
    csv_df = filtered[["Title", "HowToObtain", "HowToObtainLinks", "TitleNPC", "EnemyTag"]].copy()
    csv_df.to_csv("titles_filtered.csv", index=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)

    # HTML: keep clickable anchors in HowToObtainHTML
    html_df = filtered[["Title", "HowToObtainHTML", "TitleNPC", "EnemyTag"]].copy()
    make_sortable_html(html_df, "titles_filtered.html")

    # report missing
    found_norm = set(filtered["Title"].map(normalize_title))
    missing = [t for t in wanted_raw if normalize_title(t) not in found_norm]
    if missing:
        print("\nWARNING: Not found (check spelling/encoding):")
        for t in missing:
            print(" -", t)

    print("\nWrote:")
    print(" - titles_filtered.csv")
    print(" - titles_filtered.html")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e)
        sys.exit(1)
