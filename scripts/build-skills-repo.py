#!/usr/bin/env python3
"""Packages curated skills from ~/.claude/skills into this repo.

The INCLUDE list is the curation: nothing outside it is touched, and adding
a skill to the hub means adding its slug here AND a card in the site's
lib/skills-hub-catalog.ts. Run from anywhere:

    python3 scripts/build-skills-repo.py

Idempotent; each run replaces skills/<slug> wholesale. Committing and
pushing stays manual on purpose: the sanitization scan below only WARNS,
and a human reads its output before anything becomes public.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

SOURCE = Path.home() / ".claude" / "skills"
REPO = Path(__file__).resolve().parent.parent
DEST = REPO / "skills"

INCLUDE = [
    # תוכן וסושיאל
    "hook-generator",
    "content-scripter",
    "content-ideator",
    "competitor-research",
    "competitor-analyst",
    "shortform-analysis",
    "youtube-competitor-analysis",
    "repurpose",
    "summarize",
    # וידאו
    "video-analyzer",
    "video-downloader",
    "video-transcriber",
    "seedance-prompt",
    # קמפיינים ממומנים
    "ad-copywriter",
    "scrape-ads",
    "ad-brief",
    "meta-ads-setup",
    "meta-ads-upload",
    # קופי ושיווק
    "sales-page-copy",
    "landing-page-cro",
    "landing-page-blueprint",
    "copy-editing",
    "email-copywriting",
    "marketing-ideas",
    # כלים לקלוד
    "my-business",
    "install-rtl-extension",
    "comment-to-dm",          # hand-maintained here, see HAND_MAINTAINED below
]

# Skills authored directly in this repo rather than copied from ~/.claude/skills.
# comment-to-dm is the generic, credential-free rewrite of a private skill: its
# live twin carries real account ids, keywords and DM copy, so it must never be
# packed from the machine. The copy loop skips these and the stray sweep keeps
# them, but the sanitization scan still reads them.
HAND_MAINTAINED = {"comment-to-dm"}

# Never ship: personal state, credentials, caches, junk. raw-transcripts/
# holds Omer's own footage transcripts plus a third-party hook database,
# neither of which is being redistributed.
PRUNE_DIRS = {
    "state",
    "logs",
    "out",
    "node_modules",
    "__pycache__",
    ".git",
    "raw-transcripts",
    "backups",
}
PRUNE_FILES = {".DS_Store"}
PRUNE_GLOBS = [".env*", "*.log", "*.plist"]

# Warn-only scan. Matches are printed for a human to judge before pushing;
# plenty are benign (the word "token" in prose), which is why this never
# deletes anything on its own.
SUSPICIOUS = [
    (re.compile(r"sk-[A-Za-z0-9_-]{10,}"), "api-key-looking string"),
    (re.compile(r"Bearer\s+[A-Za-z0-9_\-.]{16,}"), "bearer token"),
    (re.compile(r"(secret|token|api[_-]?key)\s*[:=]\s*['\"][^'\"]{8,}", re.I), "assigned secret"),
    (re.compile(r"/Users/omer"), "absolute personal path"),
    (re.compile(r"omer1yaron"), "personal email/handle"),
    (re.compile(r"05\d[- ]?\d{7}"), "israeli phone number"),
]

TEXT_SUFFIXES = {".md", ".txt", ".py", ".sh", ".js", ".ts", ".json", ".yaml", ".yml", ".mdx", ".csv", ".html", ".css"}


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def prune(dest: Path) -> None:
    for path in sorted(dest.rglob("*"), reverse=True):
        if path.is_dir() and path.name in PRUNE_DIRS:
            shutil.rmtree(path)
        elif path.is_file():
            if path.name in PRUNE_FILES or any(path.match(g) for g in PRUNE_GLOBS):
                path.unlink()


def drop_pruned_pointers(dest: Path) -> None:
    """Removes lines that point at directories the prune pass deleted.

    hook-generator and content-scripter reference their local
    raw-transcripts/ as further reading; shipping the pointer without the
    files would send students hunting for something that is not there.
    """
    for path in dest.rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        kept = [line for line in text.splitlines() if "raw-transcripts" not in line]
        if len(kept) != text.count("\n") + 1:
            path.write_text("\n".join(kept) + "\n", encoding="utf-8")


def has_frontmatter(skill_md: Path) -> bool:
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    if end == -1:
        return False
    head = text[3:end]
    return "name:" in head and "description:" in head


def scan(dest: Path) -> list[str]:
    findings = []
    for path in dest.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for pattern, label in SUSPICIOUS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{path.relative_to(REPO)}:{line}  {label}: {match.group(0)[:60]}")
    return findings


def main() -> None:
    if not SOURCE.is_dir():
        fail(f"source not found: {SOURCE}")
    DEST.mkdir(exist_ok=True)

    for slug in INCLUDE:
        if slug in HAND_MAINTAINED:
            print(f"kept {slug} (hand-maintained in this repo)")
            continue
        src = SOURCE / slug
        if not src.is_dir():
            fail(f"skill not found locally: {src}")
        dest = DEST / slug
        if dest.exists():
            shutil.rmtree(dest)
        # symlinks=False dereferences: 18 local skills are symlinks into
        # ~/.agents/skills and would otherwise arrive broken.
        shutil.copytree(src, dest, symlinks=False)
        prune(dest)
        drop_pruned_pointers(dest)

        skill_md = dest / "SKILL.md"
        if not skill_md.is_file():
            fail(f"{slug}: no SKILL.md")
        if not has_frontmatter(skill_md):
            fail(
                f"{slug}: SKILL.md has no YAML frontmatter with name+description. "
                "Add it by hand in the SOURCE skill, then re-run."
            )
        print(f"packed {slug}")

    # Anything in skills/ that is no longer curated gets removed, so the
    # repo always mirrors INCLUDE exactly.
    for stray in DEST.iterdir():
        if stray.is_dir() and stray.name not in INCLUDE and stray.name not in HAND_MAINTAINED:
            shutil.rmtree(stray)
            print(f"removed stray {stray.name}")

    findings = scan(DEST)
    print(f"\n{len(INCLUDE)} skills packed into {DEST}")
    if findings:
        print(f"\nREVIEW BEFORE PUSHING ({len(findings)} suspicious hits):")
        for f in findings:
            print(f"  {f}")
    else:
        print("sanitization scan: clean")


if __name__ == "__main__":
    main()
