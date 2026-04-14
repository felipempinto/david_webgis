from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, status
from models.user import User
from core.auth import get_current_user
from uuid import UUID
from pathlib import Path
import os
import re
import shutil
import tempfile
from typing import List

import pandas as pd
import geopandas as gpd
from shapely import force_2d
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from db.session import get_db
from models.project import Project
from models.dataset import Dataset

router = APIRouter(prefix="/projects", tags=["projects"])

STORAGE_ROOT = Path("storage")
CSV_CRS = "EPSG:2232"
MAP_CRS = "EPSG:4326"

ALLOWED_DATASET_EXTENSIONS = {".csv"}
REQUIRED_SHP_EXTENSIONS = {".shp", ".dbf", ".shx"}
FILENAME_SAFE_REGEX = re.compile(r"[^A-Za-z0-9._-]")


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------

def parse_uuid(value: str, field_name: str = "id") -> UUID:
    try:
        return UUID(str(value))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}"
        )


def sanitize_filename(filename: str) -> str:
    """
    Remove path components and dangerous chars.
    Keeps only letters, numbers, dot, dash, underscore.
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )

    name = os.path.basename(filename).strip()
    name = name.replace("\x00", "")

    if not name or name in {".", ".."}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )

    safe_name = FILENAME_SAFE_REGEX.sub("_", name)

    if not safe_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )

    return safe_name


def safe_join(base: Path, *parts: str) -> Path:
    """
    Prevent path traversal.
    """
    base = base.resolve()
    candidate = base.joinpath(*parts).resolve()

    if candidate != base and base not in candidate.parents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid path"
        )

    return candidate


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def get_project_path(user_public_id, project_public_id) -> Path:
    return safe_join(
        STORAGE_ROOT,
        f"user_{user_public_id}",
        f"project_{project_public_id}",
    )


def get_dataset_folder(user_public_id, project_public_id) -> Path:
    return safe_join(
        get_project_path(user_public_id, project_public_id),
        "datasets"
    )


def get_area_folder(user_public_id, project_public_id) -> Path:
    return safe_join(
        get_project_path(user_public_id, project_public_id),
        "area"
    )


async def save_upload_file(upload: UploadFile, destination: Path) -> None:
    """
    Save uploaded file safely to disk.
    """
    ensure_dir(destination.parent)

    try:
        contents = await upload.read()
        with open(destination, "wb") as buffer:
            buffer.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {upload.filename}"
        ) from e
    finally:
        await upload.close()


def detect_file_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".csv":
        return "csv"
    return "unknown"


def csv_to_geojson(csv_path: Path):
    try:
        df = pd.read_csv(csv_path)

        if "X" not in df.columns or "Y" not in df.columns:
            raise ValueError("CSV missing X or Y columns")

        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df["X"], df["Y"]),
            crs=CSV_CRS
        ).to_crs(MAP_CRS)

        return gdf.__geo_interface__

    except Exception as e:
        raise RuntimeError(f"{csv_path.name}: {str(e)}")


def geom_to_geojson(geom):
    try:
        shapely_geom = to_shape(geom)
        gdf = gpd.GeoDataFrame(geometry=[shapely_geom], crs=MAP_CRS)
        return gdf.__geo_interface__
    except Exception as e:
        raise RuntimeError(f"Invalid geometry in database: {str(e)}")


def get_owned_project_by_public_id(db: Session, current_user: User, project_id: str) -> Project:
    project_uuid = parse_uuid(project_id, "project id")

    project = (
        db.query(Project)
        .filter(
            Project.public_id == project_uuid,
            Project.user_id == current_user.id
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return project


def validate_csv_upload(filename: str) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_DATASET_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {filename}"
        )


# -------------------------------------------------------
# CREATE PROJECT
# -------------------------------------------------------

@router.post("/")
async def create_project(
    project_name: str = Form(...),
    aoi_file: List[UploadFile] = File(...),
    extra_files: List[UploadFile] = File(default=[]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    temp_project_path = None
    final_project_path = None

    if not project_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project name is required"
        )

    if not aoi_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AOI files required"
        )

    # sanitize names first
    sanitized_aoi = []
    for upload in aoi_file:
        safe_name = sanitize_filename(upload.filename)
        sanitized_aoi.append((upload, safe_name))

    uploaded_ext = {Path(name).suffix.lower() for _, name in sanitized_aoi}
    if not REQUIRED_SHP_EXTENSIONS.issubset(uploaded_ext):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shapefile must include .shp, .dbf and .shx"
        )

    shp_files = [name for _, name in sanitized_aoi if name.lower().endswith(".shp")]
    if len(shp_files) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exactly one .shp file is required"
        )

    try:
        # temp folder for validation
        temp_project_path = Path(tempfile.mkdtemp(prefix="project_upload_"))
        temp_area_path = temp_project_path / "area"
        temp_dataset_path = temp_project_path / "datasets"

        ensure_dir(temp_area_path)
        ensure_dir(temp_dataset_path)

        # save AOI temp
        for upload, safe_name in sanitized_aoi:
            await save_upload_file(upload, temp_area_path / safe_name)

        shp_name = shp_files[0]
        shp_path = temp_area_path / shp_name

        try:
            gdf = gpd.read_file(shp_path)
            if gdf.empty:
                raise ValueError("Empty shapefile")
            gdf = gdf.to_crs(MAP_CRS)
            geom_union = gdf.geometry.union_all()
            geom_2d = force_2d(geom_union)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid shapefile: {str(e)}"
            )

        # create project in DB first
        project = Project(
            name=project_name.strip(),
            user_id=current_user.id,
            geom=geom_2d.wkt
        )

        db.add(project)
        db.flush()
        db.refresh(project)

        final_project_path = get_project_path(
            current_user.public_id,
            project.public_id
        )

        final_area_path = get_area_folder(current_user.public_id, project.public_id)
        final_dataset_path = get_dataset_folder(current_user.public_id, project.public_id)

        ensure_dir(final_area_path)
        ensure_dir(final_dataset_path)

        # move AOI from temp to final
        for file_name in os.listdir(temp_area_path):
            shutil.move(
                str(temp_area_path / file_name),
                str(final_area_path / file_name)
            )

        # validate and save extras
        created_files = []
        for upload in extra_files:
            safe_name = sanitize_filename(upload.filename)
            validate_csv_upload(safe_name)

            file_path = safe_join(final_dataset_path, safe_name)
            await save_upload_file(upload, file_path)

            try:
                # validate CSV before insert
                csv_to_geojson(file_path)
            except RuntimeError as e:
                if file_path.exists():
                    file_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid dataset file: {str(e)}"
                )

            dataset = Dataset(
                name=safe_name,
                file_path=str(file_path),
                file_type="csv",
                project_id=project.id
            )
            db.add(dataset)
            created_files.append(file_path)

        db.commit()
        db.refresh(project)

        return {
            "status": "success",
            "project_id": str(project.public_id)
        }

    except HTTPException:
        db.rollback()
        if final_project_path and final_project_path.exists():
            shutil.rmtree(final_project_path, ignore_errors=True)
        raise
    except SQLAlchemyError as e:
        db.rollback()
        if final_project_path and final_project_path.exists():
            shutil.rmtree(final_project_path, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while creating project"
        ) from e
    except Exception as e:
        db.rollback()
        if final_project_path and final_project_path.exists():
            shutil.rmtree(final_project_path, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error while creating project: {str(e)}"
        ) from e
    finally:
        if temp_project_path and temp_project_path.exists():
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
                {
                    "public_id": str(p.public_id),
                    "name": p.name
                }
                for p in projects
            ]
        }
    }


# -------------------------------------------------------
# GET PROJECT DATA
# -------------------------------------------------------

@router.get("/{project_id}")
def get_project_data(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_owned_project_by_public_id(db, current_user, project_id)

    layers = []
    errors = []

    try:
        aoi_geojson = geom_to_geojson(project.geom)
        layers.append({
            "name": "AOI",
            "public_id": f"aoi-{project.public_id}",
            "type": "polygon",
            "source": "aoi",
            "geojson": aoi_geojson,
            "created_at": None
        })
    except RuntimeError as e:
        errors.append(str(e))

    for dataset in project.datasets:
        try:
            if dataset.file_type == "csv":
                file_path = Path(dataset.file_path)

                if not file_path.exists():
                    errors.append(f"Missing file on disk: {dataset.name}")
                    continue

                geojson = csv_to_geojson(file_path)
                layers.append({
                    "name": dataset.name,
                    "public_id": str(dataset.public_id),
                    "meta": dataset.meta,
                    "source": "csv",
                    "type": "point",
                    "geojson": geojson,
                    "created_at": dataset.created_at
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
# ADD EXTRA FILES
# -------------------------------------------------------

@router.post("/{project_id}/extras")
async def add_extra_files(
    project_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_owned_project_by_public_id(db, current_user, project_id)
    dataset_path = get_dataset_folder(current_user.public_id, project.public_id)
    ensure_dir(dataset_path)

    saved_files = []
    created_disk_files = []

    try:
        for upload in files:
            safe_name = sanitize_filename(upload.filename)
            validate_csv_upload(safe_name)

            file_path = safe_join(dataset_path, safe_name)
            await save_upload_file(upload, file_path)
            created_disk_files.append(file_path)

            try:
                geojson = csv_to_geojson(file_path)
            except RuntimeError as e:
                file_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File unreadable: {str(e)}"
                )

            dataset = Dataset(
                name=safe_name,
                file_path=str(file_path),
                file_type="csv",
                project_id=project.id
            )
            db.add(dataset)
            db.flush()
            db.refresh(dataset)

            saved_files.append({
                "id": dataset.id,
                "public_id": str(dataset.public_id),
                "name": safe_name,
                "source": "csv",
                "type": "point",
                "geojson": geojson
            })

        db.commit()

        return {
            "status": "success",
            "data": saved_files
        }

    except HTTPException:
        db.rollback()
        # remove files written in this request
        for path in created_disk_files:
            path.unlink(missing_ok=True)
        raise
    except SQLAlchemyError as e:
        db.rollback()
        for path in created_disk_files:
            path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while adding files"
        ) from e
    except Exception as e:
        db.rollback()
        for path in created_disk_files:
            path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error while adding files: {str(e)}"
        ) from e


# -------------------------------------------------------
# ADD DATASETS
# -------------------------------------------------------

@router.post("/{project_id}/datasets")
async def add_files_to_project(
    project_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_owned_project_by_public_id(db, current_user, project_id)
    dataset_path = get_dataset_folder(current_user.public_id, project.public_id)
    ensure_dir(dataset_path)

    results = []
    created_disk_files = []

    try:
        for upload in files:
            safe_name = sanitize_filename(upload.filename)
            validate_csv_upload(safe_name)

            file_path = safe_join(dataset_path, safe_name)
            await save_upload_file(upload, file_path)
            created_disk_files.append(file_path)

            try:
                geojson = csv_to_geojson(file_path)
            except RuntimeError as e:
                file_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid CSV: {str(e)}"
                )

            dataset = Dataset(
                name=safe_name,
                file_path=str(file_path),
                file_type="csv",
                project_id=project.id
            )
            db.add(dataset)
            db.flush()
            db.refresh(dataset)

            results.append({
                "public_id": str(dataset.public_id),
                "name": safe_name,
                "source": "csv",
                "type": "point",
                "geojson": geojson
            })

        db.commit()

        return {
            "status": "success",
            "data": results
        }

    except HTTPException:
        db.rollback()
        for path in created_disk_files:
            path.unlink(missing_ok=True)
        raise
    except SQLAlchemyError as e:
        db.rollback()
        for path in created_disk_files:
            path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while adding datasets"
        ) from e
    except Exception as e:
        db.rollback()
        for path in created_disk_files:
            path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error while adding datasets: {str(e)}"
        ) from e


# -------------------------------------------------------
# DELETE DATASET
# -------------------------------------------------------

@router.delete("/datasets/{public_id}")
def delete_file_from_project(
    public_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dataset_uuid = parse_uuid(public_id, "dataset id")

    dataset = (
        db.query(Dataset)
        .filter(Dataset.public_id == dataset_uuid)
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    project = (
        db.query(Project)
        .filter(
            Project.id == dataset.project_id,
            Project.user_id == current_user.id
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    file_path = Path(dataset.file_path) if dataset.file_path else None

    try:
        # remove DB record first
        db.delete(dataset)
        db.commit()

        # then try to remove disk file
        if file_path and file_path.exists():
            file_path.unlink()

        return {"status": "deleted"}

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while deleting dataset"
        ) from e
    except Exception as e:
        # DB already committed; inform partial cleanup issue
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dataset deleted from database, but file cleanup failed: {str(e)}"
        ) from e


# -------------------------------------------------------
# DELETE PROJECT
# -------------------------------------------------------

@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_owned_project_by_public_id(db, current_user, project_id)
    project_path = get_project_path(current_user.public_id, project.public_id)

    try:
        # delete child datasets explicitly to avoid depending on ORM cascade
        datasets = (
            db.query(Dataset)
            .filter(Dataset.project_id == project.id)
            .all()
        )

        for dataset in datasets:
            db.delete(dataset)

        db.delete(project)
        db.commit()

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while deleting project"
        ) from e

    # filesystem cleanup after DB commit
    try:
        if project_path.exists():
            shutil.rmtree(project_path, ignore_errors=False)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Project deleted from database, but folder cleanup failed: {str(e)}"
        ) from e

    return {"status": "deleted"}