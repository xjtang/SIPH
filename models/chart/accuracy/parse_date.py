""" Module for parsing different inputs of change date

    Args:
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import argparse
import numpy as np

from ....common import log, date_to_doy
from ....io import chkExist


def parsedate(ori, des, overwrite=False):
    """ parse

    Args:
        ori (str): input file
        des (str): output path and filename
        overwrite (bool): overwrite or not

    Returns:
        0: successful
        1: error due to des
        2: error when reading input
        3: error processing
        4: error writing output

    """
    _date=['DATE','ED1','ED2']
    # check if output already exists if not create one
    if not overwrite:
        if chkExist(des) > 0:
            return 1

    # read input csv file
    log.info('Reading input file: {}'.format(ori))
    try:
        r = np.genfromtxt(ori, delimiter=',', dtype=None, names=True)
    except:
        log.error('Failed to read input from {}'.format(ori))
        return 2

    # parse dates
    log.info('Start parsing...')
    count = 0
    for x in _date:
        for y in r:
            try:
                this = y[x].decode()
                y[x] = pd(this)
                count = count + 1
            except:
                log.warning('Failed to parse: {}'.format(this))
                continue
    if count == 0:
        log.error('Processed nothing.')
        return 3

    # write output
    log.info('Writing output to: {}'.format(des))
    try:
        np.savetxt(des, r, delimiter=',', fmt='%s')
    except:
        log.error('Failed to write output to: {}'.format(des))
        return 4

    # done
    log.info('Process completed.')
    log.info('{}/{} dates parsed.'.format(count, len(r) * len(_date)))
    return 0

def pd(x):
    if (x == '') | (x == '0'):
        return 0
    elif '/' in x:
        x = x.split('/')
        year = int(x[2])
        month = int(x[1])
        day = int(x[0])
    elif len(x) == 6:
        year = int(x[0:4])
        month = int(x[4:6])
        day = 1
    elif len(x) == 8 :
        year = int(x[0:4])
        month = int(x[4:6])
        day = int(x[6:8])
    else:
        log.warning('Failed to parse: {}'.format(x))
        return x
    return date_to_doy(year, month, day)


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start parsing dates...')
    log.info('Reading from {}'.format(args.ori))
    log.info('Saving as {}'.format(args.des))
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to parse date
    parsedate(args.ori, args.des, args.overwrite)
