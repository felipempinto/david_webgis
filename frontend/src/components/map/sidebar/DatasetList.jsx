const DatasetList = ({ datasets, setDatasets }) => {

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
            await fetch(`/aois/${aoiId}/extras/${filename}`, {
                method: "DELETE"
            });

            setDatasets(prev =>
                prev.map(aoi =>
                    aoi.aoiId === aoiId
                        ? {
                            ...aoi,
                            layers: aoi.layers.filter(
                                l => l.name !== filename
                            )
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

                        {/* Shapefile base */}
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
