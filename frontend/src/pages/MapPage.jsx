import { useEffect, useState } from "react";
import { fetchDatasets } from "../api/dataset";
import Sidebar from "../components/map/sidebar/Sidebar"
import MapContainer from "../components/map/MapContainer";

const MapPage = () => {
    const [datasets, setDatasets] = useState([]);

    useEffect(() => {
        const load = async () => {
            const data = await fetchDatasets();
            setDatasets(data);
        };

        load();
    }, []);

    return (
        <div style={{ display: "flex", height: "100vh" }}>
            <Sidebar datasets={datasets} setDatasets={setDatasets} />
            <MapContainer datasets={datasets} />
        </div>
    );
};

export default MapPage;
