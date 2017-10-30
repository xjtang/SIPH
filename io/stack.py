""" Module for IO of stacked images
"""
from __future__ import division

import os
import numpy as np

from osgeo import gdal
from PIL import Image

from ..common import constants as cons
from ..common import (log, apply_mask, result2mask, crop, get_date, tablize,
                        apply_stretch, sidebyside, nodata_mask, thematic_map)


def stackMerge(stacks, des, _type=gdal.GDT_Int16, overwrite=False):
    """ merge list of stacks with same spatial reference

    Args:
        stacks (list, str): path and filename of stacks

    Returns:
        0: successful
        1: output already exists
        2: error during process

    """
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(des))
        return 1

    # read spatial reference from first image
    geo = stackGeo(stacks[0])

    # get total number of bands
    nband = 0
    for img in stacks:
        img2 = gdal.Open(img, gdal.GA_ReadOnly)
        nband += img2.RasterCount

    # write output
    _driver = gdal.GetDriverByName('GTiff')
    output = _driver.Create(des, geo['samples'], geo['lines'], nband, _type)
    output.SetProjection(geo['proj'])
    output.SetGeoTransform(geo['geotrans'])
    count = 1
    for img in stacks:
        img2 = gdal.Open(img, gdal.GA_ReadOnly)
        for i in range(0, img2.RasterCount):
            array = img2.GetRasterBand(i+1).ReadAsArray()
            nodata = img2.GetRasterBand(i+1).GetNoDataValue()
            band = img2.GetRasterBand(i+1).GetDescription()
            output.GetRasterBand(count).WriteArray(array)
            output.GetRasterBand(count).SetNoDataValue(nodata)
            output.GetRasterBand(count).SetDescription(band)
            count += 1

    # done
    return 0


def stackGeo(img):
    """ grab spatial reference from image file

    Args:
        img (str): the link to the image stack file

    Returns:
        geo (dic): sptial reference

    """
    img2 = gdal.Open(img, gdal.GA_ReadOnly)
    geo = {'proj': img2.GetProjection()}
    geo['geotrans'] = img2.GetGeoTransform()
    geo['lines'] = img2.RasterYSize
    geo['samples'] = img2.RasterXSize
    geo['bands'] = img2.RasterCount
    img2 = None
    return geo


def array2stack(array, geo, des, bands='NA', nodata='NA', _type=gdal.GDT_Int16,
                overwrite=False):
    """ Save array as stack image

    Args:
        array (ndarray): array to be saved as stack image
        geo (dic): spatial reference
        des (str): destination to save the output stack image
        bands (list, str): description of each band, NA for no description
        nodata (int): nodata value
        _type (object): gdal data type
        overwrite (bool): overwrite or not

    Returns:
        0: successful
        1: output already exists
        2: error during process

    """
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(des))
        return 1

    # get array dimensions
    if len(array.shape) == 3:
        (lines, samples, nband) = array.shape
    else:
        (lines, samples) = array.shape
        nband = 1

    # write output
    try:
        _driver = gdal.GetDriverByName('GTiff')
        output = _driver.Create(des, samples, lines, nband, _type)
        output.SetProjection(geo['proj'])
        output.SetGeoTransform(geo['geotrans'])
        for i in range(0, nband):
            if nband > 1:
                output.GetRasterBand(i+1).WriteArray(array[:,:,i])
            else:
                output.GetRasterBand(i+1).WriteArray(array)
            if not nodata == 'NA':
                output.GetRasterBand(i+1).SetNoDataValue(nodata)
            if not bands == 'NA':
                if type(bands) == str:
                    bands = [bands]
                output.GetRasterBand(i+1).SetDescription(bands[i])
    except:
        log.error('Failed to write output to {}'.format(des))
        return 2

    # done
    return 0


def stack2array(img, band=0, _type=np.int16):
    """ Convert stacked image to rgb picture file (e.g. png)

    Args:
        img (str): the link to the image stack file
        band (list, int): what band to read, 0 for all bands
        _type (object): numpy data type

    Returns:
        array (ndarray): array of image data

    """
    img2 = gdal.Open(img, gdal.GA_ReadOnly)
    if type(band) == int:
        if band == 0:
            nband = img2.RasterCount
            if nband == 1:
                array = img2.GetRasterBand(1).ReadAsArray().astype(_type)
            else:
                array = np.zeros((img2.RasterYSize, img2.RasterXSize,
                                    nband)).astype(_type)
                for i in range(0, nband):
                    array[:,:,i] = img2.GetRasterBand(i +
                                    1).ReadAsArray().astype(_type)
        else:
            array = img2.GetRasterBand(band).ReadAsArray().astype(_type)
    else:
        array = np.zeros((img2.RasterYSize, img2.RasterXSize,
                            len(band))).astype(_type)
        for i, x in enumerate(band):
            array[:,:,i] = img2.GetRasterBand(x).ReadAsArray().astype(_type)
    img2 = None
    return array


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


def stack2table(img, band=1, nodata=cons.MASK_NODATA, _type=np.int16):
    """ read stack image and convert to a table with x y pixel coordinates

    Args:
        img (str): the link to the image stack file
        band (int): what band to read, one band only
        nodata (int): nodata value
        _type (object): numpy data type

    Returns:
        table (ndarray): table of image data

    """
    array = stack2array(img, band, _type)
    table = tablize(array)
    return table[table[:, 2] != nodata, :]
