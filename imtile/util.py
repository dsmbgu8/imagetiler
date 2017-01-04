from __future__ import absolute_import, print_function, division
import sys,os

from os.path import exists as pathexists, join as pathjoin, split as pathsplit
from os.path import splitext, basename

import numpy as np
from scipy.sparse import csr_matrix

from skimage.io import imread, imsave
class DefaultLoader:
    """
    demo imageloader function class (for skimage collections)
    """
    
    def __call__(self, fname, **kwargs):
        return imread(fname,plugin='matplotlib')

class DefaultSaver:
    """
    demo imagesaver function class 
    """
    def __call__(self, fname, img, **kwargs):
        return imsave(fname,img.squeeze())

class DefaultMasker:
    """        
    Summary: demo mask function, marks all pixels in image img as valid
    
    Arguments:
    None
    
    Keyword Arguments:
    - imgf: image file (default=None)
    - img: image array (default None)
    
    Output:
    - boolean mask with the same number of pixels as img
    """
    def __call__(self, img, **kwargs):
        return np.ones([img.shape[0],img.shape[1]],dtype=np.bool8)
    
def timeit(func):
    '''
    Decorator to time the invocation of a function
    '''
    import time
    gettime = time.time
    
    outstr = '%s.%s elapsed time: %0.3f seconds'
    def wrapper(*args,**kwargs):
        starttime  = gettime()
        res = func(*args,**kwargs)
        print(outstr%(func.__module__,str(func).split()[1], gettime()-starttime))
        return res
    return wrapper
