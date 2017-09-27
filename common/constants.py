""" Module for commonly used constants
"""
# common
NODATA = -9999
SCALE_FACTOR = 10000

# images
IMGBIT = 255
MASK_COLOR = (IMGBIT, 0, 0)
RESULT_MIN = 2012000
RESULT_SIDE = 2

# VIIRS
SR_BANDS = (23, 24, 25)
QA_BANDS = (13, 14, 16, 18, 19)
VZA_BAND = 1

# HLS
L30_BANDS = ('band02', 'band03', 'band04', 'band05', 'band06', 'band07',
                'band09', 'QA')
S30_BANDS = ('B02', 'B03', 'B04', 'B8A', 'B11', 'B12', 'B10', 'QA')

# download
_HTTP = 'https://e4ftl01.cr.usgs.gov/'
_FTP = 'ftp://ladsweb.nascom.nasa.gov/'
CHUNK = 1024*1024

# classification
FOREST = 0
NF = 2
CHANGE = 1
TEST_BAND = 3
MEAN_THRES = 7500
AMP_THRES = 1500
SLOPE_THRES = 3
