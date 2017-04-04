from __future__ import absolute_import, print_function, division

from .util import *
from .basetiler import *
from .recttiler import *
from .regiontiler import *
from .masktiler import *

from skimage.measure import label as imlabel

from numpy.random import randint, permutation as randperm

MATCH_POS=-1

class ClassMaskTiler(BaseTiler):
    def __init__(self,tpmask,tnmask,fpmask,tiledim,**kwargs):
        super(ClassMaskTiler,self).__init__(tiledim,**kwargs)
        
        self.tile_ul = {'tp':[],'fp':[],'tn':[]}
        self.tpmask  = tpmask
        self.tnmask  = tnmask        
        self.fpmask  = fpmask
        self.tpcomp  = kwargs.pop('tpcomp',[])
        self.fpcomp  = kwargs.pop('fpcomp',[])
        if len(self.tpcomp) == 0:
            self.tpcomp = imlabel(self.tpmask)
        if len(self.fpcomp) == 0:
            self.fpcomp = imlabel(self.fpmask)
        self.ntn     = kwargs.pop('ntn',MIN_TILES)
        self.ntprand = kwargs.pop('ntprand',MIN_TILES)
        self.tp_conn = kwargs.pop('tp_conn',8) # collect octtiles for fp
        self.fp_conn = kwargs.pop('fp_conn',1) # don't collect quadtiles for fp

        print('orig mask alignment:',(self.fpmask & self.tpmask).sum())
        print('flip mask alignment:',(self.fpmask & np.flipud(self.tpmask)).sum())
        
    def collect(self):
        if any([len(self.tile_ul[tc]) for tc in self.tile_ul]):
            return self.tile_ul              
        
        # collect (upper-left) coords for true positives first
        tiler = RectTiler(self.tpcomp,self.tiledim,conn=self.tp_conn)
        self.tile_ul['tp'] = tiler.collect()
        ntp_base = len(self.tile_ul['tp'])

        if self.ntprand != 0:
            raccept=0.75 #'none' # 'min' # 
            # get another ntprand random tiles for each tp component    
            tptiler = RegionTiler(self.tpcomp,self.tiledim,numtiles=self.ntprand,
                                  accept=raccept,exclude_coords=tp,mode='coverage',
                                  verbose=self.verbose)
            self.tile_ul['tp'].extend(tptiler.collect())

        self.ntp = len(self.tile_ul['tp'])
        print(self.ntp,'tp tiles')

        # grab the same number of tn as tp
        if self.tnmask.any():
            # accept no overlapping tiles with tpmask, but sample with replacemen
            ntn = self.ntn if (self.ntn != MATCH_POS) else ntp_base
            tntiler = MaskTiler(self.tnmask,self.tiledim,numtiles=ntn,accept='none',
                                replacement=True,verbose=self.verbose)
            self.tile_ul['tn'] = tntiler.collect()
            
        self.ntn = len(self.tile_ul['tn'])
        print(self.ntn,'tn tiles')
                        
        # collect false positives, excluding tiles overlapping true positives     
        ufplab = np.unique(self.fpcomp[self.fpmask])
        nfp = len(ufplab)
        if nfp != 0:
            if nfp > MAX_TILES:
                ufplab = randperm(ufplab)[:MAX_TILES]            
            fptiler = RectTiler(self.fpcomp,self.tiledim,rclab=ufplab,
                                mask=self.tpmask,conn=self.fp_conn)
            self.tile_ul['fp'] = fptiler.collect()

        self.nfp = len(self.tile_ul['fp'])
        print(self.nfp,'fp tiles')

        return self.tile_ul
