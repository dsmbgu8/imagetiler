from __future__ import absolute_import, print_function, division

from .util import *
from .recttiler import *
from .masktiler import *

from skimage.measure import label as imlabel

from numpy.random import randint, permutation as randperm

from warnings import warn, filterwarnings
filterwarnings("ignore", message='.*is a low contrast image.*')

MIN_TILES = 25
MAX_TILES = 200
        
class ClassMaskTiler:
    def __init__(self,tpmask,tnmask,fpmask,tiledim,**kwargs):
        self.fp_conn = kwargs.pop('fp_conn',1) # don't collect quad tiles for fp
        self.verbose = kwargs.pop('verbose',True)
        self.tile_ul = {'tp':[],'fp':[],'tn':[]}
        self.tiledim = tiledim
        self.tpmask  = tpmask
        self.tnmask  = tnmask        
        self.fpmask  = fpmask
        self.tpcomp  = imlabel(self.tpmask)
        self.fpcomp  = imlabel(self.fpmask)
        self.ntn     = MIN_TILES
        self.ntprand = MIN_TILES

        print('orig mask alignment:',(self.fpmask & self.tpmask).sum())
        print('flip mask alignment:',(self.fpmask & np.flipud(self.tpmask)).sum())
        
    def collect(self):
        if any([len(self.tile_ul[tc]) for tc in self.tile_ul]):
            return self.tile_ul
        
        # collect (upper-left) coords for true positives first
        tiler = QuadTiler(self.tpcomp,self.tiledim)
        tp = tiler.collect()

        # grab the same number of tn as tp
        ntn = min(max(len(tp),self.ntn,MIN_TILES),MAX_TILES)        
        tiler = MaskTiler(self.tnmask,self.tiledim,ntn,accept='none',
                          replacement=True,verbose=self.verbose)
        tn = tiler.collect()

        # collect false positives        
        ufplab = np.unique(self.fpcomp[self.fpmask])
        if len(ufplab) > MAX_TILES:
            ufplab = randperm(ufplab)[:MAX_TILES]            
        tiler = QuadTiler(self.fpcomp,self.tiledim,rclab=ufplab,
                          mask=self.tpmask,conn=self.fp_conn)
        fp = tiler.collect()

        if self.ntprand != 0:
            # get another ntprand random tiles for each tp component    
            tiler = RegionTiler(self.tpcomp,self.tiledim,self.ntprand,accept='max',
                                replacement=True,verbose=self.verbose)
            tpr = tiler.collect()
            tp.extend(tpr)                

        self.ntp = len(tp)
        self.ntn = len(tn)
        self.nfp = len(fp)

        self.tile_ul['tp'] = tp
        self.tile_ul['tn'] = tn
        self.tile_ul['fp'] = fp

        print(self.ntp,'labeled tiles')
        print(self.ntn,'negative tiles')
        print(self.nfp,'unlabeled components')        

        return self.tile_ul
