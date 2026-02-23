import "./AttributeTable.css";

const AttributeTable = ({ layer, onClose }) => {

    if (!layer?.geojson?.features?.length) {
        return null;
    }

    const features = layer.geojson.features;
    const columns = Object.keys(features[0].properties);

    return (
        <div className="attribute-table-container">
            <div className="table-header">
                <h3>📊 {layer.name}</h3>
                <button
                    className="table-close-btn"
                    onClick={onClose}
                >
                    Close
                </button>
            </div>

            <div className="table-wrapper">
                <table className="attribute-table">
                    <thead>
                        <tr>
                            {columns.map(col => (
                                <th key={col}>{col}</th>
                            ))}
                        </tr>
                    </thead>

                    <tbody>
                        {features.map((feature, i) => (
                            <tr key={i}>
                                {columns.map(col => (
                                    <td key={col}>
                                        {String(feature.properties[col] ?? "")}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default AttributeTable;