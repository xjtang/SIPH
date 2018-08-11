""" Module to combine regrowth map with biomass

    Args:
        --overwrite: overwrite or not
        rate: regrowth rate image
        year1: regrowth start year image
        year2: regrowth end year image
        biomass: biomassi image
        des: destination

"""
import os
import argparse
import numpy as np

from ...common import log
from ...io import stackGeo, stack2array, list2csv


def rgw_bms(rate, year1, year2, biomass, des, overwrite=False):
    """ combine regrowth maps with biomass map

    Args:
        rate (str): path and file name of regrowth rate image
        year1 (str): path and file name of regrowth start year image
        year2 (str): path and file name of regrowth end year2 image
        biomass (str): path and file name of biomass image
        des (str): path and file name of output
        overwrite (bool): overwrite or not

    Returns:
        0: successful
        1: error due to des
        2: error reading inputs
        3: error during processing
        4: error writing output

    """
    # check if output exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(os.path.basename(des)))
        return 1

    # initialize output
    log.info('Reading input...')
    try:
        geo = stackGeo(rate)
        array1 = stack2array(rate, 1, np.int16)
        array2 = stack2array(year1, 1, np.int16)
        array3 = stack2array(year2, 1, np.int16)
        array4 = stack2array(biomass, 1, np.int16)
    except:
        log.error('Failed to read inputs.')
        return 2

    # loop through pixels
    log.info('Combining...')
    try:
        result = [['Rate','Start','End','Biomass']]
        for i in range(0, geo['lines']):
            for j in range(0, geo['samples']):
                if array1[i, j] > 0:
                    result.append([array1[i, j], array2[i, j], array3[i, j],
                                    array4[i, j]])
        log.info('Total records: {}.'.format(len(result)))
    except:
        log.error('Failed during processing.')
        return 3

    # write output
    log.info('Writing output: {}'.format(des))
    if list2csv(result, des, overwrite) > 0:
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
    parser.add_argument('rate', default='./', help='regrowth rate image')
    parser.add_argument('year1', default='./', help='regrowth year image')
    parser.add_argument('year2', default='./', help='regrowth year image')
    parser.add_argument('biomass', default='./', help='biomass image')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Combining regrowth images with biomass image...')
    log.info('Regrowth rate image: {}'.format(args.rate))
    log.info('Regrowth start year image: {}'.format(args.year1))
    log.info('Regrowth end year image: {}'.format(args.year2))
    log.info('Biomass image: {}'.format(args.biomass))
    log.info('Saving as {}'.format(args.des))
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to combine regrowth image with biomass image
    rgw_bms(args.rate, args.year1, args.year2, args.biomass, args.des,
            args.overwrite)
