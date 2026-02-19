import DatasetList from "./DatasetList";
import UploadPanel from "./UploadPanel";
import "./Sidebar.css";

const Sidebar = ({
    datasets,
    setDatasets,
    userId,
    setAoiId
}) => {
    return (
        <div className="sidebar">
            <h3>AOI Layers</h3>

            <DatasetList
                datasets={datasets}
                setDatasets={setDatasets}
            />

            <UploadPanel
                userId={userId}
                setAoiId={setAoiId}
                setDatasets={setDatasets}
            />
        </div>
    );
};

export default Sidebar;
