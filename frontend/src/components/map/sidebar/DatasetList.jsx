import { useState } from "react";
import {
    addAOIExtras,
    fetchAOIData,
    deleteAOIExtra,
    handleDeleteAOI
} from "../../../api/aoi";


const DatasetList = ({ datasets, setDatasets, userId, setSelectedTable }) => {

    const [uploadingFor, setUploadingFor] = useState(null);

    const handleAddCSV = async (userId, aoiId, files) => {
        try {
            setUploadingFor(aoiId);

            await addAOIExtras(userId, aoiId, files);

            const result = await fetchAOIData(userId, aoiId);

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

    const deleteLayer = async (aoiId, filename) => {
        try {
            await deleteAOIExtra(userId, aoiId, filename);
            const updatedLayers = await fetchAOIData(userId, aoiId);

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
                            onClick={() => handleDeleteAOI(userId, aoi.aoiId, setDatasets)}
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

                                    handleAddCSV(userId, aoi.aoiId, files);
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

                                <span
                                    className="dataset-name aoi-layer"
                                    title={shapefile.name}
                                >
                                    🟦 {shapefile.name}
                                </span>
                            </div>
                        )}

                        {/* CSVs associados */}
                        {csvLayers.map(csv => (
                            <div
                                key={csv.name}
                                className="dataset-item csv-item"
                            >
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
                                            csv.name
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
