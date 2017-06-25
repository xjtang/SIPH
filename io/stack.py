""" Module for reading stacked images
"""
from __future__ import division

import os
import numpy as np

from osgeo import gdal

from ..common import log


def percent_cloudy(img, mask, verbose=False):
    """ read mask band of stacked image and return percent cloudy

    Args:
        img (str): path to input image
        des (str): index of mask band from 1
        verbose (bool): verbose or not

    Returns:
        pct (float): percent cloudy
        -1: error

    """
    # flow control
    while True:
        # read image
        if verbose:
            log.info('Reading input image: {}'.format(img))
        try:
            img2 = gdal.Open(img, gdal.GA_ReadOnly)
        except:
            log.error('Failed to read data from {}'.format(img))
            pct = -1
            break

        # read mask band data
        if verbose:
            log.info('Reading mask band: {}'.format(mask))
        try:
            mask2 = img2.GetRasterBand(mask).ReadAsArray().astype(np.uint8)
        except:
            log.error('Failed to read mask band {}'.format(mask))
            pct = -1
            break

        # calculate percentage
        if verbose:
            log.info('Calculating percentage...')
        pct = float((mask2.sum()) / (mask2.shape[0] * mask2.shape[1]) * 100)

        # continue next
        break

    # clean up
    img2 = None
    mask2 = None

    # done
    if pct >= 0:
        if verbose:
            log.info('Percetn cloudy: {:.2f}%'.format(pct))
    return pct
