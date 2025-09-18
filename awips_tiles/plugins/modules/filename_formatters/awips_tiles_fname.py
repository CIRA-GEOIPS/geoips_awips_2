# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Filename formatter for full-day text windspeed products."""

# TODO: Remove the following import before pushing
from ipdb import set_trace as shell

import logging

from os.path import join as pathjoin

from geoips.filenames.base_paths import PATHS as GPATHS
from datetime import datetime, timezone

LOG = logging.getLogger(__name__)

interface = "filename_formatters"
family = "xarray_area_product_to_filename"
name = "awips_tiles_fname"

SOURCE_NAME_MAPPING = {
    "abi": "ABI",
    "ahi": "HFD",
    "fci": "MFD",
    "seviri": "MFD"
}

PLATFORM_NAME_MAPPING = {
    "goes-17": "WFD",
    "goes-16": "EFD",
    "himawari-8": "EFD"
}


def call(
    xarray_obj,
    area_def,
    product_name,
    output_type=".nc",
    basedir=pathjoin(GPATHS["GEOIPS_OUTDIRS"]),
    extra_field=None,
):
    """Create Filenames for AWIPS Tiles.

    Parameters
    ----------
    xarray_obj : xarray.Dataset
    area_def : AreaDefinition
    product_name : str
    output_type : str
    basedir : str
    extra_field : str

    Returns
    -------
    str
    """
    platform = PLATFORM_NAME_MAPPING[xarray_obj.platform_name]
    source = SOURCE_NAME_MAPPING[xarray_obj.source_name]
    product = product_name.upper()

    shell()
    return assemble_awips_tiles_fname(
        basedir=basedir,
        source_name=source,
        platform_name=platform,
        product_name=product,
        start_datetime=xarray_obj.start_datetime,
        dt_format="%Y%j%H%M%S",
        extension=output_type,
        creation_time=datetime.now(timezone.utc),
    )


def assemble_awips_tiles_fname(
    basedir,
    source_name,
    platform_name,
    product_name,
    start_datetime,
    dt_format="%Y%m%d.%H%M",
    extension=".nc",
    creation_time=datetime.now(timezone.utc),
):
    """Produce output product path using product / sensor specifications.

    Parameters
    ----------
    basedir : str
         base directory
    source_name : str
        Name of source (sensor)
    platform_name : str
        Name of platform (satellite)
    product_name : str
        Name of product
    start_datetime : datetime.datetime
        Start time of data used to generate product
    dt_format : str, default="%Y%m%d.%H%M"
        Format used to display start_datetime within filename
    extension : str, default=".nc"
        File extension, specifying type.
    creation_time : datetime.datetime, default=None
        Include given creation_time of file in filename
        If None, do not include creation time.

    Returns
    -------
    str
        full path of output filename of the format:
          <basedir>/OR_<sensor_name>_<data_provider>_<platform_name>_
          surface_winds_<YYYYMMDD_HHMM>
    """
    fname = "-".join(
        [
            source_name,
            product_name,
            "T<tilenum>"
        ]
    )

    fname = "_".join(
        [
            "OR",
            fname,
            platform_name,
            f"s{start_datetime.strftime(dt_format)}",
            f"c{creation_time.strftime(dt_format)}"
        ]
    )

    if extension is not None:
        fname = fname + extension

    return pathjoin(basedir, fname)
