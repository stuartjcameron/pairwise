# -*- coding: utf-8 -*-
"""
Created on Fri Feb 09 03:23:49 2018

@author: Stuart
"""
from __future__ import print_function
from __future__ import division
import operator as op
from random import random
def kth_pair(k, n):
    """ Return the kth combination of 2 entries from the range 0 <= i < n
        Returns none if k is not in the range 0 <= k < n """
    for i in xrange(n):
        n -= 1
        if k < n:
            return i, k + i + 1
        k -= n

def pair_to_k(a, b, n):
    """ Return the position number of a pair a, b (reverse of kth_pair) """
    for i in xrange(a):
        b += n - i - 2
    return b - 1

def nc2(n):
    return reduce(op.mul, xrange(n, n-2, -1)) // 2    


def random_weighted_selection(weights, rand=None):
    sum_weights = float(sum(weights))
    prob_selection = [weight / sum_weights for weight in weights]
    #print 'prob_selection', prob_selection
    if rand is None:
        rand = random()
    #print 'rand', rand
    for i, prob in enumerate(prob_selection):
        if rand < prob:
            return i
        rand -= prob
        
        
        
weights = [25, 30, 45]
print(random_weighted_selection(weights))

for i in range(100):
    print i, random_weighted_selection(weights, rand=i/100.0)