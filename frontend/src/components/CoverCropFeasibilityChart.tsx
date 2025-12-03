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
  year: number;
  member_minima: Record<string, number | null>;
}

interface CoverCropFeasibilityData {
  city: string;
  criterion: string;
  years: number[];
  yearly_data: YearlyData[];
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

  // Calculer le % de membres qui vérifient le critère pour chaque année
  const chartData = data.yearly_data.map((yearData) => {
    const memberMinima = yearData.member_minima;
    const validMembers = Object.values(memberMinima).filter(
      (min) => min !== null && min !== undefined
    );
    const membersMeetingCriterion = validMembers.filter((min) => min! >= threshold);
    const percentage =
      validMembers.length > 0
        ? (membersMeetingCriterion.length / validMembers.length) * 100
        : 0;

    return {
      year: yearData.year,
      percentage: Math.round(percentage * 10) / 10,
    };
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
          (défaut: 25mm)
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
            formatter={(value: number) => [`${value.toFixed(1)}%`, '% de membres']}
            labelFormatter={(label) => `Année: ${label}`}
          />
          <Legend />
          <ReferenceLine y={50} stroke="#ff7300" strokeDasharray="5 5" label="50%" />
          <Line 
            type="monotone" 
            dataKey="percentage" 
            stroke="#8884d8" 
            strokeWidth={2}
            dot={{ r: 3 }}
            name="% de membres vérifiant le critère"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

