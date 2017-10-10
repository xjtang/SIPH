""" Module for IO of HLS data
"""
from __future__ import division

import os
import numpy as np

from osgeo import gdal

from ..common import log
from ..common import constants as cons


def mask2array(mask, _source):
    """ read mask image as array

    Args:
        mask (str): path to input mask file
        _source (str): source of mask, e.g. fmask, maja, lasrc

    Returns:
        array (ndarray): array of image data

    """
    fn = os.path.basename(mask)
    if _source == 'lasrc':
        img = gdal.Open(mask, gdal.GA_ReadOnly)
        sub = img.GetSubDatasets()
        img2 = gdal.Open(sub[13][0], gdal.GA_ReadOnly)
        array = img2.GetRasterBand(1).ReadAsArray().astype(np.int16)
    elif _source == 'fmask':
        img = gdal.Open(mask, gdal.GA_ReadOnly)
        array = img.GetRasterBand(1).ReadAsArray().astype(np.int16)
    elif _source == 'maja':
        img1 = gdal.Open(mask, gdal.GA_ReadOnly)
        img2 = gdal.Open(mask.replace('_CLD_','_MSK_'), gdal.GA_ReadOnly)
        array1 = img1.GetRasterBand(1).ReadAsArray().astype(np.int16)
        array2 = img2.GetRasterBand(1).ReadAsArray().astype(np.int16)
        array = np.stack((array1, array2))
    else:
        log.error('Unknown source: {}'.format(_source))
        return 0
    return array


def bit2mask(bit, _source):
    """ intepret bits of mask images and return a mask array

    Args:
        bit (ndarray): mask bit array
        _source (str): source of mask, e.g. fmask, maja, lasrc

    Returns:
        mask (ndarray): mask array

    """
    mask = np.zeros(bit.shape[-2:], np.int16)
    if _source == 'lasrc':
        mask[bit == 255] = cons.MASK_NODATA
        mask[np.mod(np.right_shift(bit, 5), 2) > 0] = cons.MASK_WATER
        mask[np.mod(np.right_shift(bit, 4), 2) > 0] = cons.MASK_SNOW
        mask[np.mod(np.right_shift(bit, 3), 2) > 0] = cons.MASK_SHADOW
        mask[np.mod(bit, 8) > 0] = cons.MASK_CLOUD
    elif _source == 'fmask':
        return bit
    elif _source == 'maja':
        mask[bit[0] == 255] = cons.MASK_NODATA
        mask[np.mod(np.right_shift(bit[0], 2), 4) > 0] = cons.MASK_SHADOW
        mask[np.mod(np.right_shift(bit[0], 4), 16) > 0] = cons.MASK_CLOUD
        mask[np.mod(np.right_shift(bit[0], 1), 2) > 0] = cons.MASK_CLOUD
        mask[np.mod(bit[1], 2) > 0] = cons.MASK_WATER
        mask[np.mod(np.right_shift(bit[1], 5), 2) > 0] = cons.MASK_SNOW
    else:
        log.error('Unknown source: {}'.format(_source))
    return mask


def mn2ln(hn, _source, res=30):
    """ convert mask file name to Landsat style
        file name only, regardless of file type extension
        e.g. HLS.S30.T28PDC.2016074.v1.3.hdf
             to S30T28PDC2016074HLS13 (x30 T ttttt yyyyddd HLS vv)

    Args:
        hn (str): HLS style file name
        _source (str): source of mask, e.g. fmask, maja, lasrc
        res (int): resolution

    Returns:
        ln (str): Landsat style file name

    """
    if _source == 'fmask':
        hn = hn.split('.')
        return 'M{}{}{}FMASK'.format(res, hn[2], hn[3])
    elif _source == 'lasrc':
        hn = hn.split('.')
        return 'M{}{}{}LASRC'.format(res, hn[2], hn[3])
    elif _source == 'maja':
        hn = hn.split('.')
        return 'M{}{}{}MAJAA'.format(res, hn[0], hn[1])
    else:
        log.error('Unknown source: {}'.format(_source))
        return 'UNKNOWN'
