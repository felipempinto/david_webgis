import { useRef } from "react";
import { useMapInstance } from "./useMapInstance";
import MapView from "./MapView";

const MapContainer = ({ datasets }) => {
    const containerRef = useRef(null);
    const { map, isLoaded } = useMapInstance(containerRef);

    return (
        <div className="map-container">
            <MapView
                map={map}
                isLoaded={isLoaded}
                datasets={datasets}
                containerRef={containerRef}
            />
        </div>
    );
};

export default MapContainer;
