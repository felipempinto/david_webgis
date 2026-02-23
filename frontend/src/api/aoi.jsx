const API_URL = import.meta.env.VITE_API_URL;


/* =========================
    LISTAR AOIs DO USUÁRIO
========================= */
export const fetchUserAOIs = async (userId) => {
    const res = await fetch(`${API_URL}/aois/${userId}`);

    if (!res.ok) {
        throw new Error("Failed to list AOIs");
    }

    const result = await res.json();

    return result?.data?.aois ?? [];
};


/* =========================
    BUSCAR DADOS DE UMA AOI
========================= */
export const fetchAOIData = async (userId, aoiId) => {
    const res = await fetch(
        `${API_URL}/aois/${userId}/${aoiId}`
    );

    if (!res.ok) {
        throw new Error("Failed to load AOI");
    }

    const result = await res.json();

    return result?.data?.layers?.map(layer => ({
        ...layer,
        visible: true
    })) ?? [];
};


/* =========================
    CRIAR NOVA AOI
    (AOI obrigatório + extras opcionais)
========================= */
export const createAOI = async (userId, aoiFiles, extraFiles = []) => {
    const formData = new FormData();

    // 🔹 Shapefile principal
    aoiFiles.forEach(file => {
        formData.append("aoi_file", file);
    });

    // 🔹 Extras opcionais
    extraFiles.forEach(file => {
        formData.append("extra_files", file);
    });

    const res = await fetch(`${API_URL}/aois/${userId}`, {
        method: "POST",
        body: formData
    });

    if (!res.ok) {
        throw new Error("Upload failed");
    }

    return await res.json();
};


/* =========================
    ADICIONAR DADOS EXTRAS
========================= */
export const addAOIExtras = async (userId, aoiId, files) => {
    const formData = new FormData();

    files.forEach(file => {
        formData.append("files", file);
    });

    const res = await fetch(
        `${API_URL}/aois/${userId}/${aoiId}/extras`,
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


/* =========================
    DELETAR DADO EXTRA
========================= */
export const deleteAOIExtra = async (userId, aoiId, filename) => {
    const res = await fetch(
        `${API_URL}/aois/${userId}/${aoiId}/extras/${filename}`,
        {
            method: "DELETE"
        }
    );

    if (!res.ok) {
        throw new Error("Failed to delete file");
    }

    return await res.json();
};


export const handleDeleteAOI = async (userId,aoiId,setDatasets) => {
    try {
        await fetch(`${API_URL}/aois/${userId}/${aoiId}`, {
            method: "DELETE"
        });

        setDatasets(prev =>
            prev.filter(aoi => aoi.aoiId !== aoiId)
        );

    } catch (err) {
        //TODO: tratar os erros aqui
        alert(err);
    }
};