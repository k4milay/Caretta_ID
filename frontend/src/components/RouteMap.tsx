import { useEffect, useRef } from "react";
import L from "leaflet";
import type { GeoJSON } from "../services/api";

// Fix Leaflet's broken default icon paths in bundler environments
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon   from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

(L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl = undefined;
L.Icon.Default.mergeOptions({ iconUrl: markerIcon, iconRetinaUrl: markerIcon2x, shadowUrl: markerShadow });

interface Props { geojson: GeoJSON | null; }

export default function RouteMap({ geojson }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    if (!mapRef.current) {
      mapRef.current = L.map(containerRef.current).setView([36.5, 28.0], 6);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
      }).addTo(mapRef.current);
    }

    const map = mapRef.current;
    map.eachLayer((l) => { if (!(l instanceof L.TileLayer)) map.removeLayer(l); });

    if (!geojson) return;

    const layer = L.geoJSON(geojson as unknown as Parameters<typeof L.geoJSON>[0], {
      pointToLayer: (_, latlng) => L.circleMarker(latlng, {
        radius: 7, fillColor: "#0d9488", color: "#fff", weight: 2,
        opacity: 1, fillOpacity: 0.9,
      }),
      onEachFeature: (feature, layer) => {
        const p = feature.properties ?? {};
        if (feature.geometry.type === "Point") {
          layer.bindPopup(`<b>${p.location_name ?? "Gözlem"}</b><br/>${new Date(p.sighted_at).toLocaleDateString("tr-TR")}`);
        }
      },
      style: () => ({ color: "#0d9488", weight: 2.5, opacity: 0.7 }),
    }).addTo(map);

    try { map.fitBounds(layer.getBounds(), { padding: [30, 30] }); } catch { /* single point */ }

    return () => { map.eachLayer((l) => { if (!(l instanceof L.TileLayer)) map.removeLayer(l); }); };
  }, [geojson]);

  return <div ref={containerRef} style={{ height: 340, borderRadius: "var(--radius)", overflow: "hidden" }} />;
}
