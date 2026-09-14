export interface Asset {
  asset_id: string;
  asset_type: string;
  latitude: number;
  longitude: number;
  age_years: number;
  material: string;
  inspection_score: number;
  tilt_deg: number;
  corrosion_score: number;
  foundation_type: string;
  last_maintenance_date: string;
  wind_gust_kmh: number;
  rainfall_mm: number;
  flood_depth_cm: number;
  erosion_index: number;
  drainage_score: number;
  road_access_score: number;
  clearance_score: number;
  canopy_distance_m: number;
  tree_height_m: number;
  feeder_id: string;
  downstream_customers: number;
  critical_loads: string;
  redundancy: boolean;
  factor_wind: number;
  factor_rain: number;
  factor_tilt: number;
  factor_erosion: number;
  factor_corrosion: number;
  factor_drainage: number;
  factor_vegetation: number;
  factor_age: number;
  risk_score: number;
  dominant_cause: string;
  critical_load_multiplier: number;
  expected_loss: number;
  estimated_intervention_cost: number;
  priority_score: number;
  recommended_action: string;
  action_tier: string;
  expected_risk_reduction_pct: number;
  recommended_crew_type: string;
  risk_band: string;
  safety_note: string;
}

export interface Stats {
  total: number;
  critical: number;
  elevated: number;
  watch: number;
  normal: number;
  immediate: number;
  totalCustomers: number;
  incidentCount: number;
}

export interface Incident {
  asset_id: string;
  incident_date: string;
  cause: string;
  downtime_hours: number;
}
