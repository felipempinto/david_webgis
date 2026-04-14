import { useState } from "react";
import {
    addAOIExtras,
    fetchAOIData,
    deleteAOIExtra,
    handleDeleteAOI
} from "../../../api/aoi";


const DatasetList = ({ datasets, setDatasets, setSelectedTable }) => {

    const [uploadingFor, setUploadingFor] = useState(null);

    const handleAddCSV = async ( aoiId, files) => {
        try {
            setUploadingFor(aoiId);
            try {
                await addAOIExtras(aoiId, files);
            } catch (error) {
                console.error("Erro ao enviar CSV:", error);
                //Depois preciso pensar em usar de maneira inteligente.
            }
            const result = await fetchAOIData( aoiId);
            const updatedLayers = result.map(layer => ({
                ...layer,
                visible: true
            }));

            setDatasets(prev =>
                prev.map(aoi =>
                    aoi.aoiId === aoiId
                        ? {
                            ...aoi,
                            layers: updatedLayers
                        }
                        : aoi
                )
            );

        } catch (err) {
            console.error("CSV upload failed", err);
        } finally {
            setUploadingFor(null);
        }
    };

    const toggleVisibility = (aoiId, layerName) => {
        setDatasets(prev =>
            prev.map(aoi =>
                aoi.aoiId === aoiId
                    ? {
                        ...aoi,
                        layers: aoi.layers.map(layer =>
                            layer.name === layerName
                                ? { ...layer, visible: !layer.visible }
                                : layer
                        )
                    }
                    : aoi
            )
        );
    };

    // const deleteLayer = async (aoiId, filename) => {
    const deleteLayer = async (aoiId, public_id) => {
        try {
            // console.log(aoiId,filename)
            // await deleteAOIExtra(aoiId, filename);
            await deleteAOIExtra(public_id);
            const updatedLayers = await fetchAOIData(aoiId);

            setDatasets(prev =>
                prev.map(aoi =>
                    aoi.aoiId === aoiId
                        ? {
                            ...aoi,
                            layers: updatedLayers
                        }
                        : aoi
                )
            );

        } catch (err) {
            console.error("Delete failed", err);
        }
    };

    if (!datasets.length) {
        return (
            <div className="empty-datasets">
                ✨ No AOI loaded yet
            </div>
        );
    }

    return (
        <div className="dataset-list">

            {datasets.map(aoi => {
                const shapefile = aoi.layers.find(
                    l => l.source === "shapefile"
                );

                const csvLayers = aoi.layers.filter(
                    l => l.source === "csv"
                );

                return (
                    <div key={aoi.aoiId} className="aoi-group">

                        <div className="aoi-title">
                            📦 AOI {aoi.aoiId}
                        </div>
                        <button
                            className="delete-aoi-btn"
                            // disabled={!canDeleteAOI}
                            onClick={() => handleDeleteAOI( aoi.aoiId, setDatasets)}
                        >
                            🗑 Delete AOI
                        </button>
                        <div className="add-csv-section">

                            <input
                                type="file"
                                multiple
                                accept=".csv"
                                id={`csv-input-${aoi.aoiId}`}
                                style={{ display: "none" }}
                                onChange={(e) => {
                                    const files = [...e.target.files];
                                    if (!files.length) return;

                                    handleAddCSV(aoi.aoiId, files);
                                }}
                            />

                            <button
                                className="add-csv-btn"
                                disabled={uploadingFor === aoi.aoiId}
                                onClick={() =>
                                    document
                                        .getElementById(`csv-input-${aoi.aoiId}`)
                                        .click()
                                }
                            >
                                {uploadingFor === aoi.aoiId
                                    ? "Uploading..."
                                    : "+ Add CSV"}
                            </button>

                        </div>

                        {shapefile && (
                            <div className="dataset-item">
                                <label className="checkbox-container">
                                    <input
                                        type="checkbox"
                                        checked={shapefile.visible}
                                        onChange={() =>
                                            toggleVisibility(
                                                aoi.aoiId,
                                                shapefile.name
                                            )
                                        }
                                    />
                                    <span className="checkmark"></span>
                                </label>

                                <span
                                    className="dataset-name aoi-layer"
                                    title={shapefile.name}
                                >
                                    🟦 {shapefile.name}
                                </span>
                            </div>
                        )}

                        {csvLayers.map(csv => (
                            <div
                                key={csv.name}
                                className="dataset-item csv-item"
                            >
                                <label className="checkbox-container">
                                    <input
                                        type="checkbox"
                                        checked={csv.visible}
                                        onChange={() =>
                                            toggleVisibility(
                                                aoi.aoiId,
                                                csv.name
                                            )
                                        }
                                    />
                                    <span className="checkmark"></span>
                                </label>

                                <span
                                    className="dataset-name csv-layer"
                                    title={csv.name}
                                >
                                    📍 {csv.name}
                                </span>

                                <button
                                    className="table-btn"
                                    onClick={() =>
                                        setSelectedTable({
                                            ...csv,
                                            aoiId: aoi.aoiId
                                        })
                                    }
                                    title="View attributes"
                                >
                                    📊
                                </button>

                                <button
                                    className="delete-btn"
                                    onClick={() =>
                                        deleteLayer(
                                            aoi.aoiId,
                                            csv.public_id
                                            // csv.name
                                        )
                                    }
                                >
                                    ❌
                                </button>
                            </div>
                        ))}

                    </div>
                );
            })}

        </div>
    );
};

export default DatasetList;
