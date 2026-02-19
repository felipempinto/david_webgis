import { useEffect, useState } from "react";
import { fetchUserAOIs, fetchAOIData } from "../api/aoi";
import Sidebar from "../components/map/sidebar/Sidebar";
import MapContainer from "../components/map/MapContainer";

const FAKE_USER_ID = "admin";

const MapPage = () => {
    const [datasets, setDatasets] = useState([]);

    useEffect(() => {
        const load = async () => {
            try {
                const aoiIds = await fetchUserAOIs(FAKE_USER_ID);

                const allAOIs = [];

                for (const aoiId of aoiIds) {
                    const layers = await fetchAOIData(
                        FAKE_USER_ID,
                        aoiId
                    );

                    allAOIs.push({
                        aoiId,
                        layers: layers.map(layer => ({
                            ...layer,
                            visible: true
                        }))
                    });
                }

                setDatasets(allAOIs);

            } catch (err) {
                console.error("Failed to load AOIs", err);
            }
        };

        load();
    }, []);

    return (
        <div style={{ display: "flex", height: "100vh" }}>
            <Sidebar
                datasets={datasets}
                setDatasets={setDatasets}
                userId={FAKE_USER_ID}
            />
            <MapContainer datasets={datasets} />
        </div>
    );
};

export default MapPage;
