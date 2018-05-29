""" Module for commonly used constants
"""
# common
NODATA = -9999
SCALE_FACTOR = 10000
GS = (100, 300)

# images
IMGBIT = 255
MASK_COLOR = (IMGBIT, 0, 0)
RESULT_MIN = 2012000
RESULT_SIDE = 2

# VIIRS
SR_BANDS = (23, 24, 25)
QA_BANDS = (13, 14, 16, 18, 19)
VZA_BAND = 1

# MODIS
MODIS_NODATA = 32767
EVI_COEF = [2.5, 6, 7.5, 10000]
MGA_QA_BAND = 1
MGA_VZA_BAND = 2
MGA_SR_BANDS = [11, 12, 16, 17, 14]
MGQ_BANDS = [1, 2]
MVI_BANDS = [0, 1, 3, 4, 6, 5, 11]
MLC_BAND = 0
MLC_RECLASS = [[1, [0]],
                [2, [1, 2, 3, 4, 5]],
                [3, [6, 7, 8, 9, 10]],
                [4, [11]],
                [5, [12, 14]],
                [6, [13]],
                [7, [15]],
                [8, [16]],
                [255, [254, 255]]]

# HLS
L30_BANDS = ('band02', 'band03', 'band04', 'band05', 'band06', 'band07',
                'band09', 'QA')
S30_BANDS = ('B02', 'B03', 'B04', 'B8A', 'B11', 'B12', 'B10', 'QA')
T_BANDS = (2, 4, 5, 12)
MASK_NODATA = 255
MASK_CLOUD = 4
MASK_SHADOW = 2
MASK_WATER = 1
MASK_SNOW = 3
MASK_VALUES = (1, 2, 3, 4)
MASK_COLORS = ((0, 0, IMGBIT), (IMGBIT, 0, IMGBIT), (IMGBIT, IMGBIT, 0),
                (IMGBIT, 0, 0))
LASRC_BAND = 4
STRATA = (0, 2, 4, 20, 22, 24, 40, 42, 44, 200, 202, 204, 220, 222, 224, 240,
            242, 244, 400, 402, 404, 420, 422, 424, 440, 442, 444)
SCHEME = [[1, [0, 222, 444]],
            [2, [4, 40, 400]],
            [3, [44, 244, 404, 424, 440, 442]],
            [4, [2, 20, 22, 200, 202, 220, 224, 242, 422]],
            [5, [24, 42, 204, 240, 402, 420]]]

# SIF
SIF_NODATA = -999
SIF_SF = 1000
SIF_PROJ = '''GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.25
            7223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM[
            "Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251
            994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'''

# download
_HTTP = 'https://e4ftl01.cr.usgs.gov/'
_FTP = 'ftp://ladsweb.nascom.nasa.gov/'
CHUNK = 1024*1024

# classification
FOREST = 0
NF = 2
CHANGE = 1
PC = 3
PF = 4
TEST_BAND = 4
MEAN_THRES = 8000
AMP_THRES = 1000
SLOPE_THRES = 1.8
LENGTH_THRES = 365

# text
TEXT_FONT = './SIPH/share/Arial.ttf'
TEXT_SIZE = 200
TEXT_COL = (255, 255, 255)
