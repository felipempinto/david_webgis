from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from models.user import User
from core.auth import get_current_user
# from uuid import uuid4
from uuid import UUID
import os
import pandas as pd
import geopandas as gpd

from shapely import force_2d
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session
from db.session import get_db

from models.project import Project
from models.dataset import Dataset

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
import os
import shutil
import tempfile

@router.post("/")
async def create_project(
    project_name: str = Form(...),
    aoi_file: list[UploadFile] = File(...),
    extra_files: list[UploadFile] = File(default=[]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    temp_project_path = None
    final_project_path = None

    try:
        if not aoi_file:
            raise HTTPException(400, "AOI files required")

        required_ext = {".shp", ".dbf", ".shx"}

        uploaded_ext = {
            os.path.splitext(f.filename.lower())[1]
            for f in aoi_file
        }

        if not required_ext.issubset(uploaded_ext):
            raise HTTPException(400, "Shapefile must include .shp .dbf .shx")

        # 1) salva temporariamente só para validar/leitura
        temp_project_path = tempfile.mkdtemp(prefix="project_upload_")
        temp_area_path = os.path.join(temp_project_path, "area")
        temp_dataset_path = os.path.join(temp_project_path, "datasets")

        os.makedirs(temp_area_path, exist_ok=True)
        os.makedirs(temp_dataset_path, exist_ok=True)

        for file in aoi_file:
            file_path = os.path.join(temp_area_path, file.filename)
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

        shp_name = next(
            f.filename for f in aoi_file
            if f.filename.lower().endswith(".shp")
        )

        shp_path = os.path.join(temp_area_path, shp_name)

        try:
            gdf = gpd.read_file(shp_path).to_crs(MAP_CRS)
        except Exception:
            raise HTTPException(400, "Invalid shapefile")

        geom_union = gdf.geometry.union_all()
        geom_2d = force_2d(geom_union)

        # 2) cria projeto no banco
        project = Project(
            name=project_name,
            user_id=current_user.id,
            geom=geom_2d.wkt
        )

        db.add(project)
        db.flush()      # gera id e também public_id, se o model estiver configurado corretamente
        db.refresh(project)

        # 3) usa o public_id REAL do projeto salvo
        final_project_path = get_project_path(
            current_user.public_id,
            str(project.public_id)
        )

        final_area_path = os.path.join(final_project_path, "area")
        final_dataset_path = os.path.join(final_project_path, "datasets")

        os.makedirs(final_area_path, exist_ok=True)
        os.makedirs(final_dataset_path, exist_ok=True)

        # 4) move AOI da pasta temp para a final
        for file_name in os.listdir(temp_area_path):
            shutil.move(
                os.path.join(temp_area_path, file_name),
                os.path.join(final_area_path, file_name)
            )

        # 5) salva extras já no local final
        for file in extra_files:
            file_path = os.path.join(final_dataset_path, file.filename)

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
        db.refresh(project)

        return {
            "status": "success",
            "project_id": str(project.public_id)
        }

    except Exception:
        db.rollback()

        # se criou pasta final e depois falhou, remove para não deixar lixo inconsistente
        if final_project_path and os.path.exists(final_project_path):
            shutil.rmtree(final_project_path, ignore_errors=True)

        raise

    finally:
        if temp_project_path and os.path.exists(temp_project_path):
            shutil.rmtree(temp_project_path, ignore_errors=True)

# -------------------------------------------------------
# LIST PROJECTS
# -------------------------------------------------------

@router.get("/")
def list_user_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id)
        .all()
    )

    return {
        "status": "success",
        "data": {
            "projects": [
                str(p.public_id) for p in projects
            ]
        }
    }

# -------------------------------------------------------
# GET PROJECT DATA
# -------------------------------------------------------


# -------------------------------------------------------
# ADD EXTRA FILES
# -------------------------------------------------------
@router.post("/{aoi_id}/extras")
async def add_extra_files(
    aoi_id: str,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        project_uuid = UUID(aoi_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project id")

    project = (
        db.query(Project)
        .filter(
            Project.public_id == project_uuid,
            Project.user_id == current_user.id
        )
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="AOI not found")

    aoi_path = os.path.join(
        STORAGE_ROOT,
        f"user_{current_user.public_id}",
        f"project_{project.public_id}",
        "datasets"
    )

    os.makedirs(aoi_path, exist_ok=True)

    saved_files = []

    try:
        for file in files:
            file_path = os.path.join(aoi_path, file.filename)

            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

            dataset = Dataset(
                name=file.filename,
                file_path=file_path,
                file_type="csv",
                project_id=project.id
            )
            db.add(dataset)
            db.flush() 

            try:
                geojson = csv_to_geojson(file_path)
            except RuntimeError:
                raise HTTPException(
                    status_code=400,
                    detail=f"File unreadable: {file.filename}"
                )

            saved_files.append({
                "id": dataset.id,
                "name": file.filename,
                "source": "csv",
                "type": "point",
                "geojson": geojson
            })

        db.commit()

        return {
            "status": "success",
            "data": saved_files
        }

    except Exception:
        db.rollback()
        raise

def geom_to_geojson(geom):
    shapely_geom = to_shape(geom)
    gdf = gpd.GeoDataFrame(geometry=[shapely_geom], crs=MAP_CRS)
    return gdf.__geo_interface__

@router.get("/{project_id}")
def get_project_data(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    project = (
        db.query(Project)
        .filter(Project.public_id == project_id)
        .filter(Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(404, "Project not found")
    layers = []
    errors = []

    aoi_geojson = geom_to_geojson(project.geom)

    layers.append({
        "name": "AOI",
        "public_id": f"aoi-{project.public_id}",
        "type": "polygon",
        "source": "aoi",
        "geojson": aoi_geojson,
        "created_at": None
    })

    for dataset in project.datasets:
        try:
            if dataset.file_type == "csv":
                geojson = csv_to_geojson(dataset.file_path)
                layers.append({
                    "name": dataset.name,
                    "public_id":dataset.public_id,
                    "meta":dataset.meta,
                    "source": "csv",
                    "type": "point",
                    "geojson": geojson,
                    "created_at":dataset.created_at
                })

        except RuntimeError as e:
            errors.append(str(e))

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
    project_id: str,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    project = (
        db.query(Project)
        .filter(Project.public_id == project_id)
        .filter(Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(404, "Project not found")

    project_path = get_project_path(
        current_user.public_id,
        project_id
    )
    dataset_path = os.path.join(project_path, "datasets")
    os.makedirs(dataset_path, exist_ok=True)
    results = []
    for file in files:
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
        geojson = csv_to_geojson(file_path)
        results.append({
            "name": file.filename,
            "geojson": geojson
        })

    db.commit()

    return {
        "status": "success",
        "data": results
    }


# -------------------------------------------------------
# DELETE DATASET
# -------------------------------------------------------

# @router.delete("/{project_id}/datasets/{filename}")
@router.delete("/datasets/{public_id}")
def delete_file_from_project(
    public_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    dataset = (
        db.query(Dataset)
        .filter(Dataset.public_id == public_id)
        .first()
    )
    if not dataset:
        raise HTTPException(404, "Dataset not found")

    project = (
        db.query(Project)
        .filter(
            Project.id == dataset.project_id,
            Project.user_id == current_user.id
        )
        .first()
    )
    if not project:
        raise HTTPException(403, "Not authorized")
        
    file_path = dataset.file_path

    if not os.path.exists(file_path):
        print("não achou o faio",file_path)
        raise HTTPException(404, "File not found")

    os.remove(file_path)

    return {"status": "deleted"}


# -------------------------------------------------------
# DELETE PROJECT
# -------------------------------------------------------
@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    project = (
        db.query(Project)
        .filter(Project.public_id == project_id)
        .filter(Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(404, "Project not found")

    project_path = get_project_path(
        current_user.public_id,
        project_id
    )

    if os.path.exists(project_path):
        import shutil
        shutil.rmtree(project_path)

    db.delete(project)
    db.commit()

    return {"status": "deleted"}