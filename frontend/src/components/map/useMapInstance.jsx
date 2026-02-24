import { useEffect, useState } from "react";
import maplibregl from "maplibre-gl";

export const useMapInstance = (containerRef) => {
    const [map, setMap] = useState(null);
    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        if (!containerRef.current) return;

        // const mapInstance = new maplibregl.Map({
        //     container: containerRef.current,
        //     style: "https://demotiles.maplibre.org/style.json",
        //     center: [0, 0],
        //     zoom: 2
        // });
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

        mapInstance.on("load", () => {
            setIsLoaded(true);
        });

        setMap(mapInstance);

        return () => mapInstance.remove();
    }, [containerRef]);

    return { map, isLoaded };
};
