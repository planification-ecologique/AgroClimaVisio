interface HeaderProps {
  selectedYear: number;
  onYearChange: (year: number) => void;
  availableYears: number[];
  comparisonMode: boolean;
  onComparisonModeToggle: () => void;
}

export default function Header({
  selectedYear,
  onYearChange,
  availableYears,
  comparisonMode,
  onComparisonModeToggle
}: HeaderProps) {
  return (
    <header className="app-header">
      <div className="header-content">
        <h1>AgroClimaVisio</h1>
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

