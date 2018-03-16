""" Module for IO of SIF data
"""
from __future__ import division

import os
import numpy as np

from osgeo import gdal

from . import nc2array
from ..common import log, enlarge2, date_to_doy
from ..common import constants as cons


def sif2stack(_file, des, overwrite=False, verbose=False):
    """ read sif product and convert to stack image

    Args:
        _file (str): path to input SIF file
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
        sif = nc2array(_file, 0)
        sif_std = nc2array(_file, 2)
        sif_da = nc2array(_file, 1)
        sif_par = nc2array(_file, 3)
        sif_par_std = nc2array(_file, 4)
        ndvi = nc2array(_file, 5)
        ndvi_std = nc2array(_file, 6)
        csza = nc2array(_file, 7)
        nob = nc2array(_file, 8)
        lat = enlarge2(nc2array(_file, 9), 720, 1).T
        lon = enlarge2(nc2array(_file, 10), 360, 1)
    except:
        _error = 2
        log.error('Failed to read input {}'.format(_file))

    # create geo info
    if verbose:
        log.info('Creating geo information...')
    geo = {'proj': cons.SIF_PROJ}
    geo['geotrans'] = (-180, 0.5, 0, 90, 0, -0.5)
    geo['lines'] = 360
    geo['samples'] = 720
    geo['bands'] = 11
    geo['nodata'] = cons.NODATA

    # generate mask band
    if verbose:
        log.info('Generating mask band...')
    try:
        mask = (sif <= cons.SIF_NODATA)
    except:
        _error = 3
        log.error('Failed to generate mask band.')

    # clean up data
    if verbose:
        log.info('Cleaning up data...')
    try:
        sif[sif <= cons.SIF_NODATA] = cons.NODATA / cons.SIF_SF
        sif_std[sif_std <= cons.SIF_NODATA] = cons.NODATA / cons.SIF_SF
        sif_da[sif_da <= cons.SIF_NODATA] = cons.NODATA / cons.SIF_SF
        sif_par[sif_par <= cons.SIF_NODATA] = cons.NODATA / cons.SIF_SF
        sif_par_std[sif_par_std <= cons.SIF_NODATA] = cons.NODATA / cons.SIF_SF
        ndvi[ndvi <= cons.SIF_NODATA] = cons.NODATA / cons.SIF_SF
        ndvi_std[ndvi_std <= cons.SIF_NODATA] = cons.NODATA / cons.SIF_SF
        csza[csza <= cons.SIF_NODATA] = cons.NODATA / cons.SIF_SF
        nob[nob <= cons.SIF_NODATA] = cons.NODATA / cons.SIF_SF

        sif = (sif * cons.SIF_SF).astype(np.int16)
        sif_std = (sif_std * cons.SIF_SF).astype(np.int16)
        sif_da = (sif_da * cons.SIF_SF).astype(np.int16)
        sif_par = (sif_par * cons.SIF_SF).astype(np.int16)
        sif_par_std = (sif_par_std * cons.SIF_SF).astype(np.int16)
        ndvi = (ndvi * cons.SIF_SF).astype(np.int16)
        ndvi_std = (ndvi_std * cons.SIF_SF).astype(np.int16)
        csza = (csza * cons.SIF_SF).astype(np.int16)
        nob = nob.astype(np.int16)
        lat = (lat * 100).astype(np.int16)
        lon = (lon * 100).astype(np.int16)
    except:
        _error = 4
        log.error('Failed to clean up data.')

    # write output
    if verbose:
        log.info('Writing output: {}'.format(des))
    try:
        # initialize output
        _driver = gdal.GetDriverByName('GTiff')
        output = _driver.Create(des, geo['samples'], geo['lines'], 12,
                                gdal.GDT_Int16)
        output.SetProjection(geo['proj'])
        output.SetGeoTransform(geo['geotrans'])
        # set nodata value
        for i in range(1,12):
            output.GetRasterBand(i).SetNoDataValue(cons.NODATA)

        # write output
        output.GetRasterBand(1).WriteArray(sif)
        output.GetRasterBand(2).WriteArray(sif_std)
        output.GetRasterBand(3).WriteArray(sif_da)
        output.GetRasterBand(4).WriteArray(sif_par)
        output.GetRasterBand(5).WriteArray(sif_par_std)
        output.GetRasterBand(6).WriteArray(ndvi)
        output.GetRasterBand(7).WriteArray(ndvi_std)
        output.GetRasterBand(8).WriteArray(csza)
        output.GetRasterBand(9).WriteArray(nob)
        output.GetRasterBand(10).WriteArray(lat)
        output.GetRasterBand(11).WriteArray(lon)
        output.GetRasterBand(12).WriteArray(mask)

        # assign band name
        output.GetRasterBand(1).SetDescription('SIF')
        output.GetRasterBand(2).SetDescription('SIF Std')
        output.GetRasterBand(3).SetDescription('SIF Daily Average')
        output.GetRasterBand(4).SetDescription('SIF Par Normalized')
        output.GetRasterBand(5).SetDescription('SIF Par Normalized Std')
        output.GetRasterBand(6).SetDescription('NDVI')
        output.GetRasterBand(7).SetDescription('NDVI Std')
        output.GetRasterBand(8).SetDescription('Cosine Solar Zenith Angle')
        output.GetRasterBand(9).SetDescription('Counts')
        output.GetRasterBand(10).SetDescription('Latitude')
        output.GetRasterBand(11).SetDescription('Longitude')
        output.GetRasterBand(12).SetDescription('SIF Mask')

    except:
        _error = 5
        log.error('Failed to write output to {}'.format(des))

    # done
    if verbose:
        log.info('Process completed.')
    return 0


def sifn2ln(fn):
    """ convert SIF style file name to Landsat style
        file name only, regardless of file type extension
        e.g. ret_f_nr5_nsvd12_v26_waves734_nolog.grid_SIF_v27_20110101_31.nc
             to F27050DGE2011001MA734 (F vv 050 DGE yyyyddd MA www)
             ret_f_nr5_nsvd12_v26_waves734_nolog.20110601_v27_all.nc
             to F27LATLON2011152DO734 (F vv LAT LON yyyyddd DO www)

    Args:
        fn (str): SIF style file name

    Returns:
        ln (str): Landsat style file name

    """
    fn = os.path.splitext(fn)[0]
    fn = fn.split('_')
    if fn[-1] == 'all':
        d = fn[6].split('.')[1]
        d = date_to_doy(int(d[0:4]), int(d[4:6]), int(d[6:8]))
        return 'F{}LATLON{}DO{}'.format(fn[7][1:], d, fn[5][5:])
    else:
        d = date_to_doy(int(fn[9][0:4]), int(fn[9][4:6]), int(fn[9][6:8]))
        return 'F{}050DGE{}MA{}'.format(fn[8][1:], d, fn[5][5:])
