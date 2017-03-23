from __future__ import absolute_import, print_function, division

from .util import *
from .basetiler import *
from .recttiler import *
from .regiontiler import *
from .masktiler import *

from skimage.measure import label as imlabel

from numpy.random import randint, permutation as randperm

class ClassMaskTiler(BaseTiler):
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
        self.ntn     = kwargs.pop('ntn',MIN_TILES)
        self.ntprand = kwargs.pop('ntprand',MIN_TILES)

        print('orig mask alignment:',(self.fpmask & self.tpmask).sum())
        print('flip mask alignment:',(self.fpmask & np.flipud(self.tpmask)).sum())
        
    def collect(self):
        if any([len(self.tile_ul[tc]) for tc in self.tile_ul]):
            return self.tile_ul
        
        # collect (upper-left) coords for true positives first
        tiler = RectTiler(self.tpcomp,self.tiledim)
        tp = tiler.collect()

        # grab the same number of tn as tp
        if self.tnmask.any():
            # accept no overlapping tiles with tpmask, but sample with replacemen
            ntn = self.ntn if (self.ntn != -1) else min(len(tp),MAX_TILES) 

            tiler = MaskTiler(self.tnmask,self.tiledim,numtiles=ntn,accept='none',
                              replacement=True,verbose=self.verbose)
            self.tile_ul['tn'] = tiler.collect()
        else:
            self.tile_ul['tn'] = []

        # collect false positives        
        ufplab = np.unique(self.fpcomp[self.fpmask])
        if len(ufplab) != 0:
            if len(ufplab) > MAX_TILES:
                ufplab = randperm(ufplab)[:MAX_TILES]            
            tiler = RectTiler(self.fpcomp,self.tiledim,rclab=ufplab,
                              mask=self.tpmask,conn=self.fp_conn)
            self.tile_ul['fp'] = tiler.collect()
        else:
            self.tile_ul['fp'] = []                

        if self.ntprand != 0:
            randaccept='none' # 'min' # 
            # get another ntprand random tiles for each tp component    
            tiler = RegionTiler(self.tpcomp,self.tiledim,numtiles=self.ntprand,
                                accept=0.75,exclude=tp,verbose=self.verbose)
            tpr = tiler.collect()
            tp.extend(tpr)                
        self.tile_ul['tp'] = tp
            
        self.ntp = len(self.tile_ul['tp'])
        self.ntn = len(self.tile_ul['tn'])
        self.nfp = len(self.tile_ul['fp'])

        print(self.ntp,'labeled tiles')
        print(self.ntn,'negative tiles')
        print(self.nfp,'unlabeled components')        

        return self.tile_ul
