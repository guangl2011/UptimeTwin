/**
 * API payload types, mirroring the FastAPI contracts (graph/schemas.py,
 * assessor/schemas.py). The backend is the source of truth — these are
 * hand-kept in sync and validated by tsc against real responses in dev.
 */

export type Segment = 'cold_chain' | 'aidc' | 'hospital'

export type NodeType = 'asset' | 'service'

export type RedundancyConfig = 'N' | 'N+1' | '2N'

export type SourceKind =
  | 'inventory_import'
  | 'technician_entry'
  | 'oem_doc'
  | 'alarm'
  | 'work_order'
  | 'sensor'

export type RiskLevel = 'low' | 'elevated' | 'high'

export type FindingKind =
  | 'single_point_of_failure'
  | 'missing_redundancy'
  | 'unserved_service'
  | 'life_safety_isolation'
  | 'thermal_buffer_short'

export interface Facility {
  id: string
  name: string
  segment: Segment
}

export interface Provenance {
  id: number
  source_kind: SourceKind
  source_system: string
  source_ref: string
}

export interface GraphNode {
  node_key: string
  node_type: NodeType
  asset_type: string | null
  name: string
  location: string | null
  attributes: Record<string, unknown>
  provenance: Provenance
}

export interface GraphEdge {
  from_node: string
  to_node: string
  failure_mode: string | null
  redundancy_config: RedundancyConfig | null
  member_group: string | null
  provenance: Provenance
}

export interface GraphSnapshot {
  facility_id: string
  version_no: number
  author: string
  notes: string | null
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface GraphVersionSummary {
  version_no: number
  author: string
  notes: string | null
  node_count: number
  edge_count: number
}

export interface UnresolvedRow {
  row: number
  reason: string
  detail: string
}

export interface InventoryPreview {
  filename: string
  parseable_nodes: number
  unresolved: UnresolvedRow[]
}

export interface InventoryImport {
  facility_id: string
  version_no: number
  nodes_created: number
  unresolved: UnresolvedRow[]
}

export interface EvidenceCitation {
  record_id: number
  kind: SourceKind
  claim: string
}

export interface CriticalityScore {
  score: number
  risk_level: RiskLevel
  drivers: string[]
}

export interface SpofEntry {
  asset_id: string
  reason: string
}

export interface Exposure {
  first_fault_tolerated: boolean
  concurrent_faults_tolerated: number
  unprotected_assets: string[]
}

/** RDS S-1 criticality tier: CI = consequence x coupling x time. */
export interface TierAssessment {
  tier: 'A' | 'B' | 'C'
  ci: number
  consequence: number
  coupling: number
  time_dim: number
  life_safety: boolean
  sla: boolean
  drivers: string[]
}

/** Thermal / ride-through buffer (RDS M3-C). Null buffer means no deficit. */
export interface ThermalExposure {
  q_load_kw: number | null
  q_cap_healthy_kw: number | null
  q_cap_after_worst_fault_kw: number | null
  worst_fault_asset: string | null
  buffer_hours_healthy: number | null
  buffer_hours_after_worst_fault: number | null
  ride_through_min: number | null
  response_hours: number | null
  thermal_mass_kj_per_k: number | null
  temp_now_c: number | null
  temp_limit_c: number | null
}

export interface ServiceAssessment {
  service_id: string
  name: string
  redundancy: RedundancyConfig
  criticality: CriticalityScore
  exposure: Exposure
  single_points_of_failure: SpofEntry[]
  evidence: EvidenceCitation[]
  data_gaps: string[]
  /** Hospital semantics (Phase 4): the service carries the life-safety attribute. */
  life_safety: boolean
  /** RDS v1.2 S-1 tiering (CI = C x K x T) — absent in stored pre-v1.2 reports. */
  tier?: TierAssessment | null
  /** RDS v1.2 M3-C thermal buffering — absent in stored pre-v1.2 reports. */
  thermal?: ThermalExposure | null
}

/** One WP2 risk forecast with uncertainty bounds (feature-flagged; default off).
 *  Informational only — nothing in the system executes on it. Abstained rows
 *  carry a stated reason and the flat-prior fallback, never a real estimate. */
export interface RiskForecast {
  asset_key: string
  horizon_days: number
  p_fault: number
  lower: number
  upper: number
  redundancy_class: string | null
  status: 'forecast' | 'abstained'
  abstention_reason: string | null
  basis: string
}

export interface AssetAssessment {
  node_key: string
  name: string
  asset_type: string | null
  criticality: CriticalityScore
  exposed_services: string[]
  tolerated_services: string[]
  evidence: EvidenceCitation[]
}

export interface Finding {
  kind: FindingKind
  subject: string
  title: string
  detail: string
  affected_services: string[]
  evidence: EvidenceCitation[]
}

export interface AssessmentReport {
  facility_id: string
  graph_version: number
  evidence_window: { from: string | null; to: string | null } | null
  services: ServiceAssessment[]
  assets: AssetAssessment[]
  findings: Finding[]
  data_gaps: string[]
  open_questions: string[]
  /** Present only when the forecasting flag is enabled (default off). */
  forecasts: RiskForecast[]
}

export interface AssessmentSummary {
  id: number
  facility_id: string
  graph_version_no: number
  created_at: string
}
