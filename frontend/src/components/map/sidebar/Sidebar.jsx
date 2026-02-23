import DatasetList from "./DatasetList";
import UploadPanel from "./UploadPanel";
import "./Sidebar.css";

const Sidebar = ({
    datasets,
    setDatasets,
    userId,
    setSelectedTable
}) => {
    return (
        <div className="sidebar">
            <h3>AOI Layers</h3>

            <DatasetList
                datasets={datasets}
                setDatasets={setDatasets}
                userId={userId}
                setSelectedTable={setSelectedTable}
            />

            <UploadPanel
                userId={userId}
                setDatasets={setDatasets}
            />
        </div>
    );
};

export default Sidebar;
