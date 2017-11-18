""" Module for IO of VIIRS data
"""
from __future__ import division

import os
import numpy as np

from osgeo import gdal

from . import stackGeo
from ..common import log, enlarge
from ..common import constants as cons


def modis2stack(MOD09GA, des, MOD09GQ='NA', overwrite=False, verbose=False):
    """ read MODIS surface reflectance product and convert to geotiff with
        selected bands

    Args:
        MOD09GA (str): path to input MOD09GA file
        des (str): path to output
        MOD09GQ (str): path to input MOD09GQ file
        overwrite (bool): overwrite or not
        verbose (bool): verbose or not

    Returns:
        0: successful
        1: error due to des
        2: error in reading input
        3: error in calculation
        4: error in cleaning up data
        5: error in writing output

    """
    # set destinations
    des_ga = os.path.join(des, mn2ln(os.path.basename(MOD09GA)))
    if MOD09GQ != 'NA':
        des_gq = os.path.join(des, mn2ln(os.path.basename(MOD09GQ)))

    # check if output already exists
    if (not overwrite) and os.path.isfile(des_ga):
        log.error('{} already exists.'.format(os.path.basename(des_ga)))
        return 1
    if MOD09GQ != 'NA':
        if (not overwrite) and os.path.isfile(des_gq):
            log.error('{} already exists.'.format(os.path.basename(des_gq)))
            return 1

    # read input image
    if verbose:
        log.info('Reading input: {}'.format(MOD09GA))
    try:
        mga_img = gdal.Open(MOD09GA, gdal.GA_ReadOnly)
        mga_sub = mga_img.GetSubDatasets()
        mga_vza = gdal.Open(mga_sub[cons.MGA_VZA_BAND][0], gdal.GA_ReadOnly)
        mga_qa = gdal.Open(mga_sub[cons.MGA_QA_BAND][0], gdal.GA_ReadOnly)
        mga_red = gdal.Open(mga_sub[cons.MGA_SR_BANDS[0]][0], gdal.GA_ReadOnly)
        mga_nir = gdal.Open(mga_sub[cons.MGA_SR_BANDS[1]][0], gdal.GA_ReadOnly)
        mga_swir = gdal.Open(mga_sub[cons.MGA_SR_BANDS[2]][0], gdal.GA_ReadOnly)
        mga_green = gdal.Open(mga_sub[cons.MGA_SR_BANDS[3]][0], gdal.GA_ReadOnly)
    except:
        log.error('Failed to read input {}'.format(MOD09GA))
        return 2
    if MOD09GQ != 'NA':
        if verbose:
            log.info('Reading input: {}'.format(MOD09GQ))
        try:
            mgq_img = gdal.Open(MOD09GQ, gdal.GA_ReadOnly)
            mgq_sub = mgq_img.GetSubDatasets()
            mgq_red = gdal.Open(mgq_sub[cons.MGQ_BANDS[0]][0], gdal.GA_ReadOnly)
            mgq_nir = gdal.Open(mgq_sub[cons.MGQ_BANDS[1]][0], gdal.GA_ReadOnly)
        except:
            log.error('Failed to read input {}'.format(MOD09GQ))
            return 2

    # read geo info
    if verbose:
        log.info('Reading geo information...')
    try:
        mga_geo = stackGeo(mga_sub[cons.MGA_SR_BANDS[0]][0])
        if MOD09GQ != 'NA':
            mgq_geo = stackGeo(mgq_sub[cons.MGQ_BANDS[0]][0])
    except:
        log.error('Failed to read geo info.')
        return 2

    # read actual data
    if verbose:
        log.info('Reading actual data...')
    try:
        red = mga_red.GetRasterBand(1).ReadAsArray().astype(np.int16)
        nir = mga_nir.GetRasterBand(1).ReadAsArray().astype(np.int16)
        swir = mga_swir.GetRasterBand(1).ReadAsArray().astype(np.int16)
        green = mga_green.GetRasterBand(1).ReadAsArray().astype(np.int16)
        qa = mga_qa.GetRasterBand(1).ReadAsArray().astype(np.uint16)
        vza = mga_vza.GetRasterBand(1).ReadAsArray().astype(np.int16)
        if MOD09GQ != 'NA':
            red2 = mgq_red.GetRasterBand(1).ReadAsArray().astype(np.int16)
            nir2 = mgq_nir.GetRasterBand(1).ReadAsArray().astype(np.int16)
    except:
        log.error('Failed to read data.')
        return 2

    # calculate NDVI
    if verbose:
        log.info('Calculating NDVI...')
    try:
        ndvi = ((nir-red) / (nir+red) * cons.SCALE_FACTOR).astype(np.int16)
        if MOD09GQ != 'NA':
            ndvi2 = ((nir2-red2)/(nir2+red2)*cons.SCALE_FACTOR).astype(np.int16)
    except:
        log.error('Failed to calculate NDVI.')
        return 3

    # generate mask band
    if verbose:
        log.info('Generating mask band...')
    try:
        mask = modisQA(qa)
        _total = np.sum(mask)
        _size = np.shape(mask)
        if verbose:
            log.info('{}% masked'.format(_total/(_size[0]*_size[1])*100))
        mask2 = mask | vza > 3500
    except:
        log.error('Failed to generate mask band.')
        return 3

    # clean up data
    if verbose:
        log.info('Cleaning up data...')
    try:
        invalid = ~(((red>0) & (red<=10000)) & ((nir>0) & (nir<=10000)))
        red[invalid] = cons.NODATA
        nir[invalid] = cons.NODATA
        ndvi[invalid] = cons.NODATA
        vza[~((vza >= 0) & (vza <= 18000))] = cons.NODATA
        if MOD09GQ != 'NA':
            invalid = ~(((red2>0) & (red2<=10000)) & ((nir2>0) & (nir2<=10000)))
            red2[invalid] = cons.NODATA
            nir2[invalid] = cons.NODATA
            ndvi2[invalid] = cons.NODATA
    except:
        log.error('Failed to clean up data.')
        return 4

    # write output
    if verbose:
        log.info('Writing output: {}'.format(des_ga))
    try:
        # initialize output
        _driver = gdal.GetDriverByName('GTiff')
        output = _driver.Create(des_ga, mga_geo['samples'], mga_geo['lines'],
                                8, gdal.GDT_Int16)
        output.SetProjection(mga_geo['proj'])
        output.SetGeoTransform(mga_geo['geotrans'])
        output.GetRasterBand(1).SetNoDataValue(cons.NODATA)
        # write output
        output.GetRasterBand(1).WriteArray(red)
        output.GetRasterBand(2).WriteArray(nir)
        output.GetRasterBand(3).WriteArray(swir)
        output.GetRasterBand(4).WriteArray(green)
        output.GetRasterBand(5).WriteArray(ndvi)
        output.GetRasterBand(6).WriteArray(enlarge(vza, 2))
        output.GetRasterBand(7).WriteArray(enlarge(mask, 2))
        output.GetRasterBand(7).WriteArray(enlarge(mask2, 2))
        # assign band name
        output.GetRasterBand(1).SetDescription('MODIS 500m Red')
        output.GetRasterBand(2).SetDescription('MODIS 500m NIR')
        output.GetRasterBand(3).SetDescription('MODIS 500m SWIR')
        output.GetRasterBand(4).SetDescription('MODIS 500m GREEN')
        output.GetRasterBand(5).SetDescription('MODIS 500m NDVI')
        output.GetRasterBand(6).SetDescription('MODIS 1km VZA')
        output.GetRasterBand(7).SetDescription('MODIS 1km MASK')
        output.GetRasterBand(7).SetDescription('MODIS 1km MASK with VZA')
    except:
        log.error('Failed to write output to {}'.format(des_ga))
        return 5
    if MOD09GQ != 'NA':
        if verbose:
            log.info('Writing output: {}'.format(des_gq))
        try:
            # initialize output
            _driver = gdal.GetDriverByName('GTiff')
            output = _driver.Create(des_gq, mgq_geo['samples'],
                                    mgq_geo['lines'], 8, gdal.GDT_Int16)
            output.SetProjection(mgq_geo['proj'])
            output.SetGeoTransform(mgq_geo['geotrans'])
            output.GetRasterBand(1).SetNoDataValue(cons.NODATA)
            # write output
            output.GetRasterBand(1).WriteArray(red2)
            output.GetRasterBand(2).WriteArray(nir2)
            output.GetRasterBand(3).WriteArray(enlarge(swir, 2))
            output.GetRasterBand(4).WriteArray(enlarge(green, 2))
            output.GetRasterBand(5).WriteArray(ndvi2)
            output.GetRasterBand(6).WriteArray(enlarge(vza, 4))
            output.GetRasterBand(7).WriteArray(enlarge(mask, 4))
            output.GetRasterBand(8).WriteArray(enlarge(mask2, 4))
            # assign band name
            output.GetRasterBand(1).SetDescription('MODIS 250m Red')
            output.GetRasterBand(2).SetDescription('MODIS 250m NIR')
            output.GetRasterBand(3).SetDescription('MODIS 500m SWIR')
            output.GetRasterBand(4).SetDescription('MODIS 500m GREEN')
            output.GetRasterBand(5).SetDescription('MODIS 250m NDVI')
            output.GetRasterBand(6).SetDescription('MODIS 1km VZA')
            output.GetRasterBand(7).SetDescription('MODIS 1km Mask')
            output.GetRasterBand(7).SetDescription('MODIS 1km MASK with VZA')
        except:
            log.error('Failed to write output to {}'.format(des_gq))
            return 5

    # close files
    if verbose:
        log.info('Closing files...')
    mga_img = None
    mga_red = None
    mga_nir = None
    mga_swir = None
    mga_green = None
    mga_qa = None
    mga_vza = None
    mgq_img = None
    mgq_red = None
    mgq_nir = None
    output = None

    # done
    if verbose:
        log.info('Process completed.')
    return 0


def modisQA(qa):
    """ intepret MODISA and return a mask array

    Args:
        qa (ndarray): QA array

    Returns:
        mask (ndarray): mask array

    """
    mask = (np.mod(np.mod(qa, 4), 3) | np.mod(np.right_shift(qa, 2), 2) |
            (np.mod(np.right_shift(qa, 6), 4) == 3) |
            np.mod(np.right_shift(qa, 9), 2) |
            np.mod(np.right_shift(qa, 10), 2) |
            np.mod(np.right_shift(qa, 13), 2)) > 0
    return mask


def mn2ln(mn):
    """ convert MODIS style file name to Landsat style
        file name only, regardless of file type extension
        e.g. MOD09GA.A2014001.h12v09.001.2017064050806
        MOD09A1.A2006001.h08v05.005.2006012234657.hdf
             to MOD0120092014001109GA (MOD 0hh 0vv yyyyddd c pppp)

    Args:
        mn (str): MODIS style file name

    Returns:
        ln (str): Landsat style file name

    """
    mn = mn.split('.')
    return '{}0{}0{}{}{}{}'.format(mn[0][0:3], mn[2][1:3], mn[2][4:6],
                                    mn[1][1:], mn[3][-1], mn[0][3:])


def modis2composite(MOD, MYD, des, overwrite=False, verbose=False):
    return 0
