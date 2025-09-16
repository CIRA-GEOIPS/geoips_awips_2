#!/bin/bash

# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_geocolor/data/mtg/20240924.1500/*.nc \
    --reader_name fci_netcdf \
    --reader_kwargs '{"self_register": "LOW"}' \
    --self_register_dataset 'FULL_DISK' \
    --self_register_source fci \
    --product_name GeoColor \
    --filename_formatter awips_tiles_fname \
    --output_formatter awips_tiled \
    --logging_level INFO \
    --minimum_coverage 0
retval=$?

exit $retval