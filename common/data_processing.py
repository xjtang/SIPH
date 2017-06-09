""" Module for a set of small functions related to data processing
"""
import numpy as np


def enlarge(array, scaling):
    """ enlarge an array by a scaling factor
        by Chris Holden

    Args:
      array (ndarray): array to be scaled
      scaling (int): amount of scaling

    Returns:
      scaled (ndarray): scaled array

    """
    return np.kron(array, np.ones((scaling, scaling)))
