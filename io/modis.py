""" Module for IO of VIIRS data
"""
from __future__ import division

import os
import numpy as np

from osgeo import gdal

from . import stackGeo, stack2array, array2stack
from ..common import log, enlarge, reclassify
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
    des_ga = os.path.join(des,'{}.tif'.format(mn2ln(os.path.basename(MOD09GA))))
    if MOD09GQ != 'NA':
        des_gq = os.path.join(des,
                            '{}.tif'.format(mn2ln(os.path.basename(MOD09GQ))))

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
        mga_swir2 = gdal.Open(mga_sub[cons.MGA_SR_BANDS[3]][0], gdal.GA_ReadOnly)
        mga_green = gdal.Open(mga_sub[cons.MGA_SR_BANDS[4]][0], gdal.GA_ReadOnly)
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
        swir2 = mga_swir2.GetRasterBand(1).ReadAsArray().astype(np.int16)
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
        mask2 = mask | (vza > 3500)
    except:
        log.error('Failed to generate mask band.')
        return 3

    # clean up data
    # if verbose:
    #     log.info('Cleaning up data...')
    # try:
    #     invalid = ~(((red>0) & (red<=10000)) & ((nir>0) & (nir<=10000)))
    #     red[invalid] = cons.NODATA
    #     nir[invalid] = cons.NODATA
    #     ndvi[invalid] = cons.NODATA
    #     vza[~((vza >= 0) & (vza <= 18000))] = cons.NODATA
    #     if MOD09GQ != 'NA':
    #         invalid = ~(((red2>0) & (red2<=10000)) & ((nir2>0) & (nir2<=10000)))
    #         red2[invalid] = cons.NODATA
    #         nir2[invalid] = cons.NODATA
    #         ndvi2[invalid] = cons.NODATA
    # except:
    #     log.error('Failed to clean up data.')
    #     return 4

    # write output
    if verbose:
        log.info('Writing output: {}'.format(des_ga))
    try:
        # initialize output
        _driver = gdal.GetDriverByName('GTiff')
        output = _driver.Create(des_ga, mga_geo['samples'], mga_geo['lines'],
                                9, gdal.GDT_Int16)
        output.SetProjection(mga_geo['proj'])
        output.SetGeoTransform(mga_geo['geotrans'])
        output.GetRasterBand(1).SetNoDataValue(cons.NODATA)
        # write output
        output.GetRasterBand(1).WriteArray(red)
        output.GetRasterBand(2).WriteArray(nir)
        output.GetRasterBand(3).WriteArray(swir)
        output.GetRasterBand(4).WriteArray(swir2)
        output.GetRasterBand(5).WriteArray(green)
        output.GetRasterBand(6).WriteArray(ndvi)
        output.GetRasterBand(7).WriteArray(enlarge(vza, 2))
        output.GetRasterBand(8).WriteArray(enlarge(mask, 2))
        output.GetRasterBand(9).WriteArray(enlarge(mask2, 2))
        # assign band name
        output.GetRasterBand(1).SetDescription('MODIS 500m Red')
        output.GetRasterBand(2).SetDescription('MODIS 500m NIR')
        output.GetRasterBand(3).SetDescription('MODIS 500m SWIR')
        output.GetRasterBand(4).SetDescription('MODIS 500m SWIR2')
        output.GetRasterBand(5).SetDescription('MODIS 500m GREEN')
        output.GetRasterBand(6).SetDescription('MODIS 500m NDVI')
        output.GetRasterBand(7).SetDescription('MODIS 1km VZA')
        output.GetRasterBand(8).SetDescription('MODIS 1km MASK')
        output.GetRasterBand(9).SetDescription('MODIS 1km MASK with VZA')
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
                                    mgq_geo['lines'], 9, gdal.GDT_Int16)
            output.SetProjection(mgq_geo['proj'])
            output.SetGeoTransform(mgq_geo['geotrans'])
            output.GetRasterBand(1).SetNoDataValue(cons.NODATA)
            # write output
            output.GetRasterBand(1).WriteArray(red2)
            output.GetRasterBand(2).WriteArray(nir2)
            output.GetRasterBand(3).WriteArray(enlarge(swir, 2))
            output.GetRasterBand(4).WriteArray(enlarge(swir2, 2))
            output.GetRasterBand(5).WriteArray(enlarge(green, 2))
            output.GetRasterBand(6).WriteArray(ndvi2)
            output.GetRasterBand(7).WriteArray(enlarge(vza, 4))
            output.GetRasterBand(8).WriteArray(enlarge(mask, 4))
            output.GetRasterBand(9).WriteArray(enlarge(mask2, 4))
            # assign band name
            output.GetRasterBand(1).SetDescription('MODIS 250m Red')
            output.GetRasterBand(2).SetDescription('MODIS 250m NIR')
            output.GetRasterBand(3).SetDescription('MODIS 500m SWIR')
            output.GetRasterBand(4).SetDescription('MODIS 500m SWIR2')
            output.GetRasterBand(5).SetDescription('MODIS 500m GREEN')
            output.GetRasterBand(6).SetDescription('MODIS 250m NDVI')
            output.GetRasterBand(7).SetDescription('MODIS 1km VZA')
            output.GetRasterBand(8).SetDescription('MODIS 1km Mask')
            output.GetRasterBand(9).SetDescription('MODIS 1km MASK with VZA')
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
    mga_swir2 = None
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
    mask[qa==65535] = cons.NODATA
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
    if mn[0][5] == 'C':
        return '{}CMG005{}{}{}'.format(mn[0][0:3], mn[1][1:], mn[2][-1],
                                        mn[0][3:])
    else:
        return '{}0{}0{}{}{}{}'.format(mn[0][0:3], mn[2][1:3], mn[2][4:6],
                                        mn[1][1:], mn[3][-1], mn[0][3:])


def modis2composite(MOD, MYD, des, overwrite=False, verbose=False):
    """ create composit out of pairs of MODIS images

    Args:
        MOD (str): path to input Terra image
        MYD (str): path to input Aqua image
        des (str): path to output
        overwrite (bool): overwrite or not
        verbose (bool): verbose or not

    Returns:
        0: successful
        1: error due to des
        2: error in reading input
        3: error in calculation
        4: error in writing output

    """
    # check if output already exists
    des = os.path.join(des, 'COM{}'.format(os.path.basename(MOD)[3:]))
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(os.path.basename(des)))
        return 1

    # read input files
    if verbose:
        log.info('Reading input images...')
    try:
        terra = stack2array(MOD)
        aqua = stack2array(MYD)
        geo = stackGeo(MOD)
    except:
        log.error('Failed to read input image.')
        return 2

    # calculating output
    if verbose:
        log.info('Making composite...')
    try:
        comp = np.zeros(terra.shape, np.int16)
        for i in range(0, terra.shape[0]):
            for j in range(0,terra.shape[1]):
                if aqua[i, j, 5] == cons.NODATA:
                    comp[i, j, :] = terra[i, j, :]
                else:
                    if terra[i, j, 5] == cons.NODATA:
                        comp[i, j, :] = aqua[i, j, :]
                    else:
                        if aqua[i, j, 8] == 1:
                            comp[i, j, :] = terra[i, j, :]
                        else:
                            if terra[i, j, 8] == 1:
                                comp[i, j, :] = aqua[i, j, :]
                            else:
                                if terra[i, j, 6] == cons.NODATA:
                                    terra[i, j, 6] = 20000
                                if aqua[i, j, 6] == cons.NODATA:
                                    aqua[i, j, 6] = 20000
                                if terra[i, j, 6] > aqua[i, j, 6]:
                                    comp[i, j, :] = aqua[i, j, :]
                                else:
                                    comp[i, j, :] = terra[i, j, :]
    except:
        log.error('Failed to make composit.')
        return 3

    # writing output
    if verbose:
        log.info('Writing output: {}'.format(des))
    bands = ['Composite Red', 'Composite, NIR', 'Composite, SWIR',
                'Composite Green', 'Composite NDVI', 'Composite VZA',
                'Composite Mask', 'Composite Mask with VZA']
    if array2stack(comp, geo, des, bands, cons.NODATA, gdal.GDT_Int16,
                    overwrite) > 0:
         log.error('Failed to write output to {}'.format(des))
         return 4

    # done
    if verbose:
        log.info('Process completed.')
    return 0


def modisvi2stack(VI, des, overwrite=False, verbose=False):
    """ read MODIS vegetation index product and convert to geotiff

    Args:
        VI (str): path to input MxD13x1 file
        des (str): path to output
        overwrite (bool): overwrite or not
        verbose (bool): verbose or not

    Returns:
        0: successful
        1: error due to des
        2: error in reading input
        3: error in QA
        4: error in cleaning up data
        5: error in writing output

    """
    # set destinations
    des_vi = os.path.join(des,'{}.tif'.format(mn2ln(os.path.basename(VI))))

    # check if output already exists
    if (not overwrite) and os.path.isfile(des_vi):
        log.error('{} already exists.'.format(os.path.basename(des_vi)))
        return 1

    # read input image
    if verbose:
        log.info('Reading input: {}'.format(VI))
    try:
        vi_img = gdal.Open(VI, gdal.GA_ReadOnly)
        vi_sub = vi_img.GetSubDatasets()
        vi_ndvi = gdal.Open(vi_sub[cons.MVI_BANDS[0]][0], gdal.GA_ReadOnly)
        vi_evi = gdal.Open(vi_sub[cons.MVI_BANDS[1]][0], gdal.GA_ReadOnly)
        vi_red = gdal.Open(vi_sub[cons.MVI_BANDS[2]][0], gdal.GA_ReadOnly)
        vi_nir = gdal.Open(vi_sub[cons.MVI_BANDS[3]][0], gdal.GA_ReadOnly)
        vi_swir = gdal.Open(vi_sub[cons.MVI_BANDS[4]][0], gdal.GA_ReadOnly)
        vi_blue = gdal.Open(vi_sub[cons.MVI_BANDS[5]][0], gdal.GA_ReadOnly)
        vi_qa = gdal.Open(vi_sub[cons.MVI_BANDS[6]][0], gdal.GA_ReadOnly)
    except:
        log.error('Failed to read input {}'.format(VI))
        return 2

    # read geo info
    if verbose:
        log.info('Reading geo information...')
    try:
        vi_geo = stackGeo(vi_sub[cons.MVI_BANDS[0]][0])
    except:
        log.error('Failed to read geo info.')
        return 2

    # read actual data
    if verbose:
        log.info('Reading actual data...')
    try:
        ndvi = vi_ndvi.GetRasterBand(1).ReadAsArray().astype(np.int16)
        evi = vi_evi.GetRasterBand(1).ReadAsArray().astype(np.int16)
        red = vi_red.GetRasterBand(1).ReadAsArray().astype(np.int16)
        nir = vi_nir.GetRasterBand(1).ReadAsArray().astype(np.int16)
        swir = vi_swir.GetRasterBand(1).ReadAsArray().astype(np.uint16)
        blue = vi_blue.GetRasterBand(1).ReadAsArray().astype(np.int16)
        qa = vi_qa.GetRasterBand(1).ReadAsArray().astype(np.int16)
    except:
        log.error('Failed to read data.')
        return 2

    # generate mask band
    if verbose:
        log.info('Generating mask band...')
    try:
        mask = (qa!=0)
        _total = np.sum(mask)
        _size = np.shape(mask)
        if verbose:
            log.info('{}% masked'.format(_total/(_size[0]*_size[1])*100))
    except:
        log.error('Failed to generate mask band.')
        return 3

    # clean up data
    # if verbose:
    #     log.info('Cleaning up data...')
    # try:
    #     invalid = ~(((red>0) & (red<=10000)) & ((nir>0) & (nir<=10000)))
    #     red[invalid] = cons.NODATA
    #     nir[invalid] = cons.NODATA
    #     swir[invalid] = cons.NODATA
    #     blue[invalid] = cons.NODATA
    #     ndvi[invalid] = cons.NODATA
    #     evi[invalid] = cons.NODATA
    # except:
    #     log.error('Failed to clean up data.')
    #     return 4

    # write output
    if verbose:
        log.info('Writing output: {}'.format(des_vi))
    try:
        # initialize output
        _driver = gdal.GetDriverByName('GTiff')
        output = _driver.Create(des_vi, vi_geo['samples'], vi_geo['lines'], 7,
                                gdal.GDT_Int16)
        output.SetProjection(vi_geo['proj'])
        output.SetGeoTransform(vi_geo['geotrans'])
        output.GetRasterBand(1).SetNoDataValue(cons.NODATA)
        # write output
        output.GetRasterBand(1).WriteArray(ndvi)
        output.GetRasterBand(2).WriteArray(evi)
        output.GetRasterBand(3).WriteArray(red)
        output.GetRasterBand(4).WriteArray(nir)
        output.GetRasterBand(5).WriteArray(swir)
        output.GetRasterBand(6).WriteArray(blue)
        output.GetRasterBand(7).WriteArray(mask)
        # assign band name
        output.GetRasterBand(1).SetDescription('MODIS VI 16day NDVI')
        output.GetRasterBand(2).SetDescription('MODIS VI 16day EVI')
        output.GetRasterBand(3).SetDescription('MODIS VI 16day Red')
        output.GetRasterBand(4).SetDescription('MODIS VI 16day NIR')
        output.GetRasterBand(5).SetDescription('MODIS VI 16day SWIR')
        output.GetRasterBand(6).SetDescription('MODIS VI 16day Blue')
        output.GetRasterBand(7).SetDescription('MODIS VI 16day MASK')
    except:
        log.error('Failed to write output to {}'.format(des_vi))
        return 5

    # close files
    if verbose:
        log.info('Closing files...')
    vi_img = None
    vi_red = None
    vi_nir = None
    vi_swir = None
    vi_blue = None
    vi_ndvi = None
    vi_evi = None
    vi_qa = None
    output = None

    # done
    if verbose:
        log.info('Process completed.')
    return 0


def modislc2stack(LC, des, mergeclass=False, overwrite=False, verbose=False):
    """ read MODIS land cover product and convert to geotiff

    Args:
        LC (str): path to input MxD13x1 file
        des (str): path to output
        mergeclass (bool): merge class or not
        overwrite (bool): overwrite or not
        verbose (bool): verbose or not

    Returns:
        0: successful
        1: error due to des
        2: error in reading input
        3: error in merging class
        4: error in writing output

    """
    # set destinations
    des_lc = os.path.join(des,'{}.tif'.format(mn2ln(os.path.basename(LC))))

    # check if output already exists
    if (not overwrite) and os.path.isfile(des_lc):
        log.error('{} already exists.'.format(os.path.basename(des_lc)))
        return 1

    # read input image
    if verbose:
        log.info('Reading input: {}'.format(LC))
    try:
        lc_img = gdal.Open(LC, gdal.GA_ReadOnly)
        lc_sub = lc_img.GetSubDatasets()
        lc_igbp = gdal.Open(lc_sub[cons.MLC_BAND][0], gdal.GA_ReadOnly)
    except:
        log.error('Failed to read input {}'.format(LC))
        return 2

    # read geo info
    if verbose:
        log.info('Reading geo information...')
    try:
        lc_geo = stackGeo(lc_sub[cons.MLC_BAND][0])
    except:
        log.error('Failed to read geo info.')
        return 2

    # read actual data
    if verbose:
        log.info('Reading actual data...')
    try:
        igbp = lc_igbp.GetRasterBand(1).ReadAsArray().astype(np.int8)
    except:
        log.error('Failed to read data.')
        return 2

    # clean up data
    if mergeclass:
        if verbose:
            log.info('Merging class')
        try:
            igbp = reclassify(igbp, cons.MLC_RECLASS)
        except:
            log.error('Failed to merge class.')
            return 3

    # write output
    if verbose:
        log.info('Writing output: {}'.format(lc_vi))
    try:
        # initialize output
        _driver = gdal.GetDriverByName('GTiff')
        output = _driver.Create(des_lc, lc_geo['samples'], lc_geo['lines'], 1,
                                gdal.GDT_Int16)
        output.SetProjection(lc_geo['proj'])
        output.SetGeoTransform(lc_geo['geotrans'])
        output.GetRasterBand(1).SetNoDataValue(255)
        # write output
        output.GetRasterBand(1).WriteArray(igbp)
        # assign band name
        if mergeclass:
            output.GetRasterBand(1).SetDescription('MODIS Land Cover Merged')
        else:
            output.GetRasterBand(1).SetDescription('MODIS Land Cover IGBP')
    except:
        log.error('Failed to write output to {}'.format(lc_vi))
        return 4

    # close files
    if verbose:
        log.info('Closing files...')
    lc_img = None
    lc_igbp = None
    output = None

    # done
    if verbose:
        log.info('Process completed.')
    return 0


def pheno2stack(pheno, des, overwrite=False, verbose=False):
    """ read MODIS phenology product and convert to geotiff

    Args:
        pheno (str): path to input MCD12Q2 file
        des (str): path to output
        overwrite (bool): overwrite or not
        verbose (bool): verbose or not

    Returns:
        0: successful
        1: error due to des
        2: error in reading input
        3: error in calculating indices

    """
    # set destinations
    des_pheno = os.path.join(des,
                                '{}.tif'.format(mn2ln(os.path.basename(pheno))))

    # check if output already exists
    if (not overwrite) and os.path.isfile(des_pheno):
        log.error('{} already exists.'.format(os.path.basename(des_pheno)))
        return 1

    # read input image
    if verbose:
        log.info('Reading input: {}'.format(pheno))
    try:
        pheno_img = gdal.Open(pheno, gdal.GA_ReadOnly)
        pheno_sub = pheno_img.GetSubDatasets()
        pheno_inc = gdal.Open(pheno_sub[0][0], gdal.GA_ReadOnly)
        pheno_max = gdal.Open(pheno_sub[1][0], gdal.GA_ReadOnly)
        pheno_dec = gdal.Open(pheno_sub[2][0], gdal.GA_ReadOnly)
        pheno_min = gdal.Open(pheno_sub[3][0], gdal.GA_ReadOnly)
    except:
        log.error('Failed to read input {}'.format(pheno))
        return 2

    # read geo info
    if verbose:
        log.info('Reading geo information...')
    try:
        geo = stackGeo(pheno_sub[0][0])
    except:
        log.error('Failed to read geo info.')
        return 2

    # read actual data
    if verbose:
        log.info('Reading actual data...')
    try:
        inc = pheno_inc.GetRasterBand(1).ReadAsArray().astype(np.int16)
        _max = pheno_max.GetRasterBand(1).ReadAsArray().astype(np.int16)
        dec = pheno_dec.GetRasterBand(1).ReadAsArray().astype(np.int16)
        _min = pheno_min.GetRasterBand(1).ReadAsArray().astype(np.int16)
    except:
        log.error('Failed to read data.')
        return 2

    # write output
    if verbose:
        log.info('Writing output: {}'.format(des_nbar))
    try:
        # initialize output
        _driver = gdal.GetDriverByName('GTiff')
        output = _driver.Create(des_pheno, geo['samples'], geo['lines'], 4,
                                gdal.GDT_Int16)
        output.SetProjection(geo['proj'])
        output.SetGeoTransform(geo['geotrans'])
        output.GetRasterBand(1).SetNoDataValue(32767)
        output.GetRasterBand(2).SetNoDataValue(32767)
        output.GetRasterBand(3).SetNoDataValue(32767)
        output.GetRasterBand(4).SetNoDataValue(32767)
        # write output
        output.GetRasterBand(1).WriteArray(inc)
        output.GetRasterBand(2).WriteArray(_max)
        output.GetRasterBand(3).WriteArray(dec)
        output.GetRasterBand(4).WriteArray(_min)
        # assign band name
        output.GetRasterBand(1).SetDescription('MODIS Greenness Increase')
        output.GetRasterBand(2).SetDescription('MODIS Greenness Maximum')
        output.GetRasterBand(3).SetDescription('MODIS Greenness Decrease')
        output.GetRasterBand(4).SetDescription('MODIS Greenness Minimum')
    except:
        log.error('Failed to write output to {}'.format(des_nbar))
        return 3

    # close files
    if verbose:
        log.info('Closing files...')
    pheno_img = None
    pheno_inc = None
    pheno_max = None
    pheno_dec = None
    pheno_min = None
    output = None

    # done
    if verbose:
        log.info('Process completed.')
    return 0


def nbar2stack(nbar, des, overwrite=False, verbose=False):
    """ read MODIS NBAR product and convert to geotiff

    Args:
        nbar (str): path to input MCD43A4 file
        des (str): path to output
        overwrite (bool): overwrite or not
        verbose (bool): verbose or not

    Returns:
        0: successful
        1: error due to des
        2: error in reading input
        3: error in calculating indices
        4: error in generating mask
        5: error in writing output

    """
    # set destinations
    des_nbar = os.path.join(des,'{}.tif'.format(mn2ln(os.path.basename(nbar))))

    # check if output already exists
    if (not overwrite) and os.path.isfile(des_nbar):
        log.error('{} already exists.'.format(os.path.basename(des_nbar)))
        return 1

    # read input image
    if verbose:
        log.info('Reading input: {}'.format(nbar))
    try:
        nbar_img = gdal.Open(nbar, gdal.GA_ReadOnly)
        nbar_sub = nbar_img.GetSubDatasets()
        nbar_red = gdal.Open(nbar_sub[7][0], gdal.GA_ReadOnly)
        nbar_nir = gdal.Open(nbar_sub[8][0], gdal.GA_ReadOnly)
        nbar_blue = gdal.Open(nbar_sub[9][0], gdal.GA_ReadOnly)
        nbar_green = gdal.Open(nbar_sub[10][0], gdal.GA_ReadOnly)
        nbar_swir = gdal.Open(nbar_sub[12][0], gdal.GA_ReadOnly)
        nbar_swir2 = gdal.Open(nbar_sub[13][0], gdal.GA_ReadOnly)
        nbar_qa_red = gdal.Open(nbar_sub[0][0], gdal.GA_ReadOnly)
        nbar_qa_nir = gdal.Open(nbar_sub[1][0], gdal.GA_ReadOnly)
        nbar_qa_blue = gdal.Open(nbar_sub[2][0], gdal.GA_ReadOnly)
        nbar_qa_green = gdal.Open(nbar_sub[3][0], gdal.GA_ReadOnly)
        nbar_qa_swir = gdal.Open(nbar_sub[5][0], gdal.GA_ReadOnly)
        nbar_qa_swir2 = gdal.Open(nbar_sub[6][0], gdal.GA_ReadOnly)
    except:
        log.error('Failed to read input {}'.format(nbar))
        return 2

    # read geo info
    if verbose:
        log.info('Reading geo information...')
    try:
        geo = stackGeo(nbar_sub[0][0])
    except:
        log.error('Failed to read geo info.')
        return 2

    # read actual data
    if verbose:
        log.info('Reading actual data...')
    try:
        red = nbar_red.GetRasterBand(1).ReadAsArray().astype(np.int16)
        nir = nbar_nir.GetRasterBand(1).ReadAsArray().astype(np.int16)
        blue = nbar_blue.GetRasterBand(1).ReadAsArray().astype(np.int16)
        green = nbar_green.GetRasterBand(1).ReadAsArray().astype(np.int16)
        swir = nbar_swir.GetRasterBand(1).ReadAsArray().astype(np.int16)
        swir2 = nbar_swir2.GetRasterBand(1).ReadAsArray().astype(np.int16)
        qa_red = nbar_qa_red.GetRasterBand(1).ReadAsArray().astype(np.int16)
        qa_nir = nbar_qa_nir.GetRasterBand(1).ReadAsArray().astype(np.int16)
        qa_blue = nbar_qa_blue.GetRasterBand(1).ReadAsArray().astype(np.int16)
        qa_green = nbar_qa_green.GetRasterBand(1).ReadAsArray().astype(np.int16)
        qa_swir = nbar_qa_swir.GetRasterBand(1).ReadAsArray().astype(np.int16)
        qa_swir2 = nbar_qa_swir2.GetRasterBand(1).ReadAsArray().astype(np.int16)
    except:
        log.error('Failed to read data.')
        return 2

    # calcualte indices
    if verbose:
        log.info('Calculating EVI and LSWI...')
    try:
        evi = (cons.SCALE_FACTOR * cons.EVI_COEF[0] * ((nir - red) /
                (nir + cons.EVI_COEF[1]*red - cons.EVI_COEF[2]*blue +
                cons.EVI_COEF[3]))).astype(np.int16)
        lswi = ((nir - swir2) / (nir + swir2) *
                    cons.SCALE_FACTOR).astype(np.int16)
    except:
        log.error('Failed to calculate indices.')
        return 3

    # generate mask band
    if verbose:
        log.info('Generating mask band...')
    try:
        mask_evi = ((qa_red != 0) + (qa_nir != 0) + (qa_blue != 0)) > 0
        mask_lswi = ((qa_swir2 != 0) + (qa_nir != 0)) > 0
        _total = np.sum(mask_evi)
        _size = np.shape(mask_evi)
        if verbose:
            log.info('{}% masked'.format(_total/(_size[0]*_size[1])*100))
    except:
        log.error('Failed to generate mask band.')
        return 4

    # write output
    if verbose:
        log.info('Writing output: {}'.format(des_nbar))
    try:
        # initialize output
        _driver = gdal.GetDriverByName('GTiff')
        output = _driver.Create(des_nbar, geo['samples'], geo['lines'], 10,
                                gdal.GDT_Int16)
        output.SetProjection(geo['proj'])
        output.SetGeoTransform(geo['geotrans'])
        output.GetRasterBand(1).SetNoDataValue(32767)
        # write output
        output.GetRasterBand(1).WriteArray(blue)
        output.GetRasterBand(2).WriteArray(green)
        output.GetRasterBand(3).WriteArray(red)
        output.GetRasterBand(4).WriteArray(nir)
        output.GetRasterBand(5).WriteArray(swir)
        output.GetRasterBand(6).WriteArray(swir2)
        output.GetRasterBand(7).WriteArray(evi)
        output.GetRasterBand(8).WriteArray(lswi)
        output.GetRasterBand(9).WriteArray(mask_evi)
        output.GetRasterBand(10).WriteArray(mask_lswi)
        # assign band name
        output.GetRasterBand(1).SetDescription('MODIS NBAR Blue')
        output.GetRasterBand(2).SetDescription('MODIS NBAR Green')
        output.GetRasterBand(3).SetDescription('MODIS NBAR Red')
        output.GetRasterBand(4).SetDescription('MODIS NBAR NIR')
        output.GetRasterBand(5).SetDescription('MODIS NBAR SWIR')
        output.GetRasterBand(6).SetDescription('MODIS NBAR SWIR2')
        output.GetRasterBand(7).SetDescription('MODIS NBAR EVI')
        output.GetRasterBand(8).SetDescription('MODIS NBAR LSWI')
        output.GetRasterBand(9).SetDescription('MODIS NBAR EVI MASK')
        output.GetRasterBand(10).SetDescription('MODIS NBAR LSWI MASK')
    except:
        log.error('Failed to write output to {}'.format(des_nbar))
        return 5

    # close files
    if verbose:
        log.info('Closing files...')
    nbar_img = None
    nbar_red = None
    nbar_nir = None
    nbar_swir = None
    nbar_blue = None
    nbar_green = None
    nbar_swir2 = None
    nbar_qa_red = None
    nbar_qa_nir = None
    nbar_qa_swir = None
    nbar_qa_blue = None
    nbar_qa_green = None
    nbar_qa_swir2 = None
    output = None

    # done
    if verbose:
        log.info('Process completed.')
    return 0


def nbarcmg2stack(nbar, des, overwrite=False, verbose=False):
    """ read MODIS NBAR CMG product and convert to geotiff

    Args:
        nbar (str): path to input MCD43C4 file
        des (str): path to output
        overwrite (bool): overwrite or not
        verbose (bool): verbose or not

    Returns:
        0: successful
        1: error due to des
        2: error in reading input
        3: error in calculating indices
        4: error in generating mask
        5: error in writing output

    """
    # set destinations
    des_nbar = os.path.join(des,'{}.tif'.format(mn2ln(os.path.basename(nbar))))

    # check if output already exists
    if (not overwrite) and os.path.isfile(des_nbar):
        log.error('{} already exists.'.format(os.path.basename(des_nbar)))
        return 1

    # read input image
    if verbose:
        log.info('Reading input: {}'.format(nbar))
    try:
        nbar_img = gdal.Open(nbar, gdal.GA_ReadOnly)
        nbar_sub = nbar_img.GetSubDatasets()
        nbar_red = gdal.Open(nbar_sub[0][0], gdal.GA_ReadOnly)
        nbar_nir = gdal.Open(nbar_sub[1][0], gdal.GA_ReadOnly)
        nbar_blue = gdal.Open(nbar_sub[2][0], gdal.GA_ReadOnly)
        nbar_green = gdal.Open(nbar_sub[3][0], gdal.GA_ReadOnly)
        nbar_swir = gdal.Open(nbar_sub[5][0], gdal.GA_ReadOnly)
        nbar_swir2 = gdal.Open(nbar_sub[6][0], gdal.GA_ReadOnly)
        nbar_qa = gdal.Open(nbar_sub[7][0], gdal.GA_ReadOnly)
        nbar_snow = gdal.Open(nbar_sub[11][0], gdal.GA_ReadOnly)
    except:
        log.error('Failed to read input {}'.format(nbar))
        return 2

    # read geo info
    if verbose:
        log.info('Reading geo information...')
    try:
        # geo = stackGeo(nbar_sub[0][0])
        geo = {'proj': cons.SIF_PROJ}
        geo['geotrans'] = (-180, 0.05, 0, -90, 0, 0.05)
        geo['lines'] = 3600
        geo['samples'] = 7200
        geo['bands'] = 8
        geo['nodata'] = 32767
    except:
        log.error('Failed to read geo info.')
        return 2

    # read actual data
    if verbose:
        log.info('Reading actual data...')
    try:
        red = nbar_red.GetRasterBand(1).ReadAsArray().astype(np.int16)
        nir = nbar_nir.GetRasterBand(1).ReadAsArray().astype(np.int16)
        blue = nbar_blue.GetRasterBand(1).ReadAsArray().astype(np.int16)
        green = nbar_green.GetRasterBand(1).ReadAsArray().astype(np.int16)
        swir = nbar_swir.GetRasterBand(1).ReadAsArray().astype(np.int16)
        swir2 = nbar_swir2.GetRasterBand(1).ReadAsArray().astype(np.int16)
        qa = nbar_qa.GetRasterBand(1).ReadAsArray().astype(np.int16)
        snow = nbar_snow.GetRasterBand(1).ReadAsArray().astype(np.int16)
    except:
        log.error('Failed to read data.')
        return 2

    # calcualte indices
    if verbose:
        log.info('Calculating EVI and LSWI...')
    try:
        evi = (cons.SCALE_FACTOR * cons.EVI_COEF[0] * ((nir - red) /
                (nir + cons.EVI_COEF[1]*red - cons.EVI_COEF[2]*blue +
                cons.EVI_COEF[3]))).astype(np.int16)
        lswi = ((nir - swir2) / (nir + swir2) *
                    cons.SCALE_FACTOR).astype(np.int16)
    except:
        log.error('Failed to calculate indices.')
        return 3

    # generate mask band
    if verbose:
        log.info('Generating mask band...')
    try:
        mask = (qa > 2)
        _total = np.sum(mask)
        _size = np.shape(mask)
        if verbose:
            log.info('{}% masked'.format(_total/(_size[0]*_size[1])*100))
    except:
        log.error('Failed to generate mask band.')
        return 4

    # write output
    if verbose:
        log.info('Writing output: {}'.format(des_nbar))
    try:
        # initialize output
        _driver = gdal.GetDriverByName('GTiff')
        output = _driver.Create(des_nbar, geo['samples'], geo['lines'], 10,
                                gdal.GDT_Int16)
        output.SetProjection(geo['proj'])
        output.SetGeoTransform(geo['geotrans'])
        output.GetRasterBand(1).SetNoDataValue(32767)
        # write output
        output.GetRasterBand(1).WriteArray(blue)
        output.GetRasterBand(2).WriteArray(green)
        output.GetRasterBand(3).WriteArray(red)
        output.GetRasterBand(4).WriteArray(nir)
        output.GetRasterBand(5).WriteArray(swir)
        output.GetRasterBand(6).WriteArray(swir2)
        output.GetRasterBand(7).WriteArray(evi)
        output.GetRasterBand(8).WriteArray(lswi)
        output.GetRasterBand(9).WriteArray(mask)
        output.GetRasterBand(10).WriteArray(snow)
        # assign band name
        output.GetRasterBand(1).SetDescription('MODIS NBAR CMG Blue')
        output.GetRasterBand(2).SetDescription('MODIS NBAR CMG Green')
        output.GetRasterBand(3).SetDescription('MODIS NBAR CMG Red')
        output.GetRasterBand(4).SetDescription('MODIS NBAR CMG NIR')
        output.GetRasterBand(5).SetDescription('MODIS NBAR CMG SWIR')
        output.GetRasterBand(6).SetDescription('MODIS NBAR CMG SWIR2')
        output.GetRasterBand(7).SetDescription('MODIS NBAR CMG EVI')
        output.GetRasterBand(8).SetDescription('MODIS NBAR CMG LSWI')
        output.GetRasterBand(9).SetDescription('MODIS NBAR CMG MASK')
        output.GetRasterBand(10).SetDescription('MODIS NBAR CMG Snow Pct')
    except:
        log.error('Failed to write output to {}'.format(des_nbar))
        return 5

    # close files
    if verbose:
        log.info('Closing files...')
    nbar_img = None
    nbar_red = None
    nbar_nir = None
    nbar_swir = None
    nbar_blue = None
    nbar_green = None
    nbar_swir2 = None
    nbar_qa = None
    nbar_snow = None
    output = None

    # done
    if verbose:
        log.info('Process completed.')
    return 0
