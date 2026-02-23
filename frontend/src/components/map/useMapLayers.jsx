import { useEffect } from "react";
import maplibregl from "maplibre-gl";
import { extendBoundsFromGeoJSON } from "./fitBounds";

export const useMapLayers = (map, isLoaded, datasets) => {

    useEffect(() => {
        if (!map || !isLoaded) return;

        const bounds = new maplibregl.LngLatBounds();

        const activeLayerIds = new Set();
        const activeSourceIds = new Set();

        datasets.forEach(aoi => {

            aoi.layers.forEach(layer => {

                const sourceId = `source-${aoi.aoiId}-${layer.name}`;
                const layerId = `layer-${aoi.aoiId}-${layer.name}`;
                const outlineId = `${layerId}-outline`;

                activeSourceIds.add(sourceId);
                activeLayerIds.add(layerId);

                if (layer.type === "polygon") {
                    activeLayerIds.add(outlineId);
                }

                if (!map.getSource(sourceId)) {
                    map.addSource(sourceId, {
                        type: "geojson",
                        data: layer.geojson
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
                            },
                            layout: {
                                visibility: layer.visible ? "visible" : "none"
                            }
                        });
                    }

                    if (layer.type === "polygon") {

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
                            id: outlineId,
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

                } else {
                    const source = map.getSource(sourceId);
                    if (source && source.setData) {
                        source.setData(layer.geojson);
                    }
                }

                if (map.getLayer(layerId)) {
                    map.setLayoutProperty(
                        layerId,
                        "visibility",
                        layer.visible ? "visible" : "none"
                    );
                }

                if (map.getLayer(outlineId)) {
                    map.setLayoutProperty(
                        outlineId,
                        "visibility",
                        layer.visible ? "visible" : "none"
                    );
                }

                if (layer.visible) {
                    extendBoundsFromGeoJSON(bounds, layer.geojson);
                }

            });
        });

        const style = map.getStyle();
        if (style && style.layers) {
            style.layers.forEach(styleLayer => {
                const id = styleLayer.id;

                if (
                    id.startsWith("layer-") &&
                    !activeLayerIds.has(id)
                ) {
                    if (map.getLayer(id)) {
                        map.removeLayer(id);
                    }
                }
            });
        }

        Object.keys(map.getStyle().sources).forEach(sourceId => {
            if (
                sourceId.startsWith("source-") &&
                !activeSourceIds.has(sourceId)
            ) {
                if (map.getSource(sourceId)) {
                    map.removeSource(sourceId);
                }
            }
        });

        if (!bounds.isEmpty()) {
            map.fitBounds(bounds, {
                padding: 40,
                duration: 800
            });
        }

    }, [map, isLoaded, datasets]);
};