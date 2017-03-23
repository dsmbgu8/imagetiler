from __future__ import absolute_import, print_function, division

from .util import *
from .basetiler import *
from .masktiler import *
from .coveragetiler import *

class RegionTiler(BaseTiler):
    """
    RegionTiler(rcomp,tiledim,**kwargs)

    Summary: tiler class for labeled connected components images.
    Generates tiles for each nonzero connected component in the rcomp image
    using either the MaskTiler or CoverageTiler class. 

    Arguments:
    - rcomp: rcomp image, 2D integer-labeled connected component image
    - tiledim: tile dimension

    Keyword Arguments:
    None

    Output:
    None
    """    
    def __init__(self,rcomp,tiledim,**kwargs):
        self.ul       = []
        self.rcomp    = rcomp
        self.rclab    = kwargs.pop('rclab',np.unique(rcomp[rcomp!=0]))
        self.tiledim  = tiledim
        self.tilefn   = kwargs.pop('tilefn','coverage')
        self.tiler    = CoverageTiler if self.tilefn=='coverage' else MaskTiler
        self.tilerkw  = kwargs
        
    def collect(self):
        if self.ul != []:
            return self.ul

        ul = []
        for r in self.rclab:
            tiler = self.tiler((self.rcomp==r),self.tiledim,**self.tilerkw)
            ul.extend(tiler.collect())
        self.ul = ul
        return self.ul
