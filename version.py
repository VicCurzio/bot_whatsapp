"""
Version y novedades del Bot de WhatsApp.

CHANGELOG.md es la unica fuente de verdad: lo que se lee en GitHub es lo mismo
que ve el usuario en la ventana de novedades. El numero de version vive aca y
lo actualiza scripts/release.py, que ademas fecha la seccion del changelog.
"""

from __future__ import annotations

import re
from pathlib import Path

__version__ = "1.0.0"

BASE_DIR = Path(__file__).resolve().parent
CHANGELOG_PATH = BASE_DIR / "CHANGELOG.md"

# Donde se recuerda que version vio el usuario por ultima vez.
STATE_DIR = Path.home() / ".bot_whatsapp"
STATE_FILE = STATE_DIR / "last_version"

_VERSION_HEADING = re.compile(r"^##\s*\[([^\]]+)\]\s*(?:-\s*(\S+))?\s*$")
_SECTION_HEADING = re.compile(r"^###\s+(.+?)\s*$")
_BULLET = re.compile(r"^[-*]\s+(.*)$")


def get_releases() -> list[dict]:
    """Lee CHANGELOG.md y devuelve las versiones publicadas, de la mas nueva a
    la mas vieja. La seccion 'Sin publicar' se ignora."""
    try:
        raw = CHANGELOG_PATH.read_text(encoding="utf-8")
    except OSError:
        return []

    releases: list[dict] = []
    current: dict | None = None
    section: dict | None = None

    for line in raw.splitlines():
        version_match = _VERSION_HEADING.match(line)
        if version_match:
            current = {
                "version": version_match.group(1),
                "date": version_match.group(2),
                "sections": [],
            }
            section = None
            releases.append(current)
            continue

        if current is None:
            continue

        section_match = _SECTION_HEADING.match(line)
        if section_match:
            section = {"title": section_match.group(1), "items": []}
            current["sections"].append(section)
            continue

        bullet_match = _BULLET.match(line)
        if bullet_match:
            if section is None:
                section = {"title": "Novedades", "items": []}
                current["sections"].append(section)
            section["items"].append(bullet_match.group(1).strip())

    return [r for r in releases if r["version"].lower() not in ("sin publicar", "unreleased")]


def _parse_version(value: str) -> tuple[int, int, int]:
    parts = []
    for chunk in str(value).split(".")[:3]:
        digits = re.sub(r"\D", "", chunk)
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)  # type: ignore[return-value]


def compare_versions(a: str, b: str) -> int:
    """Negativo si a < b."""
    pa, pb = _parse_version(a), _parse_version(b)
    return (pa > pb) - (pa < pb)


def releases_since(last_seen: str | None) -> list[dict]:
    """Todo lo publicado despues de la version que el usuario vio."""
    releases = get_releases()
    if not last_seen:
        return []
    return [r for r in releases if compare_versions(r["version"], last_seen) > 0]


def read_last_seen() -> str | None:
    try:
        return STATE_FILE.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def write_last_seen(version: str = __version__) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(version, encoding="utf-8")
    except OSError:
        # No poder escribir el estado no puede romper la app: como mucho, las
        # novedades se muestran otra vez.
        pass


def format_releases(releases: list[dict]) -> str:
    """Texto plano para mostrar en una ventana o en la consola."""
    bloques = []
    for release in releases:
        cabecera = f"v{release['version']}"
        if release["date"]:
            cabecera += f"  -  {release['date']}"
        lineas = [cabecera, "-" * len(cabecera)]

        for section in release["sections"]:
            lineas.append("")
            lineas.append(section["title"].upper())
            for item in section["items"]:
                lineas.append(f"  - {item}")

        bloques.append("\n".join(lineas))

    return "\n\n\n".join(bloques)


def pending_notes() -> str:
    """Novedades que el usuario todavia no vio; cadena vacia si no hay."""
    pending = releases_since(read_last_seen())
    return format_releases(pending) if pending else ""
