""" Module for gridding SIF netCDF and save as stacked image

    Args:
        -p (pattern): searching pattern
        -g (grid): gridding resolution in degree
        -c (comp): compositing time interval (d or w)
        -b (batch): batch process, thisjob and totaljob
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import sys
import argparse

from osgeo import gdal

from ...io import sifn2ln, sif2grid, sifn2date
from ...common import constants as cons
from ...common import log, get_files, manage_batch


def sif_to_grid(pattern, res, comp, ori, des, overwrite=False, recursive=False,
                    batch=[1,1]):
    """ grid SIF netCDF and save as stacked images

    Args:
        pattern (str): searching pattern, e.g. *.nc
        res (float): grid resolution
        comp (str): compositing time interval
        ori (str): place to look for inputs
        des (str): place to save outputs
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not
        batch (list, int): batch processing, [thisjob, totaljob]

    Returns:
        0: successful
        1: error due to des
        2: error when searching files
        3: found no file
        4: error when handling compositing

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
        sif_list = get_files(ori, pattern, recursive)
        n = len(sif_list)
    except:
        log.error('Failed to search for {}'.format(pattern))
        return 2
    else:
        if n == 0:
            log.error('Found no {}'.format(pattern))
            return 3
        else:
            log.info('Found {} files.'.format(n))

    # compositing
    if comp == 'w':
        # not the best way to do this, a bit inefficient
        sif_list2 = []
        date_list = []
        md = []
        for i, x in enumerate(sif_list):
            date_list.append(sifn2date(x[1]))
        for year in range(int(min(date_list)/1000), int(max(date_list)/1000)+1):
            for week in range(0, 52):
                sif_week = []
                for i, x in enumerate(sif_list):
                    doy = date_list[i]
                    if (doy > (year*1000+week*7))&(doy <= year*1000+week*7+7):
                        sif_week.append(os.path.join(x[0], x[1]))
                    if (week == 51)&(doy > year*1000+364)&(doy < year*1000):
                        sif_week.append(os.path.join(x[0], x[1]))
                if len(sif_week) > 0:
                    sif_list2.append(sif_week)
                    md.append(year*1000+week*7+1)
    elif comp == 'd':
        sif_list2 = [[os.path.join(x[0], x[1])] for x in sif_list]
    else:
        log.error('Invalid compositing time interval {}'.format(comp))
        return 4

    # handle batch processing
    if batch[1] > 1:
        log.info('Handling batch process...')
        sif_list2 = manage_batch(sif_list2, batch[0], batch[1])
        if comp == 'w':
            md = manage_batch(md, batch[0], batch[1])
        n = len(sif_list2)
        log.info('{} files to be processed by this job.'.format(n))

    # loop through all files
    count = 0
    log.info('Start processing files...')
    for i, sif in enumerate(sif_list2):
        log.info('Processing {}'.format(sif[0]))
        if comp == 'd':
            if sif2grid(sif, '{}.tif'.format(os.path.join(des,
                        sifn2ln(os.path.basename(sif[0]), res))), res,
                        overwrite) == 0:
                count += 1
        elif comp == 'w':
            if sif2grid(sif, '{}.tif'.format(os.path.join(des,
                        sifn2ln(os.path.basename(sif[0]), res, 'WA', md[i]))),
                        res, overwrite) == 0:
                count += 1

    # done
    log.info('Process completed.')
    log.info('Successfully processed {}/{} files.'.format(count, n))
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pattern', action='store', type=str,
                        dest='pattern', default='ret*.nc',
                        help='searching pattern')
    parser.add_argument('-g', '--grid', action='store', type=float, dest='grid',
                        default=0.5, help='gridding resolution')
    parser.add_argument('-c', '--comp', action='store', type=str, dest='comp',
                        default='d', help='compositing time interval (d or w)')
    parser.add_argument('-b', '--batch', action='store', type=int, nargs=2,
                        dest='batch', default=[1,1],
                        help='batch process, [thisjob, totaljob]')
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
    log.info('Start gridding SIF...')
    log.info('Resolution {}'.format(args.grid))
    log.info('Compositing by {}'.format(args.comp))
    log.info('Running job {}/{}'.format(args.batch[0], args.batch[1]))
    log.info('Looking for {}'.format(args.pattern))
    log.info('In {}'.format(args.ori))
    log.info('Saving in {}'.format(args.des))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to grid SIF
    sif_to_grid(args.pattern, args.grid, args.comp, args.ori, args.des,
                args.overwrite, args.recursive, args.batch)
