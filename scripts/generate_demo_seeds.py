"""Generate the two 1M sq ft demo seed facilities (RDS v1.2 case studies).

Outputs seed JSON files consumed by scripts/seed_demo.py and the onboarding
scanner. Every node/edge carries provenance pointing at its case-study
section, so each demo number resolves to a written claim. Run:

    .venv/bin/python scripts/generate_demo_seeds.py
"""

from __future__ import annotations

import json
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parents[1] / "seed"


def prov(kind: str, system: str, ref: str) -> dict:
    return {"source_kind": kind, "source_system": system, "source_ref": ref}


def node(
    key: str,
    name: str,
    asset_type: str | None,
    location: str,
    attributes: dict,
    ref: str,
    kind: str = "inventory_import",
) -> dict:
    return {
        "node_key": key,
        "name": name,
        "node_type": "asset" if asset_type else "service",
        "asset_type": asset_type,
        "location": location,
        "attributes": attributes,
        "provenance": prov(kind, "case_study", ref),
    }


def edge(frm: str, to: str, mode: str, config: str | None, group: str | None, ref: str) -> dict:
    return {
        "from_node": frm,
        "to_node": to,
        "failure_mode": mode,
        "redundancy_config": config,
        "member_group": group,
        "provenance": prov("technician_entry", "case_study", ref),
    }


def build_cold_chain() -> dict:
    """Arctic Plains Cold Distribution Center — 1,000,000 sq ft, central
    low-charge ammonia plant, four temperature zones plus a quick-turn annex."""
    ref = "case-studies/cold-chain-1msf"
    nodes: list[dict] = []
    edges: list[dict] = []

    # --- Power: two full trains (2N) behind N+1 generators -----------------
    nodes += [
        node(
            "UTILITY-A",
            "Utility feed A (138 kV)",
            "utility_feed",
            "site entrance",
            {},
            f"{ref}#power",
        ),
        node(
            "UTILITY-B",
            "Utility feed B (138 kV)",
            "utility_feed",
            "site entrance",
            {},
            f"{ref}#power",
        ),
        node(
            "GEN-1",
            "Standby generator 1 (2.5 MW diesel)",
            "generator",
            "gen yard",
            {"rated_kw": 2500, "fuel": "diesel"},
            f"{ref}#power",
        ),
        node(
            "GEN-2",
            "Standby generator 2 (2.5 MW diesel)",
            "generator",
            "gen yard",
            {"rated_kw": 2500, "fuel": "diesel"},
            f"{ref}#power",
        ),
        node(
            "ATS-A", "Automatic transfer switch A", "ats", "electrical room A", {}, f"{ref}#power"
        ),
        node(
            "ATS-B", "Automatic transfer switch B", "ats", "electrical room B", {}, f"{ref}#power"
        ),
        node(
            "UPS-A",
            "UPS train A (15 min battery)",
            "ups",
            "electrical room A",
            {"battery_minutes": 15, "rated_kva": 1500},
            f"{ref}#power",
        ),
        node(
            "UPS-B",
            "UPS train B (15 min battery)",
            "ups",
            "electrical room B",
            {"battery_minutes": 15, "rated_kva": 1500},
            f"{ref}#power",
        ),
        node(
            "PDU-A",
            "PDU train A (12 MVA)",
            "pdu",
            "electrical room A",
            {"capacity_kw": 12000},
            f"{ref}#power",
        ),
        node(
            "PDU-B",
            "PDU train B (12 MVA)",
            "pdu",
            "electrical room B",
            {"capacity_kw": 12000},
            f"{ref}#power",
        ),
    ]
    edges += [
        edge("UTILITY-A", "ATS-A", "power_loss", "2N", "sources_a", f"{ref}#power"),
        edge("GEN-1", "ATS-A", "power_loss", "N+1", "gens_a", f"{ref}#power"),
        edge("GEN-2", "ATS-A", "power_loss", "N+1", "gens_a", f"{ref}#power"),
        edge("UTILITY-B", "ATS-B", "power_loss", "2N", "sources_b", f"{ref}#power"),
        edge("GEN-1", "ATS-B", "power_loss", "N+1", "gens_a", f"{ref}#power"),
        edge("GEN-2", "ATS-B", "power_loss", "N+1", "gens_a", f"{ref}#power"),
        edge("ATS-A", "UPS-A", "power_loss", "N", None, f"{ref}#power"),
        edge("ATS-B", "UPS-B", "power_loss", "N", None, f"{ref}#power"),
        edge("UPS-A", "PDU-A", "power_loss", "N", None, f"{ref}#power"),
        edge("UPS-B", "PDU-B", "power_loss", "N", None, f"{ref}#power"),
    ]

    # --- Refrigeration: two central ammonia racks, N+1 condensers ----------
    nodes += [
        node(
            "RACK-A",
            "Freezer ammonia rack (3,000 kW)",
            "refrigeration_rack",
            "engine room",
            {"capacity_kw": 3000, "refrigerant": "R-717 (low-charge ammonia)"},
            f"{ref}#refrigeration",
            "oem_doc",
        ),
        node(
            "RACK-B",
            "Cooler ammonia rack (2,000 kW)",
            "refrigeration_rack",
            "engine room",
            {"capacity_kw": 2000, "refrigerant": "R-717 (low-charge ammonia)"},
            f"{ref}#refrigeration",
            "oem_doc",
        ),
        node(
            "COMP-A1",
            "Freezer compressor A1 (1,200 kW)",
            "compressor",
            "engine room",
            {"rated_kw": 1200},
            f"{ref}#refrigeration",
        ),
        node(
            "COMP-A2",
            "Freezer compressor A2 (1,200 kW)",
            "compressor",
            "engine room",
            {"rated_kw": 1200},
            f"{ref}#refrigeration",
        ),
        node(
            "COMP-A3",
            "Freezer compressor A3 (1,200 kW)",
            "compressor",
            "engine room",
            {"rated_kw": 1200},
            f"{ref}#refrigeration",
        ),
        node(
            "COMP-B1",
            "Cooler compressor B1 (1,100 kW)",
            "compressor",
            "engine room",
            {"rated_kw": 1100},
            f"{ref}#refrigeration",
        ),
        node(
            "COMP-B2",
            "Cooler compressor B2 (1,100 kW)",
            "compressor",
            "engine room",
            {"rated_kw": 1100},
            f"{ref}#refrigeration",
        ),
        node(
            "COND-1",
            "Evaporative condenser 1 (3,500 kW)",
            "condenser",
            "roof",
            {"capacity_kw": 3500},
            f"{ref}#refrigeration",
        ),
        node(
            "COND-2",
            "Evaporative condenser 2 (3,500 kW)",
            "condenser",
            "roof",
            {"capacity_kw": 3500},
            f"{ref}#refrigeration",
        ),
        node(
            "COND-3",
            "Evaporative condenser 3 (3,500 kW)",
            "condenser",
            "roof",
            {"capacity_kw": 3500},
            f"{ref}#refrigeration",
        ),
    ]
    edges += [
        edge("COMP-A1", "RACK-A", "mechanical_failure", "N+1", "comps_a", f"{ref}#refrigeration"),
        edge("COMP-A2", "RACK-A", "mechanical_failure", "N+1", "comps_a", f"{ref}#refrigeration"),
        edge("COMP-A3", "RACK-A", "mechanical_failure", "N+1", "comps_a", f"{ref}#refrigeration"),
        edge("COMP-B1", "RACK-B", "mechanical_failure", "N+1", "comps_b", f"{ref}#refrigeration"),
        edge("COMP-B2", "RACK-B", "mechanical_failure", "N+1", "comps_b", f"{ref}#refrigeration"),
        edge("COND-1", "RACK-A", "refrigerant_loss", "N+1", "condensers", f"{ref}#refrigeration"),
        edge("COND-2", "RACK-A", "refrigerant_loss", "N+1", "condensers", f"{ref}#refrigeration"),
        edge("COND-3", "RACK-A", "refrigerant_loss", "N+1", "condensers", f"{ref}#refrigeration"),
        edge("COND-1", "RACK-B", "refrigerant_loss", "N+1", "condensers", f"{ref}#refrigeration"),
        edge("COND-2", "RACK-B", "refrigerant_loss", "N+1", "condensers", f"{ref}#refrigeration"),
        edge("COND-3", "RACK-B", "refrigerant_loss", "N+1", "condensers", f"{ref}#refrigeration"),
    ]

    # --- Rooms and their evaporator banks -----------------------------------
    rooms = [
        ("FZ-A", "Freezer hall A (-20 C, 15,000 m2)", 850, 700, 2.2e8, -20, -15, 24, 5),
        ("FZ-B", "Freezer hall B (-20 C, 15,000 m2)", 850, 700, 2.2e8, -20, -15, 24, 5),
        ("FZ-C", "Freezer hall C (-20 C, 12,000 m2)", 700, 600, 1.9e8, -20, -15, 24, 5),
        ("CL-A", "Cooler hall A (+2 C, 8,000 m2)", 500, 450, 6.0e7, 2, 6, 24, 3),
    ]
    for key, label, load, evap_kw, c_th, t_now, t_limit, response, consequence in rooms:
        nodes += [
            node(
                f"EVAP-{key}",
                f"Evaporator bank {key} 1 ({evap_kw} kW)",
                "evaporator",
                label,
                {"capacity_kw": evap_kw},
                f"{ref}#rooms",
            ),
            node(
                f"EVAP-{key}-2",
                f"Evaporator bank {key} 2 ({evap_kw} kW)",
                "evaporator",
                label,
                {"capacity_kw": evap_kw},
                f"{ref}#rooms",
            ),
            node(
                f"ROOM-{key}",
                label,
                "cold_room",
                label,
                {"setpoint_c": t_now, "volume_m2": None},
                f"{ref}#rooms",
            ),
        ]
        edges += [
            edge(
                "RACK-A" if key.startswith("FZ") else "RACK-B",
                f"EVAP-{key}",
                "mechanical_failure",
                "N",
                None,
                f"{ref}#rooms",
            ),
            edge(
                "RACK-A" if key.startswith("FZ") else "RACK-B",
                f"EVAP-{key}-2",
                "mechanical_failure",
                "N",
                None,
                f"{ref}#rooms",
            ),
        ]
        # service: fed by the room's N+1 evaporator pair, protects the room
        svc_key = f"SVC-{key}"
        nodes.append(
            node(
                svc_key,
                f"{label} temperature hold",
                None,
                label,
                {
                    "consequence": consequence,
                    "sla": True,
                    "response_hours": response,
                    "load_kw": load,
                    "thermal_mass_kj_per_k": c_th,
                    "temp_now_c": t_now,
                    "temp_limit_c": t_limit,
                },
                f"{ref}#services",
                "technician_entry",
            )
        )
        edges += [
            edge(
                f"EVAP-{key}",
                svc_key,
                "mechanical_failure",
                "N+1",
                f"evaps_{key}",
                f"{ref}#services",
            ),
            edge(
                f"EVAP-{key}-2",
                svc_key,
                "mechanical_failure",
                "N+1",
                f"evaps_{key}",
                f"{ref}#services",
            ),
            edge(svc_key, f"ROOM-{key}", "refrigerant_loss", "N", None, f"{ref}#services"),
        ]

    # Quick-turn annex: single unprotected evaporator (a real SPOF) and a
    # lightly-loaded room that still buffers for days — cold chain races on
    # consequence, not on thermal time.
    nodes += [
        node(
            "EVAP-FZ-D",
            "Annex evaporator FZ-D (900 kW, single)",
            "evaporator",
            "annex quick-turn freezer",
            {"capacity_kw": 900},
            f"{ref}#annex",
        ),
        node(
            "ROOM-FZ-D",
            "Annex quick-turn freezer (-18 C, 4,000 m2)",
            "cold_room",
            "annex",
            {"setpoint_c": -18},
            f"{ref}#annex",
        ),
        node(
            "SVC-FZ-D",
            "Annex quick-turn freezer temperature hold",
            None,
            "annex",
            {
                "consequence": 4,
                "sla": True,
                "response_hours": 12,
                "load_kw": 600,
                "thermal_mass_kj_per_k": 2.5e7,
                "temp_now_c": -18,
                "temp_limit_c": -14,
            },
            f"{ref}#services",
            "technician_entry",
        ),
    ]
    edges += [
        edge("RACK-A", "EVAP-FZ-D", "mechanical_failure", "N", None, f"{ref}#annex"),
        edge("EVAP-FZ-D", "SVC-FZ-D", "mechanical_failure", "N", None, f"{ref}#services"),
        edge("SVC-FZ-D", "ROOM-FZ-D", "refrigerant_loss", "N", None, f"{ref}#services"),
    ]

    # --- Power service feeds the refrigeration plant ------------------------
    nodes.append(
        node(
            "SVC-POWER",
            "Facility power distribution (refrigeration + docks)",
            None,
            "site",
            {
                "consequence": 4,
                "sla": True,
                "response_hours": 4,
                "load_kw": 11000,
            },
            f"{ref}#services",
            "technician_entry",
        )
    )
    edges += [
        edge("PDU-A", "SVC-POWER", "power_loss", "2N", "pdu_trains", f"{ref}#power"),
        edge("PDU-B", "SVC-POWER", "power_loss", "2N", "pdu_trains", f"{ref}#power"),
        edge("SVC-POWER", "RACK-A", "power_loss", "N", None, f"{ref}#power"),
        edge("SVC-POWER", "RACK-B", "power_loss", "N", None, f"{ref}#power"),
    ]

    return {
        "facility_id": "arctic_plains_1msf",
        "name": "Arctic Plains Cold Distribution Center (1M sq ft)",
        "segment": "cold_chain",
        "author": "case_study_seed",
        "notes": (
            "RDS v1.2 demo: 1M sq ft cold-chain DC — 2N power trains, "
            "N+1 ammonia plant, four zones + quick-turn annex."
        ),
        "nodes": nodes,
        "edges": edges,
    }


def build_aidc() -> dict:
    """Meridian AI Campus — 1,000,000 sq ft, ~240 MW IT+mechanical, liquid
    cooled GB200-class halls (NVIDIA DSX anchor: 972,500 SF / 240 MW)."""
    ref = "case-studies/aidc-1msf"
    nodes: list[dict] = []
    edges: list[dict] = []

    # --- Power: 2N trains, 5+1 generator farm -------------------------------
    nodes += [
        node(
            "UTILITY-A", "Utility feed A (230 kV)", "utility_feed", "substation", {}, f"{ref}#power"
        ),
        node(
            "UTILITY-B", "Utility feed B (230 kV)", "utility_feed", "substation", {}, f"{ref}#power"
        ),
        *[
            node(
                f"GEN-{i}",
                f"Standby generator {i} (50 MW)",
                "generator",
                "gen yard",
                {"rated_kw": 50000, "fuel": "diesel"},
                f"{ref}#power",
            )
            for i in range(1, 6)
        ],
        node("ATS-A", "Automatic transfer switch A", "ats", "power room A", {}, f"{ref}#power"),
        node("ATS-B", "Automatic transfer switch B", "ats", "power room B", {}, f"{ref}#power"),
        node(
            "UPS-A1",
            "UPS train A1 (Scalable Unit A)",
            "ups",
            "power room A",
            {"battery_minutes": 15, "rated_kva": 50000},
            f"{ref}#power",
        ),
        node(
            "UPS-A2",
            "UPS train A2 (Scalable Unit A)",
            "ups",
            "power room A",
            {"battery_minutes": 15, "rated_kva": 50000},
            f"{ref}#power",
        ),
        node(
            "UPS-B1",
            "UPS train B1 (Scalable Unit B)",
            "ups",
            "power room B",
            {"battery_minutes": 15, "rated_kva": 50000},
            f"{ref}#power",
        ),
        node(
            "UPS-B2",
            "UPS train B2 (Scalable Unit B)",
            "ups",
            "power room B",
            {"battery_minutes": 15, "rated_kva": 50000},
            f"{ref}#power",
        ),
        node("PDU-A1", "PDU A1", "pdu", "power room A", {"capacity_kw": 100000}, f"{ref}#power"),
        node("PDU-A2", "PDU A2", "pdu", "power room A", {"capacity_kw": 100000}, f"{ref}#power"),
        node("PDU-B1", "PDU B1", "pdu", "power room B", {"capacity_kw": 100000}, f"{ref}#power"),
        node("PDU-B2", "PDU B2", "pdu", "power room B", {"capacity_kw": 100000}, f"{ref}#power"),
    ]
    edges += [
        edge("UTILITY-A", "ATS-A", "power_loss", "2N", "sources_a", f"{ref}#power"),
        edge("UTILITY-B", "ATS-B", "power_loss", "2N", "sources_b", f"{ref}#power"),
        *[
            edge(f"GEN-{i}", "ATS-A", "power_loss", "N+1", "gens", f"{ref}#power")
            for i in range(1, 6)
        ],
        *[
            edge(f"GEN-{i}", "ATS-B", "power_loss", "N+1", "gens", f"{ref}#power")
            for i in range(1, 6)
        ],
        edge("ATS-A", "UPS-A1", "power_loss", "N", None, f"{ref}#power"),
        edge("ATS-A", "UPS-A2", "power_loss", "N", None, f"{ref}#power"),
        edge("ATS-B", "UPS-B1", "power_loss", "N", None, f"{ref}#power"),
        edge("ATS-B", "UPS-B2", "power_loss", "N", None, f"{ref}#power"),
        edge("UPS-A1", "PDU-A1", "power_loss", "2N", "ups_a", f"{ref}#power"),
        edge("UPS-A2", "PDU-A2", "power_loss", "2N", "ups_a", f"{ref}#power"),
        edge("UPS-B1", "PDU-B1", "power_loss", "2N", "ups_b", f"{ref}#power"),
        edge("UPS-B2", "PDU-B2", "power_loss", "2N", "ups_b", f"{ref}#power"),
    ]

    # --- Cooling train: chillers (N+1) -> hall pumps (N+1) -> CDUs (N+1) ----
    nodes += [
        *[
            node(
                f"CH-{i}",
                f"Water-cooled chiller {i} (30 MW)",
                "chiller",
                "chiller plant",
                {"capacity_kw": 30000},
                f"{ref}#cooling",
            )
            for i in range(1, 5)
        ],
        node(
            "PUMP-A1",
            "Hall A chilled-water pump 1",
            "pump",
            "pump room A",
            {"capacity_kw": 40000},
            f"{ref}#cooling",
        ),
        node(
            "PUMP-A2",
            "Hall A chilled-water pump 2",
            "pump",
            "pump room A",
            {"capacity_kw": 40000},
            f"{ref}#cooling",
        ),
        node(
            "PUMP-B1",
            "Hall B chilled-water pump 1",
            "pump",
            "pump room B",
            {"capacity_kw": 40000},
            f"{ref}#cooling",
        ),
        node(
            "PUMP-B2",
            "Hall B chilled-water pump 2",
            "pump",
            "pump room B",
            {"capacity_kw": 40000},
            f"{ref}#cooling",
        ),
        *[
            node(
                f"CDU-A{i}",
                f"Hall A coolant distribution unit {i} (40 MW)",
                "cdu",
                "hall A",
                {"capacity_kw": 40000},
                f"{ref}#cooling",
            )
            for i in range(1, 4)
        ],
        *[
            node(
                f"CDU-B{i}",
                f"Hall B coolant distribution unit {i} (40 MW)",
                "cdu",
                "hall B",
                {"capacity_kw": 40000},
                f"{ref}#cooling",
            )
            for i in range(1, 4)
        ],
        node(
            "CRAH-1",
            "Power-room CRAH 1 (1,200 kW)",
            "crah",
            "power room A",
            {"capacity_kw": 1200},
            f"{ref}#power",
        ),
        node(
            "CRAH-2",
            "Power-room CRAH 2 (1,200 kW)",
            "crah",
            "power room B",
            {"capacity_kw": 1200},
            f"{ref}#power",
        ),
        node(
            "ROW-A",
            "GPU hall A — 768 GB200-class racks (80 MW IT)",
            "it_rack",
            "hall A",
            {"rated_kw": 80000},
            f"{ref}#it",
        ),
        node(
            "ROW-B",
            "GPU hall B — 768 GB200-class racks (80 MW IT)",
            "it_rack",
            "hall B",
            {"rated_kw": 80000},
            f"{ref}#it",
        ),
    ]
    edges += [
        *[
            edge(f"CH-{i}", pump, "mechanical_failure", "N+1", "chillers", f"{ref}#cooling")
            for i in range(1, 5)
            for pump in ("PUMP-A1", "PUMP-A2", "PUMP-B1", "PUMP-B2")
        ],
        *[
            edge("PUMP-A1", f"CDU-A{i}", "fluid_loss", "N+1", "pumps_a", f"{ref}#cooling")
            for i in range(1, 4)
        ],
        *[
            edge("PUMP-A2", f"CDU-A{i}", "fluid_loss", "N+1", "pumps_a", f"{ref}#cooling")
            for i in range(1, 4)
        ],
        *[
            edge("PUMP-B1", f"CDU-B{i}", "fluid_loss", "N+1", "pumps_b", f"{ref}#cooling")
            for i in range(1, 4)
        ],
        *[
            edge("PUMP-B2", f"CDU-B{i}", "fluid_loss", "N+1", "pumps_b", f"{ref}#cooling")
            for i in range(1, 4)
        ],
    ]

    # --- Services ------------------------------------------------------------
    # Power: 2N PDU trains + CRAH pair protect the IT load. Coolant: the loop
    # volume is the buffer — after the worst CDU fault the hall runs ~10 min
    # from its thermal limit. This is the load-sharing story of RDS M3-C.
    nodes += [
        node(
            "SVC-IT-POWER",
            "IT power distribution (both halls)",
            None,
            "site",
            {
                "consequence": 5,
                "sla": True,
                "response_hours": 4,
                "ride_through_min": 15,
            },
            f"{ref}#services",
            "technician_entry",
        ),
        node(
            "SVC-COOLANT-A",
            "Hall A coolant supply (FWS <= 32 C)",
            None,
            "hall A",
            {
                "consequence": 5,
                "sla": True,
                "response_hours": 4,
                "load_kw": 100000,
                "thermal_mass_kj_per_k": 7.6e5,
                "temp_now_c": 32,
                "temp_limit_c": 47,
            },
            f"{ref}#services",
            "technician_entry",
        ),
        node(
            "SVC-COOLANT-B",
            "Hall B coolant supply (FWS <= 32 C)",
            None,
            "hall B",
            {
                "consequence": 5,
                "sla": True,
                "response_hours": 4,
                "load_kw": 100000,
                "thermal_mass_kj_per_k": 7.6e5,
                "temp_now_c": 32,
                "temp_limit_c": 47,
            },
            f"{ref}#services",
            "technician_entry",
        ),
    ]
    edges += [
        edge("PDU-A1", "SVC-IT-POWER", "power_loss", "2N", "pdu_a", f"{ref}#power"),
        edge("PDU-A2", "SVC-IT-POWER", "power_loss", "2N", "pdu_a", f"{ref}#power"),
        edge("PDU-B1", "SVC-IT-POWER", "power_loss", "2N", "pdu_b", f"{ref}#power"),
        edge("PDU-B2", "SVC-IT-POWER", "power_loss", "2N", "pdu_b", f"{ref}#power"),
        edge("CRAH-1", "SVC-IT-POWER", "control_failure", "N+1", "crahs", f"{ref}#power"),
        edge("CRAH-2", "SVC-IT-POWER", "control_failure", "N+1", "crahs", f"{ref}#power"),
        *[
            edge(
                f"CDU-A{i}",
                "SVC-COOLANT-A",
                "mechanical_failure",
                "N+1",
                "cdu_a",
                f"{ref}#services",
            )
            for i in range(1, 4)
        ],
        *[
            edge(
                f"CDU-B{i}",
                "SVC-COOLANT-B",
                "mechanical_failure",
                "N+1",
                "cdu_b",
                f"{ref}#services",
            )
            for i in range(1, 4)
        ],
        edge("SVC-COOLANT-A", "ROW-A", "refrigerant_loss", "N", None, f"{ref}#services"),
        edge("SVC-COOLANT-B", "ROW-B", "refrigerant_loss", "N", None, f"{ref}#services"),
        edge("SVC-IT-POWER", "ROW-A", "power_loss", "N", None, f"{ref}#power"),
        edge("SVC-IT-POWER", "ROW-B", "power_loss", "N", None, f"{ref}#power"),
    ]

    return {
        "facility_id": "meridian_aidc_1msf",
        "name": "Meridian AI Campus (1M sq ft, ~240 MW)",
        "segment": "aidc",
        "author": "case_study_seed",
        "notes": (
            "RDS v1.2 demo: 1M sq ft AIDC — 2N power trains, 5+1 generators, "
            "N+1 chiller/CDU liquid-cooling train, ~10 min coolant buffer."
        ),
        "nodes": nodes,
        "edges": edges,
    }


def main() -> None:
    SEED_DIR.mkdir(exist_ok=True)
    for builder, filename in [
        (build_cold_chain, "cold_chain_mega_1msf.json"),
        (build_aidc, "aidc_campus_1msf.json"),
    ]:
        seed = builder()
        path = SEED_DIR / filename
        path.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        assets = sum(1 for n in seed["nodes"] if n["node_type"] == "asset")
        services = sum(1 for n in seed["nodes"] if n["node_type"] == "service")
        print(f"{path.name}: {assets} assets, {services} services, {len(seed['edges'])} edges")


if __name__ == "__main__":
    main()
