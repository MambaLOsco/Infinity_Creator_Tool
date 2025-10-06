"""Credits and attribution helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from ..ingest.license_gate import LicenseProbe, NormalizedLicense


@dataclass
class CreditLine:
    """Represents an attribution line."""

    title: str
    creator: str
    license_name: str
    license_url: str

    def render(self) -> str:
        return f"- {self.title} by {self.creator} ({self.license_name}) {self.license_url}"


def build_credits(
    *,
    title: str,
    creator: str,
    license_probe: LicenseProbe,
    description: str | None = None,
) -> List[CreditLine]:
    lines: List[CreditLine] = []
    if license_probe.attribution_required:
        lines.append(
            CreditLine(
                title=title,
                creator=creator,
                license_name=license_probe.name,
                license_url=license_probe.url,
            )
        )
    return lines


def render_credits(lines: Iterable[CreditLine]) -> str:
    header = "# Credits\n"
    body = "\n".join(line.render() for line in lines) or "- No attribution required."
    return header + body + "\n"
