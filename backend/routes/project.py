from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from models.user import User
from core.auth import get_current_user
from uuid import uuid4
import os
import pandas as pd
import geopandas as gpd

router = APIRouter(prefix="/projects")

STORAGE_ROOT = "storage"

CSV_CRS = "EPSG:2232"
MAP_CRS = "EPSG:4326"


# ##### Routes schema:
# POST   /projects/{user_id}
# GET    /projects/{user_id}
# GET    /projects/{user_id}/{project_id}
# DELETE /projects/{user_id}/{project_id}

# POST   /projects/{user_id}/{project_id}/datasets
# DELETE /projects/{user_id}/{project_id}/datasets/{filename}

# -------------------------------------------------------
# Helpers
# -------------------------------------------------------

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


def get_project_path(user_id, project_id):
    return os.path.join(
        STORAGE_ROOT,
        f"user_{user_id}",
        f"project_{project_id}",
    )


# -------------------------------------------------------
# CREATE PROJECT
# -------------------------------------------------------
@router.post("/")
async def create_project(
    project_name: str = Form(...),
    aoi_file: list[UploadFile] = File(...),
    extra_files: list[UploadFile] = File(default=[]),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.public_id
# async def create_project(
#         user_id: str,
#         project_name: str = Form(...),
#         aoi_file: list[UploadFile] = File(...),
#         extra_files: list[UploadFile] = File(default=[])
#     ):

    if not aoi_file:
        raise HTTPException(400, "AOI files required")

    required_ext = {".shp", ".dbf", ".shx"}

    uploaded_ext = {
        os.path.splitext(f.filename.lower())[1]
        for f in aoi_file
    }

    if not required_ext.issubset(uploaded_ext):
        raise HTTPException(
            400,
            "Shapefile must include .shp .dbf .shx"
        )

    project_id = str(uuid4())

    project_path = get_project_path(user_id, project_id)

    area_path = os.path.join(project_path, "area")
    dataset_path = os.path.join(project_path, "datasets")

    os.makedirs(area_path, exist_ok=True)
    os.makedirs(dataset_path, exist_ok=True)

    for file in aoi_file:
        file_path = os.path.join(area_path, file.filename)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

    shp_name = next(
        f.filename for f in aoi_file
        if f.filename.lower().endswith(".shp")
    )

    try:
        gpd.read_file(os.path.join(area_path, shp_name))
    except Exception:
        raise HTTPException(400, "Invalid shapefile")

    for file in extra_files:
        file_path = os.path.join(dataset_path, file.filename)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

    return {
        "status": "success",
        "project_id": project_id
    }


# -------------------------------------------------------
# LIST PROJECTS
# -------------------------------------------------------

@router.get("/")
def list_user_projects(
    current_user: User = Depends(get_current_user)
):

    user_id = current_user.public_id

    user_path = os.path.join(STORAGE_ROOT, f"user_{user_id}")

    if not os.path.exists(user_path):
        return {"status": "success", "data": {"projects": []}}

    projects = []

    for folder in os.listdir(user_path):
        if folder.startswith("project_"):
            projects.append(folder.replace("project_", ""))

    return {
        "status": "success",
        "data": {
            "projects": projects
        }
    }
# @router.get("/")
# def list_user_projects(user_id: str):
#     user_path = os.path.join(STORAGE_ROOT, f"user_{user_id}")

#     if not os.path.exists(user_path):
#         return {"status": "success", "data": {"projects": []}}

#     projects = []

#     for folder in os.listdir(user_path):

#         if folder.startswith("project_"):
#             projects.append(
#                 folder.replace("project_", "")
#             )

#     print(projects)
#     return {
#         "status": "success",
#         "data": {
#             "projects": projects
#         }
#     }


# -------------------------------------------------------
# GET PROJECT DATA
# -------------------------------------------------------

# @router.get("/{project_id}")
# def get_project_data(user_id: str, project_id: str):

#     project_path = get_project_path(user_id, project_id)
@router.get("/{project_id}")
def get_project_data(
    project_id: str,
    current_user: User = Depends(get_current_user)
):

    user_id = current_user.public_id

    project_path = get_project_path(user_id, project_id)

    if not os.path.exists(project_path):
        raise HTTPException(404, "Project not found")

    dataset_path = os.path.join(project_path,"datasets")
    area_path = os.path.join(project_path, "area")

    layers = []
    errors = []

    csv_files = list_files(dataset_path, ".csv")
    for csv in csv_files:

        try:
            geojson = csv_to_geojson(
                os.path.join(dataset_path, csv)
            )

            layers.append({
                "name": csv,
                "source": "csv",
                "type": "point",
                "geojson": geojson
            })

        except RuntimeError as e:
            errors.append(str(e))

    # area
    shp_files = list_files(area_path, ".shp")

    for shp in shp_files:

        try:

            gdf = gpd.read_file(
                os.path.join(area_path, shp)
            )

            if not gdf.empty:
                layers.append({
                    "name": shp,
                    "source": "shapefile",
                    "type": "polygon",
                    "geojson": gdf.to_crs(MAP_CRS).__geo_interface__
                })

        except Exception as e:
            errors.append(str(e))
    print("KKKK")
    return {
        "status": "success",
        "data": {
            "layers": layers,
            "errors": errors
        }
    }


# -------------------------------------------------------
# ADD DATASETS
# -------------------------------------------------------

@router.post("/{project_id}/datasets")
async def add_files_to_project(
    user_id: str,
    project_id: str,
    files: list[UploadFile] = File(...)
):

    project_path = get_project_path(user_id, project_id)

    if not os.path.exists(project_path):
        raise HTTPException(404, "Project not found")

    dataset_path = os.path.join(project_path, "datasets")

    results = []

    for file in files:

        file_path = os.path.join(dataset_path, file.filename)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        try:
            geojson = csv_to_geojson(file_path)

            results.append({
                "name": file.filename,
                "geojson": geojson
            })

        except RuntimeError:
            raise HTTPException(
                400,
                f"{file.filename} unreadable"
            )

    return {
        "status": "success",
        "data": results
    }


# -------------------------------------------------------
# DELETE DATASET
# -------------------------------------------------------

@router.delete("/{project_id}/datasets/{filename}")
def delete_file_from_project(
    user_id: str,
    project_id: str,
    filename: str
):

    if "/" in filename or "\\" in filename:
        raise HTTPException(400, "Invalid filename")

    dataset_path = os.path.join(
        get_project_path(user_id, project_id),
        "datasets"
    )

    file_path = os.path.join(dataset_path, filename)

    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found")

    os.remove(file_path)

    return {"status": "deleted"}


# -------------------------------------------------------
# DELETE PROJECT
# -------------------------------------------------------

@router.delete("/{project_id}")
def delete_project(user_id: str, project_id: str):

    project_path = get_project_path(user_id, project_id)

    if not os.path.exists(project_path):
        raise HTTPException(404, "Project not found")

    for root, dirs, files in os.walk(project_path, topdown=False):

        for file in files:
            os.remove(os.path.join(root, file))

        for dir in dirs:
            os.rmdir(os.path.join(root, dir))

    os.rmdir(project_path)

    return {"status": "deleted"}




# from fastapi import APIRouter, HTTPException, UploadFile, File, Form
# from uuid import uuid4
# import os
# import pandas as pd
# import geopandas as gpd

# router = APIRouter(prefix="/projects")

# STORAGE_ROOT = "storage"

# CSV_CRS = "EPSG:2232"
# MAP_CRS = "EPSG:4326"


# # ##### Routes schema:
# # POST   /projects/{user_id}
# # GET    /projects/{user_id}
# # GET    /projects/{user_id}/{project_id}
# # DELETE /projects/{user_id}/{project_id}

# # POST   /projects/{user_id}/{project_id}/datasets
# # DELETE /projects/{user_id}/{project_id}/datasets/{filename}

# # -------------------------------------------------------
# # Helpers
# # -------------------------------------------------------

# def csv_to_geojson(csv_path: str):
#     try:
#         df = pd.read_csv(csv_path)

#         if "X" not in df.columns or "Y" not in df.columns:
#             raise ValueError("CSV missing X or Y columns")

#         gdf = gpd.GeoDataFrame(
#             df,
#             geometry=gpd.points_from_xy(df["X"], df["Y"]),
#             crs=CSV_CRS
#         )

#         gdf = gdf.to_crs(MAP_CRS)

#         return gdf.__geo_interface__

#     except Exception as e:
#         raise RuntimeError(f"{os.path.basename(csv_path)}: {str(e)}")


# def list_files(path: str, extension: str):
#     if not os.path.exists(path):
#         return []

#     return [
#         f for f in os.listdir(path)
#         if f.lower().endswith(extension)
#     ]


# def get_project_path(user_id, project_id):
#     return os.path.join(
#         STORAGE_ROOT,
#         f"user_{user_id}",
#         f"project_{project_id}",
#     )


# # -------------------------------------------------------
# # CREATE PROJECT
# # -------------------------------------------------------
# @router.post("/{user_id}")
# async def create_project(
#         user_id: str,
#         project_name: str = Form(...),
#         aoi_file: list[UploadFile] = File(...),
#         extra_files: list[UploadFile] = File(default=[])
#     ):

#     if not aoi_file:
#         raise HTTPException(400, "AOI files required")

#     required_ext = {".shp", ".dbf", ".shx"}

#     uploaded_ext = {
#         os.path.splitext(f.filename.lower())[1]
#         for f in aoi_file
#     }

#     if not required_ext.issubset(uploaded_ext):
#         raise HTTPException(
#             400,
#             "Shapefile must include .shp .dbf .shx"
#         )

#     project_id = str(uuid4())

#     project_path = get_project_path(user_id, project_id)

#     area_path = os.path.join(project_path, "area")
#     dataset_path = os.path.join(project_path, "datasets")

#     os.makedirs(area_path, exist_ok=True)
#     os.makedirs(dataset_path, exist_ok=True)

#     for file in aoi_file:
#         file_path = os.path.join(area_path, file.filename)

#         with open(file_path, "wb") as buffer:
#             buffer.write(await file.read())

#     shp_name = next(
#         f.filename for f in aoi_file
#         if f.filename.lower().endswith(".shp")
#     )

#     try:
#         gpd.read_file(os.path.join(area_path, shp_name))
#     except Exception:
#         raise HTTPException(400, "Invalid shapefile")

#     for file in extra_files:
#         file_path = os.path.join(dataset_path, file.filename)

#         with open(file_path, "wb") as buffer:
#             buffer.write(await file.read())

#     return {
#         "status": "success",
#         "project_id": project_id
#     }


# # -------------------------------------------------------
# # LIST PROJECTS
# # -------------------------------------------------------

# @router.get("/{user_id}")
# def list_user_projects(user_id: str):
#     user_path = os.path.join(STORAGE_ROOT, f"user_{user_id}")

#     if not os.path.exists(user_path):
#         return {"status": "success", "data": {"projects": []}}

#     projects = []

#     for folder in os.listdir(user_path):

#         if folder.startswith("project_"):
#             projects.append(
#                 folder.replace("project_", "")
#             )

#     print(projects)
#     return {
#         "status": "success",
#         "data": {
#             "projects": projects
#         }
#     }


# # -------------------------------------------------------
# # GET PROJECT DATA
# # -------------------------------------------------------

# @router.get("/{user_id}/{project_id}")
# def get_project_data(user_id: str, project_id: str):

#     project_path = get_project_path(user_id, project_id)

#     if not os.path.exists(project_path):
#         raise HTTPException(404, "Project not found")

#     dataset_path = os.path.join(project_path,"datasets")
#     area_path = os.path.join(project_path, "area")

#     layers = []
#     errors = []

#     csv_files = list_files(dataset_path, ".csv")
#     for csv in csv_files:

#         try:
#             geojson = csv_to_geojson(
#                 os.path.join(dataset_path, csv)
#             )

#             layers.append({
#                 "name": csv,
#                 "source": "csv",
#                 "type": "point",
#                 "geojson": geojson
#             })

#         except RuntimeError as e:
#             errors.append(str(e))

#     # area
#     shp_files = list_files(area_path, ".shp")

#     for shp in shp_files:

#         try:

#             gdf = gpd.read_file(
#                 os.path.join(area_path, shp)
#             )

#             if not gdf.empty:
#                 layers.append({
#                     "name": shp,
#                     "source": "shapefile",
#                     "type": "polygon",
#                     "geojson": gdf.to_crs(MAP_CRS).__geo_interface__
#                 })

#         except Exception as e:
#             errors.append(str(e))
#     print("KKKK")
#     return {
#         "status": "success",
#         "data": {
#             "layers": layers,
#             "errors": errors
#         }
#     }


# # -------------------------------------------------------
# # ADD DATASETS
# # -------------------------------------------------------

# @router.post("/{user_id}/{project_id}/datasets")
# async def add_files_to_project(
#     user_id: str,
#     project_id: str,
#     files: list[UploadFile] = File(...)
# ):

#     project_path = get_project_path(user_id, project_id)

#     if not os.path.exists(project_path):
#         raise HTTPException(404, "Project not found")

#     dataset_path = os.path.join(project_path, "datasets")

#     results = []

#     for file in files:

#         file_path = os.path.join(dataset_path, file.filename)

#         with open(file_path, "wb") as buffer:
#             buffer.write(await file.read())

#         try:
#             geojson = csv_to_geojson(file_path)

#             results.append({
#                 "name": file.filename,
#                 "geojson": geojson
#             })

#         except RuntimeError:
#             raise HTTPException(
#                 400,
#                 f"{file.filename} unreadable"
#             )

#     return {
#         "status": "success",
#         "data": results
#     }


# # -------------------------------------------------------
# # DELETE DATASET
# # -------------------------------------------------------

# @router.delete("/{user_id}/{project_id}/datasets/{filename}")
# def delete_file_from_project(
#     user_id: str,
#     project_id: str,
#     filename: str
# ):

#     if "/" in filename or "\\" in filename:
#         raise HTTPException(400, "Invalid filename")

#     dataset_path = os.path.join(
#         get_project_path(user_id, project_id),
#         "datasets"
#     )

#     file_path = os.path.join(dataset_path, filename)

#     if not os.path.exists(file_path):
#         raise HTTPException(404, "File not found")

#     os.remove(file_path)

#     return {"status": "deleted"}


# # -------------------------------------------------------
# # DELETE PROJECT
# # -------------------------------------------------------

# @router.delete("/{user_id}/{project_id}")
# def delete_project(user_id: str, project_id: str):

#     project_path = get_project_path(user_id, project_id)

#     if not os.path.exists(project_path):
#         raise HTTPException(404, "Project not found")

#     for root, dirs, files in os.walk(project_path, topdown=False):

#         for file in files:
#             os.remove(os.path.join(root, file))

#         for dir in dirs:
#             os.rmdir(os.path.join(root, dir))

#     os.rmdir(project_path)

#     return {"status": "deleted"}