"""Walk skills/ and return components in dashboard order.

A component is any folder with a `component.toml`. Nothing else needs
registering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib  # py311+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


@dataclass
class Component:
    name: str
    path: Path
    config: dict[str, Any] = field(default_factory=dict)

    @property
    def title(self) -> str:
        return self.config.get("component", {}).get("title", self.name)

    @property
    def panel_enabled(self) -> bool:
        return bool(self.config.get("panel", {}).get("enabled", True))

    @property
    def panel_order(self) -> int:
        return int(self.config.get("panel", {}).get("order", 100))

    @property
    def freshness_hours(self) -> float | None:
        v = self.config.get("panel", {}).get("freshness_hours")
        return float(v) if v is not None else None

    @property
    def cron(self) -> dict[str, Any] | None:
        c = self.config.get("cron")
        return c if c else None

    @property
    def migrations_dir(self) -> Path:
        return self.path / "migrations"

    @property
    def stats_script(self) -> Path:
        return self.path / "scripts" / "stats.py"


def load_component(path: Path) -> Component | None:
    cfg_path = path / "component.toml"
    if not cfg_path.is_file():
        return None
    with cfg_path.open("rb") as fh:
        cfg = tomllib.load(fh)
    declared = cfg.get("component", {}).get("name")
    name = declared or path.name
    if declared and declared != path.name:
        raise ValueError(f"component.toml name {declared!r} does not match folder {path.name!r}")
    return Component(name=name, path=path, config=cfg)


def discover_components(skills_root: Path, panel_only: bool = False) -> list[Component]:
    components: list[Component] = []
    for child in sorted(p for p in skills_root.iterdir() if p.is_dir()):
        comp = load_component(child)
        if comp is None:
            continue
        if panel_only and not comp.panel_enabled:
            continue
        components.append(comp)
    components.sort(key=lambda c: (c.panel_order, c.name))
    return components


if __name__ == "__main__":
    import json
    import sys

    skills_root = Path(__file__).resolve().parents[2] / "skills"
    if len(sys.argv) > 1:
        skills_root = Path(sys.argv[1]).resolve()
    out = [
        {
            "name": c.name,
            "title": c.title,
            "order": c.panel_order,
            "panel_enabled": c.panel_enabled,
            "cron": c.cron,
        }
        for c in discover_components(skills_root)
    ]
    print(json.dumps(out, indent=2))
