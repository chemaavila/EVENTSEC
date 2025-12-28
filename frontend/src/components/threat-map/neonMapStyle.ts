// Dark neon MapLibre style (tokenless, raster OSM tiles) for a premium sci-fi look.
// Note: For production, use a ToS-compliant tile provider or self-host tiles.

export const neonMapStyle: any = {
  version: 8,
  name: "EventSec Neon Dark",
  glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
  sources: {
    "osm-raster": {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors"
    }
  },
  layers: [
    { id: "background", type: "background", paint: { "background-color": "#050814" } },
    {
      id: "osm",
      type: "raster",
      source: "osm-raster",
      paint: {
        "raster-opacity": 0.18,
        "raster-saturation": -1,
        "raster-contrast": 0.6,
        "raster-brightness-min": 0.05,
        "raster-brightness-max": 0.25
      }
    }
  ]
};


