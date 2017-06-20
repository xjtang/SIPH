""" Module for reading VIIRS data
"""
from __future__ import division

import os
import numpy as np
import h5py

from osgeo import gdal

from ..common import log, enlarge


SR_BANDS = (23, 24, 25)
QA_BANDS = (13, 14, 16, 18, 19)
VZA_BAND = 1
NODATA = -9999
SCALE_FACTOR = 10000


def viirs2gtif(img, des, overwrite=False, verbose=False):
    """ read VIIRS surface reflectance product and convert to geotiff with
        selected bands

    Args:
        img (str): path to input VIIRS file
        des (str): path to output
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
    _error = 0

    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(des.split('/')[-1]))
        return 1

    while True:
        # read input image
        if verbose:
            log.info('Reading input: {}'.format(img))
        try:
            vs_img = gdal.Open(img, gdal.GA_ReadOnly)
            vs_sub = vs_img.GetSubDatasets()
            vs_i1 = gdal.Open(vs_sub[SR_BANDS[0]][0], gdal.GA_ReadOnly)
            vs_i2 = gdal.Open(vs_sub[SR_BANDS[1]][0], gdal.GA_ReadOnly)
            vs_i3 = gdal.Open(vs_sub[SR_BANDS[2]][0], gdal.GA_ReadOnly)
            vs_vza = gdal.Open(vs_sub[VZA_BAND][0], gdal.GA_ReadOnly)
        except:
            _error = 2
            log.error('Failed to read input {}'.format(img))
            break

        # read geo info
        if verbose:
            log.info('Reading geo information...')
        try:
            vs_geo = viirsGeo(img, 500)
        except:
            _error = 2
            log.error('Failed to read geo info from {}'.format(img))
            break

        # read actual data
        if verbose:
            log.info('Reading actual data...')
        try:
            red = vs_i1.GetRasterBand(1).ReadAsArray().astype(np.int16)
            nir = vs_i2.GetRasterBand(1).ReadAsArray().astype(np.int16)
            swir = vs_i3.GetRasterBand(1).ReadAsArray().astype(np.int16)
            vza = enlarge(vs_vza.GetRasterBand(1).ReadAsArray().astype(np.int16), 2)
        except:
            _error = 2
            log.error('Failed to read data from {}'.format(img))
            break

        # calculate NDVI
        if verbose:
            log.info('Calculating NDVI...')
        try:
            ndvi = ((nir - red) / (nir + red) * SCALE_FACTOR).astype(np.int16)
        except:
            _error = 3
            log.error('Failed to calculate NDVI.')
            break

        # generate mask band
        if verbose:
            log.info('Generating mask band...')
        try:
            mask = enlarge(viirsQA(vs_img), 2)
            _total = np.sum(mask)
            _size = np.shape(mask)
            if verbose:
                log.info('{}% masked'.format(_total/(_size[0]*_size[1])*100))
        except:
            _error = 3
            log.error('Failed to generate mask band.')
            break

        # clean up data
        if verbose:
            log.info('Cleaning up data...')
        try:
            invalid = ~(((red >= 0) & (red <= 10000)) & ((nir >= 0) & (nir <= 10000)) &
                        ((swir >= 0) & (swir <= 10000)))
            red[invalid] <- NODATA
            nir[invalid] <- NODATA
            swir[invalid] <- NODATA
            vza[~((vza >= 0) & (vza <= 18000))] <- NODATA
        except:
            _error = 4
            log.error('Failed to clean up data.')
            break

        # write output
        if verbose:
            log.info('Writing output: {}'.format(des))
        try:
            # initialize output
            _driver = gdal.GetDriverByName('GTiff')
            output = _driver.Create(des, vs_i1.RasterYSize, vs_i1.RasterXSize,
                                    6, gdal.GDT_Int16)
            output.SetProjection(vs_geo['proj'])
            output.SetGeoTransform(vs_geo['geotrans'])
            output.GetRasterBand(1).SetNoDataValue(NODATA)
            # write output
            output.GetRasterBand(1).WriteArray(red)
            output.GetRasterBand(2).WriteArray(nir)
            output.GetRasterBand(3).WriteArray(swir)
            output.GetRasterBand(4).WriteArray(ndvi)
            output.GetRasterBand(5).WriteArray(vza)
            output.GetRasterBand(6).WriteArray(mask)
            # assign band name
            output.GetRasterBand(1).SetDescription('VIIRS 500m I1 Red')
            output.GetRasterBand(2).SetDescription('VIIRS 500m I2 NIR')
            output.GetRasterBand(3).SetDescription('VIIRS 500m I3 SWIR')
            output.GetRasterBand(4).SetDescription('VIIRS 500m NDVI')
            output.GetRasterBand(5).SetDescription('VIIRS 500m VZA')
            output.GetRasterBand(6).SetDescription('VIIRS 500m Mask')
        except:
            _error = 5
            log.error('Failed to write output to {}'.format(des))
            break

        # continue next
        break

    # close files
    if verbose:
        log.info('Closing files...')
    vs_img = None
    vs_i1 = None
    vs_i2 = None
    vs_i3 = None
    vs_vza = None
    output = None

    # done
    if _error == 0:
        if verbose:
            log.info('Process completed.')
    return _error


def viirsQA(vs_img, verbose=False):
    """ intepret VIIRS QA and return a mask array

    Args:
        img (obj): gdal image object
        verbose (bool): verbose or not

    Returns:
        mask (ndarray): mask array

    """
    # read QA bands
    if verbose:
        log.info('Reading QA bands...')
    vs_sub = vs_img.GetSubDatasets()
    vs_qf1 = gdal.Open(vs_sub[QA_BANDS[0]][0], gdal.GA_ReadOnly)
    vs_qf2 = gdal.Open(vs_sub[QA_BANDS[1]][0], gdal.GA_ReadOnly)
    # vs_qf4 = gdal.Open(vs_sub[QA_BANDS[2]][0], gdal.GA_ReadOnly)
    # vs_qf6 = gdal.Open(vs_sub[QA_BANDS[3]][0], gdal.GA_ReadOnly)
    vs_qf7 = gdal.Open(vs_sub[QA_BANDS[4]][0], gdal.GA_ReadOnly)

    # read actual data
    if verbose:
        log.info('Reading actual data...')
    qf1 = vs_qf1.GetRasterBand(1).ReadAsArray()
    qf2 = vs_qf2.GetRasterBand(1).ReadAsArray()
    # qf4 = vs_qf4.GetRasterBand(1).ReadAsArray()
    # qf6 = vs_qf6.GetRasterBand(1).ReadAsArray()
    qf7 = vs_qf7.GetRasterBand(1).ReadAsArray()

    # process
    if verbose:
        log.info('Generating mask bands...')
    mask_qf1 = (np.mod(np.right_shift(qf1, 1) + 1, 2) |
                np.mod(np.right_shift(qf1, 3), 2))
    # mask_qf2 = ((np.mod(qf2, 4) // 3) | np.right_shift(qf2, 3)) # sea water
    mask_qf2 = np.right_shift(qf2, 3)
    # mask_qf4 = np.mod(np.right_shift(qf4, 1), 16) # unsure
    # mask_qf6 = np.mod(np.right_shift(qf6, 3), 8) # unsure
    mask_qf7 = (np.mod(qf7, 4) | np.mod(np.right_shift(qf7, 4), 2))
                # (np.mod(np.right_shift(qf7, 2), 4) // 3) | # unsure


    # just to double check
    # mask2_qf1 = (~get_bits(qf1, 1)) | get_bits(qf1, 2)
    # mask2_qf2 = ((get_bits(qf2, 0) & get_bits(qf2, 1)) | get_bits(qf2, 3) |
    #             get_bits(qf2, 4) | get_bits(qf2, 5) | get_bits(qf2, 6) |
    #             get_bits(qf2, 7))
    # mask2_qf4 = (get_bits(qf4, 1) | get_bits(qf4, 2) | get_bits(qf4, 3) |
    #             get_bits(qf4, 4))
    # mask2_qf6 = (get_bits(qf6, 3) | get_bits(qf6, 4) | get_bits(qf6, 5))
    # mask2_qf7 = (get_bits(qf7, 0) | get_bits(qf7, 1) | get_bits(qf7, 4) |
    #            (get_bits(qf7, 2) & get_bits(qf7, 3)))
    # mask2 = (mask2_qf1 | mask2_qf2 | mask2_qf4 | mask2_qf6 | mask2_qf7) > 0

    # prepare outputs
    if verbose:
        log.info('Combining mask bands...')
    # mask = (mask_qf1 | mask_qf2 | mask_qf4 | mask_qf6 | mask_qf7) > 0
    mask = (mask_qf1 | mask_qf2 | mask_qf7) > 0

    # close files
    if verbose:
        log.info('Closing files...')
    vs_qf1 = None
    vs_qf2 = None
    # vs_qf4 = None
    # vs_qf6 = None
    vs_qf7 = None

    # done
    if verbose:
        log.info('Process completed.')
    return mask


def vn2ln(vn):
    """ convert VIISR style file name to Landsat style
        file name only, regardless of file type extension
        e.g. VNP09GA.A2014001.h12v09.001.2017064050806
             to VNP0120092014001109GA (VNP 0hh 0vv yyyyddd c pppp)

    Args:
        vn (str): VIIRS style file name

    Returns:
        ln (str): Landsat style file name

    """
    vn = vn.split('.')
    return 'VNP0{}0{}{}{}{}'.format(vn[2][1:3], vn[2][4:6], vn[1][1:],
                                    vn[3][-1], vn[0][3:])


def viirsGeo(img, res):
    """ read spatial reference from VIIRS HDF5 file
        modified from the sample code from NASA

    Args:
        img (obj): gdal image object
        res (int): resolution, 500 or 1000

    Returns:
        geo (dic): spatial reference information

    """
    # projection
    geo = {'proj': ('PROJCS["unnamed",GEOGCS["Unknown datum based upon the cust'
                    'om spheroid", DATUM["Not specified (based on custom sphero'
                    'id)", SPHEROID["Custom spheroid",6371007.181,0]],PRIMEM["G'
                    'reenwich",0], UNIT["degree",0.0174532925199433]], PROJECTI'
                    'ON["Sinusoidal"],PARAMETER["longitude_of_center",0],PARAME'
                    'TER["false_easting",0],PARAMETER["false_northing",0],UNIT['
                    '"Meter",1]]')}

    # pixel resolution
    if res == 500:
        geo['xres'] = 463.31271652777775
        geo['yres'] = -463.31271652777775
    elif res == 1000:
        geo['xres'] = 926.6254330555555
        geo['yres'] = -926.6254330555555
    else:
        log.error('Invalid resolution {}.'.format(res))

    # upper left conner
    f = h5py.File(img)
    meta_raw = f['HDFEOS INFORMATION']['StructMetadata.0'].value.split()
    meta = [s.decode('utf-8') for s in meta_raw]
    ulc = [i for i in meta if 'UpperLeftPointMtrs' in i]
    ulcLon = float(ulc[0].replace('=', ',').replace('(', '').replace(')',
                    '').split(',')[1])
    ulcLat = float(ulc[0].replace('=', ',').replace('(', '').replace(')',
                    '').split(',')[2])
    geo['ulc'] = (ulcLon,  0, ulcLat, 0)

    # geo transform values
    geo['geotrans'] = (ulcLon, geo['xres'], 0, ulcLat, 0, geo['yres'])

    # clean up
    f = None
    meta_raw = None
    meta = None

    # done
    return geo
