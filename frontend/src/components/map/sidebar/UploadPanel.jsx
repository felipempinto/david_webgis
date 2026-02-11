import { useState } from "react";
import { uploadDataset } from "../../../api/dataset";

const UploadPanel = ({ setDatasets }) => {
    const [fileName, setFileName] = useState("");
    const [isUploading, setIsUploading] = useState(false);
    const [success, setSuccess] = useState(false);

    const handleUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setFileName(file.name);
        setIsUploading(true);
        setSuccess(false);

        try {
            const result = await uploadDataset(file);
            setDatasets(prev => [...prev, { ...result, visible: true }]);
            setSuccess(true);
            setTimeout(() => setSuccess(false), 1000);
        } catch (error) {
            console.error("Upload failed", error);
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="upload-panel">
            <h4>Upload new dataset</h4>

            <input
                type="file"
                id="file-upload"
                className="file-input"
                onChange={handleUpload}
                disabled={isUploading}
            />

            <label
                htmlFor="file-upload"
                className={`upload-button ${success ? "upload-success" : ""}`}
            >
                <span>📁</span>
                {isUploading ? "Uploading..." : "Choose file"}
            </label>

            {fileName && (
                <div className="file-name">
                    <span>✓</span> {fileName}
                </div>
            )}
        </div>
    );
};

export default UploadPanel;