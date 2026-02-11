import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";

export const useMap = (
    containerRef,
    style,
    center = [0, 0],
    zoom = 2
) => {
    const mapRef = useRef(null);
    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        if (!containerRef.current) return;

        const map = new maplibregl.Map({
            container: containerRef.current,
            style,
            center,
            zoom
        });

        map.addControl(new maplibregl.NavigationControl());

        map.on("load", () => {
            setIsLoaded(true);
        });

        mapRef.current = map;

        return () => {
            setIsLoaded(false);
            map.remove();
            mapRef.current = null;
        };
    }, [containerRef, style,  zoom]);

    return {
        map: mapRef.current,
        isLoaded
    };
};
