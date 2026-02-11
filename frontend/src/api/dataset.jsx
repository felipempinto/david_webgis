const API_URL = import.meta.env.VITE_API_URL;

export const fetchUserDatasets = async (userId) => {
    const res = await fetch(`${API_URL}/datasets/${userId}`);

    if (!res.ok) {
        throw new Error("Failed to list datasets");
    }

    const result = await res.json();

    return result?.data?.datasets ?? [];
};


export const fetchDatasets = async (userId, datasetId) => {
    const res = await fetch(
        `${API_URL}/datasets/${userId}/${datasetId}`
    );

    if (!res.ok) {
        throw new Error("Failed to load datasets");
    }

    const result = await res.json();

    return result?.data?.layers?.map(layer => ({
        ...layer,
        visible: true
    })) ?? [];
};


export const uploadDataset = async (userId, files) => {
    const formData = new FormData();

    files.forEach(file => {
        formData.append("files", file);
    });

    const res = await fetch(`${API_URL}/datasets/${userId}`, {
        method: "POST",
        body: formData
    });

    if (!res.ok) {
        throw new Error("Upload failed");
    }

    return await res.json(); // retorna dataset_id
};
