""" Module for a set of small functions frequently used by other modules
"""
from calendar import isleap


def date_to_doy(year,month,day,day_only=False):
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
