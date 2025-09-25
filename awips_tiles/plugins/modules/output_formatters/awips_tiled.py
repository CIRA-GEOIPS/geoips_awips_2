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
from datetime import datetime, timedelta
import numpy as np
import satpy.scene
import xarray as xr
from geoips.xarray_utils.time import (
    get_min_from_xarray_time,
    get_max_from_xarray_time,
    get_datetime_from_datetime64,
)
from geoips.filenames.base_paths import PATHS as geoips_variables
import satpy

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
    working_directory=geoips_variables["GEOIPS_OUTDIRS"],
):
    """Write AWIPS2 compatible NetCDF files from SMAP or SMOS windspeed data.

    Parameters
    ----------
    xarray_dict : Dict[str, xarray.Dataset]
    working_directory : str

    Returns
    -------
    List[str]
    """
    working_dir = Path(working_directory)
    utc_date_format = "%Y-%m-%d %H:%M:%S UTC"
    success_outputs = []

    ## DEBUGGING
    shell()

    scn = satpy.Scene()
    scn["xyz"] = xarray_dict["xyz"]


def split_dataset(
    ds,
    product_name,
    ncols=8,
    nrows=10,
    lat_name="latitude",
    lon_name="longitude",
):
    """
    Split an xarray Dataset variable into smaller datasets,
    and add latitude/longitude slices as 1D x and y variables.
    A fixedgrid_projection variable is also added.

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
    da = ds[product_name]

    ny, nx = da.sizes[lat_name], da.sizes[lon_name]

    # Determine chunk sizes
    x_chunk = nx // ncols
    y_chunk = ny // nrows

    tiles = []

    for i in range(nrows):
        for j in range(ncols):
            y_start, y_end = i * y_chunk, (i + 1) * y_chunk
            x_start, x_end = j * x_chunk, (j + 1) * x_chunk

            sub_da = da.isel(
                **{
                    lat_name: slice(y_start, y_end),
                    lon_name: slice(x_start, x_end),
                }
            )

            sub_lat = ds[lat_name].isel({lat_name: slice(y_start, y_end)})
            sub_lon = ds[lon_name].isel({lon_name: slice(x_start, x_end)})

            sub_ds = sub_da.to_dataset(name=product_name)

            sub_ds["y"] = xr.DataArray(sub_lat, dims=[lat_name])
            sub_ds["x"] = xr.DataArray(sub_lon, dims=[lon_name])

            sub_ds["fixedgrid_projection"] = xr.DataArray(
                0,  # scalar
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

            # Copy attributes
            sub_ds.attrs = ds.attrs.copy()
            sub_ds[product_name].attrs = da.attrs.copy()
            sub_ds["x"].attrs = {"long_name": "longitude"}
            sub_ds["y"].attrs = {"long_name": "latitude"}

            tiles.append(sub_ds)

    return tiles
