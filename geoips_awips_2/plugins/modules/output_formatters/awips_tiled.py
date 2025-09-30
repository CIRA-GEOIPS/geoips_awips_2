# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""Routines for writing SMAP or SMOS windspeed data in AWIPS2 compatible format."""
import logging
from pathlib import Path
import xarray as xr
import numpy as np
from geoips.filenames.base_paths import PATHS as GPATHS
from datetime import datetime, timezone

# TODO: Remove the following import before pushing
from ipdb import set_trace as shell

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "xrdict_area_product_outfnames_to_outlist"
name = "awips_tiled"


def call(
    xarray_dict,
    area_def,
    product_name,
    output_fnames,
    working_directory=GPATHS["GEOIPS_OUTDIRS"],
):
    """Write AWIPS2 compatible NetCDF files from SMAP or SMOS windspeed data.

    Parameters
    ----------
    xarray_dict : xr.Dataset
        Input dataset with geolocation information.
    area_def : matplotlib.area_definition
        Area definition (currently unused, placeholder for compatibility).
    product_name : str
        The variable name in the dataset to split.
    output_fnames : list of str
        A list containing a filename template with "tilenum".
        Example: ["OR_ABI-L3-PRVIS-T{tilenum}_WFD_s1999364245959_c1999364245959.nc"]
    working_directory : str
        Directory to write output files (default: GPATHS["GEOIPS_OUTDIRS"]).

    Returns
    -------
    List[str]
        Paths of written NetCDF files
    """
    shell()
    if len(output_fnames) != 1:
        raise ValueError("output_fnames must be a 1-length list containing 'tilenum'")

    fname_template = output_fnames[0]
    if "tilenum" not in fname_template:
        raise ValueError("The output filename template must contain 'tilenum'")

    working_dir = Path(working_directory)
    working_dir.mkdir(parents=True, exist_ok=True)

    # Generate tiles
    tiles = split_dataset(xarray_dict, product_name)

    written_files = []
    for idx, tile in enumerate(tiles, start=1):
        tilenum_str = f"{idx:03d}"  # zero-padded index
        fname = fname_template.format(tilenum=tilenum_str)
        fpath = working_dir / fname

        # Write NetCDF
        tile.to_netcdf(fpath)

        written_files.append(str(fpath))

    return written_files


def split_dataset(
    ds,
    product_name,
    ncols=8,
    nrows=10,
    lat_name="latitude",
    lon_name="longitude",
):
    """Split an xarray Dataset variable into tiles.

    Parameters
    ----------
    ds : xr.Dataset
        The input dataset with latitude/longitude coordinates.
    product_name : str
        The variable name in the dataset to split.
    ncols : int
        Number of columns (splits along longitude).
    nrows : int
        Number of rows (splits along latitude).
    lat_name : str
        Name of latitude coordinate in the dataset (default: 'latitude').
    lon_name : str
        Name of longitude coordinate in the dataset (default: 'longitude').

    Returns
    -------
    list of xr.Dataset
        List of smaller datasets (ncols * nrows).
    """

    # Helper: sanitize ONLY variable attrs (datetime -> str)
    def _sanitize_var_attrs(attrs: dict) -> dict:
        clean = {}
        for k, v in (attrs or {}).items():
            if isinstance(v, (datetime.datetime, datetime.date)):
                clean[k] = v.isoformat()
            else:
                clean[k] = v
        return clean

    da = ds[product_name]
    # Identify data dims (assume last two are spatial)
    y_dim, x_dim = da.dims[-2], da.dims[-1]
    ny, nx = da.sizes[y_dim], da.sizes[x_dim]

    # Robust tile edges (covers remainders in last tiles)
    y_edges = np.linspace(0, ny, nrows + 1, dtype=int)
    x_edges = np.linspace(0, nx, ncols + 1, dtype=int)

    tiles = []
    for i in range(nrows):
        for j in range(ncols):
            y_start, y_end = y_edges[i], y_edges[i + 1]
            x_start, x_end = x_edges[j], x_edges[j + 1]

            # Slice main product
            sub_da = da.isel(
                {y_dim: slice(y_start, y_end), x_dim: slice(x_start, x_end)}
            )

            # Extract 1D coords from 2D lat/lon:
            #   y: take a column (first x) across rows
            #   x: take a row (first y) across cols
            lat2d = ds[lat_name].isel(
                {y_dim: slice(y_start, y_end), x_dim: slice(x_start, x_end)}
            )
            lon2d = ds[lon_name].isel(
                {y_dim: slice(y_start, y_end), x_dim: slice(x_start, x_end)}
            )
            y_1d = lat2d.isel({x_dim: 0}).values  # shape (tile_rows,)
            x_1d = lon2d.isel({y_dim: 0}).values  # shape (tile_cols,)

            # Build tile dataset: product variable uses ('y','x'); coords are 1D
            var_attrs = _sanitize_var_attrs(sub_da.attrs)
            tile = xr.Dataset(
                data_vars={
                    product_name: (("y", "x"), sub_da.values, var_attrs),
                },
                coords={
                    "y": ("y", y_1d, {"long_name": "latitude"}),
                    "x": ("x", x_1d, {"long_name": "longitude"}),
                },
            )

            # Global attrs via your Fortran-matching builder:
            # NOTE: pass pixel offsets (y_start, x_start), not tile indices (i, j)
            tile.attrs = _build_tile_attrs(
                ds,
                product_name,
                y_start,  # tile_row_offset (pixels)
                x_start,  # tile_column_offset (pixels)
                y_1d,  # tile_lat (1D)
                x_1d,  # tile_lon (1D)
            )

            # Add fixedgrid_projection scalar variable
            tile["fixedgrid_projection"] = xr.DataArray(
                0,
                attrs={
                    "grid_mapping_name": "geostationary",
                    "latitude_of_projection_origin": [0],
                    "longitude_of_projection_origin": [-137],
                    "semi_major_axis": [6378137],
                    "semi_minor_axis": [6356752.31414],
                    "perspective_point_height": [35786023],
                    "sweep_angle_axis": "x",
                },
            )

            tiles.append(tile)

    return tiles


def _build_tile_attrs(
    ds, product_name, tile_row_offset, tile_col_offset, tile_lat, tile_lon
):
    """Construct attributes matching Fortran make_GEGEOC_ECFG_tiles.f90 output.

    Parameters
    ----------
    ds : xarray.Dataset
        The full source dataset (used to derive start time and metadata).
    product_name : str
        The name of the product (e.g., "GeoColor").
    tile_row_offset : int
        Starting pixel row index of the tile.
    tile_col_offset : int
        Starting pixel column index of the tile.
    tile_lat : np.ndarray
        Latitude array for this tile (used for center computation).
    tile_lon : np.ndarray
        Longitude array for this tile.

    Returns
    -------
    dict
        Dictionary of NetCDF global attributes.
    """
    # --- Temporal attributes ---
    startdatetime = getattr(ds, "start_datetime", datetime.now(timezone.utc))
    start_str = startdatetime.strftime("%Y%m%d_%H%M")

    # --- Compute geographic centers ---
    lat_center = float(tile_lat.mean())
    lon_center = float(tile_lon.mean())

    # --- Build attributes dictionary ---
    attrs = {
        # === General metadata ===
        "title": "GeoColor AWIPS tiles for ECONUS (GOES-16)",
        "ICD_version": "ICD-GEO-16-001",
        "Conventions": "CF-1.6",
        "product_name": "GEGEOC-010-B12-M3C02",  # Typically determined by band (can be parameterized)
        "satellite_id": "GEOCOLR",
        "projection": "Fixed Grid",
        # === Channel and band metadata ===
        "channel_id": 2,
        "central_wavelength": 0.64,
        "abi_mode": 3,
        # === Source and production info ===
        "source_scene": "CONUS",
        "production_location": "RAMMB",
        "production_site": "RAMMB",
        "institution": "NOAA/NESDIS",
        "project": "GOES-R Series",
        "bit_depth": 12,
        # === Temporal coverage ===
        "start_date_time": start_str,
        "time_coverage_start": start_str,
        "time_coverage_end": start_str,
        # === Tile geometry ===
        "product_center_latitude": lat_center,
        "product_center_longitude": lon_center,
        "tile_center_latitude": lat_center,
        "tile_center_longitude": lon_center,
        "tile_row_offset": int(tile_row_offset),
        "tile_column_offset": int(tile_col_offset),
        "product_rows": 1024,
        "product_columns": 1024,
        "product_tile_width": 1024,
        "product_tile_height": 1024,
        "number_product_tiles": 15,
        # === Spatial resolution ===
        "pixel_x_size": 2.0,
        "pixel_y_size": 2.0,
        "source_spatial_resolution": 1.0,
        "request_spatial_resolution": 1.0,
        # === Temporal periodicity ===
        "periodicity": 5.0,
    }

    return attrs
