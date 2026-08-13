#!/usr/bin/env python3
"""Refresh the stats blocks in README.md and index.html from the GitHub API.

Rewrites whatever sits between <!-- STATS:START --> and <!-- STATS:END --> in
both files, so the numbers are never hand-maintained. Run by
.github/workflows/stats.yml on a schedule; stdlib only, no dependencies.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

USER = os.environ.get("GH_USER", "ELATTAR-Ayoub")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = "https://api.github.com"

# github-linguist colours for the languages likely to show up
COLOURS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572a5",
    "CSS": "#663399", "HTML": "#e34c26", "Vue": "#41b883", "Dart": "#00b4ab",
    "Jupyter Notebook": "#da5b0b", "C#": "#178600", "Shell": "#89e051",
    "Java": "#b07219", "Go": "#00add8", "Rust": "#dea584", "SCSS": "#c6538c",
    "PHP": "#4f5d95", "Ruby": "#701516", "C++": "#f34b7d", "C": "#555555",
    "Svelte": "#ff3e00", "Kotlin": "#a97bff", "Swift": "#f05138",
}
FALLBACK = "#8b949e"


def get(path):
    req = urllib.request.Request(path if path.startswith("http") else API + path)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "stats-refresh")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode()), r.headers


def collect():
    user, _ = get(f"/users/{USER}")

    repos, page = [], 1
    while True:
        batch, _ = get(f"/users/{USER}/repos?per_page=100&type=owner&page={page}")
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    owned = [r for r in repos if not r["fork"]]

    totals = {}
    for r in owned:
        try:
            langs, _ = get(f"/repos/{r['full_name']}/languages")
        except urllib.error.HTTPError as e:
            print(f"  skip {r['full_name']}: HTTP {e.code}", file=sys.stderr)
            continue
        for k, v in langs.items():
            totals[k] = totals.get(k, 0) + v

    grand = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    top = [(k, 100 * v / grand) for k, v in ranked[:6]]
    rest = sum(v for _, v in ranked[6:])
    if rest:
        top.append(("Other", 100 * rest / grand))

    return {
        "languages": top,
        "repos": len(owned),
        "stars": sum(r["stargazers_count"] for r in owned),
        "followers": user["followers"],
        "since": user["created_at"][:4],
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


def markdown_block(s):
    rows = "\n".join(f"| {k} | {p:.1f}% |" for k, p in s["languages"])
    return (
        "| Language | Share |\n| --- | --- |\n" + rows + "\n\n"
        f"**{s['repos']}** repos &nbsp;·&nbsp; **{s['stars']}** stars &nbsp;·&nbsp; "
        f"**{s['followers']}** followers &nbsp;·&nbsp; on GitHub since **{s['since']}**\n\n"
        f"<sub>refreshed automatically · {s['updated']}</sub>"
    )


def html_block(s):
    rows = "\n".join(
        '          <div class="row"><span class="nm">{k}</span>'
        '<span class="track"><span class="fill" style="width:{p:.1f}%;background:{c}"></span></span>'
        '<span class="pc">{p:.1f}%</span></div>'.format(k=k, p=p, c=COLOURS.get(k, FALLBACK))
        for k, p in s["languages"]
    )
    return (
        '        <div class="bars">\n' + rows + "\n        </div>\n"
        '        <div class="figures">\n'
        f'          <div><b data-stat="repos">{s["repos"]}</b><span>repos</span></div>\n'
        f'          <div><b data-stat="stars">{s["stars"]}</b><span>stars</span></div>\n'
        f'          <div><b data-stat="followers">{s["followers"]}</b><span>followers</span></div>\n'
        f'          <div><b>{s["since"]}</b><span>since</span></div>\n'
        "        </div>"
    )


def splice(path, block):
    src = open(path, encoding="utf-8").read()
    out, n = re.subn(
        r"(<!-- STATS:START -->).*?(<!-- STATS:END -->)",
        lambda m: m.group(1) + "\n" + block + "\n" + m.group(2),
        src, flags=re.S,
    )
    if not n:
        raise SystemExit(f"{path}: STATS markers not found")
    if out != src:
        open(path, "w", encoding="utf-8", newline="\n").write(out)
        print(f"  updated {path}")
        return True
    print(f"  {path} already current")
    return False


if __name__ == "__main__":
    stats = collect()
    print(f"repos={stats['repos']} stars={stats['stars']} "
          f"followers={stats['followers']} since={stats['since']}")
    for lang, pct in stats["languages"]:
        print(f"  {lang:20s} {pct:5.1f}%")
    changed = splice("README.md", markdown_block(stats))
    changed |= splice("index.html", html_block(stats))
    print("changed" if changed else "no change")
