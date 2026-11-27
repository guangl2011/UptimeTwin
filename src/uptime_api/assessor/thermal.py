"""Deterministic thermal-buffer analysis — time to service loss (RDS v1.2 M3-C).

The protected space is a thermal capacitor. While supply capacity exceeds
demand nothing moves; after the worst single fault the deficit heats (or
warms) the space:

    C_th * dT/dt = Q_load - Q_cap
    tau_b = C_th * (T_limit - T_now) / (Q_load - Q_cap_after_fault)

``C_th`` (kJ/K) comes from D9 — room volume + product thermal mass for cold
storage, coolant loop volume for liquid-cooled halls, UPS ride-through for
power services. Pure functions over an immutable snapshot: same graph in,
same buffer numbers out, every value traced to the node attributes that
produced it.

Simplifications (stated, not hidden): capacity is the steady-state sum of
the service's direct suppliers; the "worst single fault" is the largest
capacity one of them can lose (a redundant group member loses only its own
share, an unprotected supplier loses everything upstream of it — already
captured by that capacity). Load-sharing-dependent risk-rate growth
(lambda up as survivors pick up load) is a reliability-rate effect tracked
separately from this capacity model and does not change tau_b here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from uptime_api.graph.enums import NodeType

if TYPE_CHECKING:
    from uptime_api.assessor.schemas import EvidenceCitation, Finding, ThermalExposure
    from uptime_api.assessor.scoring import _Topology
    from uptime_api.graph.schemas import NodeOut


def _attr_float(node_attributes: dict[str, object], key: str) -> float | None:
    value = node_attributes.get(key)
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _capacity_kw(node_attributes: dict[str, object]) -> float | None:
    for key in ("capacity_kw", "rated_kw"):
        value = _attr_float(node_attributes, key)
        if value is not None:
            return value
    return None


def _direct_supplier_capacities(topology: _Topology, service_key: str) -> list[tuple[str, float]]:
    """Direct asset suppliers of a service: (asset_key, capacity_kw).

    Suppliers with no declared capacity are skipped — the thermal model
    never guesses a number it was not given.
    """
    suppliers: list[tuple[str, float]] = []
    for edge in topology.in_edges.get(service_key, []):
        node = topology.nodes_by_key[edge.from_node]
        if node.node_type is not NodeType.ASSET:
            continue
        capacity = _capacity_kw(node.attributes)
        if capacity is not None:
            suppliers.append((edge.from_node, capacity))
    return sorted(suppliers)


def assess_thermal(topology: _Topology) -> dict[str, ThermalExposure]:
    """Thermal exposure per service key; services without coupling omitted."""
    from uptime_api.assessor.schemas import ThermalExposure

    exposures: dict[str, ThermalExposure] = {}
    for node in sorted(topology.snapshot.nodes, key=lambda n: n.node_key):
        if node.node_type is not NodeType.SERVICE:
            continue
        attributes = node.attributes
        ride_through_min = _attr_float(attributes, "ride_through_min")
        c_th = _attr_float(attributes, "thermal_mass_kj_per_k")
        load_kw = _attr_float(attributes, "load_kw")
        t_now = _attr_float(attributes, "temp_now_c")
        t_limit = _attr_float(attributes, "temp_limit_c")
        response_hours = _attr_float(attributes, "response_hours")

        thermal_coupled = (
            c_th is not None and load_kw is not None and t_now is not None and t_limit is not None
        )
        if not thermal_coupled and ride_through_min is None:
            continue

        suppliers = _direct_supplier_capacities(topology, node.node_key)
        q_cap_healthy = sum(capacity for _, capacity in suppliers)
        worst_asset, worst_loss = None, 0.0
        if suppliers:
            worst_asset, worst_loss = max(suppliers, key=lambda item: item[1])
        q_cap_after = q_cap_healthy - worst_loss

        buffer_healthy: float | None = None
        buffer_after: float | None = None
        if c_th is not None and load_kw is not None and t_now is not None and t_limit is not None:
            headroom_k = max(0.0, t_limit - t_now)
            healthy_deficit_kw = max(0.0, load_kw - q_cap_healthy)
            after_deficit_kw = max(0.0, load_kw - q_cap_after)
            if healthy_deficit_kw > 0:
                buffer_healthy = c_th * headroom_k / healthy_deficit_kw / 3600.0
            if after_deficit_kw > 0:
                buffer_after = c_th * headroom_k / after_deficit_kw / 3600.0
        elif ride_through_min is not None:
            # Power service: the buffer is the UPS ride-through — the time
            # the protected load survives after the worst power-chain fault.
            buffer_healthy = ride_through_min / 60.0
            buffer_after = buffer_healthy

        exposures[node.node_key] = ThermalExposure(
            q_load_kw=load_kw,
            q_cap_healthy_kw=q_cap_healthy if suppliers else None,
            q_cap_after_worst_fault_kw=q_cap_after if suppliers else None,
            worst_fault_asset=worst_asset,
            buffer_hours_healthy=buffer_healthy,
            buffer_hours_after_worst_fault=buffer_after,
            ride_through_min=ride_through_min,
            response_hours=response_hours,
            thermal_mass_kj_per_k=c_th,
            temp_now_c=t_now,
            temp_limit_c=t_limit,
        )
    return exposures


def detect_thermal_findings(
    topology: _Topology,
    service_tier: dict[str, str],
    thermal: dict[str, ThermalExposure],
) -> list[Finding]:
    """Tier C services whose post-fault buffer is shorter than the response
    time (S-1.1 T=3): the fault wins the race to the limit unless someone
    moves faster. Treated as data gaps, not risk assertions, when response
    time is unknown."""
    from uptime_api.assessor.enums import FindingKind
    from uptime_api.assessor.schemas import Finding

    findings: list[Finding] = []
    for service_key, exposure in sorted(thermal.items()):
        if service_tier.get(service_key) != "C":
            continue
        buffer_after = exposure.buffer_hours_after_worst_fault
        if buffer_after is None:
            continue  # no post-fault deficit: nothing races a limit
        response = exposure.response_hours
        if response is None:
            continue  # unscored response time: abstain, do not assert
        if buffer_after >= response:
            continue
        node = topology.nodes_by_key[service_key]
        title = (
            f"{service_key} buffer ({buffer_after:.1f} h) "
            f"< response time ({response:g} h)"
        )
        if exposure.ride_through_min is not None and exposure.q_load_kw is None:
            # Ride-through path: the buffer is UPS ride-through minutes, not a
            # thermal-mass deficit, so there are no kW figures to cite.
            detail = (
                f"Tier C service {service_key}: the ride-through buffer "
                f"({buffer_after:.1f} h) expires before the {response:g} h "
                "response time — shrink the response (staged parts / on-site "
                "spares) or add ride-through capacity; see RDS S-1.5."
            )
        else:
            detail = (
                f"Tier C service {service_key}: after the worst single fault "
                f"(loss of {exposure.worst_fault_asset}), the remaining capacity "
                f"{exposure.q_cap_after_worst_fault_kw:g} kW falls below the "
                f"{exposure.q_load_kw:g} kW demand and the protected space reaches "
                f"its limit in {buffer_after:.1f} h — shorter than the {response:g} h "
                "response time. Shrink the response (staged parts / on-site spares) "
                "or add capacity; see RDS S-1.5."
            )
        findings.append(
            Finding(
                kind=FindingKind.THERMAL_BUFFER_SHORT,
                subject=service_key,
                title=title,
                detail=detail,
                affected_services=[service_key],
                evidence=[_service_citation(node)],
            )
        )
    return findings


def _service_citation(node: NodeOut) -> EvidenceCitation:
    """Re-export of the node citation for finding evidence construction."""
    from uptime_api.assessor.scoring import _node_citation

    return _node_citation(node)
