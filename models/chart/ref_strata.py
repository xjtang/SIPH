""" Module for creating strata from reference dataset

    Args:
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import argparse
import numpy as np

from ...io import csv2ndarray, chkExist
from ...common import log
from ...common import constants as cons


def gen_strata(ori, des, overwrite=False):
    """ create stratification from map

    Args:
        ori (str): input csv file
        des (str): output file
        overwrite (bool): overwrite or not

    Returns:
        0: successful
        1: error due to des
        2: error reading input
        3: error processing
        4: error writing output

    """
    c2s = cons.CLASS2STRATA

    # check if output exists, if not try to create one
    if chkExist(des) > 0:
        return 1

    # read input csv
    log.info('Reading input csv...')
    try:
        ref = csv2ndarray(ori, True)
    except:
        log.error('Failed to read input csv.')
        return 2

    # statifying
    log.info('Start creating strata...')
    try:
        for i in range(0, len(ref)):
            ref['L1'][i] = ref['C1'][i]

            if ref['C3'][i] > 0:
                ref['L2'][i] = ref['C3'][i]
            elif ref['C2'][i] > 0:
                ref['L2'][i] = ref['C2'][i]
            else:
                ref['L2'][i] = ref['C1'][i]

            if ref['L1'][i] == ref['L2'][i]:
                ref['ST'][i] = c2s[ref['L1'][i]]
            else:
                L1C = c2s[ref['L1'][i]]
                L2C = c2s[ref['L2'][i]]
                if ((L2C == 2) & (L1C != 2)):
                    ref['ST'][i] = 10
                elif L2C == 9:
                    ref['ST'][i] = 11
                elif L2C == 6:
                    ref['ST'][i] = 12
                elif ((L1C in [1, 3]) & (L2C in [4, 5, 7, 8])):
                    ref['ST'][i] = 13
                elif ((L1C in [2, 4, 5, 6, 7, 8]) & (L2C in [1, 3])):
                    ref['ST'][i] = 14
                else:
                    ref['ST'][i] = 15
    except:
        log.error('Failed to create strata.')
        return 3

    # writing output
    log.info('Writing output...')
    try:
        np.savetxt(des, ref, delimiter=',', fmt='%d,%d,%d,%d,%d,%d,%d',
                    header='PID,C1,C2,C3,L1,L2,ST', comments='')
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
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start creating strata...')
    log.info('Input csv: {}'.format(args.ori))
    log.info('Saving as {}'.format(args.des))
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to generate strata
    gen_strata(args.ori, args.des, args.overwrite)
