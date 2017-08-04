""" Module for IO of stacked images
"""
from __future__ import division

import os
import numpy as np

from osgeo import gdal
from PIL import Image

from ..common import (log, apply_mask, result2mask, crop, get_date,
                        apply_stretch, sidebyside)


def stack2array(img, band=1, _type=np.int16):
    """ Convert stacked image to rgb picture file (e.g. png)

    Args:
        img (str): the link to the image stack file
        band (list, int): what band to read

    Returns:
        array: array of image data

    """
    img2 = gdal.Open(img, gdal.GA_ReadOnly)
    if type(band) == int:
        array = img2.GetRasterBand(band).ReadAsArray().astype(_type)
    else:
        array = np.zeros((img2.RasterYSize, img2.RasterXSize,
                            len(band))).astype(_type)
        for i, x in enumerate(band):
            array[:,:,i] = img2.GetRasterBand(x).ReadAsArray().astype(_type)
    img2 = None
    return array


def stack2image(img, des, bands=[3,2,1], stretch=[0,5000], mask=0, result='NA',
                _format='rgb', window=0, overwrite=False, verbose=False):
    """ Convert stacked image to regular image file (e.g. png)

    Args:
        img (str): the link to the gtif image file
        des (str): destination to save the output preview image
        bands (list, int): band composite, [red, green, blue]
        stretch (list, int): stretch, [min, max]
        mask (int): mask band, 0 for no mask
        result (str): the link to result image if needed
        _format (str): format of output image, e.g. rgb, grey, combo
        window(list, int): chop image, [xmin, ymin, xmax, ymax], 0 for no chop
        overwrite (bool): overwrite or not
        verbose (bool): verbose or not

    Returns:
        0: successful
        1: error due to des
        2: error in reading image
        3: error due to chopping
        4: error due to generation of output image
        5: error due to writing output

    """
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(des.split('/')[-1]))
        return 1

    # read iamge
    if verbose:
        log.info('Reading input image stack...')
    try:
        # read spectral image
        array = stack2array(img, bands)
        # read mask
        if mask > 0:
            mask_array = stack2array(img, mask, np.uint8)
        else:
            mask_array = 'NA'
        # read result layer
        if result != 'NA':
            result_array = result2mask(stack2array(result, 1, np.int32),
                                        get_date(img.split('/')[-1]))
        else:
            result_array = 'NA'
    except:
        log.error('Failed to read input stack {}'.format(img))
        return 2

    # chopping image
    if type(window) == list:
        if verbose:
            log.info('Chopping image...')
        try:
            array = crop(array, window)
            if type(mask_array) == np.ndarray:
                mask_array = crop(mask_array, window)
            if type(result_array) == np.ndarray:
                result_array = crop(result_array, window)
        except:
            log.error('Failed to chop image {}'.format(window))
            return 3

    # generate output image
    if verbose:
        log.info('Generating output image...')
    try:
        if _format == 'rgb':
            output = apply_stretch(array, stretch)
            if type(mask_array) == np.ndarray:
                output = apply_mask(output, mask_array)
            if type(result_array) == np.ndarray:
                output = apply_mask(output, result_array)
        elif _format == 'combo':
            array1 = apply_stretch(array, stretch)
            array2 = np.array(array1)
            if type(mask_array) == np.ndarray:
                array2 = apply_mask(array2, mask_array)
            if type(result_array) == np.ndarray:
                array2 = apply_mask(array2, result_array)
            output = sidebyside(array1, array2)
        elif _format == 'abs':
            array = abs(array)
            output = apply_stretch(array, stretch)
            if type(mask_array) == np.ndarray:
                output = apply_mask(output, mask_array)
            if type(result_array) == np.ndarray:
                output = apply_mask(output, result_array)
        else:
            log.error('Unkown format: {}'.format(_format))
            return 4
    except:
        log.error('Failed to generate output image: {}'.format(_format))
        return 4

    # write output
    if verbose:
        log.info('Writing output...')
    try:
        img_out = Image.fromarray(output, 'RGB')
        img_out.save(des)
        img_out = None
    except:
        log.error('Failed to write output to {}'.format(des))
        return 5

    # done
    log.info('Process completed.')
    return 0
