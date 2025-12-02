import { useState, useEffect } from 'react';
import ClimateChart from '../components/ClimateChart';
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
          <h1>Données climatiques mensuelles - Points représentatifs</h1>
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
        </div>
        <div className="charts-chart-container">
          <ClimateChart
            startDate={startDate}
            endDate={endDate}
            experiment="ssp370"
            variable={selectedVariable}
            cities={selectedCities}
            members={selectedMembers}
          />
        </div>
      </div>
    </div>
  );
}

