# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Filename formatter for full-day text windspeed products."""

# TODO: Remove the following import before pushing
from ipdb import set_trace as shell

import logging

from pathlib import Path

from geoips.filenames.base_paths import PATHS as GPATHS
from datetime import datetime, timezone

LOG = logging.getLogger(__name__)

interface = "filename_formatters"
family = "xarray_area_product_to_filename"
name = "awips_tiles_fname"

# Existing MAPPINGS remain
SOURCE_NAME_MAPPING = {"abi": "ABI", "ahi": "HFD", "fci": "MFD", "seviri": "MFD"}
PLATFORM_NAME_MAPPING = {"goes-17": "WFD", "goes-16": "EFD", "himawari-8": "EFD"}

# New mapping for GeoColor RGB channels (extendable if needed)
COLOR_MAPPING = {
    "red": "R",
    "green": "G",
    "blue": "B",
    "geocolor_r": "R",
    "geocolor_g": "G",
    "geocolor_b": "B",
}


def call(
    xarray_obj,
    area_def,
    product_name,
    output_type=".nc",
    basedir=Path(GPATHS["GEOIPS_OUTDIRS"]),
    extra_field=None,
):
    """Create Filenames for AWIPS and GeoColor Tiles.

    Detects product type and dispatches to the correct filename assembler.
    """
    product_lower = product_name.lower()
    platform = PLATFORM_NAME_MAPPING.get(xarray_obj.platform_name, "UNK")
    source = SOURCE_NAME_MAPPING.get(xarray_obj.source_name, "UNK")

    if "geocolor" in product_lower:
        # Use Fortran-style GEOC naming
        fname = assemble_geocolor_fname(
            basedir=basedir,
            product_name=product_name,
            start_datetime=xarray_obj.start_datetime,
            color_key=product_lower,  # used for COLOR_MAPPING lookup
        )
    else:
        # Default AWIPS-style filename
        fname = assemble_awips_tiles_fname(
            basedir=basedir,
            source_name=source,
            platform_name=platform,
            product_name=product_name.upper(),
            start_datetime=xarray_obj.start_datetime,
            dt_format="%Y%j%H%M%S",
            extension=output_type,
            creation_time=datetime.now(timezone.utc),
        )

    return fname


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
    """Produce AWIPS output product path."""
    fname = "-".join([source_name, product_name, "T{tilenum}"])
    fname = "_".join(
        [
            "OR",
            fname,
            platform_name,
            f"s{start_datetime.strftime(dt_format)}",
            f"c{creation_time.strftime(dt_format)}",
        ]
    )
    if extension:
        fname += extension

    return str(Path(basedir) / fname)


def assemble_geocolor_fname(
    basedir,
    product_name,
    start_datetime,
    color_key=None,
    extension=".nc",
):
    """Produce GeoColor filenames matching Deb's Fortran code.

    Format:
        RAMMB_A2ECFG_GEOC_<COLOR>_<YYYYMMDD>_<HHMM>_T{tilenum}.nc
    """
    # Determine color code
    color_letter = COLOR_MAPPING.get(color_key, "R")

    # Extract date and time components
    date_str = start_datetime.strftime("%Y%m%d")
    time_str = start_datetime.strftime("%H%M")

    fname = "_".join(
        ["RAMMB_A2ECFG_GEOC", color_letter, date_str, time_str, "T{tilenum}"]
    )

    if extension:
        fname += extension

    return str(Path(basedir) / fname)
