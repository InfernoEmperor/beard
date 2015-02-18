# -*- coding: utf-8 -*-
#
# This file is part of Beard.
# Copyright (C) 2014 CERN.
#
# Beard is a free software; you can redistribute it and/or modify it
# under the terms of the Revised BSD License; see LICENSE file for
# more details.

"""Clustering evaluation metrics.

.. codeauthor:: Evangelos Tzemis <evangelos.tzemis@cern.ch>

"""
from __future__ import division
import numpy as np
from operator import mul
from itertools import groupby
from sklearn.metrics.cluster.supervised import check_clusterings


def _zero(x, y):
    return 0.0


def paired_precision_recall_fscore(labels_true, labels_pred):
    """Compute the pairwise variant of precision, recall and F-score.

    Precision is the ability not to label as positive a sample
    that is negative. The best value is 1 and the worst is 0.

    Recall is the ability to succesfully find all the positive samples.
    The best value is 1 and the worst is 0.

    F-score (Harmonic mean) can be thought as a weighted harmonic mean of
    the precision and recall, where an F-score reaches its best value at 1
    and worst at 0.

    Parameters
    ----------
    :param labels_true: 1d array containing the ground truth cluster labels.
    :param labels_pred: 1d array containing the predicted cluster labels.

    Returns
    -------
    :return float precision: calculated precision
    :return float recall: calculated recall
    :return float harmonic_mean: calculated harmonic_mean

    Reference
    ---------
    Levin, Michael et al., "Citation-based bootstrapping for large-scale
    author disambiguation", Journal of the American Society for Information
    Science and Technology 63.5 (2012): 1030-1047.

    """
    # Check that labels_* are 1d arrays and have the same size
    labels_true, labels_pred = check_clusterings(labels_true, labels_pred)

    # Check that input given is not the empty set
    if labels_true.shape == (0, ):
        raise ValueError(
            "input labels must not be empty.")

    # Assigns each label to its own cluster
    default_clustering = range(len(labels_pred))

    # Calculate precision
    numerator = _general_merge_distance(labels_true, labels_pred,
                                        fm=_zero, fs=mul)
    denominator = _general_merge_distance(default_clustering,
                                          labels_pred,
                                          fm=_zero, fs=mul)
    try:
        precision = 1.0 - numerator/denominator
    except ZeroDivisionError:
        precision = 1.0

    # Calculate recall
    numerator = _general_merge_distance(labels_true, labels_pred,
                                        fm=mul, fs=_zero)
    denominator = _general_merge_distance(labels_true,
                                          default_clustering,
                                          fm=mul, fs=_zero)
    try:
        recall = 1.0 - numerator/denominator
    except ZeroDivisionError:
        recall = 1.0

    # Calculate harmonic_mean - f_score

    # If both are zero (minimum score) then harmonic_mean is also zero
    if precision+recall == 0.0:
        harmonic_mean = 0.0
    else:
        harmonic_mean = 2.0*precision*recall/(precision + recall)

    return precision, recall, harmonic_mean


def paired_precision_score(labels_true, labels_pred):
    """Compute the pairwise variant of precision.

    Precision is the ability not to label as positive a sample
    that is negative. The best value is 1 and the worst is 0.

    Parameters
    ----------
    :param labels_true: 1d array containing the ground truth cluster labels.
    :param labels_pred: 1d array containing the predicted cluster labels.

    Returns
    -------
    :return float precision: calculated precision

    """
    p, _, _ = paired_precision_recall_fscore(labels_true, labels_pred)
    return p


def paired_recall_score(labels_true, labels_pred):
    """Compute the pairwise variant of recall.

    Recall is the ability to succesfully find all the positive samples.
    The best value is 1 and the worst is 0.

    Parameters
    ----------
    :param labels_true: 1d array containing the ground truth labels.
    :param labels_pred: 1d array containing the predicted labels.

    Returns
    -------
    :return float recall: calculated recall

    """
    _, r, _ = paired_precision_recall_fscore(labels_true, labels_pred)
    return r


def paired_f_score(labels_true, labels_pred):
    """Compute the pairwise variant of F score.

    F score can be thought as a weighted harmonic mean of the precision
    and recall, where an F score reaches its best value at 1
    and worst at 0.

    Parameters
    ----------
    :param labels_true: 1d array containing the ground truth cluster labels.
    :param labels_pred: 1d array containing the predicted cluster labels.

    Returns
    -------
    :return float harmonic_mean: calculated harmonic mean (f_score)

    """
    _, _, f = paired_precision_recall_fscore(labels_true, labels_pred)
    return f


def _cluster_samples(labels):
    """Group input to sets that belong to the same cluster.

    Parameters
    ----------
    :param labels: array with the cluster labels

    Returns
    -------
    :return: dictionary with keys the cluster ids and values a tuple containing
             the ids of elements tha belong to this cluster.

    """
    groupped_samples = groupby(np.argsort(labels), lambda i: labels[i])

    return {k: tuple(values) for k, values in groupped_samples}


def _general_merge_distance(y_true, y_pred,
                            fs=lambda x, y: 1.0, fm=lambda x, y: 1.0):
    """Implementation of Slice algorithm for computing generalized merge distance.

    Slice is a linear time algorithm.

    Merge Distance is the minimum number of splits and merges
    to get from R-flat to y_true.

    Parameters
    ----------
    :param y_true: array with the ground truth cluster labels.
    :param y_pred: array with the predicted cluster labels.
    :param fs: Optional. Function defining the cost of split.
    :param fm: Optional. Function defining the cost of merge.

    Returns
    -------
    :return float: Cost of getting from y_pred to y_true.

    Reference
    ---------
    Menestrina, David Michael., "Matching and unifying records in a
    distributed system", Department of Computer Science Thesis, Ph.D.
    dissertation, Stanford University (2010).
    """
    r = _cluster_samples(y_pred)
    s = _cluster_samples(y_true)
    r_sizes = {k: len(v) for k, v in r.items()}

    cost = 0.0
    for si in s.values():
        # determine which clusters in r contain the records of si
        p_map = {}
        for element in si:
            cl = y_pred[element]
            if cl not in p_map:
                p_map[cl] = 0
            p_map[cl] += 1

        # Compute cost to generate si
        si_cost = 0.0
        total_recs = 0
        for i, count in p_map.items():
            # add the cost to split ri
            if r_sizes[i] > count:
                si_cost += fs(count, r_sizes[i] - count)
            r_sizes[i] -= count
            if total_recs != 0:
                # Cost to merge into si
                si_cost += fm(count, total_recs)
            total_recs += count
        cost += si_cost
    return cost
