import { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface MonthlyDataPoint {
  year: number;
  month: number;
  date: string;
  value: number;
  days_count: number;
}

interface PointData {
  name: string;
  lat: number;
  lon: number;
  data: MonthlyDataPoint[];
}

interface ClimateData {
  start_date: string;
  end_date: string;
  experiment: string;
  variable: string;
  points: PointData[];
  error?: string;
}

interface ClimateChartProps {
  startDate: string;
  endDate: string;
  experiment?: string;
  variable: string;
  cities?: string[];
  members?: string[];
}

const COLORS = [
  '#8884d8', // Bleu
  '#82ca9d', // Vert
  '#ffc658', // Jaune
  '#ff7300', // Orange
  '#8dd1e1', // Cyan
  '#d084d0', // Violet
];

export default function ClimateChart({ startDate, endDate, experiment = 'ssp370', variable, cities, members }: ClimateChartProps) {
  const [data, setData] = useState<ClimateData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  const variableLabels = {
    pr: 'Précipitations',
    tas: 'Température',
  };
  
  const variableUnits = {
    pr: 'mm',
    tas: '°C',
  };

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`${API_BASE_URL}/api/charts/monthly`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            start_date: startDate,
            end_date: endDate,
            experiment: experiment,
            variable: variable,
            cities: cities && cities.length > 0 ? cities : undefined,
            members: members && members.length > 0 ? members : undefined,
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

    if (startDate && endDate) {
      fetchData();
    }
  }, [startDate, endDate, experiment, variable, cities, members]);

  if (isLoading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>Chargement des données...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', color: 'red' }}>
        <p>Erreur: {error}</p>
      </div>
    );
  }

  if (!data || !data.points || data.points.length === 0) {
    return (
      <div style={{ padding: '20px' }}>
        <p>Aucune donnée disponible pour cette période.</p>
      </div>
    );
  }

  // Transformer les données pour le graphique
  // Créer un objet avec une entrée par date, avec une valeur pour chaque point
  const chartDataMap = new Map<string, Record<string, number>>();

  data.points.forEach((point, index) => {
    point.data.forEach((dataPoint) => {
      const dateKey = dataPoint.date;
      if (!chartDataMap.has(dateKey)) {
        chartDataMap.set(dateKey, { date: dateKey });
      }
      chartDataMap.get(dateKey)![point.name] = dataPoint.value;
    });
  });

  const chartData = Array.from(chartDataMap.values()).sort((a, b) => 
    a.date.localeCompare(b.date)
  );

  const unit = variableUnits[data.variable as keyof typeof variableUnits] || '';
  const label = variableLabels[data.variable as keyof typeof variableLabels] || 'Données';

  return (
    <div style={{ width: '100%', height: '500px', padding: '20px' }}>
      <h2 style={{ marginBottom: '20px' }}>
        {label} mensuelles - {data.experiment.toUpperCase()}
      </h2>
      <p style={{ marginBottom: '20px', color: '#666' }}>
        Période: {new Date(data.start_date).toLocaleDateString('fr-FR')} - {new Date(data.end_date).toLocaleDateString('fr-FR')}
      </p>
      
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
            interval="preserveStartEnd"
          />
          <YAxis 
            label={{ value: `${label} (${unit})`, angle: -90, position: 'insideLeft' }}
            tick={{ fontSize: 12 }}
          />
          <Tooltip 
            formatter={(value: number) => [`${value.toFixed(2)} ${unit}`, '']}
            labelFormatter={(label) => `Date: ${label}`}
          />
          <Legend />
          {data.points.map((point, index) => (
            <Line
              key={point.name}
              type="monotone"
              dataKey={point.name}
              stroke={COLORS[index % COLORS.length]}
              strokeWidth={2}
              dot={false}
              name={`${point.name} (${point.lat.toFixed(2)}°N, ${point.lon.toFixed(2)}°E)`}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      
    </div>
  );
}
