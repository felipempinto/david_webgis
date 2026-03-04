import { useMapLayers } from "./useMapLayers";

const MapView = ({ map, isLoaded, datasets, containerRef }) => {

    useMapLayers(map, isLoaded, datasets);

    return (
        <div
            ref={containerRef}
            className="map-view"
        />
    );
};

export default MapView;
