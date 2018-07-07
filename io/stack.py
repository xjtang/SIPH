""" Module for IO of stacked images
"""
from __future__ import division

import os
import numpy as np

from osgeo import gdal

from ..common import constants as cons
from ..common import log, tablize


def stackMerge(stacks, des, _type=gdal.GDT_Int16, overwrite=False):
    """ merge list of stacks with same spatial reference

    Args:
        stacks (list, str): path and filename of stacks
        des (str): destination
        _type (int): gdal data type
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

    # read spatial reference from first image
    geo = stackGeo(stacks[0])
    if _type == -9999:
        _type = geo['type']

    # get total number of bands
    nband = 0
    for img in stacks:
        img2 = gdal.Open(img, gdal.GA_ReadOnly)
        nband += img2.RasterCount

    # write output
    try:
        _driver = gdal.GetDriverByName('GTiff')
        if geo['samples'] * geo['lines'] > 10000 * 10000:
            output = _driver.Create(des, geo['samples'], geo['lines'], nband,
                                    _type, ['COMPRESS=PACKBITS'])
        else:
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
    except:
        log.error('Failed to write output to {}'.format(des))
        return 2

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
    geo['type'] = img2.GetRasterBand(1).DataType
    try:
        geo['nodata'] = img2.GetRasterBand(1).GetNoDataValue()
    except:
        geo['nodata'] = 'NA'
    img2 = None
    return geo


def array2stack(array, geo, des, bands='NA', nodata='NA', _type=gdal.GDT_Int16,
                overwrite=False, driver_name='GTiff', ops=[]):
    """ Save array as stack image

    Args:
        array (ndarray): array to be saved as stack image
        geo (dic): spatial reference
        des (str): destination to save the output stack image
        bands (list, str): description of each band, NA for no description
        nodata (int): nodata value
        _type (int): gdal data type
        overwrite (bool): overwrite or not
        driver_name (str): name of the output driver
        ops (list, str): options for output file

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
        _driver = gdal.GetDriverByName(driver_name)
        output = _driver.Create(des, samples, lines, nband, _type, options=ops)
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
