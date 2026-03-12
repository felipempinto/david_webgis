import { useEffect, useRef } from "react";
import * as turf from "@turf/turf";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

export const useMeasureTool = (map, isLoaded, measureMode) => {

    const pointsRef = useRef([]);
    const popupRef = useRef(null);

    useEffect(() => {
        if (!map || !isLoaded) return;

        if (!map.getSource("measure-source")) {

            map.addSource("measure-source", {
                type: "geojson",
                data: {
                    type: "FeatureCollection",
                    features: []
                }
            });

            map.addLayer({
                id: "measure-points",
                type: "circle",
                source: "measure-source",
                paint: {
                    "circle-radius": 6,
                    "circle-color": "#000000"
                },
                filter: ["==", "$type", "Point"]
            });

            map.addLayer({
                id: "measure-line",
                type: "line",
                source: "measure-source",
                paint: {
                    "line-width": 3,
                    "line-color": "#000000"
                },
                filter: ["==", "$type", "LineString"]
            });
        }

    }, [map, isLoaded]);

    useEffect(() => {
        if (!map || !isLoaded) return;

        const handleClick = (e) => {
            if (!measureMode) return;

            const coords = [e.lngLat.lng, e.lngLat.lat];
            pointsRef.current.push(coords);

            updateMeasure();
        };

        map.on("click", handleClick);

        return () => map.off("click", handleClick);

    }, [map, isLoaded, measureMode]);

    const updateMeasure = () => {

        const features = [];

        pointsRef.current.forEach(coord => {
            features.push({
                type: "Feature",
                geometry: {
                    type: "Point",
                    coordinates: coord
                }
            });
        });

        if (pointsRef.current.length > 1) {

            const line = turf.lineString(pointsRef.current);

            features.push({
                type: "Feature",
                geometry: line.geometry
            });

            const lengthKm = turf.length(line, { units: "kilometers" });
            const lengthMiles = turf.length(line, { units: "miles" });
            const lengthMeters = lengthKm * 1000;

            let mainDistance;

            if (lengthKm < 1) {
                mainDistance = `${lengthMeters.toFixed(0)} m`;
            } else {
                mainDistance = `${lengthKm.toFixed(2)} km`;
            }

            if (popupRef.current) popupRef.current.remove();

            const html = `
                <div class="measure-popup">
                    <div class="measure-title">Distance</div>
                    <div class="measure-main">${mainDistance}</div>
                    <div class="measure-sub">${lengthMiles.toFixed(2)} miles</div>
                </div>
            `;

            const location = pointsRef.current[pointsRef.current.length - 1];

            popupRef.current = new maplibregl.Popup({
                closeButton: false,
                closeOnClick: false
            })
                .setLngLat(location)
                .setHTML(html)
                .addTo(map);
        }

        map.getSource("measure-source").setData({
            type: "FeatureCollection",
            features
        });
    };

    const clearMeasure = () => {

        pointsRef.current = [];

        if (popupRef.current) popupRef.current.remove();

        map.getSource("measure-source")?.setData({
            type: "FeatureCollection",
            features: []
        });
    };

    return { clearMeasure };
};