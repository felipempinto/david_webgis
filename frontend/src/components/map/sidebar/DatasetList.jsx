const DatasetList = ({ datasets, setDatasets }) => {
    const toggleVisibility = (name) => {
        setDatasets(prev =>
            prev.map(ds =>
                ds.name === name ? { ...ds, visible: !ds.visible } : ds
            )
        );
    };

    if (!datasets.length) {
        return <div className="empty-datasets">✨ No datasets yet – upload one above</div>;
    }

    return (
        <div className="dataset-list">
            {datasets.map(ds => (
                <div key={ds.name} className="dataset-item">
                    <label className="checkbox-container">
                        <input
                            type="checkbox"
                            checked={ds.visible}
                            onChange={() => toggleVisibility(ds.name)}
                        />
                        <span className="checkmark"></span>
                    </label>
                    <span className="dataset-name" title={ds.name}>
                        {ds.name}
                    </span>
                </div>
            ))}
        </div>
    );
};

export default DatasetList;