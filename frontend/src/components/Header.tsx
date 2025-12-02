import { Link, useLocation } from 'react-router-dom';

interface HeaderProps {
  selectedYear: number;
  onYearChange: (year: number) => void;
  availableYears: number[];
  comparisonMode: boolean;
  onComparisonModeToggle: () => void;
  mapStyle: 'desaturated' | 'aerial';
  onMapStyleChange: (style: 'desaturated' | 'aerial') => void;
}

export default function Header({
  selectedYear,
  onYearChange,
  availableYears,
  comparisonMode,
  onComparisonModeToggle,
  mapStyle,
  onMapStyleChange
}: HeaderProps) {
  const location = useLocation();
  
  return (
    <header className="app-header">
      <div className="header-content">
        <h1>AgroClimaVisio</h1>
        <nav className="header-nav">
          <Link 
            to="/" 
            className={location.pathname === '/' ? 'active' : ''}
          >
            Cartes
          </Link>
          <Link 
            to="/charts" 
            className={location.pathname === '/charts' ? 'active' : ''}
          >
            Graphiques
          </Link>
        </nav>
        <div className="header-controls">
          <div className="year-selector">
            <label>Année moyenne:</label>
            <select
              value={selectedYear}
              onChange={(e) => onYearChange(Number(e.target.value))}
            >
              {availableYears.map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>
          <div className="map-style-selector">
            <label>Fond de carte:</label>
            <select
              value={mapStyle}
              onChange={(e) => onMapStyleChange(e.target.value as 'desaturated' | 'aerial')}
            >
              <option value="desaturated">Désaturé (IGN)</option>
              <option value="aerial">Aérien (IGN)</option>
            </select>
          </div>
          <button
            className={`comparison-toggle ${comparisonMode ? 'active' : ''}`}
            onClick={onComparisonModeToggle}
          >
            Mode comparaison
          </button>
          <button className="export-btn">
            Exporter
          </button>
        </div>
      </div>
    </header>
  );
}

