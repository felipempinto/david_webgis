import { useEffect, useRef } from "react";
import * as turf from "@turf/turf";
import maplibregl from "maplibre-gl";



// TODO:
// https://maplibre.org/maplibre-gl-js/docs/examples/measure-distances/
// https://github.com/jdsantos/maplibre-gl-measures


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

            // pontos
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

            // linha
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
            console.log("coords",coords)

            updateMeasure(e);
        };

        map.on("click", handleClick);

        return () => map.off("click", handleClick);

    }, [map, isLoaded, measureMode]);

    const updateMeasure = (e) => {

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

            const length = turf.length(line, { units: "kilometers" });

            if (popupRef.current) popupRef.current.remove();
            const html = `

            <b>${length.toFixed(2)} km</b>
            `
            const location = pointsRef.current[pointsRef.current.length - 1]
            // const location = e.lngLat;
            popupRef.current = new maplibregl.Popup()
                //console.log()
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