""" Module for getting observation footprint from swath data and save as
    shapefile

    Args:
        -p (pattern): searching pattern
        -b (batch): batch process, thisjob and totaljob
        -e (epsg): coordinate system in EPSG
        -R (recursive): recursive when searching, or not
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import argparse

from ..common import log, get_files, manage_batch
from ..io import csv2shape


def batch_swath_footprint(pattern, ori, des, epsg=3857, overwrite=False,
                            recursive=False, batch=[1,1]):
    """ Get observation footprint from swath data and save as shapefile

    Args:
        pattern (str): searching pattern, e.g. MOD*csv
        ori (str): place to look for inputs
        des (str): place to save outputs
        epsg (int): coordinate system in EPSG
        recursive (bool): recursive when searching file, or not
        overwrite (bool): overwrite or not
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
        csv_list = get_files(ori, pattern, recursive)
        n = len(csv_list)
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
        csv_list = manage_batch(csv_list, batch[0], batch[1])
        n = len(csv_list)
        log.info('{} files to be processed by this job.'.format(n))

    # loop through all files
    count = 0
    log.info('Start extracting observation footprint...')
    for swath in csv_list:
        log.info('Processing {}'.format(swath[1]))
        if csv2shape('{}/{}'.format(swath[0], swath[1]),
                        '{}/{}.shp'.format(des, swath[1].split('.csv')[0]),
                        'ellipse', epsg, overwrite, False) == 0:
            count += 1

    # done
    log.info('Process completed.')
    log.info('Successfully generated {}/{} shapefiles.'.format(count, n))
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pattern', action='store', type=str,
                        dest='pattern', default='VNP*tif',
                        help='searching pattern')
    parser.add_argument('-b', '--batch', action='store', type=int, nargs=2,
                        dest='batch', default=[1,1],
                        help='batch process, thisjob and totaljob')
    parser.add_argument('-e', '--epsg', action='store', type=int, dest='epsg',
                        default=3857, help='coordinate system in EPSG')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
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
    log.info('Start extracting observation footprint from swath data...')
    log.info('Running job {}/{}'.format(args.batch[0], args.batch[1]))
    log.info('Looking for {}'.format(args.pattern))
    log.info('In {}'.format(args.ori))
    log.info('Saving in {}'.format(args.des))
    log.info('EPSG:{}'.format(args.epsg))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to generate footprint files
    batch_swath_footprint(args.pattern, args.ori, args.des, args.epsg,
                            args.overwrite, args.recursive, args.batch)
