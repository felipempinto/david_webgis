import DatasetList from "./DatasetList";
import UploadPanel from "./UploadPanel";
import "./Sidebar.css";

const Sidebar = ({
    datasets,
    setDatasets,
    setSelectedTable
}) => {
    return (
        <div className="sidebar">
            <h3>AOI Layers</h3>

            <DatasetList
                datasets={datasets}
                setDatasets={setDatasets}
                setSelectedTable={setSelectedTable}
            />

            <UploadPanel
                setDatasets={setDatasets}
            />
        </div>
    );
};

export default Sidebar;
