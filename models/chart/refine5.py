""" Module for refining classification results

    Args:
        --overwrite: overwrite or not
        ori: origin
        lc: MODIS land cover
        vcf: MODIS VCF
        des: destination

"""
import os
import argparse
import numpy as np

from osgeo import gdal

from ...common import log, get_files, show_progress
from ...io import stack2array, stackGeo, array2stack


def refine_results(map1, map2, des, overwrite=False):
    """ refine classification results

    Args:
        map1 (str): map1
        map2 (str): map2
        des (str): place to save output map
        overwrite (bool): overwrite or not

    Returns:
        0: successful
        1: error due to des
        2: error when reading inputs
        3: error during processing
        4: error writing output

    """
    m2c = [0,2,2,4,4,5,10,10,9,9,10,11,12,13,12,16,16,25,0,0,0,0,0,0,0,0,0,0,0]
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(os.path.basename(des)))
        return 1

    # read input image
    log.info('Reading input maps...')
    try:
        m1 = stack2array(map1)
        m2 = np.kron(stack2array(map2), np.ones((2,2,1))).astype(m1.dtype)
    except:
        log.error('Failed to read input maps.')
        return 2

    # read geo info
    log.info('Reading geo information...')
    try:
        geo = stackGeo(map1)
    except:
        log.error('Failed to read geo info.')
        return 2

    # refine classification results
    log.info('Refining maps...')
    try:
        (lines, samples, nband) = m1.shape
        for i in range(0,lines):
            for j in range(0, samples):
                p1 = m1[i, j]
                p2 = m2[i, j]
                # if (sum(p1 == 10) >= 12) & (sum(p2 == 12) >= 12):
                #     p1[p1==10] = 12
                # if (sum(p1 == 16) >= 12) & (sum(p2 == 12) >= 12):
                #     p1[p1==16] = 12
                # if (sum(p1 == 11) >= 12) & (sum(p2 == 12) >= 12):
                #     p1[p1==11] = 12
                if (sum(p1 == 16) >= 10) & (sum(p2 == 7) >= 5):
                    p1[p1==16] = 10
                if (sum(p1 == 16) >= 12) & (sum(p2 == 12) >= 12):
                    p1[p1==16] = 12
                if (sum(p1 == 11) >= 12) & (sum(p2 == 12) >= 12):
                    p1[p1==11] = 12
                m1[i, j] = p1
            progress = show_progress(i, lines, 5)
            if progress >= 0:
                log.info('{}% done.'.format(progress))
    except:
        log.error('Failed to refine results.')
        return 3

    # write output
    log.info('Writing output...')
    try:
        array2stack(m1, geo, des, 'NA', 255, gdal.GDT_Byte, overwrite, 'GTiff',
                    ['COMPRESS=LZW'])
    except:
        log.error('Failed to write output to {}'.format(des))
        return 4

    # done
    log.info('Process completed.')
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('map1', default='./', help='map1')
    parser.add_argument('map2', default='./', help='map2')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start comparing...')
    log.info('Map 1: {}'.format(args.map1))
    log.info('Map 2: {}'.format(args.map2))
    log.info('Saving as {}'.format(args.des))
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to refine classification results
    refine_results(args.map1, args.map2, args.des, args.overwrite)
