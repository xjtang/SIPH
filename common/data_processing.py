""" Module for common functions related to data processing
"""
import numpy as np

from scipy import ndimage as nd


def enlarge(array, scaling):
    """ enlarge an array by a scaling factor
        by Chris Holden

    Args:
        array (ndarray): array to be scaled
        scaling (int): amount of scaling

    Returns:
        scaled (ndarray): scaled array

    """
    return np.kron(array, np.ones((scaling, scaling))).astype(array.dtype)


def enlarge2(array, x, y):
    """ enlarge an array by different scaling factor for x and y

    Args:
        array (ndarray): array to be scaled
        x (int): amount of scaling on x
        y (int): amount of scaling on y

    Returns:
        scaled (ndarray): scaled array

    """
    return np.kron(array, np.ones((x, y))).astype(array.dtype)


def crop(array, window):
    """ crop a part of an array

    Args:
        array (ndarray): array to be cropped
        window (list, int): crop window, [xmin, ymin, xmax, ymax]

    Returns:
        cropped (ndarray): cropped array

    """
    w = [x - 1 for x in window]
    return array[w[0]:w[2], w[1]:w[3]]


def mirror(array):
    """ mirrow an array and add split line in the middle

    Args:
        array (ndarray): array to be mirrored

    Returns:
        mirrored (ndarray): mirrored array

    """
    s = list(array.shape)
    s[1] = 1
    return np.concatenate((array, np.zeros(s), array),
                            axis=1).astype(array.dtype)

def sidebyside(array1, array2):
    """ put two arrays side by side and add split line in the middle

    Args:
        array1 (ndarray): first array
        array2 (ndarray): second array

    Returns:
        sided (ndarray): side by side array

    """
    s = list(array1.shape)
    s[1] = 1
    return np.concatenate((array1, np.zeros(s), array2),
                            axis=1).astype(array1.dtype)


def reclassify(array, scheme):
    """ reclassify array

    Args:
        array (ndarray): input array
        scheme (list): classification scheme

    Returns:
        reclassed (ndarray): reclassified array

    """
    reclassed = np.copy(array)
    for i in range(0, len(scheme)):
        for j in scheme[i][1]:
            reclassed[array == j] = scheme[i][0]
    return reclassed


def tablize(array):
    """ convert to a table with x y pixel coordinates

    Args:
        array (ndarray): input array

    Returns:
        table (ndarray): output table

    """
    table = np.zeros((array.shape[0] * array.shape[1], 3), array.dtype)
    for i in range(0, array.shape[0]):
        table[(array.shape[1] * i):(array.shape[1] * (i + 1)), 0] = i
        table[(array.shape[1] * i):(array.shape[1] * (i + 1)), 1] = range(0,
                                                                array.shape[1])
        table[(array.shape[1] * i):(array.shape[1] * (i + 1)), 2] = array[i, :]
    return table


def dilate(array, value=1, iterations=1):
    """ dilate a raster

    Args:
        array (ndarray): input array
        value (int): what value to dilate
        iterations (int): dilate how many pixels

    Returns:
        array (ndarray): output array

    """
    array2 = (array == value)
    array2 = nd.binary_dilation(array2,
                                iterations=iterations).astype(array2.dtype)
    array[array2] = value
    return array


def ndarray_append(array, _dtype):
    """ append a field to a structured array

    Args:
        array (ndarray): input array
        _type (dtype): dtype of the field to be appended

    Returns:
        array2 (ndarray): output array

    """
    _dtype = np.dtype(array.dtype.descr + _dtype)
    array2 = np.zeros(array.shape, dtype=_dtype)
    for x in array.dtype.names:
        array2[x] = array[x]
    return array2
