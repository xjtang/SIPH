""" Module for visualizing cloud related stuff
"""
import os

from ..common import log
from ..io import csv2list, stack2array
from ..common import doy_to_date as d2d


def nob_per_month(_file, verbose=False):
    """ read list of images and calculate number of clear observation per month

    Args:
        file (str): path to list of image file
        verbose (bool): verbose or not

    Returns:
        nobpm (list): number of clear observasion per month
        -1: error

    """
    # read image list
    try:
        if verbose:
            log.info('Reading image list...')
        img_list = csv2list(_file, True)
    except:
        log.error('Failed to read image list.')
        return -1

    # initialize output
    if verbose:
        log.info('Initializing output...')
    nobpm = [[x, 0] for x in range(1,13)]

    # loop through images
    if verbose:
        log.info('Looping through image list...')
    for img in img_list:
        if verbose:
            log.info('Extracting nob from {}'.format(img[2].split('/')[-1]))
        nobpm[d2d(img[0])[1], 1] += 1 - percent_cloudy(img[2], 6)

    # done
    if verbose:
        log.info('Successfully generated nobpm.')
    return nobpm


def percent_cloudy(img, mask):
    """ read mask band of stacked image and return percent cloudy

    Args:
        img (str): path to input image
        des (str): index of mask band from 1

    Returns:
        pct (float): percent cloudy

    """
    mask2 = stack2array(img, mask, np.uint8)
    return float((mask2.sum()) / (mask2.shape[0] * mask2.shape[1]) * 100)
