const API_URL = import.meta.env.VITE_API_URL;
import { apiFetch } from "./client";

export const fetchUserAOIs = async () => {
    const result = await apiFetch("/projects");
    return result?.data?.projects ?? [];
};

export const fetchAOIData = async (projectId) => {
    const result = await apiFetch(`/projects/${projectId}`);
    return result?.data?.layers?.map(layer => ({
        ...layer,
        visible: true
    })) ?? [];
};

export const createAOI = async (projectName, aoiFiles, extraFiles = []) => {
    const formData = new FormData();
    formData.append("project_name", projectName);
    aoiFiles.forEach(file => {
        formData.append("aoi_file", file);
    });
    extraFiles.forEach(file => {
        formData.append("extra_files", file);
    });
    const token = localStorage.getItem("token");
    const res = await fetch(`${API_URL}/projects`, {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`
        },
        body: formData
    });

    if (!res.ok) {
        throw new Error("Upload failed");
    }

    return res.json();
};

export const addAOIExtras = async (userId, aoiId, files) => {
    const formData = new FormData();

    files.forEach(file => {
        formData.append("files", file);
    });

    const res = await fetch(
        `${API_URL}/projects/${userId}/${aoiId}/extras`,
        {
            method: "POST",
            body: formData
        }
    );

    if (!res.ok) {
        throw new Error("Failed to upload extra files");
    }

    return await res.json();
};


// export const deleteAOIExtra = async (aoiId, filename) => {
export const deleteAOIExtra = async (publicId) => {
    const token = localStorage.getItem("token");

    const res = await fetch(
        // `${API_URL}/projects/${aoiId}/datasets/${filename}`,
        `${API_URL}/projects/datasets/${publicId}`,
        {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        }
    );

    if (!res.ok) {
        throw new Error("Failed to delete file");
    }

    return await res.json();
};


export const handleDeleteAOI = async (aoiId,setDatasets) => {
    const token = localStorage.getItem("token");
    try {
        await fetch(
            `${API_URL}/projects/${aoiId}`
            , {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        setDatasets(prev =>
            prev.filter(aoi => aoi.aoiId !== aoiId)
        );

    } catch (err) {
        //TODO: tratar os erros aqui
        alert(err);
    }
};