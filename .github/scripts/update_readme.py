import os
import re
import requests
from datetime import datetime, timezone, timedelta

GITHUB_USERNAME = "Subrata0Ghosh"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

# ── Fetch public repos sorted by last push ─────────────────────────────────
url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos?sort=pushed&direction=desc&per_page=20&type=owner"
response = requests.get(url, headers=headers)
repos = response.json()

if not isinstance(repos, list):
    print(f"API Error: {repos}")
    exit(1)

# Filter out forks and the profile repo itself, take top 5 active
filtered = [
    r for r in repos
    if not r.get("fork")
    and r["name"].lower() != GITHUB_USERNAME.lower()
    and not r.get("archived")
][:5]

# ── Status indicator ────────────────────────────────────────────────────────
def get_status(pushed_at: str) -> str:
    dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    age = datetime.now(timezone.utc) - dt
    if age < timedelta(days=3):
        return "🟢 Active"
    elif age < timedelta(days=14):
        return "🟡 In Progress"
    elif age < timedelta(days=60):
        return "🔵 Maintenance"
    else:
        return "⚫ Paused"

# ── Language emoji map ──────────────────────────────────────────────────────
LANG_EMOJI = {
    "Dart": "🦋 Dart",
    "Flutter": "🦋 Flutter",
    "Python": "🐍 Python",
    "JavaScript": "⚡ JavaScript",
    "TypeScript": "🔷 TypeScript",
    "Java": "☕ Java",
    "Kotlin": "🎯 Kotlin",
    "Swift": "🍎 Swift",
    "HTML": "🌐 HTML",
    "CSS": "🎨 CSS",
    "C": "⚙ C",
    "C++": "⚙ C++",
    "Shell": "🐚 Shell",
}

def fmt_lang(lang):
    if not lang:
        return "—"
    return LANG_EMOJI.get(lang, f"`{lang}`")

# ── Build table rows ────────────────────────────────────────────────────────
rows = []
for repo in filtered:
    name    = repo["name"]
    desc    = (repo.get("description") or "No description")[:55]
    if len(repo.get("description") or "") > 55:
        desc += "…"
    lang    = fmt_lang(repo.get("language"))
    stars   = repo.get("stargazers_count", 0)
    forks   = repo.get("forks_count", 0)
    link    = repo["html_url"]
    status  = get_status(repo["pushed_at"])
    pushed  = repo["pushed_at"][:10]

    rows.append(
        f"| [**`{name}`**]({link}) | {desc} | {lang} | ⭐{stars} 🍴{forks} | {status} | `{pushed}` |"
    )

table_header = (
    "| 🚀 Repository | 📝 Description | 🛠 Language | 📊 Stats | 📡 Status | 📅 Pushed |\n"
    "|:---|:---|:---:|:---:|:---:|:---:|"
)

table_body = "\n".join(rows) if rows else "| No recent activity found | — | — | — | — | — |"

now_ist = (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).strftime("%d %b %Y · %I:%M %p IST")

dynamic_block = f"""{table_header}
{table_body}

<sub>🤖 Auto-updated by GitHub Actions · Last refresh: **{now_ist}**</sub>"""

# ── Inject into README ──────────────────────────────────────────────────────
readme_path = "README.md"
with open(readme_path, "r", encoding="utf-8") as f:
    content = f.read()

pattern = r"<!-- RECENTLY_ACTIVE:START -->.*?<!-- RECENTLY_ACTIVE:END -->"
replacement = f"<!-- RECENTLY_ACTIVE:START -->\n{dynamic_block}\n<!-- RECENTLY_ACTIVE:END -->"

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content == content:
    print("⚠️  Markers not found in README.md — nothing updated.")
else:
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"✅ README updated with {len(filtered)} repos at {now_ist}")
