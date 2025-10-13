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

"""Routines for writing AWIPS2 tiles."""
import logging
from pathlib import Path
import xarray as xr
import numpy as np
from geoips.filenames.base_paths import PATHS as GPATHS
from datetime import datetime, date, timezone

# TODO: Remove the following debug statement
from ipdb import set_trace as shell

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "xrdict_area_product_outfnames_to_outlist"
name = "awips_tiled"

SATELLITE_CONSTANTS = {
    "goes-18": {
        "longitude": -137,
        "altitude": 3.5786023e7,
    },
    "goes-17": {
        "longitude": -104.7,
        "altitude": 3.5786023e7,
    },
    "goes-16": {
        "longitude": -75.2,
        "altitude": 3.5786023e7,
    },
    "goes-19": {
        "longitude": -75.2,
        "altitude": 3.5786023e7,
    },
    "himawari-8": {
        "longitude": 140.7,
        "altitude": 3.5786023e7,
    },
    "himawari-9": {
        "longitude": 140.7,
        "altitude": 3.5786023e7,
    },
}

# Shared int16 fill for all packed variables
INT16_FILL = np.int16(-999)


def call(
    xarray_dict,
    area_def,
    product_name,
    output_fnames,
    fill_value=INT16_FILL,
    title=None,
    ncols=None,
    nrows=None,
):
    """Write AWIPS2 compatible tiled data as NetCDF files.

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
        e.g. ["OR_ABI-L3-PRVIS-T{tilenum}_WFD_s9999999_c9999999.nc"]
    fill_value : int, optional
        The value we want to set instead of NaN in the final product.
        Default: -999
    title : str, optional
        Title for global attributes. If None, it will be generated.
        e.g. "<product_name> AWIPS tiles for <sector_name> (<platform_name>)"

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

    # Generate tiles
    tiles = split_dataset(
        xarray_dict,
        product_name,
        title=title,
    )

    written_files = []
    for idx, tile in enumerate(tiles, start=1):
        tilenum_str = f"{idx:03d}"  # zero-padded index
        fname = fname_template.format(tilenum=tilenum_str)
        fpath = Path(fname)

        # Write NetCDF
        enc = build_tile_encodings(tile, product_name, fill_value=fill_value)
        tile.to_netcdf(fpath, engine="netcdf4", encoding=enc)

        written_files.append(str(fpath))

    return written_files


def _sanitize_attrs(attrs: dict) -> dict:
    """Sanitize dataset attributes."""
    clean = {}
    for k, v in (attrs or {}).items():
        if isinstance(v, (datetime, date)):
            clean[k] = v.isoformat()
        else:
            clean[k] = v
    return clean


def split_dataset(
    ds,
    product_name,
    ncols=8,
    nrows=10,
    lat_name="latitude",
    lon_name="longitude",
    title=None,
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
    title : str, optional
        Title for global attributes. If None, it will be generated.

    Returns
    -------
    list of xr.Dataset
        List of smaller datasets (ncols * nrows).
    """
    da = ds[product_name]
    sat_consts = SATELLITE_CONSTANTS.get(ds.platform_name)
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
            var_attrs = _sanitize_attrs(sub_da.attrs)
            var_attrs["coordinates"] = "y x"
            var_attrs["grid_mapping"] = "fixedgrid_projection"
            var_attrs["units"] = "%"  # This should change based off metadata
            var_attrs["_Unsigned"] = "true"  # Possibly incorrect

            tile = xr.Dataset(
                data_vars={
                    product_name: (("y", "x"), sub_da.values, var_attrs),
                },
                coords={
                    "y": ("y", y_1d, {"long_name": "latitude"}),
                    "x": ("x", x_1d, {"long_name": "longitude"}),
                },
            )

            tile["x"].attrs["axis"] = "X"
            tile["x"].attrs["standard_name"] = "projection_x_coordinate"
            tile["x"].attrs["units"] = "m"  # the original data was in 'rad' though
            tile["x"].attrs["_Unsigned"] = "true"

            tile["y"].attrs["axis"] = "Y"
            tile["y"].attrs["standard_name"] = "projection_y_coordinate"
            tile["y"].attrs["units"] = "m"  # the original data was in 'rad' though
            tile["y"].attrs["_Unsigned"] = "true"

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
                    # satellite sub-point THE ONLY VARYING VALUE
                    #   probably good to get this dynamically
                    #   or we could just create a case/switch statement
                    #   google "nadir longitude of geostationary satellite {name}"
                    "longitude_of_projection_origin": [sat_consts["longitude"]],
                    # -137 is GOES-West
                    # should be varible based on the satellite metadata
                    "semi_major_axis": [6378137],
                    "semi_minor_axis": [6356752.31414],
                    # radius of the earth in short/long directions
                    "perspective_point_height": [35786023],
                    # the actual orbital distance for geostationary satellite
                    "sweep_angle_axis": "x",
                    # direction that the satellite scans.
                    # Ask deb if this is always true
                },
            )

            tiles.append(tile)

    return tiles


def _build_tile_attrs(
    ds,
    product_name,
    tile_row_offset,
    tile_col_offset,
    tile_lat,
    tile_lon,
    ncols=8,
    nrows=10,
    resolution=0.5,
    datetime_pattern="%Y-%m-%dT%H:%M:%S.%fZ",
    title=None,
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
    ncols : int, default=8
        Number of tiles along the x-direction in the full product.
    nrows : int, default=10
        Number of tiles along the y-direction in the full product.
    resolution : float, default=0.5
        Kilometers per pixel.
    datetime_pattern : str, default="YYYY-mm-ddTHH:MM:SS.fZ"
        Display pattern used for times.
    title : str, optional
        Title for global attributes. If None, a default will be generated.

    Returns
    -------
    dict
        Dictionary of NetCDF global attributes.
    """
    # Pull the source variable and full product shape. If it's not there, error.
    if product_name not in ds:
        raise KeyError(f"Expected variable '{product_name}' in dataset.")
    var = ds[product_name]
    if var.ndim < 2:
        raise ValueError(f"Variable '{product_name}' must be at least 2D (got {var.ndim}D).")
    y_dim, x_dim = var.dims[-2], var.dims[-1]
    product_rows = int(var.sizes[y_dim])
    product_columns = int(var.sizes[x_dim])

    # Validate required dataset fields; fail fast to catch upstream issues.
    if not hasattr(ds, "platform_name"):
        raise AttributeError("Dataset is missing 'platform_name'.")
    platform_name = ds.platform_name

    # Satellite constants are mandatory
    platform_key = str(platform_name).lower()
    if platform_key not in SATELLITE_CONSTANTS:
        raise KeyError(f"No SATELLITE_CONSTANTS entry for platform '{platform_name}'.")
    sat_consts = SATELLITE_CONSTANTS[platform_key]
    if "longitude" not in sat_consts or "altitude" not in sat_consts:
        raise KeyError(f"SATELLITE_CONSTANTS for '{platform_name}'"
                       + "must include 'longitude' and 'altitude'.")
    subpoint_lon = float(sat_consts["longitude"])
    sat_alt_m = float(sat_consts["altitude"])

    # Prefer area_id; if it doesn't exist, error.
    area_id = getattr(ds, "area_id", None)
    if area_id is None:
        raise AttributeError("Dataset is missing 'area_id'.")
    source_scene = str(area_id)

    if not hasattr(ds, "start_datetime"):
        raise AttributeError("Dataset is missing 'start_datetime'.")
    start_dt = ds.start_datetime
    if not isinstance(start_dt, datetime):
        raise TypeError("'start_datetime' must be a datetime.datetime object.")
    # Always write UTC and format with the provided pattern.
    start_dt_utc = start_dt.astimezone(timezone.utc)
    start_str = start_dt_utc.strftime(datetime_pattern)

    # creation_time is 'now' in UTC with the same pattern.
    creation_time = datetime.now(timezone.utc).strftime(datetime_pattern)

    if title is None:
        title = f"{product_name} AWIPS tiles for {source_scene} ({platform_name})"
    title = str(title)

    # Compute tile centers from the 1D coordinate vectors.
    if tile_lat.size == 0 or tile_lon.size == 0:
        raise ValueError("tile_lat and tile_lon must be non-empty 1D arrays.")
    tile_center_latitude = float(np.nanmean(tile_lat))
    tile_center_longitude = float(np.nanmean(tile_lon))

    # Product center equals satellite sub-point by design.
    product_center_latitude = 0.0
    product_center_longitude = subpoint_lon

    # Assemble attributes exactly as requested.
    attrs = {
        # === Dynamic ===
        "creation_time": creation_time,
        "number_product_tiles": int(ncols * nrows),
        "pixel_x_size": float(resolution),
        "pixel_y_size": float(resolution),
        "product_center_latitude": product_center_latitude,
        "product_center_longitude": product_center_longitude,
        "product_columns": product_columns,
        "product_name": product_name.upper(),
        "product_rows": product_rows,
        "product_tile_height": int(tile_lat.size),
        "product_tile_width": int(tile_lon.size),
        "satellite_altitude": sat_alt_m,
        "satellite_id": str(platform_name),
        "satellite_latitude": product_center_latitude,
        "satellite_longitude": product_center_longitude,
        "source_scene": source_scene,
        "start_date_time": start_str,
        "tile_center_latitude": tile_center_latitude,
        "tile_center_longitude": tile_center_longitude,
        "tile_column_offset": int(tile_col_offset),
        "tile_row_offset": int(tile_row_offset),
        "time_coverage_end": start_str,
        "time_coverage_start": start_str,
        "title": title,

        # === Static ===
        "bit_depth": 16,
        "channel_id": 17,
        "Conventions": "CF-1.7",
        "central_wavelength": 0.64,
        "creator": "GeoIPS",
        "production_location": "CIRA",
        "projection": "fixedgrid_projection",
    }

    # Only ABI gets abi_mode
    source_name = getattr(ds, "source_name", None)
    if source_name is None:
        raise AttributeError("Dataset is missing 'source_name' (needed for ABI-only abi_mode).")
    if str(source_name).lower() == "abi":
        attrs["abi_mode"] = 1

    return attrs


def _compute_scale_and_offset(data, codes_max=32767):
    """Compute (scale_factor, add_offset) for packing to int16.

    Parameters
    ----------
    data : np.ndarray
        Input numeric array; only finite values are considered.
    codes_max : int, optional
        Maximum positive code value to map data into (default: 32767).

    Returns
    -------
    tuple of float
        (scale_factor, add_offset) that maps finite data to [0, codes_max].
    """
    finite_mask = np.isfinite(data)
    if not np.any(finite_mask):
        return 1.0, 0.0

    data_min = float(np.nanmin(data[finite_mask]))
    data_max = float(np.nanmax(data[finite_mask]))

    if data_max == data_min:
        return 1.0, data_min

    scale_factor = (data_max - data_min) / float(codes_max)
    if scale_factor == 0.0 or not np.isfinite(scale_factor):
        scale_factor = 1.0

    return scale_factor, data_min


def build_int16_encoding(
    data_array,
    fill_value=INT16_FILL,
    codes_max=32767,
):
    """Build xarray/netCDF encoding for packing a float array to int16.

    Parameters
    ----------
    data_array : xr.DataArray
        Source data to be written; may contain NaNs.
    fill_value : np.int16, optional
        int16 storage value for missing data (default: -999).
    zlib : bool, optional
        Enable zlib compression (default: True).
    complevel : int, optional
        Compression level 0–9 (default: 4).
    codes_max : int, optional
        Maximum positive code value to map data into (default: 32767).

    Returns
    -------
    dict
        Encoding dictionary for use with xarray's to_netcdf().
    """
    scale_factor, add_offset = _compute_scale_and_offset(
        data_array.values, codes_max=codes_max
    )
    return {
        "dtype": "int16",
        "_FillValue": np.int16(fill_value),
        "scale_factor": np.float32(scale_factor),
        "add_offset": np.float32(add_offset),
    }


def build_tile_encodings(
    tile_dataset,
    product_name,
    x_name="x",
    y_name="y",
    fill_value=INT16_FILL,
    codes_max=32767,
):
    """Build combined encodings for product, x, and y variables in a tile.

    Parameters
    ----------
    tile_dataset : xr.Dataset
        Dataset containing the product, x, and y variables.
    product_name : str
        Name of the product variable in the dataset.
    x_name : str, optional
        Name of the x coordinate variable (default: "x").
    y_name : str, optional
        Name of the y coordinate variable (default: "y").
    fill_value : np.int16, optional
        int16 storage value for missing data (default: -999).
    zlib : bool, optional
        Enable zlib compression (default: True).
    complevel : int, optional
        Compression level 0–9 (default: 4).
    codes_max : int, optional
        Maximum positive code value to map data into (default: 32767).

    Returns
    -------
    dict
        Mapping of variable name -> encoding dict suitable for to_netcdf().
    """
    encodings = {}
    encodings[product_name] = build_int16_encoding(
        tile_dataset[product_name],
        fill_value=fill_value,
        codes_max=codes_max,
    )
    encodings[x_name] = build_int16_encoding(
        tile_dataset[x_name],
        fill_value=fill_value,
        codes_max=codes_max,
    )
    encodings[y_name] = build_int16_encoding(
        tile_dataset[y_name],
        fill_value=fill_value,
        codes_max=codes_max,
    )
    return encodings