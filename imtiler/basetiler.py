from __future__ import absolute_import, print_function, division

from .util import *

from warnings import warn, filterwarnings
filterwarnings("ignore", message='.*is a low contrast image.*')

MIN_TILES = 25
MAX_TILES = 200

class BaseTiler(object):
    def __init__(self,tiledim,**kwargs):
        self.rndstate = kwargs.pop('random_state',42)
        self.tiledim  = tiledim
        self.verbose  = kwargs.pop('verbose',True)
        self.ul       = []

        np.random.seed(self.rndstate)

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
    
