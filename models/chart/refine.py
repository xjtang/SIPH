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


def refine_results(ori, lc, vcf, des, overwrite=False):
    """ refine classification results

    Args:
        ori (str): path and filename of classification results
        lc (str): path and filename of MODIS land cover maps
        vcf (str): path and filename of MODIS VCF
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
        r = stack2array(ori)
        lc = stack2array(lc)
        vcf = stack2array(vcf)
        lc = np.kron(lc, np.ones((2,2,1))).astype(lc.dtype)
    except:
        log.error('Failed to read input maps.')
        return 2

    # read geo info
    log.info('Reading geo information...')
    try:
        geo = stackGeo(ori)
    except:
        log.error('Failed to read geo info.')
        return 2

    # refine classification results
    log.info('Refining maps...')
    try:
        (lines, samples, nband) = r.shape
        for i in range(0,lines):
            for j in range(0, samples):
                p = r[i, j, :]

                plc = np.zeros(nband, np.int8)
                plc[0:18] = lc[i, j, :]
                plc[18] = lc[i, j, -1]
                for k in range(0, len(plc)):
                    plc[k] = m2c[plc[k]]
                plc_label = np.bincount(plc).argmax()

                pvcf = np.zeros(nband, np.int8)
                pvcf[0:18] = vcf[i, j, 1:]
                pvcf[18] = vcf[i, j, -1]

                # fix short plantation in beginning
                if p[3] != 18:
                    if p[0] == 18:
                        p[0] = p[3]
                    if p[1] == 18:
                        p[1] = p[3]
                    if p[2] == 18:
                        p[2] = p[3]
                    r[i, j, :] = p

                # deel with unclassified
                if max(p == 0) == 1:
                    uclc = plc[p == 0]
                    p_label = np.bincount(uclc).argmax()
                    # mostly uc
                    if sum(p == 0) > 8:
                        p[p == 0] = p_label
                    # uc in the beginning
                    elif (sum(p == 0) <= 3) & (p[0] == 0):
                        if p_label in [13, 25]:
                            p[p == 0] = p_label
                        else:
                            p[p == 0] = p[p != 0][0]
                    # uc in the end
                    elif p[-1] == 0:
                        if p_label in [13, 25]:
                            p[p == 0] = p_label
                        else:
                            p[p == 0] = p[p != 0][-1]
                    # single uc
                    elif sum(p == 0) < 3:
                        for k in range(0, len(p)):
                            if p[k] == 0:
                                p[k] == p[k-1]
                    r[i, j, :] = p

                # urban barren fix
                if sum((p == 13) & (plc == 16)) >= 5:
                    p[(p==13)&(plc==16)] = 16
                    r[i, j, :] = p
                # urban grassland fix
                if sum((p == 13) & (plc == 10)) >= 5:
                    p[(p==13)&(plc==10)] = 10
                    r[i, j, :] = p

                # urban check 2
                if sum((p == 13) & (plc != 13)) >= 8:
                    if plc_label == 10:
                        p[(p==13)&(plc!=13)] = 10
                    elif plc_label == 10:
                        p[(p==13)&(plc!=13)] = 12
                    elif plc_label == 12:
                        p[(p==13)&(plc!=13)] = 12
                    r[i, j, :] = p

                # stable class check check
                if len(np.unique(p)) == 1:
                    mvcf = pvcf.mean()
                    p_class = np.unique(p)[0]
                    if p_class == 9:
                        if mvcf >= 60:
                            if plc_label <= 5:
                                p_label = plc_label
                            else:
                                p_label = 4
                        elif mvcf >= 40:
                            if plc_label == 2:
                                p_label = 2
                        else:
                            p_label = 9
                        r[i, j, :] = p_label
                    elif p_class == 12:
                        if plc_label == 13:
                            p_label = 13
                        elif plc_label == 9:
                            p_label = 9
                        elif plc_label not in [10, 12]:
                            if mvcf >= 20:
                                p_label = 9
                        else:
                            if mvcf >= 30:
                                p_label = 9
                            else:
                                p_label = 12
                        r[i, j, :] = p_label
                    elif p_class == 18:
                        p_label = 18
                        if (plc_label <= 2) & (mvcf >= 50):
                            p_label = 2
                        if (plc_label == 12) & (mvcf <= 10):
                            p_label = 12
                        if (plc_label == 9) & (mvcf <= 30):
                            p_label = 9
                        r[i, j, :] = p_label

            progress = show_progress(i, lines, 5)
            if progress >= 0:
                log.info('{}% done.'.format(progress))
    except:
        log.error('Failed to refine results.')
        return 3

    # write output
    log.info('Writing output...')
    try:
        array2stack(r, geo, des, 'NA', 255, gdal.GDT_Int16, overwrite, 'GTiff',
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
    parser.add_argument('ori', default='./', help='classification results')
    parser.add_argument('lc', default='./', help='MODIS land cover maps')
    parser.add_argument('vcf', default='./', help='MODIS VCF')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start comparing...')
    log.info('Classification results: {}'.format(args.ori))
    log.info('MODIS land cover: {}'.format(args.lc))
    log.info('MODIS VCF: {}'.format(args.vcf))
    log.info('Saving as {}'.format(args.des))
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to refine classification results
    refine_results(args.ori, args.lc, args.vcf, args.des, args.overwrite)
