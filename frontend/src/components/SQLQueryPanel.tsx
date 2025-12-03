import { useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface SQLQueryResult {
  query: string;
  row_count: number;
  columns: string[];
  results: Record<string, any>[];
  error?: string;
  traceback?: string;
  allowed?: boolean;
}

export default function SQLQueryPanel() {
  const [query, setQuery] = useState<string>('');
  const [result, setResult] = useState<SQLQueryResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const executeQuery = async () => {
    if (!query.trim()) {
      return;
    }

    setIsLoading(true);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/dev/sql`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({
        query,
        row_count: 0,
        columns: [],
        results: [],
        error: error instanceof Error ? error.message : 'Erreur inconnue',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      executeQuery();
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '100%' }}>
      <h2 style={{ marginBottom: '15px' }}>SQL Query (Développement)</h2>
      <div style={{ marginBottom: '15px' }}>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Entrez votre requête SELECT ici...&#10;Ctrl/Cmd + Enter pour exécuter"
          style={{
            width: '100%',
            minHeight: '150px',
            padding: '10px',
            fontFamily: 'monospace',
            fontSize: '14px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            resize: 'vertical',
          }}
        />
      </div>
      <div style={{ marginBottom: '15px' }}>
        <button
          onClick={executeQuery}
          disabled={isLoading || !query.trim()}
          style={{
            padding: '10px 20px',
            backgroundColor: '#3498db',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isLoading || !query.trim() ? 'not-allowed' : 'pointer',
            opacity: isLoading || !query.trim() ? 0.6 : 1,
          }}
        >
          {isLoading ? 'Exécution...' : 'Exécuter (Ctrl/Cmd + Enter)'}
        </button>
      </div>

      {result && (
        <div style={{ marginTop: '20px' }}>
          {result.error ? (
            <div style={{ padding: '15px', backgroundColor: '#fee', border: '1px solid #fcc', borderRadius: '4px' }}>
              <h3 style={{ color: '#c00', marginTop: 0 }}>Erreur</h3>
              <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{result.error}</pre>
              {result.traceback && (
                <details style={{ marginTop: '10px' }}>
                  <summary style={{ cursor: 'pointer', color: '#666' }}>Traceback (développement)</summary>
                  <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px', color: '#666' }}>
                    {result.traceback}
                  </pre>
                </details>
              )}
            </div>
          ) : result.allowed === false ? (
            <div style={{ padding: '15px', backgroundColor: '#ffe', border: '1px solid #fc0', borderRadius: '4px' }}>
              <p style={{ color: '#c60', margin: 0 }}>{result.error}</p>
            </div>
          ) : (
            <div>
              <div style={{ marginBottom: '10px', color: '#666' }}>
                <strong>{result.row_count}</strong> ligne{result.row_count !== 1 ? 's' : ''} retournée{result.row_count !== 1 ? 's' : ''}
                {result.columns.length > 0 && ` • ${result.columns.length} colonne${result.columns.length !== 1 ? 's' : ''}`}
              </div>
              {result.results && result.results.length > 0 ? (
                <div style={{ overflowX: 'auto', border: '1px solid #ddd', borderRadius: '4px' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f5f5f5' }}>
                        {result.columns.map((col) => (
                          <th
                            key={col}
                            style={{
                              padding: '8px',
                              textAlign: 'left',
                              borderBottom: '2px solid #ddd',
                              fontWeight: 'bold',
                            }}
                          >
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.results.slice(0, 100).map((row, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid #eee' }}>
                          {result.columns.map((col) => (
                            <td key={col} style={{ padding: '8px' }}>
                              {row[col] !== null && row[col] !== undefined ? String(row[col]) : <em style={{ color: '#999' }}>NULL</em>}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {result.results.length > 100 && (
                    <div style={{ padding: '10px', textAlign: 'center', color: '#666', fontSize: '12px' }}>
                      Affichage des 100 premières lignes sur {result.results.length}
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ padding: '15px', backgroundColor: '#f5f5f5', borderRadius: '4px', color: '#666' }}>
                  Aucun résultat
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

