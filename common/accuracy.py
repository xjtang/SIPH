""" Module for common functions related to accuracy assessment
"""
import math
import numpy as np


def conf_mat(ref, _map):
    """ calculate confusion matrix

    Args:
        ref (list, int): list of reference labels
        _map (list, int): list of map labels

    Returns:
        conf (ndarray): confusion matrix

    """
    ref_cls = np.sort(np.unique(np.array((ref, _map)))).tolist()
    map_cls = ref_cls
    nclass = max(len(ref_cls), len(map_cls))
    conf = np.zeros([nclass + 1, nclass + 1], dtype='int16')
    conf[0, 1:] = map_cls
    conf[1:, 0] = ref_cls
    conf[0, 0] = len(_map)
    for i in range(0, len(_map)):
        conf[ref_cls.index(ref[i]) + 1, map_cls.index(_map[i]) + 1] += 1
    return conf


def accuracy_assessment(sta, ref, _map, sta_size):
    """ accuracy assessment where stratification is different from map

    Args:
        sta (ndarray, int): list of strata
        ref (ndarray, int): list of reference labels
        _map (ndarray, int): list of map labels
        sta_size (ndarray, int): size of each stratum

    Returns:
        r (dict): results inlcuding accuracies and confusion matrix

    """
    # get basic information
    sta_cls = np.sort(np.unique(sta)).tolist()
    ref_cls = np.sort(np.unique(np.array((ref, _map)))).tolist()
    map_cls = ref_cls
    n = sta_size[:, 1].sum()
    n_cls = max(len(ref_cls), len(map_cls))
    n_sta = len(sta_cls)
    n_smp = len(ref)
    sta_cnt = np.zeros(n_sta, dtype='int32')
    nh = np.zeros(n_sta, dtype='int32')
    for i in range(0, n_sta):
        nh[i] = (sta == sta_cls[i]).sum()
        sta_cnt[i] = sta_size[sta_size[:, 0].tolist().index(sta_cls[i]), 1]

    # initialize coefficients
    y_all = np.zeros(n_smp, dtype='int32')
    y_user = np.zeros([n_smp, n_cls], dtype='int32')
    x_user = np.zeros([n_smp, n_cls], dtype='int32')
    y_prod = np.zeros([n_smp, n_cls], dtype='int32')
    x_prod = np.zeros([n_smp, n_cls], dtype='int32')
    y_area = np.zeros([n_smp, n_cls], dtype='int32')
    y_err = np.zeros([n_cls, n_cls, n_smp], dtype='int32')

    # initialize coefficient means
    yh_all = np.zeros(n_sta)
    yh_user = np.zeros([n_cls, n_sta])
    xh_user = np.zeros([n_cls, n_sta])
    yh_prod = np.zeros([n_cls, n_sta])
    xh_prod = np.zeros([n_cls, n_sta])
    yh_area = np.zeros([n_cls, n_sta])
    yh_err = np.zeros([n_cls, n_cls, n_sta])

    # initialize coefficient variances and covariances
    yv_all = np.zeros(n_sta)
    yv_user = np.zeros([n_cls, n_sta])
    xv_user = np.zeros([n_cls, n_sta])
    co_user = np.zeros([n_cls, n_sta])
    yv_prod = np.zeros([n_cls, n_sta])
    xv_prod = np.zeros([n_cls, n_sta])
    co_prod = np.zeros([n_cls, n_sta])
    yv_area = np.zeros([n_cls, n_sta])

    # initialize accuracies
    X_user = np.zeros(n_cls)
    X_prod = np.zeros(n_cls)
    conf = np.zeros([n_cls, n_cls])
    a_user = np.zeros(n_cls)
    a_prod = np.zeros(n_cls)
    a_all = 0.0
    area = np.zeros(n_cls)

    # initialize standard error
    v_area = np.zeros(n_cls)
    v_user = np.zeros(n_cls)
    v_prod = np.zeros(n_cls)
    v_all = 0.0
    se_area = np.zeros(n_cls)
    se_user = np.zeros(n_cls)
    se_prod = np.zeros(n_cls)
    se_all = 0.0

    # calculate coefficients
    for i in range(0, n_smp):
        y_all[i] = (_map[i] == ref[i])
        y_user[i, :] = (_map[i] == ref[i]) & (map_cls == _map[i])
        x_user[i, :] = (map_cls == _map[i])
        y_prod[i, :] = (_map[i] == ref[i]) & (map_cls == ref[i])
        x_prod[i, :] = (map_cls == ref[i])
        y_area[i, :] = (map_cls == ref[i])
        y_err[map_cls.index(_map[i]), map_cls.index(ref[i]), i] = 1

    # calculate coefficients means
    for i in range(0, n_sta):
        yh_all[i] = (y_all[sta == sta_cls[i]]).mean()
        yh_user[:, i] = (y_user[sta == sta_cls[i], :]).mean(0)
        xh_user[:, i] = (x_user[sta == sta_cls[i], :]).mean(0)
        yh_prod[:, i] = (y_prod[sta == sta_cls[i], :]).mean(0)
        xh_prod[:, i] = (x_prod[sta == sta_cls[i], :]).mean(0)
        yh_area[:, i] = (y_area[sta == sta_cls[i], :]).mean(0)
        yh_err[:, :, i] = (y_err[:, :, sta == sta_cls[i]]).mean(2)

    # calculate coefficients variance
    for i in range(0, n_sta):
        yv_all[i] = (y_all[sta == sta_cls[i]]).var(ddof=1)
        for j in range(0, n_cls):
            yv_user[j, i] = (y_user[sta == sta_cls[i], j]).var(ddof=1)
            xv_user[j, i] = (x_user[sta == sta_cls[i], j]).var(ddof=1)
            yv_prod[j, i] = (y_prod[sta == sta_cls[i], j]).var(ddof=1)
            xv_prod[j, i] = (x_prod[sta == sta_cls[i], j]).var(ddof=1)
            yv_area[j, i] = (y_area[sta == sta_cls[i], j]).var(ddof=1)

    # calculate coefficients covariance
    for i in range(0, n_sta):
        for j in range(0, n_cls):
            co_user[j, i] = np.cov(y_user[sta == sta_cls[i], j],
                                x_user[sta == sta_cls[i], j])[1, 0]
            co_prod[j, i] = np.cov(y_prod[sta == sta_cls[i], j],
                                x_prod[sta == sta_cls[i], j])[1, 0]

    # calculate accuracies
    a_all = (np.matmul(yh_all, sta_cnt)) / n
    for i in range(0, n_cls):
        X_user[i] = np.matmul(xh_user[i, :], sta_cnt)
        X_prod[i] = np.matmul(xh_prod[i, :], sta_cnt)
        a_user[i] = ((np.matmul(yh_user[i, :], sta_cnt)) /
                        (np.matmul(xh_user[i, :], sta_cnt)))
        a_prod[i] = ((np.matmul(yh_prod[i, :], sta_cnt)) /
                        (np.matmul(xh_prod[i, :], sta_cnt)))
        area[i] = (np.matmul(yh_area[i, :], sta_cnt)) / n
        for j in range(0, n_cls):
            conf[i, j] = (np.matmul(yh_err[i, j, :], sta_cnt)) / n

    # calculate standard errors
    v_all = np.matmul((((sta_cnt/n)**2) * (1 - nh / sta_cnt)), (yv_all / nh))
    se_all = math.sqrt(v_all)
    for i in range(0, n_cls):
        v_area[i] = np.matmul((((sta_cnt/n)**2) * (1 - nh / sta_cnt)),
                                            (yv_area[i, :] / nh))
        se_area[i] = math.sqrt(v_area[i])
        v_user[i] = np.matmul((((sta_cnt/X_user[i])**2) * (1 - nh / sta_cnt)),
                        ((yv_user[i, :] + a_user[i]**2 * xv_user[i, :] -
                            2 * a_user[i] * co_user[i, :]) / nh))
        se_user[i] = math.sqrt(v_user[i])
        v_prod[i] = np.matmul((((sta_cnt/X_prod[i])**2) * (1 - nh / sta_cnt)),
                        ((yv_prod[i, :] + a_prod[i]**2 * xv_prod[i, :] -
                            2 * a_prod[i] * co_prod[i, :]) / nh))
        se_prod[i] = math.sqrt(v_prod[i])

    # prepare output
    r = {
        'oval_acc' : (a_all, se_all),
        'user_acc' : (a_user, se_user),
        'prod_acc' : (a_prod, se_prod),
        'area' : area,
        'se_area' : se_area,
        'conf' : conf,
    }

    # done
    return r


def numeric_example():
    """ data for numeric example to test the accuracy assessment function

    Returns:
        r (tuple): example data

    """
    sta = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                    2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                    3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                    4, 4, 4, 4, 4, 4, 4, 4, 4, 4], dtype='int8')
    _map = np.array([1, 1, 1, 1, 1, 1, 1, 2, 2, 2,
                        1, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                        2, 2, 3, 3, 3, 3, 3, 3, 2, 2,
                        4, 4, 4, 4, 4, 4, 4, 4, 4, 4], dtype='int8')
    ref = np.array([1, 1, 1, 1, 1, 3, 2, 1, 2, 3,
                    1, 2, 2, 2, 2, 2, 1, 1, 2, 2,
                    3, 3, 3, 3, 3, 4, 4, 2, 2, 1,
                    4, 4, 4, 4, 4, 4, 4, 3, 3, 2], dtype='int8')
    sta_size = np.array([[1,40000],[2,30000],[3,20000],[4,10000]],dtype='int32')
    return (sta, ref, _map, sta_size)
