#!/bin/bash

# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/* \
    --reader_name abi_netcdf \
    --resampled_read \
    --product_name GeoColor \
    --filename_formatter awips_tiles_fname \
    --output_formatter awips_tiled \
    --sector_list goes_west
retval=$?

exit $retval