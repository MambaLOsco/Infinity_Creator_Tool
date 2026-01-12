"""Credits builder."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..ingest.license_gate import LicenseInfo


@dataclass
class CreditsBuilder:
    entries: List[LicenseInfo] = field(default_factory=list)

    def add_entry(self, info: LicenseInfo) -> None:
        self.entries.append(info)

    def __bool__(self) -> bool:
        return bool(self.entries)

    def render_markdown(self) -> str:
        lines = ["# Credits", ""]
        for entry in self.entries:
            creator = entry.creator or "Unknown creator"
            license_line = f"[{entry.license_code}]({entry.license_url})" if entry.license_url else entry.license_code
            lines.append(f"- **{entry.title}** by {creator} – {license_line}")
        return "\n".join(lines) + "\n"

    def to_dict(self) -> dict:
        return {
            "entries": [
                {
                    "title": entry.title,
                    "creator": entry.creator,
                    "license_code": entry.license_code,
                    "license_url": entry.license_url,
                    "source": entry.source,
                }
                for entry in self.entries
            ]
        }
