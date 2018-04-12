""" Module for IO of GOES short wave radiation data
"""
from __future__ import division

import os
import math
import numpy as np

from osgeo import gdal

from . import nc2array
from ..common import log, enlarge2, date_to_doy
from ..common import constants as cons


def goes2stack(_file, des, overwrite=False, verbose=False):
    """ read GOES product and convert to stack image

    Args:
        _file (str): path to input GOES file
        des (str): path to output
        overwrite (bool): overwrite or not
        verbose (bool): verbose or not

    Returns:
        0: successful
        1: error due to des
        2: error in reading input
        3: error in generating mask band
        4: error in cleaning up data
        5: error in writing output

    """
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(des.split('/')[-1]))
        return 1

    # read input netCDF
    if verbose:
        log.info('Reading input: {}'.format(_file))
    try:
        land = nc2array(_file, 3)
        ssi = nc2array(_file, 4).data
        ssic = nc2array(_file, 5)
        dli = nc2array(_file, 6).data
        dlic = nc2array(_file, 7)
        lat = enlarge2(nc2array(_file, 1), 2400, 1).T
        lon = enlarge2(nc2array(_file, 2), 2400, 1)
    except:
        log.error('Failed to read input {}'.format(_file))
        return 2

    # create geo info
    if verbose:
        log.info('Creating geo information...')
    geo = {'proj': cons.SIF_PROJ}
    geo['geotrans'] = (int((lon[0, 0] - 0.025) * 1000) / 1000, 0.05, 0,
                        int((lat[0, 0] - 0.025) * 1000 ) / 1000, 0, 0.05)
    geo['lines'] = 2400
    geo['samples'] = 2400
    geo['bands'] = 7
    geo['nodata'] = -32768

    # clean up data
    if verbose:
        log.info('Cleaning up data...')
    try:
        land = land.astype(np.int16)
        ssi = (ssi * 10).astype(np.int16)
        ssic = ssic.astype(np.int16)
        dli = (dli * 10).astype(np.int16)
        dlic = dlic.astype(np.int16)
        lat = (lat * 100).astype(np.int16)
        lon = (lon * 100).astype(np.int16)
    except:
        log.error('Failed to clean up data.')
        return 4

    # write output
    if verbose:
        log.info('Writing output: {}'.format(des))
    try:
        # initialize output
        _driver = gdal.GetDriverByName('GTiff')
        output = _driver.Create(des, geo['samples'], geo['lines'], geo['bands'],
                                gdal.GDT_Int16)
        output.SetProjection(geo['proj'])
        output.SetGeoTransform(geo['geotrans'])
        # set nodata value
        for i in range(1,7):
            output.GetRasterBand(i).SetNoDataValue(geo['nodata'])

        # write output
        output.GetRasterBand(1).WriteArray(land)
        output.GetRasterBand(2).WriteArray(ssi)
        output.GetRasterBand(3).WriteArray(ssic)
        output.GetRasterBand(4).WriteArray(dli)
        output.GetRasterBand(5).WriteArray(dlic)
        output.GetRasterBand(6).WriteArray(lat)
        output.GetRasterBand(7).WriteArray(lon)

        # assign band name
        output.GetRasterBand(1).SetDescription('Land Mask')
        output.GetRasterBand(2).SetDescription('Surface Solar Irradiance')
        output.GetRasterBand(3).SetDescription('SSI Confidence')
        output.GetRasterBand(4).SetDescription('Downward Longwave Irradiance')
        output.GetRasterBand(5).SetDescription('DLI Confidence')
        output.GetRasterBand(6).SetDescription('Latitude')
        output.GetRasterBand(7).SetDescription('Longitude')
    except:
        log.error('Failed to write output to {}'.format(des))
        return 5

    # done
    if verbose:
        log.info('Process completed.')
    return 0


def gn2ln(gn):
    """ convert GOES style file name to Landsat style
        file name only, regardless of file type extension
        e.g. 20160101090000-OSISAF-RADFLX-01H-GOES13.nc
             to G13005DGE201600101H09 (G13005DGE yyyyddd ppp hh)

    Args:
        gn (str): GEOS style file name

    Returns:
        ln (str): Landsat style file name

    """
    gn = os.path.splitext(gn)[0]
    gn = gn.split('-')
    d = date_to_doy(int(gn[0][0:4]), int(gn[0][4:6]), int(gn[0][6:8]))
    return 'G13005DGE{}{}{}'.format(d, gn[3], gn[0][8:10])
