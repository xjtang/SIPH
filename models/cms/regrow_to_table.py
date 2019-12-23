""" Module to export regrow stack image to csv

    Args:
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import argparse
import numpy as np

from ...common import log
from ...io import stackGeo, stack2array, chkExist


def regrow2csv(ori, des, overwrite=False):
    """ converting to csv

    Args:
        ori (str): path and file name of input
        des (str): path and file name of output
        overwrite (bool): overwrite or not

    Returns:
        0: successful
        1: error due to des
        2: error when processing
        3: error writing output

    """
    lbl = 'rg, agb15, start, end'
    _fmt = '%d,%d,%d,%d'
    # lbl = 'Fr,Flr,Fd,Ff,Fn,str,end,b03,b04,b05,b06,b07,b08,b09,b10,b11,b12,b13,b14,b15,b16'
    # _fmt = '%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d'

    # check if output exists
    if chkExist(des) > 0:
        return 1

    # initialize output
    log.info('Reading input...')
    try:
        geo = stackGeo(ori)
        array = stack2array(ori, 0, np.int16)
    except:
        log.error('Failed to read {}'.format(ori))
        return 2

    # process data
    log.info('Converting...')
    try:
        table = []
        for i in range(0, geo['lines']):
            for j in range(0, geo['samples']):
                if array[i, j, 0] == 5:
                    table.append(array[i, j, :])
        table = np.array(table, np.int16)
    except:
        log.error('Failed during processing.')
        return 3

    # write output
    log.info('Writing output...')
    try:
        np.savetxt(des, table, delimiter=',', fmt=_fmt, header=lbl, comments='')
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
    log.info('Converting regrow stack to csv...')
    log.info('Regrow stack: {}'.format(args.ori))
    log.info('Saving as {}'.format(args.des))
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to convert image to csv
    regrow2csv(args.ori, args.des, args.overwrite)
