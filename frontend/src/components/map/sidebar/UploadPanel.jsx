import { useState } from "react";
import { createAOI, fetchAOIData } from "../../../api/aoi";

const UploadPanel = ({ userId, setAoiId, setDatasets }) => {
    const [showForm, setShowForm] = useState(false);
    const [aoiFiles, setAoiFiles] = useState([]);
    const [extraFiles, setExtraFiles] = useState([]);
    const [isUploading, setIsUploading] = useState(false);
    const [success, setSuccess] = useState(false);

    const resetForm = () => {
        setAoiFiles([]);
        setExtraFiles([]);
        setShowForm(false);
    };

    const validateShapefile = (files) => {
        const extensions = files.map(f =>
            f.name.toLowerCase().split(".").pop()
        );

        const required = ["shp", "dbf", "shx"];

        return required.every(ext => extensions.includes(ext));
    };

    const handleUpload = async () => {
        if (!aoiFiles.length) {
            alert("AOI files are required (.shp + .dbf + .shx)");
            return;
        }

        if (!validateShapefile(aoiFiles)) {
            alert("Shapefile must include .shp, .dbf and .shx");
            return;
        }

        setIsUploading(true);
        setSuccess(false);

        try {
            const result = await createAOI(userId, aoiFiles, extraFiles);
            const newAoiId = result.aoi_id;

            setAoiId(newAoiId);

            const response = await fetchAOIData(userId, newAoiId);

            const layersWithVisibility = response.map(layer => ({
                ...layer,
                visible: true
            }));

            // 🔥 IMPORTANTE: acumular AOIs
            setDatasets(prev => [
                ...prev,
                {
                    aoiId: newAoiId,
                    layers: layersWithVisibility
                }
            ]);

            setSuccess(true);
            setTimeout(() => setSuccess(false), 1000);

            resetForm();

        } catch (error) {
            console.error("AOI upload failed", error);
            alert("Upload failed. Check console.");
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="upload-panel">

            {!showForm && (
                <button
                    className="upload-button"
                    onClick={() => setShowForm(true)}
                >
                    + Add New AOI
                </button>
            )}

            {showForm && (
                <div className="aoi-form">

                    <h4>Create New AOI</h4>

                    <div className="form-section">
                        <label>AOI Shapefile</label>
                        <span className="form-hint">
                            Select all related files (.shp, .dbf, .shx)
                        </span>

                        <input
                            type="file"
                            multiple
                            accept=".shp,.dbf,.shx,.prj,.cpg"
                            onChange={(e) =>
                                setAoiFiles([...e.target.files])
                            }
                            disabled={isUploading}
                            className="file-input-modern"
                        />

                        {aoiFiles.length > 0 && (
                            <div className="file-preview">
                                {aoiFiles.map(f => f.name).join(", ")}
                            </div>
                        )}
                    </div>

                    <div className="form-section">
                        <label>Extra CSV Data</label>

                        <input
                            type="file"
                            multiple
                            accept=".csv"
                            onChange={(e) =>
                                setExtraFiles([...e.target.files])
                            }
                            disabled={isUploading}
                            className="file-input-modern"
                        />

                        {extraFiles.length > 0 && (
                            <div className="file-preview">
                                {extraFiles.map(f => f.name).join(", ")}
                            </div>
                        )}
                    </div>

                    <div className="form-actions">
                        <button
                            className="primary-btn"
                            onClick={handleUpload}
                            disabled={isUploading}
                        >
                            {isUploading ? "Uploading..." : "Create AOI"}
                        </button>

                        <button
                            className="secondary-btn"
                            onClick={resetForm}
                            disabled={isUploading}
                        >
                            Cancel
                        </button>
                    </div>

                    {success && (
                        <div className="success-msg">
                            AOI created successfully
                        </div>
                    )}
                </div>
            )}

        </div>
    );
};

export default UploadPanel;
