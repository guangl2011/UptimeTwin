"""Service criticality tiering — RDS v1.2 S-1 (C x K x T with overrides).

The tiering object is the SERVICE, not the asset: "freezer room A stays
below -18 C", "GPU hall A coolant supply", "critical branch power". Assets
inherit the highest tier of the services they support (the assessor's
exposure map already links them).

Three scoring dimensions (S-1.1):
  C  consequence of service loss, 1-5 — declared per service (D3/D12
     grounding); unscored services default to 3 and say so.
  K  coupling, 1-3 — derived from the topology's redundancy semantics:
     2N with members  = 1 (immediate full backup in place),
     N+1              = 2 (redundant but margin <= one unit),
     N / no redundancy = 3 (load-sharing survivors or first-fault loss).
  T  time, 1-3 — buffer time vs response time:
     buffer >= 5x response = 1, 1-5x = 2, buffer < response = 3.
     No declared thermal/ride-through coupling counts as unbounded (T=1,
     the comfort-HVAC case) and says so — absence of data is not urgency.

CI = C x K x T (1-45). Tier rules (S-1.2), override order:
  1. life-safety service -> Tier C, always.
  2. contractual SLA penalty -> at least Tier B.
  3. C >= 4 and (K = 3 or T = 3) -> C.
  4. CI >= 18 and C >= 3 -> C.
  5. C <= 2 and CI <= 6 -> A.
  6. otherwise B.
Deterministic, explainable: every rule that fired is a named driver.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from uptime_api.assessor.enums import ServiceTier
from uptime_api.graph.enums import RedundancyConfig

if TYPE_CHECKING:
    from uptime_api.assessor.schemas import TierAssessment
    from uptime_api.assessor.scoring import _Topology
    from uptime_api.graph.schemas import EdgeOut, NodeOut

# Unscaled-consequence default: an unscored service asserts consequence 3
# ("obvious economic loss") rather than inventing precision it lacks.
DEFAULT_CONSEQUENCE = 3
# Typical detect + travel + restore when the operator has not scored it.
DEFAULT_RESPONSE_HOURS = 4.0

_SLA_ATTR = "sla"
_CONSEQUENCE_ATTR = "consequence"
_LIFE_SAFETY_ATTR = "life_safety"
_RESPONSE_ATTR = "response_hours"


def coupling_dimension(topology: _Topology, incoming: list[EdgeOut]) -> tuple[int, list[str]]:
    """K (1-3) from the service's supply redundancy, with drivers.

    S-1.1 semantics: K=1 when a full backup path is in place (2N);
    K=2 for N+1 with margin still left after the first loss (>= 3 members);
    K=3 when the first fault exhausts the redundancy (2-member N+1, whose
    survivor picks up full load) or the path is unprotected.
    """
    drivers: list[str] = []
    if not incoming:
        return 3, ["no supply edges — coupling scored 3 (first fault loses service)"]
    if any(not topology.edge_tolerates_single_fault(edge) for edge in incoming):
        return 3, ["unprotected supply path — first fault reaches the service (K=3)"]
    if any(edge.redundancy_config is RedundancyConfig.N2 for edge in incoming):
        drivers.append("2N supply — full backup path in place (K=1)")
        return 1, drivers
    smallest_group = min(
        (topology.group_sizes.get(edge.member_group, 1) for edge in incoming if edge.member_group),
        default=1,
    )
    if smallest_group >= 3:
        drivers.append(
            f"N+1 supply with margin left after the first loss "
            f"(smallest group {smallest_group} members) — K=2"
        )
        return 2, drivers
    drivers.append(
        "N+1 pair — the first fault exhausts redundancy and the survivor "
        "picks up the full load (K=3)"
    )
    return 3, drivers


def time_dimension(buffer_hours: float | None, response_hours: float) -> tuple[int, list[str]]:
    """T (1-3) from buffer-vs-response; None buffer = unbounded (T=1)."""
    if buffer_hours is None:
        return 1, ["no thermal/ride-through coupling declared — buffer unbounded (T=1)"]
    if buffer_hours >= 5.0 * response_hours:
        return 1, [f"buffer {buffer_hours:.1f} h >= 5x response {response_hours:g} h (T=1)"]
    if buffer_hours >= response_hours:
        return 2, [f"buffer {buffer_hours:.1f} h within 1-5x response {response_hours:g} h (T=2)"]
    return 3, [f"buffer {buffer_hours:.1f} h < response {response_hours:g} h (T=3)"]


def _attr_flag(attributes: dict[str, object], key: str) -> bool:
    value = attributes.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _attr_int(attributes: dict[str, object], key: str, default: int) -> tuple[int, bool]:
    value = attributes.get(key)
    if isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 5:
        return int(value), True
    return default, False


def tier_service(
    topology: _Topology,
    node: NodeOut,
    buffer_hours: float | None,
) -> TierAssessment:
    """Tier one service node."""
    from uptime_api.assessor.schemas import TierAssessment

    attributes = node.attributes
    incoming = topology.in_edges.get(node.node_key, [])

    consequence, consequence_scored = _attr_int(attributes, _CONSEQUENCE_ATTR, DEFAULT_CONSEQUENCE)
    response = _number(attributes, _RESPONSE_ATTR, DEFAULT_RESPONSE_HOURS)
    life_safety = _attr_flag(attributes, _LIFE_SAFETY_ATTR)
    sla = _attr_flag(attributes, _SLA_ATTR)

    coupling, k_drivers = coupling_dimension(topology, incoming)
    time_dim, t_drivers = time_dimension(buffer_hours, response)
    ci = consequence * coupling * time_dim

    drivers = list(k_drivers) + list(t_drivers)
    if consequence_scored:
        drivers.append(f"consequence scored {consequence} (C={consequence})")
    else:
        drivers.append(
            f"consequence not scored — defaulted to {DEFAULT_CONSEQUENCE}; "
            "add the service's consequence rating to replace the default"
        )

    tier = _classify(
        consequence=consequence,
        coupling=coupling,
        time_dim=time_dim,
        ci=ci,
        life_safety=life_safety,
        sla=sla,
        drivers=drivers,
    )
    return TierAssessment(
        tier=tier,
        ci=ci,
        consequence=consequence,
        coupling=coupling,
        time_dim=time_dim,
        life_safety=life_safety,
        sla=sla,
        drivers=drivers,
    )


def _number(attributes: dict[str, object], key: str, default: float) -> float:
    value = attributes.get(key)
    if isinstance(value, bool) or value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    return default


def _classify(
    consequence: int,
    coupling: int,
    time_dim: int,
    ci: int,
    life_safety: bool,
    sla: bool,
    drivers: list[str],
) -> ServiceTier:
    """S-1.2 rules in override order; every fired rule becomes a driver."""
    tier: ServiceTier | None = None

    if life_safety:
        tier = ServiceTier.C
        drivers.append("life-safety service — forced Tier C (S-1.2 coverage rule 1)")
    elif consequence >= 4 and (coupling == 3 or time_dim == 3):
        tier = ServiceTier.C
        drivers.append(
            f"C={consequence} >= 4 with K={coupling}/T={time_dim} in the worst band — Tier C"
        )
    elif ci >= 18 and consequence >= 3:
        tier = ServiceTier.C
        drivers.append(f"CI={ci} >= 18 with C={consequence} >= 3 — Tier C")

    if tier is None:
        if consequence <= 2 and ci <= 6:
            tier = ServiceTier.A
            drivers.append(f"C={consequence} <= 2 and CI={ci} <= 6 — Tier A")
        else:
            tier = ServiceTier.B
            drivers.append(f"CI={ci} — Tier B (remainder class)")

    if sla and tier is ServiceTier.A:
        tier = ServiceTier.B
        drivers.append("contractual SLA penalty — raised to at least Tier B (S-1.2 rule 2)")

    return tier
