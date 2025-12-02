import { useState } from 'react';
import RainfallChart from '../components/RainfallChart';
import Header from '../components/Header';
import './RainfallPage.css';

export default function RainfallPage() {
  const [startDate, setStartDate] = useState<string>('2025-01-01');
  const [endDate, setEndDate] = useState<string>('2030-12-31');
  const [experiment, setExperiment] = useState<string>('ssp370');

  return (
    <div className="rainfall-page">
      <Header
        selectedYear={2025}
        onYearChange={() => {}}
        availableYears={[2025, 2030, 2040, 2050]}
        comparisonMode={false}
        onComparisonModeToggle={() => {}}
        mapStyle="desaturated"
        onMapStyleChange={() => {}}
      />
      <div className="rainfall-content">
        <div className="rainfall-controls">
          <h1>Précipitations mensuelles - Points représentatifs</h1>
          <div className="controls-grid">
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
              <label htmlFor="experiment">Scénario:</label>
              <select
                id="experiment"
                value={experiment}
                onChange={(e) => setExperiment(e.target.value)}
              >
                <option value="historical">Historique</option>
                <option value="ssp370">SSP3-7.0</option>
                <option value="ssp585">SSP5-8.5</option>
                <option value="ssp245">SSP2-4.5</option>
                <option value="ssp126">SSP1-2.6</option>
              </select>
            </div>
          </div>
        </div>
        <div className="rainfall-chart-container">
          <RainfallChart
            startDate={startDate}
            endDate={endDate}
            experiment={experiment}
          />
        </div>
      </div>
    </div>
  );
}

