"""Seed the two 1M sq ft demo facilities into a running API.

    .venv/bin/python scripts/seed_demo.py [--base-url http://localhost:8000]

Idempotent: existing facilities with the same id are skipped. After
seeding, run one assessment per facility so the console cockpit has a
scored report to read.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib import error, request

SEEDS = [
    Path(__file__).resolve().parents[1] / "seed" / "cold_chain_mega_1msf.json",
    Path(__file__).resolve().parents[1] / "seed" / "aidc_campus_1msf.json",
]


def call(base: str, method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    req = request.Request(
        f"{base}{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req) as res:
            body = res.read().decode()
            return res.status, json.loads(body) if body else {}
    except error.HTTPError as err:
        return err.code, json.loads(err.read().decode() or "{}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    for seed_path in SEEDS:
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        facility_id = seed["facility_id"]
        status, _ = call(base, "GET", f"/facilities/{facility_id}")
        if status == 200:
            print(f"[seed] {facility_id} exists — skipping create")
        else:
            status, body = call(
                base,
                "POST",
                "/facilities",
                {"id": facility_id, "name": seed["name"], "segment": seed["segment"]},
            )
            assert status == 201, body
            print(f"[seed] created {facility_id} ({seed['segment']})")

        status, body = call(
            base,
            "POST",
            f"/facilities/{facility_id}/graph/versions",
            {
                "author": seed["author"],
                "notes": seed["notes"],
                "nodes": seed["nodes"],
                "edges": seed["edges"],
            },
        )
        if status == 201:
            print(
                f"[seed] graph v{body['version_no']} committed: "
                f"{len(seed['nodes'])} nodes, {len(seed['edges'])} edges"
            )
        elif status == 422 and "already" in body.get("detail", "").lower():
            print(f"[seed] graph already committed for {facility_id} — skipping")
        else:
            raise SystemExit(f"[seed] commit failed: {status} {body}")

        status, body = call(base, "POST", f"/facilities/{facility_id}/assessments", {})
        assert status == 201, body
        print(
            f"[seed] assessment v{body['graph_version']}: "
            f"{len(body['services'])} services, {len(body['assets'])} assets, "
            f"{len(body['findings'])} findings"
        )
        for service in body["services"]:
            tier = service.get("tier")
            thermal = service.get("thermal")
            buffer_txt = (
                f", tau_b={thermal['buffer_hours_after_worst_fault']:.1f} h post-fault"
                if thermal and thermal.get("buffer_hours_after_worst_fault") is not None
                else ", no post-fault deficit"
                if thermal
                else ""
            )
            print(
                f"  - {service['service_id']}: "
                f"tier={tier['tier'] if tier else '?'} CI={tier['ci'] if tier else '?'}"
                f"{buffer_txt}"
            )


if __name__ == "__main__":
    main()
