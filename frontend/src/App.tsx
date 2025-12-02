import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import ParametersPanel from './components/ParametersPanel';
import Map from './components/Map';
import ChartsPage from './pages/ChartsPage';
import type { MapRequest, MapData, Preset } from './types';
import './App.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [selectedYear, setSelectedYear] = useState<number>(2020);
  const [comparisonMode, setComparisonMode] = useState<boolean>(false);
  const [mapRequest, setMapRequest] = useState<MapRequest | null>(null);
  const [mapData, setMapData] = useState<MapData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [availableYears, setAvailableYears] = useState<number[]>([2020, 2030, 2040, 2050]);
  const [mapStyle, setMapStyle] = useState<'desaturated' | 'aerial'>('desaturated');

  // Charger les presets et années disponibles au démarrage
  useEffect(() => {
    const fetchPresets = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/presets`);
        const data = await response.json();
        setPresets(data.presets);
      } catch (error) {
        console.error('Erreur lors du chargement des presets:', error);
      }
    };

    const fetchYears = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/years`);
        const data = await response.json();
        setAvailableYears(data.years);
      } catch (error) {
        console.error('Erreur lors du chargement des années:', error);
      }
    };

    fetchPresets();
    fetchYears();
  }, []);

  // Charger les données de carte quand les paramètres changent
  useEffect(() => {
    if (!mapRequest) return;

    const fetchMapData = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`${API_BASE_URL}/api/maps/data`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(mapRequest),
        });
        const data = await response.json();
        setMapData(data);
      } catch (error) {
        console.error('Erreur lors du chargement des données de carte:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMapData();
  }, [mapRequest]);

  const handleParametersChange = (request: MapRequest) => {
    setMapRequest(request);
    setSelectedYear(request.period.year);
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/charts" element={<ChartsPage />} />
        <Route
          path="/"
          element={
            <div className="app">
              <Header
                selectedYear={selectedYear}
                onYearChange={(year) => {
                  setSelectedYear(year);
                  if (mapRequest) {
                    setMapRequest({
                      ...mapRequest,
                      period: { ...mapRequest.period, year }
                    });
                  }
                }}
                availableYears={availableYears}
                comparisonMode={comparisonMode}
                onComparisonModeToggle={() => setComparisonMode(!comparisonMode)}
                mapStyle={mapStyle}
                onMapStyleChange={setMapStyle}
              />
              <div className="app-content">
                <div className="parameters-sidebar">
                  <ParametersPanel
                    onParametersChange={handleParametersChange}
                    presets={presets}
                    availableYears={availableYears}
                  />
                </div>
                <div className="map-area">
                  <Map mapData={mapData} isLoading={isLoading} mapStyle={mapStyle} />
                </div>
              </div>
            </div>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
