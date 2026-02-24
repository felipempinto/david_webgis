import { useRef } from "react";
import { useMapInstance } from "./useMapInstance";
import MapView from "./MapView";
import AttributeTable from "./sidebar/AttributeTable";

const MapContainer = ({ datasets, selectedTable, setSelectedTable }) => {
    const containerRef = useRef(null);
    const { map, isLoaded } = useMapInstance(containerRef);
    console.log(selectedTable)

    return (
        <div className="map-container">
            <MapView
                map={map}
                isLoaded={isLoaded}
                datasets={datasets}
                containerRef={containerRef}
            />

            {selectedTable && (
                <AttributeTable
                    layer={selectedTable}
                    map={map}
                    aoiId={selectedTable?.aoiId}
                    onClose={() => setSelectedTable(null)}
                />
            )}
        </div>
    );
};

export default MapContainer;
