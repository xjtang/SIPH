""" Module for common functions frequently used by other modules
"""
from __future__ import division

import os
import fnmatch

from calendar import isleap


def date_to_doy(year,month,day,day_only=False):
    """ convert date to day-of-year

    Args:
        year (int): year
        month (int): month
        day (int): day
        day_only (bool): return day only or day with year

    Returns:
        doy (int): day of year

    """
    # initialize
    doy = 0

    # leap yaer
    day_in_month = [0,31,28,31,30,31,30,31,31,30,31,30]
    if isleap(year):
        day_in_month[2] = 29

    # calculate doy
    doy = sum(day_in_month[0:month]) + day
    if not day_only:
        doy = doy + year * 1000

    # done
    return doy


def doy_to_date(doy):
    """ convert day of year to date

    Args:
        doy (int): day of year

    Returns:
        (year, month, day) (int): year, month, day

    """
    # initialize
    year, month, day = 0, 0, 0

    # leap year
    year = doy//1000
    day_in_month = [31,28,31,30,31,30,31,31,30,31,30,31]
    if isleap(year):
        day_in_month[1] = 29

    # calculate date
    doy = doy - year * 1000
    for i in range(0,12):
        doy = doy - day_in_month[i]
        if doy <= 0:
            month = i + 1
            day = doy + day_in_month[i]
            break

    return (year, month, day)


def get_files(path, pattern, recursive=False):
    """ search files with pattern

    Args:
        path (str): location to search in
        pattern (str): searching pattern

    Returns:
        file_list (list): list of files, [path, name]

    """
    if recursive:
        return [[x[0], x[1]] for x in [[pn, f] for pn, dn, fn in os.walk(path)
                for f in fn] if fnmatch.fnmatch(x[1],pattern)]
    else:
        return [[path, f] for f in fnmatch.filter(os.listdir(path), pattern)]


def manage_batch(works, job, n_job):
    """ manage batch job work loads

    Args:
        works (list): list of work loads
        job (int): sequence of this job
        n_job (int): total number of jobs

    Returns:
        thisjob (list): work load for this job

    """
    return works[(job - 1):len(works):n_job]


def show_progress(i, n, step):
    """ calculate percent progress for reporting

    Args:
        i (int): current number
        n (int): total number
        step (int): interval between reporting

    Returns:
        pct (int): report percent
        -1: no need to report

    """
    if int(((i - 1) / n * 100) // step) < int((i / n * 100) // step):
        return int(i / n * 100)
    else:
        return -1


def get_date(x, start=9, _format='YYYYDDD'):
    """ extract date from filename

    Args:
        x (str): filename
        start (int): date starting index
        _format (str): format of the date, e.g. YYYYDDD

    Returns:
        date (int): date

    """
    return int(x[start:(start + len(_format))])
