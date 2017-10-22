""" Module for creating strata from masks

    Args:
        -p (pattern): searching pattern
        -b (batch): batch process, thisjob and totaljob
        -m (mask): mask bands
        -v (value): mask value
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import sys
import argparse

from osgeo import gdal

from ...io import mask2strata, stack2array, array2stack, stackGeo
from ...common import constants as cons
from ...common import log, get_files, manage_batch


def create_strata(pattern, mask, value, ori, des, overwrite=False, recursive=False,
                    batch=[1,1]):
    """ converting masks to stacked images

    Args:
        pattern (str): searching pattern, e.g. S30*tif
        mask (str): mask bands
        value (int, list): mask values
        ori (str): place to look for inputs
        des (str): place to save outputs
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not
        batch (list, int): batch processing, [thisjob, totaljob]

    Returns:
        0: successful
        1: error due to des
        2: error when searching files
        3: found no file
        4: error during processing

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
        n = len(img_list)
    except:
        log.error('Failed to search for {}'.format(pattern))
        return 2
    else:
        if n == 0:
            log.error('Found no {}'.format(pattern))
            return 3
        else:
            log.info('Found {} files.'.format(n))

    # handle batch processing
    if batch[1] > 1:
        log.info('Handling batch process...')
        img_list = manage_batch(img_list, batch[0], batch[1])
        n = len(img_list)
        log.info('{} files to be processed by this job.'.format(n))

    # loop through all files
    count = 0
    log.info('Start processing files...')
    for img in img_list:
        log.info('Processing {}'.format(img[1]))
        geo = stackGeo(os.path.join(img[0], img[1]))
        array = stack2array(os.path.join(img[0], img[1]), mask)
        strata = mask2strata(array, value)
        if array2stack(strata, geo, os.path.join(des,
                        '{}_strata.tif'.format(os.path.splitext(img[1])[0])),
                        ['Strata'], cons.MASK_NODATA, gdal.GDT_Int16,
                        overwrite) == 0:
            count += 1

    # done
    log.info('Process completed.')
    log.info('Successfully processed {}/{} files.'.format(count, n))
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pattern', action='store', type=str,
                        dest='pattern', default='S*tif',
                        help='searching pattern')
    parser.add_argument('-b', '--batch', action='store', type=int, nargs=2,
                        dest='batch', default=[1,1],
                        help='batch process, [thisjob, totaljob]')
    parser.add_argument('-m', '--mask', action='store', type=int, nargs='+',
                        dest='mask', default=[9,10,11], help='mask bands')
    parser.add_argument('-v', '--value', action='store', type=int, nargs='+',
                        dest='value', default=[cons.MASK_CLOUD],
                        help='mask value')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # check arguments
    if not 1 <= args.batch[0] <= args.batch[1]:
        log.error('Invalid batch inputs: {}'.format(args.batch))
        sys.exit(1)

    # print logs
    log.info('Start creating strata...')
    log.info('Running job {}/{}'.format(args.batch[0], args.batch[1]))
    log.info('Looking for {}'.format(args.pattern))
    log.info('In {}'.format(args.ori))
    log.info('Saving in {}'.format(args.des))
    log.info('Masks bands: {}'.format(args.mask))
    log.info('Mask value: {}'.format(args.value))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to create strata
    create_strata(args.pattern, args.mask, args.value, args.ori, args.des,
                    args.overwrite, args.recursive, args.batch)
