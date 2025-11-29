import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { MapData } from '../types';

interface MapProps {
  mapData: MapData | null;
  isLoading: boolean;
}

export default function Map({ mapData, isLoading }: MapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    // Vérifier que le conteneur a une taille
    const rect = mapContainer.current.getBoundingClientRect();

    if (rect.width === 0 || rect.height === 0) {
      console.warn('Map container has zero size, waiting for layout...');
      // Attendre un peu pour que le layout se stabilise
      setTimeout(() => {
        if (mapContainer.current && !map.current) {
          initializeMap();
        }
      }, 100);
      return;
    }

    initializeMap();

    function initializeMap() {
      if (!mapContainer.current || map.current) return;

      // Initialisation de la carte MapLibre avec style Positron (fond gris clair, gratuit, sans clé API)
      try {
        map.current = new maplibregl.Map({
          container: mapContainer.current,
          style: {
            version: 8,
            sources: {
              'carto-positron': {
                type: 'raster',
                tiles: [
                  'https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
                  'https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
                  'https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'
                ],
                tileSize: 256,
                attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>'
              }
            },
            layers: [
              {
                id: 'carto-positron-layer',
                type: 'raster',
                source: 'carto-positron',
                minzoom: 0,
                maxzoom: 22
              }
            ],
            glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf'
          },
          center: [1.4437, 43.6047], // Toulouse
          zoom: 10
        });

        // Ajouter les contrôles de navigation
        map.current.addControl(new maplibregl.NavigationControl(), 'top-right');

        // Gestion des erreurs de chargement
        map.current.on('error', (e) => {
          console.error('Map error:', e);
        });

        map.current.on('load', () => {
          console.log('Map loaded successfully');
          // Forcer le resize après le chargement
          map.current?.resize();
        });
      } catch (error) {
        console.error('Error initializing map:', error);
      }
    }

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!map.current || !mapData) return;

    // TODO: Ajouter les couches de données climatiques
    // Pour l'instant, on garde juste la carte de base
    console.log('Map data updated:', mapData);
  }, [mapData]);

  return (
    <div className="map-container">
      <div ref={mapContainer} className="map" style={{ width: '100%', height: '100%' }} />
      {isLoading && (
        <div className="map-loading">
          <div className="loading-spinner">Chargement...</div>
        </div>
      )}
    </div>
  );
}

