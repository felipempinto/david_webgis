from fastapi import APIRouter, HTTPException
from fastapi import UploadFile, File, Depends
from uuid import uuid4
import os
import pandas as pd
import geopandas as gpd

router = APIRouter()

STORAGE_ROOT = "storage"
# DATASET_PATH = "files"
# AOI_SHP_PATH = os.path.join(DATASET_PATH, "AOI_Limit", "AOI_Limit.shp")

CSV_CRS = "EPSG:2232"
MAP_CRS = "EPSG:4326"


def list_csv_files(path: str):
    if not os.path.exists(path):
        return []

    return [
        f for f in os.listdir(path)
        if f.lower().endswith(".csv")
    ]


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


def load_aoi_geojson(shp_path: str):
    if not os.path.exists(shp_path):
        return None

    try:
        gdf = gpd.read_file(shp_path)

        if gdf.empty:
            return None

        return gdf.to_crs(MAP_CRS).__geo_interface__

    except Exception as e:
        raise RuntimeError(f"AOI load failed: {str(e)}")

def list_files(path: str, extension: str):
    if not os.path.exists(path):
        return []

    return [
        f for f in os.listdir(path)
        if f.lower().endswith(extension)
    ]



@router.get("/datasets/{user_id}/{dataset_id}")
def get_datasets(user_id: str, dataset_id: str):

    dataset_path = os.path.join(
        STORAGE_ROOT,
        f"user_{user_id}",
        f"dataset_{dataset_id}"
    )

    if not os.path.exists(dataset_path):
        raise HTTPException(status_code=404, detail="Dataset not found")

    csv_files = list_files(dataset_path, ".csv")
    shp_files = list_files(dataset_path, ".shp")

    layers = []
    errors = []

    # CSVs
    for csv in csv_files:
        try:
            geojson = csv_to_geojson(os.path.join(dataset_path, csv))

            layers.append({
                "name": csv,
                "source": "csv",
                "type": "point",
                "geojson": geojson
            })

        except RuntimeError as e:
            errors.append(str(e))

    # Shapefiles (ex: AOI ou qualquer polígono)
    for shp in shp_files:
        try:
            gdf = gpd.read_file(os.path.join(dataset_path, shp))

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

# @router.get("/datasets")
# def get_datasets():
#     try:
#         csv_files = list_csv_files(DATASET_PATH)

#         csv_layers = []
#         csv_errors = []

#         for csv in csv_files:
#             path = os.path.join(DATASET_PATH, csv)

#             try:
#                 geojson = csv_to_geojson(path)

#                 csv_layers.append({
#                     "name": csv,
#                     "source": "csv",
#                     "type": "point",
#                     "geojson": geojson
#                 })

#             except RuntimeError as e:
#                 csv_errors.append(str(e))

#         # AOI
#         try:
#             aoi_geojson = load_aoi_geojson(AOI_SHP_PATH)
#         except RuntimeError as e:
#             raise HTTPException(status_code=500, detail=str(e))

#         return {
#             "status": "success",
#             "data": {
#                 "layers": (
#                     csv_layers +
#                     ([
#                         {
#                             "name": "AOI_Limit",
#                             "source": "shapefile",
#                             "type": "aoi",
#                             "geojson": aoi_geojson
#                         }
#                     ] if aoi_geojson else [])
#                 ),
#                 "errors": csv_errors
#             },
#             "error": None
#         }

#     except HTTPException:
#         raise

#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail={
#                 "status": "error",
#                 "data": None,
#                 "error": {
#                     "code": "DATASET_PROCESSING_FAILED",
#                     "message": str(e)
#                 }
#             }
#         )




@router.post("/datasets/{user_id}")
async def upload_dataset(user_id: str, files: list[UploadFile] = File(...)):
    print("start")
    dataset_id = str(uuid4())
    dataset_path = os.path.join(
        STORAGE_ROOT,
        f"user_{user_id}",
        f"dataset_{dataset_id}"
    )
    print(dataset_path)
    os.makedirs(dataset_path, exist_ok=True)

    for file in files:
        file_path = os.path.join(dataset_path, file.filename)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

    return {
        "status": "success",
        "dataset_id": dataset_id
    }


@router.get("/datasets/{user_id}")
def list_user_datasets(user_id: str):

    user_path = os.path.join(
        STORAGE_ROOT,
        f"user_{user_id}"
    )

    if not os.path.exists(user_path):
        return {
            "status": "success",
            "data": {
                "datasets": []
            }
        }

    dataset_ids = []

    for folder in os.listdir(user_path):
        full_path = os.path.join(user_path, folder)

        if os.path.isdir(full_path) and folder.startswith("dataset_"):
            dataset_id = folder.replace("dataset_", "")
            dataset_ids.append(dataset_id)

    return {
        "status": "success",
        "data": {
            "datasets": dataset_ids
        }
    }
