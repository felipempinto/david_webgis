from fastapi import APIRouter, HTTPException
from fastapi import UploadFile, File, Depends
from uuid import uuid4
import os
import pandas as pd
import geopandas as gpd

router = APIRouter()

STORAGE_ROOT = "storage"

CSV_CRS = "EPSG:2232"
MAP_CRS = "EPSG:4326"



def csv_to_geojson(csv_path: str):
    try:
        df = pd.read_csv(csv_path)

        if "X" not in df.columns or "Y" not in df.columns:
            raise ValueError("CSV missing X or Y columns")

        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df["X"], df["Y"]),
            crs=CSV_CRS
        )

        gdf = gdf.to_crs(MAP_CRS)

        return gdf.__geo_interface__

    except Exception as e:
        raise RuntimeError(f"{os.path.basename(csv_path)}: {str(e)}")



def list_files(path: str, extension: str):
    if not os.path.exists(path):
        return []

    return [
        f for f in os.listdir(path)
        if f.lower().endswith(extension)
    ]


############################### NEW ROUTES ###############################

@router.post("/aois/{user_id}")
async def create_aoi(
    user_id: str,
    aoi_file: list[UploadFile] = File(...),
    extra_files: list[UploadFile] = File(default=[])
):
    if not aoi_file:
        raise HTTPException(status_code=400, detail="AOI files required")

    # 🔹 Validação extensões
    required_ext = {".shp", ".dbf", ".shx"}
    uploaded_ext = {
        os.path.splitext(f.filename.lower())[1]
        for f in aoi_file
    }

    if not required_ext.issubset(uploaded_ext):
        raise HTTPException(
            status_code=400,
            detail="Shapefile must include .shp, .dbf and .shx"
        )

    aoi_id = str(uuid4())

    aoi_path = os.path.join(
        STORAGE_ROOT,
        f"user_{user_id}",
        f"aoi_{aoi_id}"
    )

    os.makedirs(aoi_path, exist_ok=True)

    # 🔹 Salva arquivos AOI
    for file in aoi_file:
        file_path = os.path.join(aoi_path, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

    # 🔹 Valida leitura
    shp_name = next(
        f.filename for f in aoi_file
        if f.filename.lower().endswith(".shp")
    )

    try:
        gpd.read_file(os.path.join(aoi_path, shp_name))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid shapefile")

    # 🔹 Salva extras
    for file in extra_files:
        file_path = os.path.join(aoi_path, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

    return {
        "status": "success",
        "aoi_id": aoi_id
    }



@router.get("/aois/{user_id}")
def list_user_aois(user_id: str):

    user_path = os.path.join(STORAGE_ROOT, f"user_{user_id}")

    if not os.path.exists(user_path):
        return {"status": "success", "data": {"aois": []}}

    aois = []

    for folder in os.listdir(user_path):
        if folder.startswith("aoi_"):
            aois.append(folder.replace("aoi_", ""))

    return {
        "status": "success",
        "data": {
            "aois": aois
        }
    }


@router.post("/aois/{user_id}/{aoi_id}/extras")
async def add_extra_files(
    user_id: str,
    aoi_id: str,
    files: list[UploadFile] = File(...)
):
    aoi_path = os.path.join(
        STORAGE_ROOT,
        f"user_{user_id}",
        f"aoi_{aoi_id}"
    )

    if not os.path.exists(aoi_path):
        raise HTTPException(status_code=404, detail="AOI not found")

    for file in files:
        file_path = os.path.join(aoi_path, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

    # return {"status": "success"}

    try:
        geojson = csv_to_geojson(file_path)

        return {
            "status":"sucess",
            "data":{
                "name": file.filename,
                "source": "csv",
                "type": "point",
                "geojson": geojson
            }
        }

    except RuntimeError as e:
        raise HTTPException(status_code=400, detail="File unreadable")


@router.delete("/aois/{user_id}/{aoi_id}/extras/{filename}")
def delete_extra_file(user_id: str, aoi_id: str, filename: str):

    if "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    aoi_path = os.path.join(
        STORAGE_ROOT,
        f"user_{user_id}",
        f"aoi_{aoi_id}"
    )

    if not os.path.isdir(aoi_path):
        raise HTTPException(status_code=404, detail="AOI not found")

    file_path = os.path.join(aoi_path, filename)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV can be deleted")

    os.remove(file_path)

    return {"status": "deleted"}


@router.delete("/aois/{user_id}/{aoi_id}")
def delete_aoi(user_id:str,aoi_id:str):
    aoi_path = os.path.join(
        STORAGE_ROOT,
        f"user_{user_id}",
        f"aoi_{aoi_id}"
    )

    if not os.path.exists(aoi_path):
        raise HTTPException(status_code=404, detail="AOI not found")

    for file in os.listdir(aoi_path):
        os.remove(os.path.join(aoi_path,file))


    os.rmdir(aoi_path)
    
    return {"status": "deleted"}
    


@router.get("/aois/{user_id}/{aoi_id}")
def get_aoi_data(user_id: str, aoi_id: str):

    aoi_path = os.path.join(
        STORAGE_ROOT,
        f"user_{user_id}",
        f"aoi_{aoi_id}"
    )

    if not os.path.exists(aoi_path):
        raise HTTPException(status_code=404, detail="AOI not found")

    csv_files = list_files(aoi_path, ".csv")
    shp_files = list_files(aoi_path, ".shp")

    layers = []
    errors = []

    for csv in csv_files:
        try:
            geojson = csv_to_geojson(os.path.join(aoi_path, csv))

            layers.append({
                "name": csv,
                "source": "csv",
                "type": "point",
                "geojson": geojson
            })

        except RuntimeError as e:
            errors.append(str(e))

    for shp in shp_files:
        try:
            gdf = gpd.read_file(os.path.join(aoi_path, shp))

            if not gdf.empty:
                layers.append({
                    "name": shp,
                    "source": "shapefile",
                    "type": "polygon",
                    "geojson": gdf.to_crs(MAP_CRS).__geo_interface__
                })

        except Exception as e:
            errors.append(f"{shp}: {str(e)}")

    return {
        "status": "success",
        "data": {
            "layers": layers,
            "errors": errors
        }
    }

#########################################################################


# def list_csv_files(path: str):
#     if not os.path.exists(path):
#         return []

#     return [
#         f for f in os.listdir(path)
#         if f.lower().endswith(".csv")
#     ]



# def load_aoi_geojson(shp_path: str):
#     if not os.path.exists(shp_path):
#         return None

#     try:
#         gdf = gpd.read_file(shp_path)

#         if gdf.empty:
#             return None

#         return gdf.to_crs(MAP_CRS).__geo_interface__

#     except Exception as e:
#         raise RuntimeError(f"AOI load failed: {str(e)}")




# @router.get("/datasets/{user_id}/{dataset_id}")
# def get_datasets(user_id: str, dataset_id: str):

#     dataset_path = os.path.join(
#         STORAGE_ROOT,
#         f"user_{user_id}",
#         f"dataset_{dataset_id}"
#     )

#     if not os.path.exists(dataset_path):
#         raise HTTPException(status_code=404, detail="Dataset not found")

#     csv_files = list_files(dataset_path, ".csv")
#     shp_files = list_files(dataset_path, ".shp")

#     layers = []
#     errors = []

#     # CSVs
#     for csv in csv_files:
#         try:
#             geojson = csv_to_geojson(os.path.join(dataset_path, csv))

#             layers.append({
#                 "name": csv,
#                 "source": "csv",
#                 "type": "point",
#                 "geojson": geojson
#             })

#         except RuntimeError as e:
#             errors.append(str(e))

#     # Shapefiles (ex: AOI ou qualquer polígono)
#     for shp in shp_files:
#         try:
#             gdf = gpd.read_file(os.path.join(dataset_path, shp))

#             if not gdf.empty:
#                 layers.append({
#                     "name": shp,
#                     "source": "shapefile",
#                     "type": "polygon",
#                     "geojson": gdf.to_crs(MAP_CRS).__geo_interface__
#                 })

#         except Exception as e:
#             errors.append(f"{shp}: {str(e)}")

#     return {
#         "status": "success",
#         "data": {
#             "layers": layers,
#             "errors": errors
#         }
#     }


# @router.post("/datasets/{user_id}")
# async def upload_dataset(user_id: str, files: list[UploadFile] = File(...)):
#     print("start")
#     dataset_id = str(uuid4())
#     dataset_path = os.path.join(
#         STORAGE_ROOT,
#         f"user_{user_id}",
#         f"dataset_{dataset_id}"
#     )
#     print(dataset_path)
#     os.makedirs(dataset_path, exist_ok=True)

#     for file in files:
#         file_path = os.path.join(dataset_path, file.filename)

#         with open(file_path, "wb") as buffer:
#             buffer.write(await file.read())

#     return {
#         "status": "success",
#         "dataset_id": dataset_id
#     }


# @router.get("/datasets/{user_id}")
# def list_user_datasets(user_id: str):

#     user_path = os.path.join(
#         STORAGE_ROOT,
#         f"user_{user_id}"
#     )

#     if not os.path.exists(user_path):
#         return {
#             "status": "success",
#             "data": {
#                 "datasets": []
#             }
#         }

#     dataset_ids = []

#     for folder in os.listdir(user_path):
#         full_path = os.path.join(user_path, folder)

#         if os.path.isdir(full_path) and folder.startswith("dataset_"):
#             dataset_id = folder.replace("dataset_", "")
#             dataset_ids.append(dataset_id)

#     return {
#         "status": "success",
#         "data": {
#             "datasets": dataset_ids
#         }
#     }
