"""
Changelog tracking system to log manuscript formatting changes.
Supports explainable AI formatting reports.
"""

from typing import List, Dict, Optional
from datetime import datetime


class ChangeLog:
    """Tracks all formatting and structural changes made to a manuscript."""

    def __init__(self):
        self.changes: List[Dict] = []
        self.timestamp = datetime.now().isoformat()

    def add_change(
        self,
        category: str,
        old_value: str,
        new_value: str,
        reason: str,
        change_type: str = "auto_fix",
        severity: str = "info",
        field: Optional[str] = None,
    ):
        """
        Record a change made during formatting.

        Args:
            category: Type of change (abstract, citation, heading, formatting, reference)
            old_value: Original content/value
            new_value: Updated content/value
            reason: Explanation of why change was made
            change_type: auto_fix | suggestion | warning
            severity: info | warning | critical
            field: Optional field name (e.g. abstract, references, title)
        """

        change = {
            "category": category,
            "old_value": (old_value[:200] if old_value else ""),
            "new_value": (new_value[:200] if new_value else ""),
            "reason": reason,
            "change_type": change_type,
            "severity": severity,
            "field": field,
            "timestamp": datetime.now().isoformat(),
        }

        self.changes.append(change)

    def get_changes_by_category(self, category: str) -> List[Dict]:
        """Return changes belonging to a specific category."""
        return [c for c in self.changes if c["category"] == category]

    def get_summary(self) -> Dict:
        """Generate structured summary of changes."""

        categories = {}

        for change in self.changes:
            cat = change["category"]

            if cat not in categories:
                categories[cat] = []

            categories[cat].append(change)

        return {
            "total_changes": len(self.changes),
            "by_category": categories,
            "timestamp": self.timestamp,
        }

    def get_stats(self) -> Dict:
        """Generate quick statistics for dashboard."""

        stats = {
            "total_changes": len(self.changes),
            "auto_fixes": 0,
            "suggestions": 0,
            "warnings": 0,
        }

        for change in self.changes:
            if change["change_type"] == "auto_fix":
                stats["auto_fixes"] += 1
            elif change["change_type"] == "suggestion":
                stats["suggestions"] += 1
            elif change["change_type"] == "warning":
                stats["warnings"] += 1

        return stats

    def to_dict(self) -> Dict:
        """Convert full changelog to dictionary."""
        return {
            "timestamp": self.timestamp,
            "total_changes": len(self.changes),
            "changes": self.changes,
        }

    def to_markdown(self) -> str:
        """Generate human-readable markdown report of formatting changes."""

        md = "# Manuscript Formatting Report\n\n"

        md += f"**Generated:** {self.timestamp}\n\n"
        md += f"**Total Changes:** {len(self.changes)}\n\n"

        summary = self.get_summary()

        for category, changes in summary["by_category"].items():

            md += f"## {category.upper()}\n\n"

            for change in changes:

                md += f"- **Change:** `{change['old_value']}` -> `{change['new_value']}`\n"
                md += f"  - **Reason:** {change['reason']}\n"
                md += f"  - **Type:** {change['change_type']}\n"
                md += f"  - **Severity:** {change['severity']}\n\n"

        return md