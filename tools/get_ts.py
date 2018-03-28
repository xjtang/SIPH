""" Module for grabing time series of one pixel from YATSM cache file

    Args:
        --overwrite: overwrite or not
        x: pixel location, x
        y: pixel location, y
        ori: origin of config yaml file
        des: destination

"""
import os
import sys
import argparse
import yaml
import numpy as np

from ..io import csv2list
from ..common import log, get_files


def grab_ts(x, y, ori, des, overwrite=False):
    """ Grab time series for a single pixel from YATSM cache file

    Args:
        x (int): pixel location x
        y (int): pixel location y
        ori (str): oath to config file
        des (str): output path and filename
        overwrite (bool): overwrite or not

    Returns:
        0: successful
        1: error due to des
        2: error reading input
        3: error during processing
        4: error during writing output

    """
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(des.split('/')[-1]))
        return 1

    # read input images
    log.info('Reading config file...')
    try:
        with open(ori, 'r') as stream:
            config = yaml.load(stream)
            img_list = config['dataset']['input_file']
            cache_path = config['dataset']['cache_line_dir']
    except:
        log.error('Failed to read config file {}'.format(ori))
        return 2

    # looking for cache file
    log.info('Locating line cache...')
    cache_file = get_files(cache_path, 'yatsm*{}*npz'.format(y))
    if len(cache_file) == 0:
        log.error('Found no cache for line {}'.format(y))
        return 3

    # grab dates from image list
    log.info('Grabing dates...')
    try:
        dates = csv2list(img_list, True)
    except:
        log.error('Failed to grab dates from {}'.format(img_list))
        return 4

    # grab pixel from cache file
    log.info('Grabing time series...')
    try:
        cache = np.load(os.path.join(cache_file[0][0], cache_file[0][1]))
        ts = cache['Y'][:, :, x]
    except:
        log.error('Failed to grab time series from {}'.format(cache_file[0][1]))
        return 4

    # write output
    log.info('Writing output: {}'.format(des))
    try:
        r = np.append([[x[0] for x in dates]], ts, axis=0)
        np.savetxt(des, r.T, delimiter=',', fmt='%d')
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
    parser.add_argument('x', type=int, default=1, help='pixel location x')
    parser.add_argument('y', type=int, default=1, help='pixel location y')
    parser.add_argument('ori', default='./', help='origin of config files')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start grabing time series...')
    log.info('Pixel: [{}, {}]'.format(args.x, args.y))
    log.info('Config file: {}.'.format(args.ori))
    log.info('Saving as {}'.format(args.des))
    if args.overwrite:
        log.info('Overwriting existing output.')

    # run function to grab time series
    grab_ts(args.x, args.y, args.ori, args.des, args.overwrite)
