import { useMapLayers } from "./useMapLayers";

const MapView = ({ map, isLoaded, datasets, containerRef }) => {

    useMapLayers(map, isLoaded, datasets);

    return (
    <div
        ref={containerRef}
        style={{
            width: "100%",
            height: "100%"
        }}
    />
);
};

export default MapView;
