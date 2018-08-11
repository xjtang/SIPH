""" Module for generating image highlighting pixels over the SD threshold

    Args:
        -p (pattern): searching pattern
        -b (batch): batch process, thisjob and totaljob
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        ori: origin
        des: destination
        img: an example image to get the spatial reference

"""
import os
import argparse
import numpy as np
import scipy.io as sio

from osgeo import gdal

from ...io import stackGeo, array2stack
from ...common import log, get_files, manage_batch, get_int
from ...common import constants as cons


def batch_area_over_threshold(pattern, ori, des, img, overwrite=False,
                                recursive=False, batch=[1,1]):
    """ Generage regular image file from stack image

    Args:
        pattern (str): searching pattern, e.g. ts*mat
        ori (str): place to look for inputs
        des (str): place to save outputs
        img (str): path to example image
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not
        batch (list, int): batch processing, [thisjob, totaljob]

    Returns:
        0: successful
        1: error when initializing
        2: error when searching files
        3: found no file

    """
    # get list of available cache files
    log.info('Searching for cache files...')
    cache_list = get_files(ori, pattern, recursive)
    ncache = len(cache_list)
    if ncache == 0:
        log.error('Found no cache files with {} in {}'.format(pattern, ori))
        return 1
    else:
        log.info('Found {} cache files.'.format(ncache))

    # get list of dates
    try:
        date_list = sio.loadmat(os.path.join(cache_list[0][0],
                                cache_list[0][1]))['Date']
        log.info('Total {} dates to be processed.'.format(len(date_list)))
    except:
        log.error('Failed to get date list.')
        return 1

    # figure out what dates this job is going to process
    try:
        date_list = manage_batch(date_list, batch[0], batch[1])
        ndate = len(date_list)
        log.info('{} to be proceessed by this job.'.format(ndate))
    except:
        log.error('Failed to manage batch job.')
        return 1

    # get image spatial reference
    try:
        geo = stackGeo(img)
        if geo['lines'] == ncache:
            log.info('Image size matches ncache found.')
        elif geo['lines'] > ncache:
            log.warning('Some cache file may be missing {}/{}.'.format(ncache,
                        geo['lines']))
        else:
            log.error('nlines {} does not match ncache {}.'.format(geo['lines'],
                        ncache))
            return 1
    except:
        log.error('Failed to read spatial reference from {}'.format(img))
        return 1

    # initialize output
    result = np.zeros((geo['lines'], geo['samples']), np.int16) + cons.NODATA
    count = 0

    # loop through image list
    for d in date_list:
        # loop through cache files
        for f in cache_list:
            try:
                # read cache file
                cache = sio.loadmat(os.path.join(f[0], f[1]))
                # figure out which line this is
                i = get_int(f[1])[0] - 1
                # generate results
                j = np.argmax(np.amin((cache['Date'] == d), 1))
                x = cache['Data'][:, j]
                x[(x==1)|(x==5)|(x==7)] = 0
                x[x>=2] = 1
                result[i, :] = x
            except:
                log.warning('Failed to process line {}.'.format(i + 1))
                continue
        # write output
        fn = os.path.join(des, 'AOSD_{}_{}.tif'.format(d[0], d[1]))
        if array2stack(result, geo, fn, ['Area over SD threshold'], cons.NODATA,
                        gdal.GDT_Int16, overwrite) == 0:
            count += 1
        else:
            log.warning('Failed to process data {}.{}'.format(d[0], d[1]))

    # done
    log.info('Process completed.')
    log.info('{}/{} successful.'.format(count, ndate))
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pattern', action='store', type=str,
                        dest='pattern', default='ts*mat',
                        help='searching pattern')
    parser.add_argument('-b', '--batch', action='store', type=int, nargs=2,
                        dest='batch', default=[1,1],
                        help='batch process, thisjob and totaljob')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    parser.add_argument('img', default='./', help='example image')
    args = parser.parse_args()

    # check arguments
    if not 1 <= args.batch[0] <= args.batch[1]:
        log.error('Invalid batch inputs: [{}, {}]'.format(args.batch[0],
                    args.batch[1]))
        sys.exit(1)

    # print logs
    log.info('Start generating images...')
    log.info('Running job {}/{}'.format(args.batch[0], args.batch[1]))
    log.info('Looking for {}'.format(args.pattern))
    log.info('In {}'.format(args.ori))
    log.info('Saving in {}'.format(args.des))
    log.info('Copy spatial reference from {}'.format(args.img))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting existing image.')

    # run function to generate images of area over SD threhold
    batch_area_over_threshold(args.pattern, args.ori, args.des, args.img,
                                args.overwrite, args.recursive, args.batch)
