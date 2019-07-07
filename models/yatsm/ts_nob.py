""" Module for calculating number of clear observations from YATSM cache files

    Args:
        -y (yearly): calculate yearly
        -g (grow): calculate growing season
        --overwrite: overwrite or not
        img: an image to grab spatial reference
        ori: origin of config yaml file
        des: destination

"""
import os
import sys
import argparse
import yaml
import numpy as np

from ...io import stack2array, stackGeo, array2stack, csv2list
from ...common import log, get_files


def get_ts_nob(img, ori, des, yearly=False, grow=False, overwrite=False):
    """ Calculate numebr of observation from YATSM cache files

    Args:
        img (str): an image for getting spatial reference
        ori (str): config yaml file
        des (str): output path and/or filename
        yearly (bool): yearly result or not
        grow (bool): growing season only or not
        overwrite (bool): overwrite or not

    Returns:
        0: successful
        1: error due to des
        2: error reading input
        3: error during processing
        4: error during writing output

    """
    # check if output already exists
    if yearly:
        if not os.path.exists(des):
            log.warning('{} does not exist, trying to create one.'.format(des))
            try:
                os.makedirs(des)
            except:
                log.error('Cannot create output folder {}'.format(des))
                return 1
    else:
        if (not overwrite) and os.path.isfile(des):
            log.error('{} already exists.'.format(des.split('/')[-1]))
            return 1

    # read input config file
    log.info('Reading config file...')
    try:
        with open(ori, 'r') as stream:
            config = yaml.load(stream)
            img_list = config['dataset']['input_file']
            cache_path = config['dataset']['cache_line_dir']
    except:
        log.error('Failed to read config file {}'.format(ori))
        return 2

    # grab dates from image list
    log.info('Grabing dates...')
    try:
        ts_dates = [x[0] for x in csv2list(img_list, True)]
        ts_years = [int(x/1000) for x in ts_dates]
        ts_doys = [x-int(x/1000)*1000 for x in ts_dates]
    except:
        log.error('Failed to grab dates from {}'.format(img_list))
        return 2

    # get spatial reference
    log.info('Reading spatial reference...')
    try:
        geo = stackGeo(img)
        lines = geo['lines']
        samples = geo['samples']
    except:
        log.error('Failed to read spatial from {}'.format(img))
        return 2

    # initialize output
    log.info('Initializing output...')
    try:
        nob = np.zeros((lines, samples, 2), np.int16) + cons.NODATA
    except:
        log.error('Failed to initialize output of size {},{}'.format(lines,
                    samples))
        return 3

    # calculate nob
    log.info('Calculating nob...')
    if yearly:
        years = range(min(ts_years), max(ts_years) + 1)
    else:
        years = [0]
        des2 = des
    for year in years:
        if year > 0:
            log.info('Processing year {}...'.format(year))
            des2 = os.path.join(des, 'nob_{}.tif'.format(year))
        for i in range(0, lines):
            cache_file = get_files(cache_path, '*{}*npz'.format(i))
            cache = np.load(os.path.join(cache_file[0][0], cache_file[0][1]))
            for j in range(0, samples):
                ts = cache['Y'][:, :, x]



    # done
    log.info('Process completed.')
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-y', '--yearly', action='store_true',
                        help='yearly results or not')
    parser.add_argument('-g', '--grow', action='store_true',
                        help='just growing season or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('img', default='./', help='image to get spatial')
    parser.add_argument('ori', default='./', help='origin of config files')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start calculating nob...')
    log.info('Get spatial reference from {}'.format(args.img))
    log.info('Config file: {}'.format(args.ori))
    log.info('Saving as {}'.format(args.des))
    if args.yearly:
        log.info('Yearly results.')
    if args.grow:
        log.info('Growing season only.')
    if args.overwrite:
        log.info('Overwriting existing image.')

    # run function to get nob
    get_ts_nob(args.img, args.ori, args.des, args.yearly, args.grow,
                args.overwrite)
