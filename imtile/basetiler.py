from __future__ import absolute_import, print_function, division

from .util import *

class BaseTiler(object):
    def __init__(self,**kwargs):
        pass

    def collect(self):
        pass

    def extract(self, img, **kwargs):
        ul = self.collect()            
        return extract_tiles(img,ul,self.tiledim,**kwargs)

    def save(self, img, outdir, outext, savefunc, **kwargs):
        ul = self.collect()            
        return save_tiles(img,ul,self.tiledim,**kwargs)
    
    def plot(self, img, **kwargs):
        ul = self.collect()            
        return plot_tiles(img,ul,self.tiledim,**kwargs)
    
