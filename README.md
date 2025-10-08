    # # # This source code is subject to the license referenced at
    # # # https://github.com/NRLMMD-GEOIPS.

Basic GeoIPS Plugin Template
=============================

This template repository contains everything necessary to create a fully
compatible GeoIPS Plugin Package.  Each file within this repository contains
appropriate modification instructions.

To create your own functional plugin for GeoIPS, follow the
[step by step instructions](./docs/source/userguide/template_instructions.rst) for
modifying the template files within this repo.

@ Once this repository has been set up properly, you can remove this "Basic
GeoIPS Plugin Template" section in the README.md, leaving the appropriate
content for your package's README file.


geoips_awips_2 GeoIPS Plugin
==========================

The geoips_awips_2 package is a GeoIPS-compatible plugin, intended to be used within
the GeoIPS ecosystem.  Please see the
[GeoIPS Documentation](https://github.com/NRLMMD-GEOIPS/geoips#readme) for
more information on the GeoIPS plugin architecture and base infrastructure.

Package Overview
-----------------

The geoips_awips_2 plugin provides the capability for

@ Please include a brief description of what capability this package provides.

@ This section should be no more than 1-2 paragraphs, if you have additional
@ information to include, please include in a "docs" subdirectory.

@ Example overview:

@ The template_basic_plugin package provides template files which can be used to create
@ a fully compatible GeoIPS plugin.  This template repository is focused on basic functionality -
@ ie, simple readers, products, output formats, etc.  Additional template repositories will be
@ created for more sophisticated and complicated use cases.

System Requirements
---------------------

* geoips >= 1.14.2
* Test data repos contained in $GEOIPS_TESTDATA_DIR for tests to pass.
* @ Add any additional system requirements, such as gfortran, etc

IF REQUIRED: Install base geoips package
------------------------------------------------------------
SKIP IF YOU HAVE ALREADY INSTALLED BASE GEOIPS ENVIRONMENT

If GeoIPS Base is not yet installed, follow the
[installation instructions](https://github.com/NRLMMD-GEOIPS/geoips#installation)
within the geoips source repo documentation:

Install geoips_awips_2 package
----------------------------
```bash

    # Ensure GeoIPS Python environment is enabled.

    # Clone and install geoips_awips_2
    git clone https://github.com/CIRA-GEOIPS/geoips_awips_2 $GEOIPS_PACKAGES_DIR/geoips_awips_2
    pip install -e $GEOIPS_PACKAGES_DIR/geoips_awips_2

    # Add any additional clone/install/setup steps here
```

Test geoips_awips_2 installation
-----------------------------
```bash

    # Ensure GeoIPS Python environment is enabled.

    # This script will run ALL tests within this package
    $GEOIPS_PACKAGES_DIR/geoips_awips_2/tests/test_all.sh

    # Individual direct test calls, for reference
    $GEOIPS_PACKAGES_DIR/geoips_awips_2/tests/scripts/<test_script_name>.sh
```

Metadata Review
--------------
```
# === Dynamic ===
"creation_time":        THE CURRENT DATETIME
"number_product_tiles": 80, LIKELY NOT WRITTEN IN STONE
        - Describes number of total tiles in dataset
"pixel_x_size": 2.0,    NUMBER OF KM/PIXEL ALONG LAT LINES
"pixel_y_size": 2.0,    NUMBER OF KM/PIXEL ALONG LON LINES
"product_center_latitude": 0.0,  SATELLITE SUB-POINT
"product_center_longitude": SATELLITE SUB-POINT,
"product_columns": NUMBER OF PIXELS IN X DIRECTION,
"product_name":     PRODUCT WE'RE GENERATING (PRVIS, GEOCC, SNCL)
"product_rows":     TOTAL PIXELS IN Y DIRECTION
"product_tile_height": SIZE OF EA. TILE IN PIXELS (NUMBER OF ROWS)
"product_tile_width": SIZE OF EA. TILE IN PIXELS (NUMBER OF COLUMNS)
"satellite_altitude":   ADD ALTITUDE TO LIST OF SATELLITE CONSTANTS
        - Maybe we can get this dynamically in the future
"satellite_id": ID OF SATELLITE,
        - We don't know what these are... Himawari appears to be "GOES-H8"
"satellite_latitude":   SAME AS PRODUCT_CENTER_LATITUDE
"satellite_longitude":  SAME AS PRODUCT_CENTER_LONGITUDE
"source_scene":     Geolocation
        - "Full Disk" "CONUS",
"start_date_time": start_str,
"tile_center_latitude": SET ON TILE-BY-TILE BASIS
        - It's in Deb's but not Robert's
"tile_center_longitude":  SEE ABOVE
"tile_column_offset": SIZE OF IMAGE DIVIDED BY NUMBER OR TILES PER COLUMN?
        - Index of 1st pixel in that tile
"tile_row_offset": SIZE OF IMAGE DIVIDED BY NUMBER OR TILES PER ROW?
        - Index of 1st pixel in that tile
"time_coverage_end": start_str,
"time_coverage_start": start_str,
"title": WHATEVER I WANT!
        - e.g. "GeoColor AWIPS tiles for ECONUS (GOES-16)"
          or   "Sectorized Cloud and Moisture Full Disk Imagery"

# === Static ===
"_NCProperties": "version=2,netcdf=4.9.3-development,hdf5=1.12.2"
"abi_mode": 3,      ONLY FOR ABI
        - ABI has ~6 different scan modes
"bit_depth": 16,    NUMBER OF BITS PER PIXEL
        - With 8-bit depth w/ 3 channs allows for 256 colors
"channel_id": 17,    PROBABLY RELATED TO CONFIG FILE?
        - The name of this variable is definable in the config file
        - Jeremy remembers Alan saying this ^
"Conventions": "CF-1.7",
"central_wavelength": 0.64
"creator": GeoIPS
"production_location": "CIRA",
"projection": "fixedgrid_projection", MAY CHANGE IN THE FUTURE

# === To Investigate ===
"_NCProperties": "version=2,netcdf=4.9.3-development,hdf5=1.12.2"
"ICD_version": "SE-08_7034704_GS_AWIPS_Ext_ICD_RevB.3",
        - Name of the "interface control document" which describes how products
            get into AWIPS2
"bit_depth": 12,    NUMBER OF BITS PER PIXEL
        - With 8-bit depth w/ 3 channs allows for 256 colors
        - Why 12?
"channel_id": 2,    PROBABLY RELATED TO CONFIG FILE?
        - The name of this variable is definable in the config file
        - Jeremy remembers Alan saying this ^
"satellite_id": ID OF SATELLITE,
        - We don't know what these are... Himawari appears to be "GOES-H8"
"periodicity"


# === Do We Actually Need It??? ===
"_NCProperties": "version=2,netcdf=4.9.3-development,hdf5=1.12.2"
"abi_mode": 3,      ONLY FOR ABI
"ICD_version": "SE-08_7034704_GS_AWIPS_Ext_ICD_RevB.3",
        - Name of the "interface control document" which describes how products
            get into AWIPS2
        - Jeremy thinks we DON'T need this
"project": "CIRA",
"source_spatial_resolution": 1.0,
"request_spatial_resolution": 1.0,
"spatial_resolution": "0.5km at nadir,
"production_site": "CIRA",
"institution": "CIRA",
```