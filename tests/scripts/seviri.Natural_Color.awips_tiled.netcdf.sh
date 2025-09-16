#!/bin/bash

# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20250624/1200/H-000-MSG3* \
    --reader_name seviri_hrit \
    --product_name Natural_Color \
    --filename_formatter awips_tiles_fname \
    --output_formatter awips_tiled
retval=$?

exit $retval