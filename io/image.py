""" Module for IO of regular image files
"""
from __future__ import division

import os
import numpy as np

from PIL import Image, ImageFont, ImageDraw

from . import stack2array
from ..common import constants as cons
from ..common import (log, apply_mask, result2mask, crop, get_date, tablize,
                        apply_stretch, sidebyside, nodata_mask, thematic_map)


def stack2image(img, des, bands=[3,2,1], stretch=[0,5000], mask=0, result='NA',
                rvalue=0, _format='rgb', window=0, overwrite=False,
                verbose=False):
    """ Convert stacked image to regular image file (e.g. png)

    Args:
        img (str): the link to the gtif image file
        des (str): destination to save the output preview image
        bands (list, int): band composite, [red, green, blue]
        stretch (list, int): stretch, [min, max]
        mask (int): mask band, 0 for no mask
        result (str): the link to result image if needed
        rvalue (int): result value, 0 to use date
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
            if rvalue == 0:
                result_array = result2mask(stack2array(result, 1, np.int32),
                                            get_date(img.split('/')[-1]))
            else:
                result_array = result2mask(stack2array(result, 1, np.int32),
                                            rvalue)
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
            nodata_array = nodata_mask(array)
            array = apply_mask(array, nodata_array, (stretch[0], stretch[0], stretch[0]))
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
        elif _format == 'hls':
            array1 = apply_stretch(array, stretch)
            array2 = np.copy(array1)
            if type(mask_array) == np.ndarray:
                array2 = thematic_map(mask_array, cons.MASK_VALUES,
                                        cons.MASK_COLORS, array2)
            output = sidebyside(array1, array2)
        else:
            log.error('Unknown format: {}'.format(_format))
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
    if verbose:
        log.info('Process completed.')
    return 0


def addTextToImage(ori, des, text, overwrite=False, verbose=False):
    """ Convert stacked image to regular image file (e.g. png)

    Args:
        img (str): the link to the image file
        des (str): destination to save the output image
        text (str): text to add
        overwrite (bool): overwrite or not
        verbose (bool): verbose or not

    Returns:
        0: successful
        1: error due to des
        2: error due to processing

    """
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(des.split('/')[-1]))
        return 1

    # read iamge
    if verbose:
        log.info('Adding text to image...')
    try:
        img = Image.open(ori)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(cons.TEXT_FONT, cons.TEXT_SIZE)
        TEXT_POS = (img.size[0] - cons.TEXT_SIZE * 10 / 2,
                    img.size[1] - cons.TEXT_SIZE * 3 / 2)
        draw.text(TEXT_POS, text, cons.TEXT_COL, font=font)
        img.save(des)
    except:
        log.error('Failed to process image {}'.format(ori))
        return 2

    # done
    if verbose:
        log.info('Process completed.')
    return 0
