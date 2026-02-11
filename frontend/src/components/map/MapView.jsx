import { useMapLayers } from "./useMapLayers";

const MapView = ({ map, isLoaded, datasets, containerRef }) => {

    useMapLayers(map, isLoaded, datasets);

    return (
        <div
            ref={containerRef}
            style={{ flex: 1 }}
        />
    );
};

export default MapView;
