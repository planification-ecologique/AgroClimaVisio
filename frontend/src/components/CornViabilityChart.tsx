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
  sowing_totals: Record<string, number | null>;
  growth_minima_60d: Record<string, number | null>;
  growth_minima_30d: Record<string, number | null>;
  harvest_minima_15d: Record<string, number | null>;
}

interface CornViabilityData {
  city: string;
  criterion: string;
  years: number[];
  yearly_data: Record<number, YearlyData>;
  total_members: number;
  members: string[];
  error?: string;
}

interface CornViabilityChartProps {
  city: string;
  startYear?: number;
  endYear?: number;
  experiment?: string;
}

export default function CornViabilityChart({
  city,
  startYear = 2025,
  endYear = 2100,
  experiment = 'ssp370'
}: CornViabilityChartProps) {
  const [data, setData] = useState<CornViabilityData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // Seuils configurables
  const [sowingThreshold, setSowingThreshold] = useState<number>(100);
  const [growthThreshold60d, setGrowthThreshold60d] = useState<number>(100);
  const [growthThreshold30d, setGrowthThreshold30d] = useState<number>(20);
  const [harvestThreshold, setHarvestThreshold] = useState<number>(10);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`${API_BASE_URL}/api/charts/corn-viability`, {
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

  // Calculer le % de membres qui vérifient tous les critères pour chaque année
  const chartData = data.years.map((year) => {
    const yearData = data.yearly_data[year];
    if (!yearData) {
      return {
        year,
        percentage_curve1: 0,
        percentage_curve2: 0,
      };
    }

    // Courbe 1 : semis + croissance 60j + récolte
    let validMembersCurve1 = 0;
    // Courbe 2 : semis + croissance 30j + récolte
    let validMembersCurve2 = 0;
    let totalValidMembers = 0;

    for (const member of data.members) {
      const sowing = yearData.sowing_totals[member];
      const growth60d = yearData.growth_minima_60d[member];
      const growth30d = yearData.growth_minima_30d[member];
      const harvest = yearData.harvest_minima_15d[member];

      // Vérifier que toutes les données sont disponibles
      if (sowing === null || sowing === undefined ||
          growth60d === null || growth60d === undefined ||
          growth30d === null || growth30d === undefined ||
          harvest === null || harvest === undefined) {
        continue;
      }

      totalValidMembers++;

      // Vérifier les critères
      const passesSowing = sowing >= sowingThreshold;
      const passesGrowth60d = growth60d >= growthThreshold60d;
      const passesGrowth30d = growth30d >= growthThreshold30d;
      const passesHarvest = harvest <= harvestThreshold;

      // Courbe 1 : semis + croissance 60j + récolte
      if (passesSowing && passesGrowth60d && passesHarvest) {
        validMembersCurve1++;
      }

      // Courbe 2 : semis + croissance 30j + récolte
      if (passesSowing && passesGrowth30d && passesHarvest) {
        validMembersCurve2++;
      }
    }

    const percentageCurve1 = totalValidMembers > 0
      ? (validMembersCurve1 / totalValidMembers) * 100
      : 0;
    const percentageCurve2 = totalValidMembers > 0
      ? (validMembersCurve2 / totalValidMembers) * 100
      : 0;

    return {
      year,
      percentage_curve1: Math.round(percentageCurve1 * 10) / 10,
      percentage_curve2: Math.round(percentageCurve2 * 10) / 10,
    };
  });

  return (
    <div style={{ width: '100%', height: '500px', padding: '10px' }}>
      <h3 style={{ marginBottom: '10px' }}>
        Viabilité du maïs - {data.city}
      </h3>
      <p style={{ fontSize: '0.9em', color: '#666', marginBottom: '10px' }}>
        {data.criterion}
      </p>
      
      {/* Contrôles des seuils */}
      <div style={{ marginBottom: '20px', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '15px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <label htmlFor="sowing-threshold" style={{ fontSize: '0.85em', fontWeight: '500', minWidth: '120px' }}>
            Semis (mm):
          </label>
          <input
            id="sowing-threshold"
            type="number"
            min="0"
            max="500"
            step="10"
            value={sowingThreshold}
            onChange={(e) => setSowingThreshold(Number(e.target.value))}
            style={{
              padding: '5px 10px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              width: '80px',
            }}
          />
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <label htmlFor="harvest-threshold" style={{ fontSize: '0.85em', fontWeight: '500', minWidth: '120px' }}>
            Récolte max (mm):
          </label>
          <input
            id="harvest-threshold"
            type="number"
            min="0"
            max="100"
            step="1"
            value={harvestThreshold}
            onChange={(e) => setHarvestThreshold(Number(e.target.value))}
            style={{
              padding: '5px 10px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              width: '80px',
            }}
          />
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <label htmlFor="growth-60d-threshold" style={{ fontSize: '0.85em', fontWeight: '500', minWidth: '120px' }}>
            Croissance 60j (mm):
          </label>
          <input
            id="growth-60d-threshold"
            type="number"
            min="0"
            max="500"
            step="10"
            value={growthThreshold60d}
            onChange={(e) => setGrowthThreshold60d(Number(e.target.value))}
            style={{
              padding: '5px 10px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              width: '80px',
            }}
          />
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <label htmlFor="growth-30d-threshold" style={{ fontSize: '0.85em', fontWeight: '500', minWidth: '120px' }}>
            Croissance 30j (mm):
          </label>
          <input
            id="growth-30d-threshold"
            type="number"
            min="0"
            max="200"
            step="5"
            value={growthThreshold30d}
            onChange={(e) => setGrowthThreshold30d(Number(e.target.value))}
            style={{
              padding: '5px 10px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              width: '80px',
            }}
          />
        </div>
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
            label={{ value: '% de membres vérifiant tous les critères', angle: -90, position: 'insideLeft' }}
            domain={[0, 100]}
          />
          <Tooltip 
            formatter={(value: number, name: string) => {
              const label = name === 'percentage_curve1' ? 'Courbe 1 (60j)' : name === 'percentage_curve2' ? 'Courbe 2 (30j)' : '';
              return [`${value.toFixed(1)}%`, label];
            }}
            labelFormatter={(label) => `Année: ${label}`}
          />
          <Legend />
          <ReferenceLine y={50} stroke="#ff7300" strokeDasharray="5 5" label="50%" />
          {chartData.some(d => d.percentage_curve1 !== undefined) && (
            <Line 
              type="monotone" 
              dataKey="percentage_curve1" 
              stroke="#8884d8" 
              strokeWidth={2}
              dot={{ r: 3 }}
              name={`Courbe 1 (60j, seuil: ${growthThreshold60d}mm)`}
            />
          )}
          {chartData.some(d => d.percentage_curve2 !== undefined) && (
            <Line 
              type="monotone" 
              dataKey="percentage_curve2" 
              stroke="#82ca9d" 
              strokeWidth={2}
              dot={{ r: 3 }}
              name={`Courbe 2 (30j, seuil: ${growthThreshold30d}mm)`}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

