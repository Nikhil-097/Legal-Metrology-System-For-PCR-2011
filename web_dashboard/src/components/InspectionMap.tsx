import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

interface InspectionSite {
  id: string;
  name: string;
  lat: number;
  lng: number;
  violationsCount: number;
  status: 'COMPLIANT' | 'NON_COMPLIANT';
}

export default function InspectionMap() {
  const centerPosition: [number, number] = [22.9734, 78.6569];

  const inspectionSites: InspectionSite[] = [
    { id: 'site-1', name: 'Okhla Phase-III Industrial Zone, New Delhi', lat: 28.5355, lng: 77.2732, violationsCount: 3, status: 'NON_COMPLIANT' },
    { id: 'site-2', name: 'APMC Market Yard, Navi Mumbai', lat: 19.0760, lng: 72.8777, violationsCount: 0, status: 'COMPLIANT' },
    { id: 'site-3', name: 'Peenya Industrial Estate, Bengaluru', lat: 13.0285, lng: 77.5197, violationsCount: 2, status: 'NON_COMPLIANT' },
    { id: 'site-4', name: 'Paltan Bazaar Market, Guwahati', lat: 26.1806, lng: 91.7539, violationsCount: 1, status: 'NON_COMPLIANT' },
    { id: 'site-5', name: 'Sanand Industrial GIDC, Gujarat', lat: 22.9868, lng: 72.3813, violationsCount: 0, status: 'COMPLIANT' },
  ];

  return (
    <MapContainer center={centerPosition} zoom={4} style={{ height: '100%', width: '100%', minHeight: '340px' }}>
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://carto.com/">CartoDB</a>'
      />
      {inspectionSites.map((site) => {
        const isViolative = site.status === 'NON_COMPLIANT';
        return (
          <CircleMarker
            key={site.id}
            center={[site.lat, site.lng]}
            radius={7}
            pathOptions={{
              color: isViolative ? '#DC2626' : '#16A34A',
              fillColor: isViolative ? '#EF4444' : '#22C55E',
              fillOpacity: 0.85,
              weight: 2,
            }}
          >
            <Popup>
              <div className="text-xs font-sans">
                <p className="font-bold text-slate-900">{site.name}</p>
                <p className={`mt-1 font-semibold ${isViolative ? 'text-red-600' : 'text-emerald-600'}`}>
                  {isViolative ? `${site.violationsCount} Statutory Infractions Detected` : 'All Commodities Compliant'}
                </p>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}