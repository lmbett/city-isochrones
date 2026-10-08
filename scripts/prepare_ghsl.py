"""Build lightweight GHSL boundary files for the isochrone page.

Inputs (data/raw): GHS-UCDB R2024A urban centres and GHS-FUA R2019A functional urban areas.
Output (data/ghsl): cities.js (search index) and one <ID>.js per urban centre
holding its UC polygon and the FUA that contains its centroid. Files are .js
(not .json) so the page works when opened directly from disk.
"""
import json
from pathlib import Path

import geopandas as gpd
import pyogrio

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "ghsl"
UCDB = RAW / "ucdb" / "GHS_UCDB_GLOBE_R2024A.gpkg"
FUA = RAW / "fua" / "GHS_FUA_UCDB2015_GLOBE_R2019A_54009_1K_V1_0.gpkg"
SIMPLIFY_M = 100  # tolerance in Mollweide metres, applied before reprojection


def strip_bom(df):
    return df.rename(columns=lambda c: c.lstrip("﻿"))


def clean(v, default=""):
    return v.lstrip("\ufeff").strip() if isinstance(v, str) and v.strip("\ufeff ") else default


def to_geojson(geom):
    return json.loads(gpd.GeoSeries([geom], crs=4326).to_json())["features"][0]["geometry"]


def round_coords(obj, nd=5):
    if isinstance(obj, dict):
        return {k: round_coords(v, nd) for k, v in obj.items()}
    if isinstance(obj, list):
        return [round_coords(x, nd) for x in obj]
    return round(obj, nd) if isinstance(obj, float) else obj


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    uc = strip_bom(pyogrio.read_dataframe(UCDB, layer="GHS_UCDB_THEME_GENERAL_CHARACTERISTICS_GLOBE_R2024A"))
    cen = pyogrio.read_dataframe(UCDB, layer="UC_centroids", read_geometry=False)
    uc = uc.merge(cen, on="ID_UC_G0")
    fua = pyogrio.read_dataframe(FUA)

    # Centroid "LON/LAT" columns are actually Mollweide metres.
    pts = gpd.GeoDataFrame(uc[["ID_UC_G0"]], geometry=gpd.points_from_xy(uc.GC_UCC_LON_2025, uc.GC_UCC_LAT_2025), crs=fua.crs)
    ll = pts.geometry.to_crs(4326)
    uc["lon"], uc["lat"] = ll.x.values, ll.y.values
    # Match each urban centre to the FUA containing its centroid (FUA uses older UC IDs).
    match = gpd.sjoin(pts, fua[["eFUA_ID", "geometry"]], predicate="within", how="left").drop_duplicates("ID_UC_G0")
    uc = uc.merge(match[["ID_UC_G0", "eFUA_ID"]], on="ID_UC_G0", how="left")

    uc["geometry"] = uc.geometry.make_valid().simplify(SIMPLIFY_M).to_crs(4326).values
    fua["geometry"] = fua.geometry.make_valid().simplify(SIMPLIFY_M).to_crs(4326).values
    fua_by_id = fua.set_index("eFUA_ID")

    index = []
    for r in uc.itertuples():
        uid = int(r.ID_UC_G0)
        rec = {
            "id": uid,
            "name": clean(r.GC_UCN_MAI_2025, f"Urban centre {uid}"),
            "country": clean(r.GC_CNT_GAD_2025),
            "pop": round(float(r.GC_POP_TOT_2025)),
            "area_km2": round(float(r.GC_UCA_KM2_2025), 1),
            "lat": round(float(r.lat), 5),
            "lon": round(float(r.lon), 5),
        }
        data = {**rec, "uc": round_coords(to_geojson(r.geometry)), "fua": None}
        if r.eFUA_ID == r.eFUA_ID and r.eFUA_ID is not None:  # not NaN
            f = fua_by_id.loc[r.eFUA_ID]
            data["fua"] = {
                "name": clean(f.eFUA_name),
                "area_km2": round(float(f.FUA_area), 1),
                "pop2015": round(float(f.FUA_p_2015)),
                "geometry": round_coords(to_geojson(f.geometry)),
            }
        rec["fua"] = data["fua"] is not None
        index.append(rec)
        (OUT / f"{uid}.js").write_text(f"window.ghslLoaded({json.dumps(data, separators=(',', ':'))});\n")

    index.sort(key=lambda d: -d["pop"])
    (OUT / "cities.js").write_text("window.GHSL_CITIES=" + json.dumps(index, separators=(",", ":"), ensure_ascii=False) + ";\n")
    print(f"{len(index)} urban centres, {sum(d['fua'] for d in index)} with FUA")


if __name__ == "__main__":
    main()
