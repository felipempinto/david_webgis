import { useEffect } from "react";
import maplibregl from "maplibre-gl";
import { extendBoundsFromGeoJSON } from "./fitBounds";

export const useMapLayers = (map, isLoaded, datasets) => {

    useEffect(() => {
        if (!map || !isLoaded) return;

        const bounds = new maplibregl.LngLatBounds();

        datasets.forEach(aoi => {

            aoi.layers.forEach(layer => {
                console.log(layer)

                const sourceId = `source-${aoi.aoiId}-${layer.name}`;
                const layerId = `layer-${aoi.aoiId}-${layer.name}`;

                if (!map.getSource(sourceId)) {

                    map.addSource(sourceId, {
                        type: "geojson",
                        data: layer.geojson
                    });

                    // 🔵 POINT
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
                            },
                            layout: {
                                visibility: layer.visible ? "visible" : "none"
                            }
                        });
                    }

                    // 🔴 AOI
                    if (layer.type === "polygon") {
                        console.log("AOI")

                        map.addLayer({
                            id: layerId,
                            type: "fill",
                            source: sourceId,
                            paint: {
                                "fill-color": "#ff0000",
                                "fill-opacity": 0.15
                            },
                            layout: {
                                visibility: layer.visible ? "visible" : "none"
                            }
                        });

                        map.addLayer({
                            id: `${layerId}-outline`,
                            type: "line",
                            source: sourceId,
                            paint: {
                                "line-color": "#ff0000",
                                "line-width": 2
                            },
                            layout: {
                                visibility: layer.visible ? "visible" : "none"
                            }
                        });
                    }
                }

                // 🔄 Atualiza visibilidade
                if (map.getLayer(layerId)) {
                    map.setLayoutProperty(
                        layerId,
                        "visibility",
                        layer.visible ? "visible" : "none"
                    );
                }

                if (map.getLayer(`${layerId}-outline`)) {
                    map.setLayoutProperty(
                        `${layerId}-outline`,
                        "visibility",
                        layer.visible ? "visible" : "none"
                    );
                }

                if (layer.visible) {
                    extendBoundsFromGeoJSON(bounds, layer.geojson);
                }

            });

        });

        if (!bounds.isEmpty()) {
            map.fitBounds(bounds, {
                padding: 40,
                duration: 1000
            });
        }

    }, [map, isLoaded, datasets]);
};