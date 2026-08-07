#!/usr/bin/env python3
"""
Cierra una version: sube el numero en version.py, convierte la seccion
"Sin publicar" del CHANGELOG en una version fechada y deja todo listo para
commitear.

    python scripts/release.py patch      # 1.0.0 -> 1.0.1  (arreglos)
    python scripts/release.py minor      # 1.0.0 -> 1.1.0  (cosas nuevas)
    python scripts/release.py major      # 1.0.0 -> 2.0.0  (cambio grande)
    python scripts/release.py 2.1.0      # numero exacto

Opciones:
    --dry     muestra que haria, sin escribir nada
    --tag     ademas crea el commit y el tag de git vX.Y.Z

Sin dependencias a proposito: solo biblioteca estandar.
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_PATH = ROOT / "version.py"
CHANGELOG_PATH = ROOT / "CHANGELOG.md"

VERSION_LINE = re.compile(r'^__version__\s*=\s*"([^"]+)"', re.MULTILINE)
UNRELEASED = re.compile(r"^##\s*\[(Sin publicar|Unreleased)\]\s*$", re.MULTILINE | re.IGNORECASE)
NEXT_HEADING = re.compile(r"^##\s*\[", re.MULTILINE)


def fail(message: str) -> None:
    print(f"\nError: {message}\n", file=sys.stderr)
    sys.exit(1)


def next_version(current: str, kind: str) -> str:
    if re.fullmatch(r"\d+\.\d+\.\d+", kind):
        return kind

    major, minor, patch = (int(p) for p in current.split("."))
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    if kind == "patch":
        return f"{major}.{minor}.{patch + 1}"

    fail(f'no entiendo "{kind}". Usa major, minor, patch o un numero tipo 2.1.0.')
    raise AssertionError  # inalcanzable, calla al type checker


def main() -> None:
    args = sys.argv[1:]
    dry_run = "--dry" in args
    should_tag = "--tag" in args
    bump = next((a for a in args if not a.startswith("--")), "patch")

    version_source = VERSION_PATH.read_text(encoding="utf-8")
    match_version = VERSION_LINE.search(version_source)
    if not match_version:
        fail("no encontre __version__ en version.py.")

    current = match_version.group(1)
    version = next_version(current, bump)

    changelog = CHANGELOG_PATH.read_text(encoding="utf-8")
    match_unreleased = UNRELEASED.search(changelog)
    if not match_unreleased:
        fail('no encontre la seccion "## [Sin publicar]" en CHANGELOG.md.')

    start = match_unreleased.end()
    rest = changelog[start:]
    next_match = NEXT_HEADING.search(rest)
    notes = (rest[: next_match.start()] if next_match else rest).strip()

    if not notes:
        fail(
            'la seccion "Sin publicar" esta vacia.\n'
            "Agrega al menos una linea contando que cambio, en palabras del usuario.\n"
            "Ejemplo:\n\n  ### Agregado\n  - Ahora se puede pausar el envio.\n"
        )

    if dry_run:
        print(f"\nVersion: {current} -> {version}")
        print(f"Fecha:   {date.today().isoformat()}")
        print("\nNotas que se publican:\n")
        print("\n".join(f"  {line}" for line in notes.splitlines()))
        print("\n(--dry: no se escribio nada)\n")
        return

    VERSION_PATH.write_text(
        VERSION_LINE.sub(f'__version__ = "{version}"', version_source, count=1),
        encoding="utf-8",
    )

    # El \n final garantiza una linea en blanco entre el encabezado nuevo y las
    # notas que quedaban debajo de "Sin publicar".
    heading = match_unreleased.group(0)
    CHANGELOG_PATH.write_text(
        changelog.replace(
            heading, f"{heading}\n\n## [{version}] - {date.today().isoformat()}\n", 1
        ),
        encoding="utf-8",
    )

    print(f"\nVersion {version} lista.")
    print("  version.py actualizado")
    print("  CHANGELOG.md actualizado")

    if should_tag:
        try:
            subprocess.run(["git", "add", "version.py", "CHANGELOG.md"], cwd=ROOT, check=True)
            subprocess.run(["git", "commit", "-m", f"Release v{version}"], cwd=ROOT, check=True)
            subprocess.run(["git", "tag", f"v{version}"], cwd=ROOT, check=True)
            print(f"  commit y tag v{version} creados")
        except subprocess.CalledProcessError:
            print("  no se pudo commitear/taggear (hay cambios sin guardar?)")
    else:
        print(f"\nFalta: revisar, commitear y taggear.\n  git tag v{version}\n")


if __name__ == "__main__":
    main()
