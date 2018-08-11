""" Module for IO of HLS data
"""
from __future__ import division

import os
import numpy as np

from osgeo import gdal

from ..io import stackGeo, stack2array
from ..common import log, enlarge, date_to_doy
from ..common import constants as cons


def sen2stack(sen, des, overwrite=False, verbose=False):
    """ read Sentinel-2 L1C and convert to stack image with selected bands

    Args:
        sen (str): path to input Sentinel file
        des (str): path to output
        overwrite (bool): overwrite or not
        verbose (bool): verbose or not

    Returns:
        0: successful
        1: error due to des
        2: error in reading input
        3: error in writing output

    """
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(des.split('/')[-1]))
        return 1

    # read input image
    if verbose:
        log.info('Reading input: {}'.format(sen))
    try:
        geo = stackGeo('{}02.jp2'.format(sen))
        blue = stack2array('{}02.jp2'.format(sen), 1, np.int16)
        green = stack2array('{}03.jp2'.format(sen), 1, np.int16)
        red = stack2array('{}04.jp2'.format(sen), 1, np.int16)
        nir = stack2array('{}08.jp2'.format(sen), 1, np.int16)
        swir1 = enlarge(stack2array('{}11.jp2'.format(sen), 1, np.int16), 2)
        swir2 = enlarge(stack2array('{}12.jp2'.format(sen), 1, np.int16), 2)
        cirrus = enlarge(stack2array('{}10.jp2'.format(sen), 1, np.int16), 6)
    except:
        log.error('Failed to read input {}'.format(img))
        return 2

    # write output
    if verbose:
        log.info('Writing output: {}'.format(des))
    try:
        # initialize output
        _driver = gdal.GetDriverByName('GTiff')
        output = _driver.Create(des, geo['samples'], geo['lines'], 7,
                                gdal.GDT_Int16)
        output.SetProjection(geo['proj'])
        output.SetGeoTransform(geo['geotrans'])
        for i in range(1,8):
            output.GetRasterBand(i).SetNoDataValue(cons.NODATA)
        # write output
        output.GetRasterBand(1).WriteArray(blue)
        output.GetRasterBand(2).WriteArray(green)
        output.GetRasterBand(3).WriteArray(red)
        output.GetRasterBand(4).WriteArray(nir)
        output.GetRasterBand(5).WriteArray(swir1)
        output.GetRasterBand(6).WriteArray(swir2)
        output.GetRasterBand(7).WriteArray(cirrus)
        # assign band name
        output.GetRasterBand(1).SetDescription('S10 B02 Blue')
        output.GetRasterBand(2).SetDescription('S10 B03 Green')
        output.GetRasterBand(3).SetDescription('S10 B04 Red')
        output.GetRasterBand(4).SetDescription('S10 B08 NIR')
        output.GetRasterBand(5).SetDescription('S10 B11 SWIR')
        output.GetRasterBand(6).SetDescription('S10 B12 SWIR')
        output.GetRasterBand(7).SetDescription('S10 B10 Cirrus')
    except:
        log.error('Failed to write output to {}'.format(des))
        return 3

    # done
    if verbose:
        log.info('Process completed.')
    return 0


def sn2ln(sn):
    """ convert Sentinel style file name to Landsat style
        file name only, regardless of file type extension
        e.g. S30T28PDC2016074HLS13 (x30 T ttttt yyyyddd HLS vv)

    Args:
        sn (str): Sentinel style file name

    Returns:
        ln (str): Landsat style file name

    """
    sn = sn.split('_')
    if sn[0][0:2] == 'S2':
        d = date_to_doy(int(sn[-4][0:4]), int(sn[-4][4:6]), int(sn[-4][6:8]))
        sn = sn[-2]
    else:
        d = date_to_doy(int(sn[1][0:4]), int(sn[1][4:6]), int(sn[1][6:8]))
        sn = sn[0]
    return 'S10{}{}S2L1C'.format(sn, d)
