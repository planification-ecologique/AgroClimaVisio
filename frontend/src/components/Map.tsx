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
    if (!map.current || !mapData || !mapData.data) return;

    // Attendre que la carte soit chargée
    if (!map.current.isStyleLoaded()) {
      map.current.once('styledata', () => {
        updateMapData();
      });
      return;
    }

    updateMapData();

    function updateMapData() {
      if (!map.current || !mapData?.data) return;

      const sourceId = 'climate-data';
      const layerId = 'climate-data-layer';
      const outlineLayerId = `${layerId}-outline`;

      // Vérifier si la source existe déjà
      const sourceExists = map.current.getSource(sourceId) !== undefined;

      if (sourceExists) {
        // Mettre à jour les données de la source existante
        const source = map.current.getSource(sourceId) as maplibregl.GeoJSONSource;
        source.setData(mapData.data as GeoJSON.FeatureCollection);
      } else {
        // Supprimer les couches existantes si elles existent
        if (map.current.getLayer(outlineLayerId)) {
          map.current.removeLayer(outlineLayerId);
        }
        if (map.current.getLayer(layerId)) {
          map.current.removeLayer(layerId);
        }

        // Ajouter la nouvelle source GeoJSON
        map.current.addSource(sourceId, {
          type: 'geojson',
          data: mapData.data as GeoJSON.FeatureCollection
        });
      }

      // Calculer les valeurs min/max pour la légende
      const features = mapData.data.features as Array<{ properties: { value: number } }>;
      const values = features.map((f) => f.properties.value);
      const minValue = Math.min(...values);
      const maxValue = Math.max(...values);

      // Fonction pour obtenir la couleur selon la valeur
      const getColor = (value: number) => {
        const normalized = (value - minValue) / (maxValue - minValue || 1);
        
        // Palette de couleurs selon le type de carte
        if (mapData.map_type === 'drought') {
          // Rouge pour sécheresse (plus rouge = plus de sécheresse)
          return `rgb(${Math.round(255 * normalized)}, ${Math.round(255 * (1 - normalized))}, 0)`;
        } else if (mapData.map_type === 'excess_water') {
          // Bleu pour excès d'eau
          return `rgb(0, ${Math.round(100 + 155 * normalized)}, ${Math.round(255 * normalized)})`;
        } else if (mapData.map_type === 'extremes') {
          // Orange/rouge pour extrêmes
          return `rgb(255, ${Math.round(255 * (1 - normalized))}, 0)`;
        } else if (mapData.map_type === 'heat_waves') {
          // Rouge/orange pour vagues de chaleur
          return `rgb(255, ${Math.round(100 + 155 * (1 - normalized))}, 0)`;
        } else {
          // Vert pour potentiel (plus vert = meilleur potentiel)
          return `rgb(${Math.round(255 * (1 - normalized))}, ${Math.round(255 * normalized)}, 0)`;
        }
      };

      // Ajouter les couches seulement si elles n'existent pas déjà
      if (!map.current.getLayer(layerId)) {
        // Ajouter la couche de remplissage
        map.current.addLayer({
          id: layerId,
          type: 'fill',
          source: sourceId,
          paint: {
            'fill-color': [
              'interpolate',
              ['linear'],
              ['get', 'value'],
              minValue,
              getColor(minValue),
              maxValue,
              getColor(maxValue)
            ],
            'fill-opacity': 0.6
          }
        });
      } else {
        // Mettre à jour le style de la couche existante
        map.current.setPaintProperty(layerId, 'fill-color', [
          'interpolate',
          ['linear'],
          ['get', 'value'],
          minValue,
          getColor(minValue),
          maxValue,
          getColor(maxValue)
        ]);
      }

      if (!map.current.getLayer(outlineLayerId)) {
        // Ajouter la couche de contour
        map.current.addLayer({
          id: outlineLayerId,
          type: 'line',
          source: sourceId,
          paint: {
            'line-color': '#666',
            'line-width': 1,
            'line-opacity': 0.3
          }
        });
      }

      // Ajouter des popups au clic
      const clickHandler = (e: maplibregl.MapLayerMouseEvent) => {
        if (e.features && e.features[0]) {
          const value = (e.features[0].properties as { value: number }).value;
          const unit = mapData.legend.unit || '';
          new maplibregl.Popup()
            .setLngLat(e.lngLat)
            .setHTML(`<strong>Valeur:</strong> ${value} ${unit}`)
            .addTo(map.current!);
        }
      };

      // Supprimer les anciens listeners avant d'en ajouter de nouveaux
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      map.current.off('click', layerId, clickHandler as any);
      map.current.on('click', layerId, clickHandler);

      // Changer le curseur au survol
      const mouseEnterHandler = () => {
        if (map.current) {
          map.current.getCanvas().style.cursor = 'pointer';
        }
      };

      const mouseLeaveHandler = () => {
        if (map.current) {
          map.current.getCanvas().style.cursor = '';
        }
      };

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      map.current.off('mouseenter', layerId, mouseEnterHandler as any);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      map.current.off('mouseleave', layerId, mouseLeaveHandler as any);
      map.current.on('mouseenter', layerId, mouseEnterHandler);
      map.current.on('mouseleave', layerId, mouseLeaveHandler);
    }
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

