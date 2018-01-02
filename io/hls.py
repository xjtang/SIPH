""" Module for IO of HLS data
"""
from __future__ import division

import os
import numpy as np

from osgeo import gdal
from pyhdf.SD import SD, SDC

from ..io import hdr2geo
from ..common import log
from ..common import constants as cons


def hls2stack(hls, des, sensor='S30', _hdr=True, overwrite=False, verbose=False):
    """ read HLS product and convert to stack image with selected bands

    Args:
        img (str): path to input HLS file
        des (str): path to output
        sensor (str): which sensor, S30 or L30
        overwrite (bool): overwrite or not
        verbose (bool): verbose or not

    Returns:
        0: successful
        1: error due to des
        2: unknown sensor
        3: error in reading input
        4: error in generating mask band
        5: error in cleaning up data
        6: error in writing output

    """
    _error = 0

    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(des.split('/')[-1]))
        return 1

    # handle sensor
    if sensor == 'L30':
        BANDS = cons.L30_BANDS
    elif sensor == 'S30':
        BANDS = cons.S30_BANDS
    else:
        log.error('Unknown sensor {}'.format(sensor))
        return 2

    # flow control
    while True:
        # read input image
        if verbose:
            log.info('Reading input: {}'.format(hls))
        try:
            hls_sd = SD(hls, SDC.READ)
            hls_blue = hls_sd.select(BANDS[0])
            hls_green = hls_sd.select(BANDS[1])
            hls_red = hls_sd.select(BANDS[2])
            hls_nir = hls_sd.select(BANDS[3])
            hls_swir1 = hls_sd.select(BANDS[4])
            hls_swir2 = hls_sd.select(BANDS[5])
            hls_cirrus = hls_sd.select(BANDS[6])
            hls_QA = hls_sd.select(BANDS[7])
        except:
            _error = 3
            log.error('Failed to read input {}'.format(hls))
            break

        # read geo info
        if verbose:
            log.info('Reading geo information...')
        try:
            if _hdr:
                geo = hdr2geo('{}.hdr'.format(hls))
            else:
                hls_img = gdal.Open(hls, gdal.GA_ReadOnly)
                hls_sub = hls_img.GetSubDatasets()
                hls_temp = gdal.Open(hls_sub[1][0], gdal.GA_ReadOnly)
                geo = {'proj': hls_temp.GetProjection()}
                geo['geotrans'] = hls_temp.GetGeoTransform()
                hls_img = None
                hls_sub = None
                hls_temp = None
        except:
            _error = 3
            log.error('Failed to read geo info from {}'.format(hls))
            break

        # read actual data
        if verbose:
            log.info('Reading actual data...')
        try:
            blue = hls_blue.get().astype(np.int16)
            green = hls_green.get().astype(np.int16)
            red = hls_red.get().astype(np.int16)
            nir = hls_nir.get().astype(np.int16)
            swir1 = hls_swir1.get().astype(np.int16)
            swir2 = hls_swir2.get().astype(np.int16)
            cirrus = hls_cirrus.get().astype(np.int16)
            QA = hls_QA.get().astype(np.int16)
        except:
            _error = 3
            log.error('Failed to read data from {}'.format(hls))
            break

        # generate mask band
        if verbose:
            log.info('Generating mask band...')
        try:
            fmask = True
            mask = hlsQA(QA, fmask)
            if not fmask:
                _total = np.sum(mask)
                _size = np.shape(mask)
                if verbose:
                    log.info('{}% masked'.format(_total/(_size[0]*_size[1])*100))
        except:
            _error = 4
            log.error('Failed to generate mask band.')
            break

        # clean up data
        if verbose:
            log.info('Cleaning up data...')
        try:
            invalid = ((blue == -1000) | (green == -1000) | (red == -1000) |
                        (nir == -1000) | (swir1 == -1000) | (swir2 == -1000))
            blue[invalid] = cons.NODATA
            green[invalid] = cons.NODATA
            red[invalid] = cons.NODATA
            nir[invalid] = cons.NODATA
            swir1[invalid] = cons.NODATA
            swir2[invalid] = cons.NODATA
            cirrus[invalid] = cons.NODATA
            mask[invalid] = cons.MASK_NODATA
        except:
            _error = 5
            log.error('Failed to clean up data.')
            break

        # write output
        if verbose:
            log.info('Writing output: {}'.format(des))
        try:
            # initialize output
            _driver = gdal.GetDriverByName('GTiff')
            output = _driver.Create(des, red.shape[1], red.shape[0], 8,
                                    gdal.GDT_Int16)
            output.SetProjection(geo['proj'])
            output.SetGeoTransform(geo['geotrans'])
            # set nodata value
            for i in range(1,8):
                output.GetRasterBand(i).SetNoDataValue(cons.NODATA)
            output.GetRasterBand(8).SetNoDataValue(cons.MASK_NODATA)

            # write output
            output.GetRasterBand(1).WriteArray(blue)
            output.GetRasterBand(2).WriteArray(green)
            output.GetRasterBand(3).WriteArray(red)
            output.GetRasterBand(4).WriteArray(nir)
            output.GetRasterBand(5).WriteArray(swir1)
            output.GetRasterBand(6).WriteArray(swir2)
            output.GetRasterBand(7).WriteArray(cirrus)
            output.GetRasterBand(8).WriteArray(mask)

            # assign band name
            output.GetRasterBand(1).SetDescription('{} {} Blue'.format(sensor,
                                                                    BANDS[0]))
            output.GetRasterBand(2).SetDescription('{} {} Green'.format(sensor,
                                                                    BANDS[1]))
            output.GetRasterBand(3).SetDescription('{} {} Red'.format(sensor,
                                                                    BANDS[2]))
            output.GetRasterBand(4).SetDescription('{} {} NIR'.format(sensor,
                                                                    BANDS[3]))
            output.GetRasterBand(5).SetDescription('{} {} SWIR1'.format(sensor,
                                                                    BANDS[4]))
            output.GetRasterBand(6).SetDescription('{} {} SWIR2'.format(sensor,
                                                                    BANDS[5]))
            output.GetRasterBand(7).SetDescription('{} {} Cirrus'.format(sensor,
                                                                    BANDS[6]))
            output.GetRasterBand(8).SetDescription('{} {} Fmask'.format(sensor,
                                                                    BANDS[7]))
        except:
            _error = 6
            log.error('Failed to write output to {}'.format(des))
            break

        # continue next
        break

    # close files
    if verbose:
        log.info('Closing files...')
    hls_blue = None
    hls_green = None
    hls_red = None
    hls_nir = None
    hls_swir1 = None
    hls_swir2 = None
    hls_cirrus = None
    hls_QA = None
    hls_SD = None

    # done
    if _error == 0:
        if verbose:
            log.info('Process completed.')
    return _error


def hlsQA(QA, fmask=False):
    """ intepret HLS QA and return a mask array

    Args:
        QA (ndarray): QA band array
        fmask (bool): output in fmask format

    Returns:
        mask (ndarray): mask array

    """
    if fmask:
        mask = np.zeros(QA.shape, QA.dtype)
        mask[np.mod(QA, 8) > 0] = 4
        mask[np.mod(np.right_shift(QA, 3), 2) > 0] = 2
        mask[np.mod(np.right_shift(QA, 4), 2) > 0] = 3
        mask[np.mod(np.right_shift(QA, 5), 2) > 0] = 1
        mask[QA == 255] = 255
    else:
        QA[QA == 255] = 0
        mask = np.mod(QA, 32) > 0
    return mask


def hn2ln(hn):
    """ convert HLS style file name to Landsat style
        file name only, regardless of file type extension
        e.g. HLS.S30.T28PDC.2016074.v1.3.hdf
             to S30T28PDC2016074HLS13 (x30 T ttttt yyyyddd HLS vv)

    Args:
        hn (str): HLS style file name

    Returns:
        ln (str): Landsat style file name

    """
    hn = hn.split('.')
    return '{}{}{}{}{}{}'.format(hn[1], hn[2], hn[3], hn[0], hn[4][1], hn[5])


def ln2tn(ln):
    """ convert Landsat style file name to style for Tmask
        file name only, regardless of file type extension
        e.g. S30T28PDC2016074HLS13.tif
             to LNDT28PDC2016074S3013

    Args:
        ln (str): Landsat style file name

    Returns:
        tn (str): Tmask style file name

    """
    ln = os.path.splitext(ln)[0]
    return '{}{}{}{}'.format('LND', ln[3:16], ln[0:3], ln[19:21])
