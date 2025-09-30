#!/bin/bash

# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/* \
    --reader_name abi_netcdf \
    --product_name GeoColor \
    --filename_formatter awips_tiles_fname \
    --output_formatter awips_tiled \
    --reader_kwargs '{ "self_register" : "LOW" }'
retval=$?

exit $retval