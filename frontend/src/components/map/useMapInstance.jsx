import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";

export const useMapInstance = (containerRef) => {
    const mapRef = useRef(null);
    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        if (!containerRef.current) return;

        if (mapRef.current) return;

        const mapInstance = new maplibregl.Map({
            container: containerRef.current,
            style: {
                version: 8,
                sources: {
                    esri: {
                        type: "raster",
                        tiles: [
                            "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                        ],
                        tileSize: 256
                    }
                },
                layers: [
                    {
                        id: "esri-satellite",
                        type: "raster",
                        source: "esri"
                    }
                ]
            },
            center: [0, 0],
            zoom: 5
        });

        mapRef.current = mapInstance;

        mapInstance.on("load", () => {
            setIsLoaded(true);

            requestAnimationFrame(() => {
                mapInstance.resize();
            });
        });

        return () => {
            mapInstance.remove();
            mapRef.current = null;
        };

    }, [containerRef]);

    return { map: mapRef.current, isLoaded };
};