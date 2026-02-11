import { useEffect, useState } from "react";
import { fetchDatasets, fetchUserDatasets } from "../api/dataset";
import Sidebar from "../components/map/sidebar/Sidebar";
import MapContainer from "../components/map/MapContainer";

const FAKE_USER_ID = "admin"; // temporário

const MapPage = () => {
    const [datasets, setDatasets] = useState([]);
    const [datasetId, setDatasetId] = useState(null);

    useEffect(() => {
        const load = async () => {
            const datasetIds = await fetchUserDatasets(FAKE_USER_ID);

            let allLayers = [];

            for (const datasetId of datasetIds) {
                const layers = await fetchDatasets(FAKE_USER_ID, datasetId);
                allLayers = [...allLayers, ...layers];
            }

            setDatasets(allLayers);
        };
        load();
    }, []);

    return (
        <div style={{ display: "flex", height: "100vh" }}>
            <Sidebar
                datasets={datasets}
                setDatasets={setDatasets}
                setDatasetId={setDatasetId}
                userId={FAKE_USER_ID}
            />
            <MapContainer datasets={datasets} />
        </div>
    );
};

export default MapPage;
