from __future__ import absolute_import, print_function, division

from .util import *
from .basetiler import *
from numpy.random import randint

def setdiff2d(A1,A2):
    if len(A1.shape) != len(A2.shape) or A2.shape[1] != A2.shape[1]:
        raise ValueError("A1 and A2 must 2D arrays")

    A1_rows = A1.view([('',A1.dtype)]*A1.shape[1])
    A2_rows = A2.view([('',A2.dtype)]*A2.shape[1])
    return np.setdiff1d(A1_rows, A2_rows).view(A1.dtype).reshape(-1, A1.shape[1])


class CoverageTiler(BaseTiler):
    """
    MaskTiler(mask,tiledim,numtiles,maxsearch=1000,accept=0.5,reinit_mask=True,
              replacement=False,verbose=False)
    
    Summary: generates randomly selected tiledim x tiledim subtiles given
    initial mask of valid pixel locations
    
    Arguments:
    - mask: [nrows x ncols] bool mask indicating valid regions to sample in img
    - tiledim: tile dimension
    
    Keyword Arguments:
    - accept: max percentage of seen (mask==1) pixels/tile to accept
              (smaller values == less overlap)
    
    Output:
    - tileij = list of tiledim x tiledim tiles (2d slices) to use to extract subimages
    """

    def __init__(self,mask,tiledim,**kwargs):
        self.numtiles    = kwargs.pop('numtiles',MIN_TILES)
        self.accept      = kwargs.pop('accept',0.75)
        self.verbose     = kwargs.pop('verbose',False)
        self.exclude     = kwargs.pop('exclude',[])
        
        nrows,ncols = mask.shape[0],mask.shape[1]         
        if nrows<tiledim or ncols<tiledim:
            msg='tiledim %d too large for shape (%d x %d)'%(tiledim,nrows,ncols)
            raise Exception(msg)

        
        self.ul        = []
        self.nrows     = nrows
        self.ncols     = ncols
        self.tiledim   = tiledim
        self.ntilepix  = tiledim*tiledim

        # assign initial mask pixels + compute threshold
        self.mask     = np.uint8(mask.copy()) # 0=invalid pixel, so we should skip it
        self.nmask    = np.count_nonzero(mask)

        rcidx = np.where(self.mask!=0)
        if len(rcidx)==0:
            raise Exception('mask empty: cannot generate tiles')
        
        rowidx,colidx = rcidx
        
        self.rowidx   = rowidx
        self.colidx   = colidx

        rowmin = rowidx.min()
        rowmax = min(nrows-tiledim,rowidx.max()+tiledim)
        colmin = colidx.min()
        colmax = min(ncols-tiledim,colidx.max()+tiledim)

        self.rowrange = np.arange(rowmin,rowmax)
        self.colrange = np.arange(colmin,colmax)
        self.pixij    = np.meshgrid(self.rowrange,self.colrange)
        self.pixij    = np.int32(np.c_[self.pixij].reshape([2,-1]).T)

        if len(self.exclude)!=0:
            exclude = set(self.exclude)
            keepidx = np.ones(len(self.pixij),dtype=np.bool8)
            for i,ij in enumerate(self.pixij):
                if (ij[0],ij[1]) in exclude:
                    keepidx[i] = 0
            self.pixij = self.pixij[keepidx]
        
        self.mincover = int(self.accept*self.nmask)
        
    def next(self):
        pixij = list(self.pixij)
        while pixij != []:
            i,j = pixij.pop(randint(len(pixij)))
            if i+self.tiledim>=self.nrows or j+self.tiledim>=self.ncols:
                continue
            
            tij = (slice(i,i+self.tiledim,None),
                   slice(j,j+self.tiledim,None))
                
            # select tile with the fewest seen (maskseen==1) pixels
            tvals = self.mask[tij]
            nmask = np.count_nonzero(tvals)
            if nmask >= self.mincover:
                return tij
        return None

    @timeit
    def collect(self):
        if self.ul != []:
            return self.ul

        ul = []
        tiles = []

        if self.verbose:
            nrows,ncols = self.mask.shape[:2]
            print('Collecting up to',self.numtiles,'tiles')
            print('Image dims: (%d x %d)'%(nrows,ncols))
            print('Tile dims: (%d x %d)'%(self.tiledim,self.tiledim))
            
        for i in range(self.numtiles):
            tij = self.next()
            if tij==None:
                break
            if self.verbose:
                print(i,tile2str(tij))

            tiles.append(tij)
            ul.append((tij[0].start,tij[1].start))

        self.tiles = tiles
        numtiles = len(tiles)
        print('Collected',numtiles,'of',self.numtiles,'requested tiles')
        self.numtiles = numtiles
        self.ul = list(set(ul))
        return self.ul
