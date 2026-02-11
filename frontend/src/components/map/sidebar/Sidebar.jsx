import DatasetList from "./DatasetList";
import UploadPanel from "./UploadPanel";
import "./Sidebar.css"; // <-- add this line

const Sidebar = ({ datasets, setDatasets }) => {
    return (
        <div className="sidebar">
            <h3>Datasets</h3>
            <DatasetList datasets={datasets} setDatasets={setDatasets} />
            <UploadPanel setDatasets={setDatasets} />
        </div>
    );
};

export default Sidebar;