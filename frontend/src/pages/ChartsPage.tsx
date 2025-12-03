import { useState, useEffect } from 'react';
import ClimateChart from '../components/ClimateChart';
import CoverCropFeasibilityChart from '../components/CoverCropFeasibilityChart';
import SQLQueryPanel from '../components/SQLQueryPanel';
import Header from '../components/Header';
import CheckboxDropdown from '../components/CheckboxDropdown';
import './ChartsPage.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface CityOption {
  name: string;
  region: string;
}

export default function ChartsPage() {
  const [startDate, setStartDate] = useState<string>('2025-01-01');
  const [endDate, setEndDate] = useState<string>('2030-12-31');
  const [selectedVariable, setSelectedVariable] = useState<string>('pr');
  const [selectedCities, setSelectedCities] = useState<string[]>(['Chartres']);
  const [selectedMembers, setSelectedMembers] = useState<string[]>(['r1']);
  const [availableCities, setAvailableCities] = useState<CityOption[]>([]);
  const [availableMembers, setAvailableMembers] = useState<string[]>([]);
  const [, setIsLoadingOptions] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'monthly' | 'cover-crop' | 'sql'>('monthly');
  const [coverCropCity, setCoverCropCity] = useState<string>('Chartres');

  // Charger les options disponibles
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/charts/options`);
        if (response.ok) {
          const data = await response.json();
          setAvailableCities(data.cities || []);
          setAvailableMembers(data.members || []);
          
          // Si r1 n'est pas disponible, utiliser le premier membre disponible
          if (data.members && data.members.length > 0 && !data.members.includes('r1')) {
            setSelectedMembers([data.members[0]]);
          }
        }
      } catch (error) {
        console.error('Erreur lors du chargement des options:', error);
      } finally {
        setIsLoadingOptions(false);
      }
    };
    
    fetchOptions();
  }, []);

  const variableOptions = [
    { value: 'pr', label: 'Précipitations (pr)' },
    { value: 'tas', label: 'Température (tas)' },
  ];

  return (
    <div className="charts-page">
      <Header
        selectedYear={2025}
        onYearChange={() => {}}
        availableYears={[2025, 2030, 2040, 2050]}
        comparisonMode={false}
        onComparisonModeToggle={() => {}}
        mapStyle="desaturated"
        onMapStyleChange={() => {}}
      />
      <div className="charts-content">
        <div className="charts-controls">
          <h1>Graphiques climatiques</h1>
          <div className="tabs" style={{ marginBottom: '20px', borderBottom: '1px solid #ddd' }}>
            <button
              onClick={() => setActiveTab('monthly')}
              style={{
                padding: '10px 20px',
                border: 'none',
                background: activeTab === 'monthly' ? '#3498db' : 'transparent',
                color: activeTab === 'monthly' ? 'white' : '#333',
                cursor: 'pointer',
                borderTopLeftRadius: '4px',
                borderTopRightRadius: '4px'
              }}
            >
              Données mensuelles
            </button>
            <button
              onClick={() => setActiveTab('cover-crop')}
              style={{
                padding: '10px 20px',
                border: 'none',
                background: activeTab === 'cover-crop' ? '#3498db' : 'transparent',
                color: activeTab === 'cover-crop' ? 'white' : '#333',
                cursor: 'pointer',
                borderTopLeftRadius: '4px',
                borderTopRightRadius: '4px'
              }}
            >
              Faisabilité couverts végétaux
            </button>
            {(import.meta.env.DEV || import.meta.env.VITE_SHOW_SQL_PANEL === 'true') && (
              <button
                onClick={() => setActiveTab('sql')}
                style={{
                  padding: '10px 20px',
                  border: 'none',
                  background: activeTab === 'sql' ? '#3498db' : 'transparent',
                  color: activeTab === 'sql' ? 'white' : '#333',
                  cursor: 'pointer',
                  borderTopLeftRadius: '4px',
                  borderTopRightRadius: '4px'
                }}
              >
                SQL Query (Dev)
              </button>
            )}
          </div>
          
          {activeTab === 'monthly' && (
            <div className="controls-grid">
            <div className="control-group">
              <label htmlFor="variable">Variable:</label>
              <select
                id="variable"
                value={selectedVariable}
                onChange={(e) => setSelectedVariable(e.target.value)}
              >
                {variableOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="control-group">
              <label htmlFor="start-date">Date de début:</label>
              <input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="control-group">
              <label htmlFor="end-date">Date de fin:</label>
              <input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
            <div className="control-group">
              <CheckboxDropdown
                label="Villes"
                options={availableCities.map(city => ({
                  value: city.name,
                  label: `${city.name} (${city.region})`
                }))}
                selectedValues={selectedCities}
                onChange={setSelectedCities}
                placeholder="Sélectionner des villes..."
              />
            </div>
            <div className="control-group">
              <CheckboxDropdown
                label="Membres d'ensemble"
                options={availableMembers.map(member => ({
                  value: member,
                  label: member
                }))}
                selectedValues={selectedMembers}
                onChange={setSelectedMembers}
                placeholder="Sélectionner des membres..."
              />
            </div>
          </div>
          )}
          
          {activeTab === 'cover-crop' && (
            <div className="controls-grid">
              <div className="control-group">
                <label htmlFor="cover-crop-city">Ville:</label>
                <select
                  id="cover-crop-city"
                  value={coverCropCity}
                  onChange={(e) => setCoverCropCity(e.target.value)}
                >
                  {availableCities.map(city => (
                    <option key={city.name} value={city.name}>
                      {city.name} ({city.region})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>
        <div className="charts-chart-container">
          {activeTab === 'monthly' && (
            <ClimateChart
              startDate={startDate}
              endDate={endDate}
              experiment="ssp370"
              variable={selectedVariable}
              cities={selectedCities}
              members={selectedMembers}
            />
          )}
          {activeTab === 'cover-crop' && (
            <CoverCropFeasibilityChart
              city={coverCropCity}
              startYear={2025}
              endYear={2100}
              experiment="ssp370"
            />
          )}
          {activeTab === 'sql' && <SQLQueryPanel />}
        </div>
      </div>
    </div>
  );
}

