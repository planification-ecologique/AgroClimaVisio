import { useState, useEffect, useRef } from 'react';
import type { ClimateParameters, MapRequest, Preset } from '../types';

interface ParametersPanelProps {
  onParametersChange: (request: MapRequest) => void;
  presets: Preset[];
  availableYears: number[];
}

export default function ParametersPanel({
  onParametersChange,
  presets,
  availableYears
}: ParametersPanelProps) {
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('2024-04-15');
  const [endDate, setEndDate] = useState<string>('2024-06-30');
  const [selectedYear, setSelectedYear] = useState<number>(2020);
  const [mapType, setMapType] = useState<MapRequest['map_type']>('potential');
  const [parameters, setParameters] = useState<ClimateParameters>({});
  const previousRequestRef = useRef<string>('');

  useEffect(() => {
    const request: MapRequest = {
      period: {
        start_date: startDate,
        end_date: endDate,
        year: selectedYear
      },
      map_type: mapType,
      parameters: parameters
    };
    
    // Éviter les appels inutiles en comparant avec la requête précédente
    const requestString = JSON.stringify(request);
    if (requestString !== previousRequestRef.current) {
      previousRequestRef.current = requestString;
      onParametersChange(request);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate, endDate, selectedYear, mapType, parameters]);

  const handlePresetChange = (presetId: string) => {
    const preset = presets.find(p => p.id === presetId);
    if (preset) {
      setStartDate(preset.start_date);
      setEndDate(preset.end_date);
      setSelectedPreset(presetId);
    }
  };

  const updateParameter = (key: keyof ClimateParameters, value: number | undefined) => {
    setParameters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  return (
    <div className="parameters-panel">
      {/* Sélection de l'année */}
      <div className="parameter-group">
        <label>Année moyenne</label>
        <select
          value={selectedYear}
          onChange={(e) => setSelectedYear(Number(e.target.value))}
        >
          {availableYears.map(year => (
            <option key={year} value={year}>{year}</option>
          ))}
        </select>
      </div>

      {/* Presets agricoles */}
      <div className="parameter-group">
        <label>Période agricole</label>
        <select
          value={selectedPreset}
          onChange={(e) => handlePresetChange(e.target.value)}
        >
          <option value="">Personnalisée</option>
          {presets.map(preset => (
            <option key={preset.id} value={preset.id}>{preset.name}</option>
          ))}
        </select>
      </div>

      {/* Dates personnalisées */}
      <div className="parameter-group">
        <label>Date de début</label>
        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
        />
      </div>

      <div className="parameter-group">
        <label>Date de fin</label>
        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
        />
      </div>

      {/* Type de carte */}
      <div className="parameter-group">
        <label>Type de carte</label>
        <select
          value={mapType}
          onChange={(e) => setMapType(e.target.value as MapRequest['map_type'])}
        >
          <option value="potential">Potentiel agro-climatique</option>
          <option value="drought">Risque de sécheresse</option>
          <option value="excess_water">Risque d'excès d'eau</option>
          <option value="extremes">Extrêmes (orages, chaleur)</option>
          <option value="heat_waves">Vagues de chaleur</option>
        </select>
      </div>

      {/* Paramètres selon le type de carte */}
      {mapType === 'potential' && (
        <div className="parameter-group">
          <h3>Potentiel agro-climatique</h3>
          <div className="parameter-input">
            <label>Pluie minimale (mm)</label>
            <input
              type="number"
              value={parameters.min_rainfall || ''}
              onChange={(e) => updateParameter('min_rainfall', e.target.value ? Number(e.target.value) : undefined)}
              placeholder="80"
            />
          </div>
          <div className="parameter-input">
            <label>Probabilité pluie minimale</label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={parameters.min_rainfall_probability || ''}
              onChange={(e) => updateParameter('min_rainfall_probability', e.target.value ? Number(e.target.value) : undefined)}
              placeholder="0.8"
            />
          </div>
          <div className="parameter-input">
            <label>Somme de températures (DJ)</label>
            <input
              type="number"
              value={parameters.degree_days_threshold || ''}
              onChange={(e) => updateParameter('degree_days_threshold', e.target.value ? Number(e.target.value) : undefined)}
              placeholder="500"
            />
          </div>
          <div className="parameter-input">
            <label>Jours {'>'} 30°C (max)</label>
            <input
              type="number"
              value={parameters.max_hot_days_30 || ''}
              onChange={(e) => updateParameter('max_hot_days_30', e.target.value ? Number(e.target.value) : undefined)}
              placeholder="10"
            />
          </div>
        </div>
      )}

      {mapType === 'drought' && (
        <div className="parameter-group">
          <h3>Risque de sécheresse</h3>
          <div className="parameter-input">
            <label>Jours consécutifs sans pluie</label>
            <input
              type="number"
              value={parameters.consecutive_dry_days || ''}
              onChange={(e) => updateParameter('consecutive_dry_days', e.target.value ? Number(e.target.value) : undefined)}
              placeholder="10"
            />
          </div>
        </div>
      )}

      {mapType === 'excess_water' && (
        <div className="parameter-group">
          <h3>Risque d'excès d'eau</h3>
          <div className="parameter-input">
            <label>Pluie cumulée 7 jours (mm)</label>
            <input
              type="number"
              value={parameters.max_7day_rainfall || ''}
              onChange={(e) => updateParameter('max_7day_rainfall', e.target.value ? Number(e.target.value) : undefined)}
              placeholder="40"
            />
          </div>
          <div className="parameter-input">
            <label>Jours non praticables (pluie {'>'} 2mm)</label>
            <input
              type="number"
              value={parameters.non_workable_days_threshold || ''}
              onChange={(e) => updateParameter('non_workable_days_threshold', e.target.value ? Number(e.target.value) : undefined)}
              placeholder="7"
            />
          </div>
        </div>
      )}

      {mapType === 'extremes' && (
        <div className="parameter-group">
          <h3>Extrêmes</h3>
          <div className="parameter-input">
            <label>Pluie extrême (mm / 30 min)</label>
            <input
              type="number"
              value={parameters.extreme_rainfall_threshold || ''}
              onChange={(e) => updateParameter('extreme_rainfall_threshold', e.target.value ? Number(e.target.value) : undefined)}
              placeholder="50"
            />
          </div>
          <div className="parameter-input">
            <label>Jours {'>'} 35°C</label>
            <input
              type="number"
              value={parameters.max_hot_days_35 || ''}
              onChange={(e) => updateParameter('max_hot_days_35', e.target.value ? Number(e.target.value) : undefined)}
              placeholder="5"
            />
          </div>
        </div>
      )}
    </div>
  );
}

