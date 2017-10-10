""" Module for merging mask with image

    Args:
        -p (pattern): searching pattern
        -b (batch): batch process, thisjob and totaljob
        -m (mask): mask source, e.g. fmask
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import sys
import argparse

from osgeo import gdal

from . import mn2ln, bit2mask, mask2array
from ..common import constants as cons
from ..common import log, get_files, manage_batch
from ..io import stackMerge


def merge_mask(pattern, ori, des, mask, overwrite=False, recursive=False,
                    batch=[1,1]):
    """ converting masks to stacked images

    Args:
        pattern (str): searching pattern, e.g. S30*tif
        ori (str): place to look for inputs
        des (str): place to save outputs
        mask (str): place to look for masks
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
        maja = get_files(mask, '*{}*MAJA*'.format(img[1][3:16]), recursive)
        fmask = get_files(mask, '*{}*FMASK*'.format(img[1][3:16]), recursive)
        lasrc = get_files(mask, '*{}*LASRC*'.format(img[1][3:16]), recursive)
        if len(maja) * len(fmask) * len(lasrc) == 0:
            log.warning('No mask for this file: {}'.format(img[1]))
        else:
            stacks = [os.path.join(img[0], img[1]),
                        os.path.join(lasrc[0][0], lasrc[0][1]),
                        os.path.join(fmask[0][0], fmask[0][1]),
                        os.path.join(maja[0][0], maja[0][1])]
            if stackMerge(stacks, os.path.join(des, img[1]), gdal.GDT_Int16,
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
                        dest='pattern', default='S30*tif',
                        help='searching pattern')
    parser.add_argument('-b', '--batch', action='store', type=int, nargs=2,
                        dest='batch', default=[1,1],
                        help='batch process, [thisjob, totaljob]')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('mask', default='./', help='mask location')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # check arguments
    if not 1 <= args.batch[0] <= args.batch[1]:
        log.error('Invalid batch inputs: [{}, {}]'.format(args.batch[0],
                    args.batch[1]))
        sys.exit(1)

    # print logs
    log.info('Start converting mask to stack...')
    log.info('Running job {}/{}'.format(args.batch[0], args.batch[1]))
    log.info('Looking for {}'.format(args.pattern))
    log.info('In {}'.format(args.ori))
    log.info('Saving in {}'.format(args.des))
    log.info('Masks in {}'.format(args.mask))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function merge masks and image
    merge_mask(args.pattern, args.ori, args.des, args.mask, args.overwrite,
                        args.recursive, args.batch)