""" Module for randomly select samples

    Args:
        -p (pattern): searching pattern
        -s (strata): strata value
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        n: number of samples
        ori: origin
        des: destination

"""
import os
import sys
import argparse
import numpy as np

from osgeo import gdal

from ..io import stack2table, stackGeo, array2stack
from ..common import log, get_files, select_samples
from ..common import constants as cons


def sample_from_images(pattern, n, ori, des, strata=0,
                        overwrite=False, recursive=True):
    """ select sample from images

    Args:
        pattern (str): searching pattern, e.g. *strata*tif
        n (int/list): number of sample to select, use list for n in each strata
        ori (str): place to look for input images
        des (str): place to save outputs
        strata(int, list): stratas, 0 for no strata
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not

    Returns:
        0: successful
        1: error due to des
        2: error when searching files
        3: found no file
        4: error compiling inputs
        5: error selecting sample
        6: error writing output

    """
    # check if output exists, if not try to create one
    if not os.path.exists(des):
        log.warning('{} does not exist, trying to create one.'.format(des))
        try:
            os.makedirs(des)
        except:
            log.error('Cannot create output folder {}'.format(des))
            return 1

    # locate files
    log.info('Locating files...'.format(ori))
    try:
        img_list = get_files(ori, pattern, recursive)
        nImg = len(img_list)
    except:
        log.error('Failed to search for {}'.format(pattern))
        return 2
    else:
        if nImg == 0:
            log.error('Found no {}'.format(pattern))
            return 3
        else:
            log.info('Found {} files.'.format(nImg))

    # compile inputs
    log.info('Start compiling input images...')
    count = 0
    population = np.empty((0,4), np.int16)
    for i, img in enumerate(img_list):
        log.info('Reading {}'.format(img[1]))
        try:
            table = stack2table(os.path.join(img[0], img[1]))
            imageID = np.zeros((table.shape[0], 1), np.int16) + i
            table = np.append(imageID, table, axis=1)
            population = np.append(population, table, axis=0)
            count += 1
        except:
            log.error('Failed to read input image {}'.format(img[1]))
            return 4
    log.info('Successfully read data from {}/{} images.'.format(count,nImg))

    # select samples
    log.info('Selecting samples...')
    try:
        if strata == 0:
            samples = select_samples(population, n)
        else:
            if type(strata) != list:
                strata = [strata]
            samples = np.empty((0,4), np.int16)
            for i in range(0, len(strata)):
                if type(n) == int:
                    n2 = n
                else:
                    n2 = n[i]
                subpopulation = population[population[:, 3] == strata[i], :]
                if subpopulation.shape[0] < n2:
                    log.warning('Population too small {}/{}'.format(
                                subpopulation.shape[0], n2))
                    continue
                subsample = select_samples(subpopulation, n2)
                samples = np.append(samples, subsample, axis=0)
        sampleID = np.reshape(np.arange(samples.shape[0], dtype=np.int16),
                                (samples.shape[0], 1))
        samples = np.append(sampleID, samples, axis=1)
    except:
        log.error('Failed to select samples.')
        return 5

    # write output
    log.info('Exporting selected samples...')
    count = 0
    for i, img in enumerate(img_list):
        log.info('Exporting {}'.format(os.path.splitext(img[1])[0]))
        geo = stackGeo(os.path.join(img[0], img[1]))
        array = np.zeros((geo['lines'], geo['samples']),
                            np.int16) + cons.MASK_NODATA
        subsample = samples[samples[:, 1] == i, :]
        log.info('Total number of samples {}.'.format(subsample.shape[0]))
        for j in range(0, subsample.shape[0]):
            array[subsample[j, 2], subsample[j, 3]] = subsample[j, 0]
        if array2stack(array, geo, os.path.join(des,
                        '{}_sample.tif'.format(os.path.splitext(img[1])[0])),
                        ['samples'], cons.MASK_NODATA, gdal.GDT_Int16,
                        overwrite) == 0:
            count += 1
        else:
            log.error('Failed to export {}'.format(os.path.splitext(img[1])[0]))
            return 6
    log.info('Successfully exported {}/{} images.'.format(count,nImg))

    # done
    log.info('Process completed.')
    log.info('Successfully exported {}/{} image of samples.'.format(count,nImg))
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pattern', action='store', type=str,
                        dest='pattern', default='*strata*tif',
                        help='searching pattern')
    parser.add_argument('-s', '--strata', action='store', type=int, nargs='+',
                        dest='strata', default=0, help='strata')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('n', type=int, nargs='*', default=[100],
                        help='n samples')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # check arguments
    if args.strata == 0:
        if len(args.n) > 1:
            log.error('More than 1 n but no strata.')
        else:
            args.n = args.n[0]
    else:
        if len(args.n) == 1:
            args.n = args.n * len(args.strata)
        else:
            if len(args.n) != len(args.strata):
                log.error('Dimemsion of n and strata does not match.')
                sys.exit(1)

    # print logs
    log.info('Start selecting samples...')
    log.info('Looking for {}'.format(args.pattern))
    log.info('In {}'.format(args.ori))
    log.info('Saving in {}'.format(args.des))
    log.info('Select {} samples.'.format(args.n))
    if args.strata != 0:
        log.info('Use stratas: {}'.format(args.strata))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting existing image.')

    # run function to select samples
    sample_from_images(args.pattern, args.n, args.ori, args.des, args.strata,
                        args.overwrite, args.recursive)
