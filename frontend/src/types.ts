export interface Period {
  start_date: string;
  end_date: string;
  year: number; // 2020, 2030, 2040, 2050
}

export interface ClimateParameters {
  min_rainfall?: number;
  min_rainfall_probability?: number;
  degree_days_threshold?: number;
  degree_days_probability?: number;
  max_hot_days_30?: number;
  max_hot_days_35?: number;
  hot_days_probability?: number;
  consecutive_dry_days?: number;
  extreme_rainfall_threshold?: number;
  max_7day_rainfall?: number;
  non_workable_days_threshold?: number;
}

export interface MapRequest {
  period: Period;
  map_type: 'potential' | 'drought' | 'excess_water' | 'extremes' | 'heat_waves';
  parameters: ClimateParameters;
}

export interface Preset {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
}

export interface MapData {
  map_type: string;
  period: Period;
  parameters: ClimateParameters;
  data: {
    type: string;
    features: any[];
  };
  legend: {
    min: number;
    max: number;
    unit: string;
  };
}

