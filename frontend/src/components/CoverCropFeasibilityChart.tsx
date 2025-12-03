import { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface YearlyData {
  member_minima_by_window: Record<number, Record<string, number | null>>;
}

interface CoverCropFeasibilityData {
  city: string;
  criterion: string;
  window_sizes: number[];
  years: number[];
  yearly_data: Record<number, YearlyData>;
  total_members: number;
  members: string[];
  error?: string;
}

interface CoverCropFeasibilityChartProps {
  city: string;
  startYear?: number;
  endYear?: number;
  experiment?: string;
}

export default function CoverCropFeasibilityChart({
  city,
  startYear = 2025,
  endYear = 2100,
  experiment = 'ssp370'
}: CoverCropFeasibilityChartProps) {
  const [data, setData] = useState<CoverCropFeasibilityData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [threshold, setThreshold] = useState<number>(25);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`${API_BASE_URL}/api/charts/cover-crop-feasibility`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            city,
            start_year: startYear,
            end_year: endYear,
            experiment
          }),
        });

        if (!response.ok) {
          throw new Error(`Erreur HTTP: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.error) {
          setError(result.error);
          setData(null);
        } else {
          setData(result);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erreur inconnue');
        setData(null);
      } finally {
        setIsLoading(false);
      }
    };

    if (city) {
      fetchData();
    }
  }, [city, startYear, endYear, experiment]);

  if (isLoading) {
    return (
      <div style={{ padding: '10px', textAlign: 'center' }}>
        <p>Chargement des données...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '10px', textAlign: 'center', color: 'red' }}>
        <p>Erreur: {error}</p>
      </div>
    );
  }

  if (!data || !data.years || data.years.length === 0) {
    return (
      <div style={{ padding: '10px', textAlign: 'center' }}>
        <p>Aucune donnée disponible</p>
      </div>
    );
  }

  // Calculer le % de membres qui vérifient le critère pour chaque année et chaque fenêtre
  const chartData = data.years.map((year) => {
    const yearData = data.yearly_data[year];
    if (!yearData || !yearData.member_minima_by_window) {
      return {
        year,
        percentage_21: 0,
        percentage_42: 0,
      };
    }

    const result: { year: number; percentage_21?: number; percentage_42?: number } = { year };

    // Calculer pour chaque taille de fenêtre
    for (const windowSize of data.window_sizes) {
      const memberMinima = yearData.member_minima_by_window[windowSize];
      if (!memberMinima) continue;

      const validMembers = Object.values(memberMinima).filter(
        (min) => min !== null && min !== undefined
      );

      // Ajuster le seuil selon la taille de fenêtre (seuil mensualisé pour 30 jours)
      const adjustedThreshold = threshold * (windowSize / 30);
      const membersMeetingCriterion = validMembers.filter((min) => min! >= adjustedThreshold);
      const percentage =
        validMembers.length > 0
          ? (membersMeetingCriterion.length / validMembers.length) * 100
          : 0;

      if (windowSize === 21) {
        result.percentage_21 = Math.round(percentage * 10) / 10;
      } else if (windowSize === 42) {
        result.percentage_42 = Math.round(percentage * 10) / 10;
      }
    }

    return result;
  });

  return (
    <div style={{ width: '100%', height: '400px', padding: '10px' }}>
      <h3 style={{ marginBottom: '10px' }}>
        Faisabilité des couverts végétaux - {data.city}
      </h3>
      <p style={{ fontSize: '0.9em', color: '#666', marginBottom: '10px' }}>
        {data.criterion}
      </p>
      <div style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '15px' }}>
        <label htmlFor="threshold" style={{ fontSize: '0.9em', fontWeight: '500' }}>
          Seuil minimum (mm):
        </label>
        <input
          id="threshold"
          type="number"
          min="0"
          max="100"
          step="1"
          value={threshold}
          onChange={(e) => setThreshold(Number(e.target.value))}
          style={{
            padding: '5px 10px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            width: '80px',
          }}
        />
        <span style={{ fontSize: '0.85em', color: '#888' }}>
          (mensualisé, défaut: 25mm/mois)
        </span>
      </div>
      <p style={{ fontSize: '0.85em', color: '#888', marginBottom: '20px' }}>
        Membres analysés: {data.total_members} ({data.members.join(', ')})
      </p>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="year" 
            label={{ value: 'Année', position: 'insideBottom', offset: -5 }}
          />
          <YAxis 
            label={{ value: '% de membres vérifiant le critère', angle: -90, position: 'insideLeft' }}
            domain={[0, 100]}
          />
          <Tooltip 
            formatter={(value: number, name: string) => {
              const label = name === 'percentage_21' ? '21 jours' : name === 'percentage_42' ? '42 jours' : '';
              return [`${value.toFixed(1)}%`, label];
            }}
            labelFormatter={(label) => `Année: ${label}`}
          />
          <Legend />
          <ReferenceLine y={50} stroke="#ff7300" strokeDasharray="5 5" label="50%" />
          {chartData.some(d => d.percentage_21 !== undefined) && (
            <Line 
              type="monotone" 
              dataKey="percentage_21" 
              stroke="#8884d8" 
              strokeWidth={2}
              dot={{ r: 3 }}
              name={`21 jours (seuil: ${(threshold * 21 / 30).toFixed(1)}mm)`}
            />
          )}
          {chartData.some(d => d.percentage_42 !== undefined) && (
            <Line 
              type="monotone" 
              dataKey="percentage_42" 
              stroke="#82ca9d" 
              strokeWidth={2}
              dot={{ r: 3 }}
              name={`42 jours (seuil: ${(threshold * 42 / 30).toFixed(1)}mm)`}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

