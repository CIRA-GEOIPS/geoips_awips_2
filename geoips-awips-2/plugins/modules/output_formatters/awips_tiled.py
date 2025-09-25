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
from geoips.filenames.base_paths import PATHS as GPATHS

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
    da = ds[product_name]

    ny = ds.dims['dim_0']
    nx = ds.dims['dim_1']

    # Determine chunk sizes
    x_chunk = nx // ncols
    y_chunk = ny // nrows

    tiles = []

    for i in range(nrows):
        for j in range(ncols):
            y_start, y_end = i * y_chunk, (i + 1) * y_chunk
            x_start, x_end = j * x_chunk, (j + 1) * x_chunk

            # Slice the main product
            sub_da = da.isel(
                **{
                    lat_name: slice(y_start, y_end),
                    lon_name: slice(x_start, x_end),
                }
            )

            # Slice latitude and longitude as 1D arrays
            sub_lat = ds[lat_name].isel({lat_name: slice(y_start, y_end)})
            sub_lon = ds[lon_name].isel({lon_name: slice(x_start, x_end)})

            # Create dataset with product, using x and y as coordinates
            sub_ds = xr.Dataset(
                {
                    product_name: (
                        ("y", "x"),
                        sub_da.data,
                        sub_da.attrs,
                    )
                },
                coords={
                    "y": ("y", sub_lat.data, {"long_name": "latitude"}),
                    "x": ("x", sub_lon.data, {"long_name": "longitude"}),
                },
                attrs=ds.attrs.copy(),
            )

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

            tiles.append(sub_ds)

    return tiles
