""" Class to translate an index into a pair of file names given a list of files.
    It will do this by caching 
"""

import operator as op
from random import randrange

def ncr(n, r):
    """ from https://stackoverflow.com/questions/4941753/is-there-a-math-ncr-function-in-python """
    r = min(r, n-r)
    if r == 0: return 1
    numer = reduce(op.mul, xrange(n, n-r, -1))
    denom = reduce(op.mul, xrange(1, r+1))
    return numer//denom


def ncr2(n):
    return reduce(op.mul, xrange(n, n-2, -1)) // 2    

def kth_pair_files(k, file_list):
    left, right = kth_pair(len(file_list))
    return file_list[left], file_list[right]

"""   
def kth_pair(k, n):
    for i in range(n):
        n -= 1
        if k < n:
            return i, k + i + 1
        k -= n
"""
def kth_pair(k, n):
    """ Return the kth combination of 2 entries from the range 0 <= i < n
        Returns none if k is not in the range 0 <= k < n """
    for i in xrange(n):
        n -= 1
        if k < n:
            return i, k + i + 1
        k -= n
        
        
        
nl = [1, 2, 3, 4, 5]
entries = 100
#print kth_pair(2, entries)
#combos = ncr2(entries)
#print [kth_pair(i, entries) for i in range(combos)]

def randrange_excluding(stop, excl_list):
    """ Return a random integer n such that 0 <= n < b
        but n is not in excl_list. The excl_list will be sorted in-place """
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
            
#for _ in range(50):
#    print randrange_excluding(5, [1, 2])