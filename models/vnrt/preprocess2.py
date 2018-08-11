""" Module for preprocess MODIS data

    Args:
        -p (pattern): searching pattern
        -b (batch): batch process, thisjob and totaljob
        -R (recursive): recursive when seaching files
        -Q (mgq): location of 250m MODIS data
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import sys
import argparse

from ...common import log, get_files, manage_batch
from ...io import modis2stack


def modis_preprocess(pattern, ori, des, mgq='NA', overwrite=False, recursive=False,
                        batch=[1,1]):
    """ preprocess VIIRS data

    Args:
        pattern (str): searching pattern, e.g. MOD09GA*hdf
        ori (str): place to look for inputs
        des (str): place to save outputs
        mgq (str): place to look for MODIS 250m data
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not
        batch (list, int): batch processing, [thisjob, totaljob]

    Returns:
        0: successful
        1: error due to des
        2: error when searching files
        3: found no file

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
    log.info('Locating files...')
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
    if mgq != 'NA':
        log.info('Looking for 250m data as well...')
    for img in img_list:
        log.info('Processing {}'.format(img[1]))
        mgq_fn = img[1].split('.')
        mgq_fn[4] = '*'
        mgq_fn[0] = '{}GQ'.format(mgq_fn[0][:-2])
        mgq_pattern = '.'.join(mgq_fn)
        mgq_img = get_files(mgq, mgq_pattern, recursive)
        if len(mgq_img) == 0:
            log.warning('Found no 250m data for {}'.format(img[1]))
            mgq_img = 'NA'
        else:
            mgq_img = os.path.join(mgq_img[0][0], mgq_img[0][1])
        if modis2stack(os.path.join(img[0], img[1]), des, mgq_img,
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
                        dest='pattern', default='MOD09GA*hdf',
                        help='searching pattern')
    parser.add_argument('-b', '--batch', action='store', type=int, nargs=2,
                        dest='batch', default=[1,1],
                        help='batch process, [thisjob, totaljob]')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('-Q', '--mgq', action='store', type=str,
                        dest='mgq', default='NA',
                        help='location of 250m MODIS data')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # check arguments
    if not 1 <= args.batch[0] <= args.batch[1]:
        log.error('Invalid batch inputs: [{}, {}]'.format(args.batch[0],
                    args.batch[1]))
        sys.exit(1)

    # print logs
    log.info('Start preprocessing...')
    log.info('Running job {}/{}'.format(args.batch[0], args.batch[1]))
    log.info('Looking for {}'.format(args.pattern))
    log.info('In {}'.format(args.ori))
    log.info('Saving in {}'.format(args.des))
    if args.mgq != 'NA':
        log.info('Looking for 250m data in {}'.format(args.mgq))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to preprocess data
    modis_preprocess(args.pattern, args.ori, args.des, args.mgq, args.overwrite,
                        args.recursive, args.batch)
