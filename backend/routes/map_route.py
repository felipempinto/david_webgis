from fastapi import APIRouter, HTTPException
import os
import pandas as pd
import geopandas as gpd

router = APIRouter()

DATASET_PATH = "files"
AOI_SHP_PATH = os.path.join(DATASET_PATH, "AOI_Limit", "AOI_Limit.shp")

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


@router.get("/datasets")
def get_datasets():
    try:
        csv_files = list_csv_files(DATASET_PATH)

        csv_layers = []
        csv_errors = []

        for csv in csv_files:
            path = os.path.join(DATASET_PATH, csv)

            try:
                geojson = csv_to_geojson(path)

                csv_layers.append({
                    "name": csv,
                    "source": "csv",
                    "type": "point",
                    "geojson": geojson
                })

            except RuntimeError as e:
                csv_errors.append(str(e))

        # AOI
        try:
            aoi_geojson = load_aoi_geojson(AOI_SHP_PATH)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))

        return {
            "status": "success",
            "data": {
                "layers": (
                    csv_layers +
                    ([
                        {
                            "name": "AOI_Limit",
                            "source": "shapefile",
                            "type": "aoi",
                            "geojson": aoi_geojson
                        }
                    ] if aoi_geojson else [])
                ),
                "errors": csv_errors
            },
            "error": None
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "data": None,
                "error": {
                    "code": "DATASET_PROCESSING_FAILED",
                    "message": str(e)
                }
            }
        )
