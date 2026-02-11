const API_URL = import.meta.env.VITE_API_URL;

export const fetchDatasets = async () => {
    const res = await fetch(`${API_URL}/datasets`);

    if (!res.ok) {
        throw new Error("Failed to load datasets");
    }

    const result = await res.json();

    return result?.data?.layers?.map(layer => ({
        ...layer,
        visible: true
    })) ?? [];
};

export const uploadDataset = async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${API_URL}/datasets/upload`, {
        method: "POST",
        body: formData
    });

    if (!res.ok) {
        throw new Error("Upload failed");
    }

    return await res.json();
};

// const API_URL = import.meta.env.VITE_API_URL;

// export const fetchDatasets = async () => {
//     const res = await fetch(`${API_URL}/datasets`);

//     if (!res.ok) {
//         throw new Error("Failed to load datasets");
//     }

//     const result = await res.json();
//     return result?.data?.layers ?? [];
// };
