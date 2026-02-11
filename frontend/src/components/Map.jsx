import { useEffect, useRef, useState } from "react";
import { useMap } from "../hooks/useMap";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const API_URL = import.meta.env.VITE_API_URL;


function getFeatureCoordinates(feature) {
    const geometry = feature.geometry;

    switch (geometry.type) {
        case "Point":
            return [geometry.coordinates];

        case "MultiPoint":
        case "LineString":
            return geometry.coordinates;

        case "MultiLineString":
        case "Polygon":
            return geometry.coordinates.flat();

        case "MultiPolygon":
            return geometry.coordinates.flat(2);

        default:
            return [];
    }
}



const Map = () => {
    const containerRef = useRef(null);
    const [error, setError] = useState(null);

    const { map, isLoaded } = useMap(
        containerRef,
        "https://demotiles.maplibre.org/style.json",
        [ -74.0060,40.7128],
        10
    );

    useEffect(() => {
        if (!isLoaded || !map) return;

        const loadDatasets = async () => {
            try {
                const res = await fetch(`${API_URL}/datasets`);

                if (!res.ok) {
                    throw new Error("Failed to load datasets");
                }

                const result = await res.json();
                const layers = result?.data?.layers ?? [];
                const bounds = new maplibregl.LngLatBounds();

                layers.forEach((layer) => {
                    const sourceId = `source-${layer.name}`;
                    const layerId = `layer-${layer.name}`;

                    if (map.getSource(sourceId)) return;

                    map.addSource(sourceId, {
                        type: "geojson",
                        data: layer.geojson
                    });

                    layer.geojson.features.forEach((feature) => {
                        const coords = getFeatureCoordinates(feature);
                        coords.forEach(coord => bounds.extend(coord));
                    });

                    if (layer.type === "point") {
                        map.addLayer({
                            id: layerId,
                            type: "circle",
                            source: sourceId,
                            paint: {
                                "circle-radius": 5,
                                "circle-color": "#007cbf",
                                "circle-stroke-width": 1,
                                "circle-stroke-color": "#ffffff"
                            }
                        });
                    }

                    if (layer.type === "aoi") {
                        map.addLayer({
                            id: layerId,
                            type: "fill",
                            source: sourceId,
                            paint: {
                                "fill-color": "#ff0000",
                                "fill-opacity": 0.15
                            }
                        });

                        map.addLayer({
                            id: `${layerId}-outline`,
                            type: "line",
                            source: sourceId,
                            paint: {
                                "line-color": "#ff0000",
                                "line-width": 2
                            }
                        });
                    }
                });

                // ✅ Depois que tudo carregar:
                if (!bounds.isEmpty()) {
                    map.fitBounds(bounds, {
                        padding: 40,
                        duration: 1000
                    });
                }


            } catch (err) {
                console.error(err);
                setError(err.message);
            }
        };

        loadDatasets();
    }, [isLoaded, map]);

    return (
        <div style={{ width: "100%", height: "100vh", position: "relative" }}>
            <div
                ref={containerRef}
                style={{ width: "100%", height: "100%" }}
            />

            {error && (
                <div style={{
                    position: "absolute",
                    bottom: 10,
                    left: 10,
                    background: "#ffdddd",
                    padding: 6,
                    zIndex: 10
                }}>
                    {error}
                </div>
            )}
        </div>
    );
};

export default Map;
