# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Filename formatter for full-day text windspeed products."""
import logging

from os.path import join as pathjoin

from geoips.filenames.base_paths import PATHS as gpaths

LOG = logging.getLogger(__name__)

# TODO: Remove the following import before pushing
from ipdb import set_trace as shell

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
    "himawari-8": "EFD",
    "GK-2A":
}


def call(
    xarray_obj,
    area_def,
    product_name,
    output_type=".png",
    basedir=pathjoin(gpaths["ANNOTATED_IMAGERY_PATH"]),
    extra_field=None,
):
    """Create Filenames for AWIPS Tiles."""
    if xarray_obj.attrs['source_name'] == "abi":
        None
    elif xarray_obj.attrs['source_name'] == "ahi":

    shell()
    # return assemble_windspeeds_text_full_fname(
    #     basedir=basedir,
    #     source_name=xarray_obj.source_name,
    #     platform_name=xarray_obj.platform_name,
    #     data_provider=xarray_obj.data_provider,
    #     product_datetime=xarray_obj.start_datetime,
    #     dt_format="%Y%m%d",
    #     extension=extension,
    #     creation_time=None,
    # )
