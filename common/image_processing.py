""" Module for common functions related to image processing
"""
from __future__ import division

import numpy as np

from . import sidebyside


IMGBIT = 255
MASK_COLOR = (IMGBIT, 0, 0)
RESULT_MIN = 2012000


def apply_stretch(array, stretch):
    """ apply stretch to array

    Args:
        array (ndarray): array to be modified
        stretch (list, int): image stretch

    Returns:
        array2 (ndarray): modified array

    """
    # apply stretch
    array[array < stretch[0]] = stretch[0]
    array[array > stretch[1]] = stretch[1]
    array = ((array - stretch[0]) / (stretch[1] - stretch[0])
                * IMGBIT).astype(np.uint8)
    return array


def apply_mask(array, mask, mask_color=MASK_COLOR):
    """ apply mask to array

    Args:
        array (ndarray): array to be modified
        mask (ndarray): mask array

    Returns:
        masked (ndarray): masked array

    """
    array[mask > 0] = mask_color
    return array


def result2mask(result, value):
    """ convert result array to a mask array

    Args:
        result (ndarray): result array
        value (int): value that split result into masked and unmasked

    Returns:
        mask (ndarray): mask array

    """
    if value <= RESULT_MIN:
        return result * 0
    else:
        result[result <= RESULT_MIN] = value + 1
        result[result <= value] = value
        result[result > value] = 0
        return result / value


def nodata_mask(array, nodata=-9999):
    """ generate nodata mask from image array

    Args:
        array (ndarray): image array
        nodata (int): nodata value

    Returns:
        mask (ndarray): nodata mask

    """

    return np.amax(array == -9999, 2).astype(np.uint8)
