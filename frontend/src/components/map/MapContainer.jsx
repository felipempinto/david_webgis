import { useRef } from "react";
import { useMapInstance } from "./useMapInstance";
import MapView from "./MapView";
import AttributeTable from "./sidebar/AttributeTable";
import Sidebar from "../map/sidebar/Sidebar";
import { useMeasureTool } from "./useMesureTool"
import { useState } from "react";


const MapContainer = ({ 
    datasets,
    setDatasets,
    selectedTable,
    setSelectedTable,
    userId
}) => {
    const containerRef = useRef(null);
    const { map, isLoaded } = useMapInstance(containerRef);

    const [measureMode, setMeasureMode] = useState(false);

    const { clearMeasure } = useMeasureTool(map, isLoaded, measureMode);

    return (
        <div className="map-container">
            <div className="map-tools">

                <button
                    type="button"
                    onClick={(e) => {
                        e.currentTarget.blur();
                        setMeasureMode(!measureMode);
                    }}
                >
                    {measureMode ? "Desativar Medição" : "Medir Distância"}
                </button>

                <button
                    type="button"
                    onClick={clearMeasure}
                >
                    Limpar
                </button>

            </div>
            <MapView
                map={map}
                isLoaded={isLoaded}
                datasets={datasets}
                containerRef={containerRef}
            />
            <Sidebar
                datasets={datasets}
                setDatasets={setDatasets}
                userId={userId}
                setSelectedTable={setSelectedTable}
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
