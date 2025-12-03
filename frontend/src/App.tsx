import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ChartsPage from './pages/ChartsPage';
import MapPage from './pages/MapPage';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/charts" replace />} />
        <Route path="/charts" element={<ChartsPage />} />
        <Route path="/map" element={<MapPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
