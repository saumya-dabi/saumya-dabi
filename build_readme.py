#!/usr/bin/env python3
"""Regenerate the GitHub profile README (saumya-dabi/saumya-dabi).

Sections that change on their own:
  - Latest writing   <- live blog feed (only posts that are actually published)
  - Recently active  <- GitHub API, public non-fork repos by last push
Writes README.md only; committing is done by the runner, and only on change.
"""
from __future__ import annotations

import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://saumya-dabi-portfolio.vercel.app"
USER = "saumya-dabi"

FEATURED = [  # (repo, one-line pitch) — hand-curated; descriptions come from the repo when blank
    ("creditlens", ""),
    ("jd-fit-engine", ""),
    ("pm-agents", ""),
    ("vault-rag", ""),
    ("synapse-case-study", ""),
]


def fetch(url: str, token: str | None = None):
    headers = {"User-Agent": "profile-readme"}
    if token:
        headers["Authorization"] = f"token {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return r.read()


def latest_posts(n: int = 5) -> list[tuple[str, str, str]]:
    root = ET.fromstring(fetch(f"{SITE}/blog/feed.xml"))
    items = root.findall(".//item")
    out = []
    for it in items[:n]:
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        date = (it.findtext("pubDate") or "").strip()
        out.append((title, link, " ".join(date.split()[1:4]) if date else ""))
    return out


def repos(token: str | None) -> dict[str, dict]:
    data = json.loads(fetch(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner", token))
    return {r["name"]: r for r in data if not r["fork"] and not r["private"] and r["name"] != USER}


def token() -> str | None:
    t = os.environ.get("GITHUB_TOKEN")
    if t:
        return t
    env = Path.home() / ".hermes" / ".env"
    for line in env.read_text().splitlines() if env.exists() else []:
        if line.startswith("GITHUB_TOKEN="):
            return line.split("=", 1)[1].strip().strip("'\"")
    return None


def main() -> None:
    tok = token()
    rp = repos(tok)
    featured = []
    for name, pitch in FEATURED:
        if name in rp:
            r = rp[name]
            featured.append(f"| [**{name}**]({r['html_url']}) | {pitch or r['description'] or ''} |")
    recent = sorted(rp.values(), key=lambda r: r["pushed_at"], reverse=True)[:4]
    posts = latest_posts()

    md = f"""### Hi, I'm Saumya 👋

Product manager who ships with AI agents. I take AI-native products from nothing to production:
discovery, the spec and the evals, then the build with AI coding agents.

- **Now:** Senior Product Consultant at Alpha Realm Consulting (Mumbai)
- **Before:** IncrediPets · CreditQ · Overlayy · ShowTime Consulting · B.Tech, IIT Kanpur
- **Focus:** AI product · technical product · 0→1 · data and evals

[Portfolio]({SITE}) · [Writing]({SITE}/blog) · [Email](mailto:saumyadabi7@gmail.com)

#### Selected work

| Project | What it is |
|---|---|
""" + "\n".join(featured) + f"""

#### Latest writing

""" + "\n".join(f"- [{t}]({l}) <sub>{d}</sub>" for t, l, d in posts) + f"""

[All posts →]({SITE}/blog)

#### Recently active

""" + "\n".join(f"- [{r['name']}]({r['html_url']}) <sub>updated {r['pushed_at'][:10]}</sub>" for r in recent) + """

<sub>This README rebuilds itself from my blog feed and the GitHub API; it changes only when they do.</sub>
"""
    (ROOT / "README.md").write_text(md)
    print(md)


if __name__ == "__main__":
    main()
