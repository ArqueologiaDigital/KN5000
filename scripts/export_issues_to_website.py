#!/usr/bin/env python3
"""
Export Beads issues to a Jekyll markdown page for the documentation website.

Reads .beads/issues.jsonl and generates a formatted markdown page with all
project issues organized by status and priority.

Usage:
    python export_issues_to_website.py [output_path]

Default output: ../kn5000-docs/issues.md
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Priority labels (0 = highest)
PRIORITY_LABELS = {
    0: "Critical",
    1: "High",
    2: "Medium",
    3: "Low",
}

# Category prefixes for grouping
CATEGORY_PREFIXES = {
    "Boot:": "Boot Sequence",
    "Sound:": "Sound & Audio",
    "Video:": "Video & Display",
    "Images:": "Image Extraction",
    "Update:": "Firmware Update",
    "SubCPU:": "Sub CPU",
    "HDAE5000:": "HD-AE5000 Expansion",
    "FeatureDemo:": "Feature Demo",
    "Control Panel": "Control Panel",
    "maincpu:": "Main CPU ROM",
    "subcpu:": "Sub CPU ROM",
    "table_data:": "Table Data ROM",
}


def load_issues(jsonl_path: Path) -> list:
    """Load issues from JSONL file."""
    issues = []
    with open(jsonl_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                issues.append(json.loads(line))
    return issues


def get_category(title: str) -> str:
    """Extract category from issue title."""
    for prefix, category in CATEGORY_PREFIXES.items():
        if title.startswith(prefix) or prefix in title:
            return category
    return "Other"


def format_date(iso_date: str) -> str:
    """Format ISO date to readable format."""
    if not iso_date:
        return ""
    try:
        dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d")
    except:
        return iso_date[:10] if len(iso_date) >= 10 else iso_date


def generate_markdown(issues: list) -> str:
    """Generate markdown content from issues."""
    # Separate open and closed issues
    open_issues = [i for i in issues if i.get('status') == 'open']
    closed_issues = [i for i in issues if i.get('status') == 'closed']

    # Sort by priority (lower = higher priority)
    open_issues.sort(key=lambda x: (x.get('priority', 99), x.get('title', '')))
    closed_issues.sort(key=lambda x: x.get('closed_at', ''), reverse=True)

    # Group open issues by category
    by_category = defaultdict(list)
    for issue in open_issues:
        category = get_category(issue.get('title', ''))
        by_category[category].append(issue)

    # Generate category anchor IDs
    def category_to_anchor(cat):
        return cat.lower().replace(' ', '-').replace('&', '').replace('--', '-')

    lines = [
        "---",
        "layout: page",
        "title: Project Issues",
        "permalink: /issues/",
        "---",
        "",
        "# Project Issues",
        "",
        "This page is auto-generated from the [Beads](https://github.com/beads-ai/beads) issue tracker.",
        "",
        f"**Total Issues:** {len(issues)} ({len(open_issues)} open, {len(closed_issues)} closed)",
        "",
        "**Quick Links:** ",
    ]

    # Add category quick links
    category_links = []
    for category in sorted(by_category.keys()):
        anchor = category_to_anchor(category)
        count = len(by_category[category])
        category_links.append(f"[{category}](#{anchor}) ({count})")
    lines.append(" · ".join(category_links))

    lines.extend([
        "",
        "---",
        "",
        "## Open Issues",
        "",
    ])

    # Generate open issues by category
    for category in sorted(by_category.keys()):
        cat_issues = by_category[category]
        anchor = category_to_anchor(category)
        lines.append(f"### {category} {{#{anchor}}}")
        lines.append("")

        for issue in cat_issues:
            issue_id = issue.get('id', '')
            title = issue.get('title', 'Untitled')
            priority = issue.get('priority', 99)
            priority_label = PRIORITY_LABELS.get(priority, f"P{priority}")
            description = issue.get('description', '')
            notes = issue.get('notes', '')
            created = format_date(issue.get('created_at', ''))

            # Priority badge
            if priority == 0:
                badge = "🔴"
            elif priority == 1:
                badge = "🟠"
            elif priority == 2:
                badge = "🟡"
            else:
                badge = "⚪"

            lines.append(f"#### {badge} {title} {{#issue-{issue_id}}}")
            lines.append("")
            lines.append(f"**ID:** `{issue_id}` | **Priority:** {priority_label} | **Created:** {created}")
            lines.append("")

            if description:
                lines.append(description)
                lines.append("")

            if notes:
                lines.append(f"**Notes:** {notes}")
                lines.append("")

            # Check for dependencies
            deps = issue.get('dependencies', [])
            if deps:
                blocking = [d['depends_on_id'] for d in deps if d.get('type') == 'blocks']
                if blocking:
                    links = [f"[`{b}`](#issue-{b})" for b in blocking]
                    lines.append(f"**Depends on:** {', '.join(links)}")
                    lines.append("")

            lines.append("---")
            lines.append("")

    # Generate closed issues summary
    if closed_issues:
        lines.append("## Recently Closed")
        lines.append("")
        lines.append("| Issue | Title | Closed |")
        lines.append("|-------|-------|--------|")

        for issue in closed_issues[:20]:  # Show last 20 closed
            issue_id = issue.get('id', '')
            title = issue.get('title', 'Untitled')
            # Truncate long titles
            if len(title) > 60:
                title = title[:57] + "..."
            closed = format_date(issue.get('closed_at', ''))
            lines.append(f"| `{issue_id}` | {title} | {closed} |")

        if len(closed_issues) > 20:
            lines.append("")
            lines.append(f"*...and {len(closed_issues) - 20} more closed issues*")

        lines.append("")

    # Statistics
    lines.extend([
        "---",
        "",
        "## Statistics",
        "",
        "### By Priority",
        "",
        "| Priority | Count |",
        "|----------|-------|",
    ])

    priority_counts = defaultdict(int)
    for issue in open_issues:
        p = issue.get('priority', 99)
        priority_counts[p] += 1

    for p in sorted(priority_counts.keys()):
        label = PRIORITY_LABELS.get(p, f"P{p}")
        lines.append(f"| {label} | {priority_counts[p]} |")

    lines.extend([
        "",
        "### By Category",
        "",
        "| Category | Count |",
        "|----------|-------|",
    ])

    for category in sorted(by_category.keys()):
        lines.append(f"| {category} | {len(by_category[category])} |")

    lines.extend([
        "",
        "---",
        "",
        f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
    ])

    return "\n".join(lines)


def main():
    script_dir = Path(__file__).parent
    repo_dir = script_dir.parent
    jsonl_path = repo_dir / ".beads" / "issues.jsonl"

    if len(sys.argv) > 1:
        output_path = Path(sys.argv[1])
    else:
        output_path = script_dir.parent / "kn5000-docs" / "issues.md"

    if not jsonl_path.exists():
        print(f"Error: Issues file not found: {jsonl_path}")
        sys.exit(1)

    print(f"Loading issues from: {jsonl_path}")
    issues = load_issues(jsonl_path)
    print(f"Found {len(issues)} issues")

    markdown = generate_markdown(issues)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(markdown)

    print(f"Exported to: {output_path}")

    # Count stats
    open_count = sum(1 for i in issues if i.get('status') == 'open')
    closed_count = sum(1 for i in issues if i.get('status') == 'closed')
    print(f"Open: {open_count}, Closed: {closed_count}")


if __name__ == "__main__":
    main()
