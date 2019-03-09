# -*- coding: utf-8 -*-
"""
Created on Wed Feb 07 12:19:20 2018

@author: Stuart
"""
from random import sample, randrange
import time

def randrange_excluding(stop, excl_list):
    """ Return a random integer n such that 0 <= n < b
        but n is not in excl_list. The excl_list will be sorted in-place.
        
        Note, this function has been speed-tested to make sure it won't crash
        the application for stop==100,001, len(excl_list)==100,000 (takes around
        0.15s on my computer)
        
        randrange will raise a ValueError if the length of the exclusion list
        is the same as stop
        """
    
    if excl_list:
        excl_list.sort()
        if excl_list[-1] >= stop:
            raise ValueError("Values in excl_list are outside of the range")
        r = randrange(stop - len(excl_list))
        for x in excl_list:
            if r < x:
                return r
            else:
                r += 1
        return r
    else:
        return randrange(stop)
        
        
excl_len = 100000
stop = 1000001
excl_list = sample(xrange(stop), excl_len)
start = time.clock()
r = randrange_excluding(stop, excl_list)
finished = time.clock()
print 'time needed', finished-start

