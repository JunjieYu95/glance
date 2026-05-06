"""Per-component SQL migration runner.

Each component owns `skills/<name>/migrations/*.sql`. Files are applied in
lexicographic order. Applied state is tracked in `_migrations`, keyed by
(component, name). Re-running is a no-op.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from .db import get_connection

_BOOTSTRAP_SQL = """
CREATE TABLE IF NOT EXISTS _migrations (
    component  TEXT NOT NULL,
    name       TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (component, name)
);
"""


def _bootstrap(conn: sqlite3.Connection) -> None:
    conn.executescript(_BOOTSTRAP_SQL)
    conn.commit()


def _applied(conn: sqlite3.Connection, component: str) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM _migrations WHERE component = ?",
        (component,),
    ).fetchall()
    return {row["name"] for row in rows}


def _migration_files(migrations_dir: Path) -> list[Path]:
    if not migrations_dir.is_dir():
        return []
    return sorted(p for p in migrations_dir.glob("*.sql") if p.is_file())


def apply_component_migrations(component: str, migrations_dir: Path, conn: sqlite3.Connection | None = None) -> list[str]:
    """Apply all unapplied migrations for one component. Returns names applied."""
    own_conn = conn is None
    conn = conn or get_connection()
    try:
        _bootstrap(conn)
        already = _applied(conn, component)
        applied: list[str] = []
        for path in _migration_files(migrations_dir):
            if path.name in already:
                continue
            sql = path.read_text(encoding="utf-8")
            try:
                conn.executescript(sql)
                conn.execute(
                    "INSERT INTO _migrations (component, name) VALUES (?, ?)",
                    (component, path.name),
                )
                conn.commit()
                applied.append(path.name)
            except sqlite3.Error as exc:
                conn.rollback()
                raise RuntimeError(f"Migration {component}/{path.name} failed: {exc}") from exc
        return applied
    finally:
        if own_conn:
            conn.close()


def apply_all_migrations(skills_root: Path, components: Iterable[str] | None = None) -> dict[str, list[str]]:
    """Walk skills_root and apply every component's migrations. Idempotent."""
    conn = get_connection()
    try:
        _bootstrap(conn)
        results: dict[str, list[str]] = {}
        component_dirs = (
            [skills_root / c for c in components]
            if components is not None
            else sorted(p for p in skills_root.iterdir() if p.is_dir())
        )
        for comp_dir in component_dirs:
            if not comp_dir.is_dir():
                continue
            name = comp_dir.name
            applied = apply_component_migrations(name, comp_dir / "migrations", conn=conn)
            if applied:
                results[name] = applied
        return results
    finally:
        conn.close()


if __name__ == "__main__":
    import json
    import sys

    skills_root = Path(__file__).resolve().parents[2] / "skills"
    if len(sys.argv) > 1:
        skills_root = Path(sys.argv[1]).resolve()
    print(json.dumps(apply_all_migrations(skills_root), indent=2))
