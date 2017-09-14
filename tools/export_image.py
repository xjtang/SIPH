""" Module for exporting stack image as regular image file (e.g. png)

    Args:
        -p (pattern): searching pattern
        -b (batch): batch process, thisjob and totaljob
        -c (comp): band composite
        -s (stretch): image stretch
        -f (format): output image format (e.g. rgb)
        -m (mask): mask band, 0 for no mask
        -r (result): result file, 'NA' for no result
        -w (window): chop window
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import sys
import argparse

from ..io import stack2image
from ..common import log, get_files, manage_batch, get_date


def batch_stack2image(pattern, ori, des, bands=[3,2,1], stretch=[0,5000],
                        _format='rgb', mask=0, result='NA', rvalue=0, window=0,
                        overwrite=False, recursive=True, batch=[1,1]):
    """ Generage regular image file from stack image

    Args:
        pattern (str): searching pattern, e.g. VNP*gtif
        ori (str): place to look for inputs
        des (str): place to save outputs
        bands (list, int): band composite, [red, green, blue]
        stretch (list, int): stretch, [min, max]
        _format (str): output format, e.g. rgb
        mask (int): mask band, 0 for no mask
        result (str): path to result image
        rvalue (int): result value, 0 to use date
        window (list, int): chop image, [xmin, ymin, xmax, ymax], 0 for no chop
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not
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
        img_list = get_files(ori, pattern, recursive)
        n = len(img_list)
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
        img_list = manage_batch(img_list, batch[0], batch[1])
        n = len(img_list)
        log.info('{} files to be processed by this job.'.format(n))

    # loop through all files
    count = 0
    log.info('Start exporting image...')
    for img in img_list:
        log.info('Processing {}'.format(img[1]))
        # if result is a folder, find the result file that has the same date
        if os.path.isdir(result):
            # search for corresponding result file
            d = get_date(img[1])
            rfile = get_files(result,'*{}*.tif'.format(d))
            if len(rfile) == 0:
                log.warning('Found no result for date {}'.format(d))
                result2 = 'NA'
            else:
                result2 = os.path.join(rfile[0][0], rfile[0][1])
        else:
            result2 = result
        if stack2image('{}/{}'.format(img[0], img[1]),
                    '{}/{}.png'.format(des, img[1].split('.')[0]), bands,
                    stretch, mask, result2, rvalue, _format, window, overwrite,
                    False) == 0:
            count += 1

    # done
    log.info('Process completed.')
    log.info('Successfully exported {}/{} images.'.format(count, n))
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
    parser.add_argument('-c', '--comp', action='store', type=int, nargs=3,
                        dest='comp', default=[3,2,1], help='band composite')
    parser.add_argument('-s', '--stretch', action='store', type=int, nargs=2,
                        dest='stretch', default=[0,5000], help='image stretch')
    parser.add_argument('-f', '--format', action='store', type=str,
                        dest='format', default='rgb', help='output format')
    parser.add_argument('-m', '--mask', action='store', type=int, dest='mask',
                        default=0, help='mask band, 0 for no mask')
    parser.add_argument('-r', '--result', action='store', type=str,
                        dest='result', default='NA', help='result file')
    parser.add_argument('-v', '--rvalue', action='store', type=int,
                        dest='rvalue', default=0, help='result value')
    parser.add_argument('-w', '--window', action='store', type=int, nargs=4,
                        dest='window', default=0, help='chop window')
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
    log.info('Start exporting image...')
    log.info('Running job {}/{}'.format(args.batch[0], args.batch[1]))
    log.info('Looking for {}'.format(args.pattern))
    log.info('In {}'.format(args.ori))
    log.info('Saving in {}'.format(args.des))
    log.info('Band composite:[{}, {}, {}]'.format(args.comp[0], args.comp[1],
                                                    args.comp[2]))
    log.info('Image stretch: [{}, {}]'.format(args.stretch[0], args.stretch[1]))
    log.info('Output format: {}'.format(args.format))
    log.info('Result file: {}'.format(args.result))
    if args.rvalue == 0:
        log.info('Use date for result value.')
    else:
        log.info('Result Value: {}'.format(args.rvalue))
    if type(args.window) == list:
        log.info('Chop window: [{}, {}, {}, {}]'.format(args.window[0],
                    args.window[1], args.window[2], args.window[3]))
    if args.mask > 0:
        log.info('Mask band: {}'.format(args.mask))
    else:
        log.info('No mask band.')
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting existing image.')

    # run function to export image files
    batch_stack2image(args.pattern, args.ori, args.des, args.comp, args.stretch,
                        args.format, args.mask, args.result, args.rvalue,
                        args.window, args.overwrite, args.recursive, args.batch)
