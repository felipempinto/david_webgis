from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form
from models.user import User
from core.auth import get_current_user
from uuid import uuid4
import os
import pandas as pd
import geopandas as gpd

from sqlalchemy.orm import Session
from db.session import get_db
from models.project import Project
from models.dataset import Dataset
from models.user import UserRole

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
@router.post("/")
async def create_project(
    project_name: str = Form(...),
    aoi_file: list[UploadFile] = File(...),
    extra_files: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=403,
            detail="Only admins can create projects"
        )

    if not aoi_file:
        raise HTTPException(
            status_code=400,
            detail="AOI files required"
        )

    required_ext = {".shp", ".dbf", ".shx"}

    uploaded_ext = {
        os.path.splitext(f.filename.lower())[1]
        for f in aoi_file
    }

    if not required_ext.issubset(uploaded_ext):
        raise HTTPException(
            status_code=400,
            detail="Shapefile must include .shp .dbf .shx"
        )

    project_uuid = str(uuid4())
    project_path = os.path.join(STORAGE_ROOT, project_uuid)

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
    shp_path = os.path.join(area_path, shp_name)

    try:
        gdf = gpd.read_file(shp_path)
        gdf = gdf.to_crs(MAP_CRS)

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid shapefile"
        )

    if gdf.empty:
        raise HTTPException(
            status_code=400,
            detail="Shapefile contains no features"
        )

    geom = gdf.unary_union

    project = Project(
        name=project_name,
        user_id=current_user.id,
        geom=geom
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    for file in extra_files:
        file_path = os.path.join(dataset_path, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        dataset = Dataset(
            name=file.filename,
            file_path=file_path,
            file_type="csv",
            project_id=project.id
        )
        db.add(dataset)
    db.commit()

    return {
        "status": "success",
        "data": {
            "project_id": str(project.public_id),
            "name": project.name
        }
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
