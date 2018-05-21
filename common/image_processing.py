""" Module for common functions related to image processing
"""
from __future__ import division

import numpy as np

from . import sidebyside
from . import constants as cons


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
                * cons.IMGBIT).astype(np.uint8)
    return array


def apply_mask(array, mask, mask_color=cons.MASK_COLOR):
    """ apply mask to array

    Args:
        array (ndarray): array to be modified
        mask (ndarray): mask array

    Returns:
        masked (ndarray): masked array

    """
    array[mask > 0] = mask_color
    return array


def result2mask(result, value, side=cons.RESULT_SIDE):
    """ convert result array to a mask array

    Args:
        result (ndarray): result array
        value (int): value that split result into masked and unmasked
        side (int): which side to mask, 0 for =, 1 for >=, 2 for <=

    Returns:
        mask (ndarray): mask array

    """
    if value == 0:
        return result * 0
    if side == 0:
        result[result == value] = value
        result[result > value] = 0
        result[result < value] = 0
    elif side == 1:
        result[result >= value] = value
        result[result < value] = 0
    elif side == 2:
        if value <= cons.RESULT_MIN:
            return result * 0
        else:
            result[result <= cons.RESULT_MIN] = value + 1
            result[result <= value] = value
            result[result > value] = 0
    else:
        return result * 0
    return result / value


def nodata_mask(array, nodata=cons.NODATA):
    """ generate nodata mask from image array

    Args:
        array (ndarray): image array
        nodata (int): nodata value

    Returns:
        mask (ndarray): nodata mask

    """

    return np.amax(array == nodata, 2).astype(np.uint8)


def clean_up(array, w, t=2, nodata=cons.NODATA):
    """ clean up salt and pepper effect in result images

    Args:
        array (ndarray): image array
        w (int): window size, how much extent out from the center pixel
        t (int): clean up threhold
        nodata (int): nodata value

    Returns:
        array2 (ndarray): cleaned up array

    """
    array2 = np.copy(array)
    for i in range(w, array.shape[0] - w):
        for j in range(w, array.shape[1] - w):
            if array[i, j] == nodata:
                continue
            piece = array[(i - w):(i + w + 1), (j - w):(j + w + 1)]
            if (piece == array[i, j]).sum() <= t:
                value, count = np.unique(piece, return_counts=True)
                if value[count.argmax()] == nodata:
                    count[count.argmax()] = 0
                array2[i, j] = value[count.argmax()]
    return array2


def thematic_map(array, values, colors, overarray=0):
    """ transform array into thematic map

    Args:
        array (ndarray): input array
        values (list, int): list of values in the array
        colors (list, int): list of colors corresponding to the values

    Returns:
        tm (ndarray): thematic map

    """
    if type(overarray) == int:
        tm = np.zeros((3,array.shape[0],array.shape[1]), np.uint8) + cons.IMGBIT
    else:
        tm = overarray
    for i, x in enumerate(values):
        tm[array == x, :] = colors[i]
    return tm


def nchange(array):
    """ calculate number of change in the third dimension

    Args:
        array (ndarray): input array

    Returns:
        nchange (ndarray): number of change

    """
    nchange = np.zeros(array.shape[-2])
    for i in range(1, array.shape[2]):
        nchange = nchange + (array[:, :, i] != array[:, :, i - 1])
    return nchange
