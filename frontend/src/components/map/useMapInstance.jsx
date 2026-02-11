import { useEffect, useState } from "react";
import maplibregl from "maplibre-gl";

export const useMapInstance = (containerRef) => {
    const [map, setMap] = useState(null);
    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        if (!containerRef.current) return;

        const mapInstance = new maplibregl.Map({
            container: containerRef.current,
            style: "https://demotiles.maplibre.org/style.json",
            center: [0, 0],
            zoom: 2
        });

        mapInstance.on("load", () => {
            setIsLoaded(true);
        });

        setMap(mapInstance);

        return () => mapInstance.remove();
    }, [containerRef]);

    return { map, isLoaded };
};
