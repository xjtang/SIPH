""" Module for summarizing strata

    Args:
        -p (pattern): searching pattern
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import argparse

import numpy as np

from ...io import stack2array
from ...common import constants as cons
from ...common import log, get_files


def sum_strata(pattern, ori, des, overwrite=False, recursive=False):
    """ converting masks to stacked images

    Args:
        pattern (str): searching pattern, e.g. S30*tif
        ori (str): place to look for inputs
        des (str): place to save outputs
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not

    Returns:
        0: successful
        1: error due to des
        2: error when searching files
        3: found no file
        4: error during processing
        5: error writng output

    """
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(os.path.basename(des)))
        return 1

    # locate files
    log.info('Locating files...'.format(ori))
    try:
        strata_list = get_files(ori, pattern, recursive)
        n = len(strata_list)
    except:
        log.error('Failed to search for {}'.format(pattern))
        return 2
    else:
        if n == 0:
            log.error('Found no {}'.format(pattern))
            return 3
        else:
            log.info('Found {} files.'.format(n))

    # loop through all files
    count = 0
    r = np.zeros((len(cons.STRATA), 2))
    r[:, 0] = cons.STRATA
    log.info('Start processing files...')
    for strata in strata_list:
        log.info('Processing {}'.format(strata[1]))
        array = stack2array(os.path.join(strata[0], strata[1]))
        for x in cons.STRATA:
            r[(r[:, 0] == x), 1] += (array == x).sum()
        count += 1

    # write output
    try:
        np.savetxt(des, r, delimiter=',', fmt='%d')
    except:
        log.error('Failed to write output to: {}'.format(des))
        return 5

    # done
    log.info('Process completed.')
    log.info('Successfully processed {}/{} files.'.format(count, n))
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pattern', action='store', type=str,
                        dest='pattern', default='*strata*tif',
                        help='searching pattern')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start summarizing strata...')
    log.info('Looking for {}'.format(args.pattern))
    log.info('In {}'.format(args.ori))
    log.info('Saving as {}'.format(args.des))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to summarizing strata
    sum_strata(args.pattern, args.ori, args.des, args.overwrite, args.recursive)
