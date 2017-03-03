from __future__ import absolute_import, print_function, division

from .util import *
from numpy.random import randint


from warnings import warn, filterwarnings
filterwarnings("ignore", message='.*is a low contrast image.*')

        
class MaskTiler:
    """
    MaskTiler(mask,tiledim,numtiles,maxsearch=1000,accept=0.5,reinit_mask=True,
              replacement=False,verbose=False)
    
    Summary: generates randomly selected tiledim x tiledim subtiles given
    initial mask of valid pixel locations
    
    Arguments:
    - tiledim: tile dimension
    - mask: [nrows x ncols] bool mask indicating valid regions to sample in img
    
    Keyword Arguments:
    - accept: max percentage of seen (mask==1) pixels/tile to accept
    
    Output:
    - tileij = list of tiledim x tiledim tiles (2d slices) to use to extract subimages
    """

    def __init__(self,mask,tiledim,numtiles,**kwargs):
        self.maxsearch   = kwargs.pop('maxsearch',1000)
        self.replacement = kwargs.pop('replacement',False)
        self.reinit_mask = kwargs.pop('reinit_mask',True)
        self.accept      = kwargs.pop('accept',0.5)        
        self.verbose     = kwargs.pop('verbose',False)
        
        nrows,ncols = mask.shape[0],mask.shape[1]         
        if nrows<tiledim or ncols<tiledim:
            msg='tiledim %d too large for shape (%dx%d)'%(tiledim,nrows,ncols)
            raise Exception(msg)

        self.tiles     = []
        self.ul        = []
        self.nrows     = nrows
        self.ncols     = ncols
        self.tiledim   = tiledim
        self.numtiles  = numtiles
        self.ntilepix  = tiledim*tiledim

        self.strict = False
        if self.accept=='none':
            # 'none' -> tile cannot contain any overlapping pixels
            self.accept = 0.0
            self.strict = True
        elif self.accept=='min':
            # 'min' -> tiles can only contain 1 overlapping pixel
            self.accept = (self.ntilepix-2.0)/self.ntilepix
        elif self.accept=='max':
            # 'max' -> tiles can contain all but 1 overlapping pixel
            self.accept = 2.0/self.ntilepix
        
        # assign initial mask pixels + compute threshold
        self.maskskip  = (mask==0) # 0=invalid pixel, so we should skip it
        self.maskseen  = self.maskskip.copy() # consider invalid pixels "seen"
 
        # get range of pixel offsets from tile dim
        self.rowdim    = self.nrows-(self.nrows%self.tiledim)
        self.coldim    = self.ncols-(self.ncols%self.tiledim)
        self.rowrange  = range(0,self.rowdim,5)
        self.colrange  = range(0,self.coldim,5)
        self.pixrc     = np.meshgrid(self.rowrange,self.colrange)
        self.pixrc     = np.c_[self.pixrc].reshape([2,-1]).T
        
        # compute number of rows/cols of tiledim-sized tiles
        ntilerows      = int(np.ceil(self.nrows/tiledim))
        ntilecols      = int(np.ceil(self.ncols/tiledim))
        self.tileij    = np.meshgrid(range(ntilerows),range(ntilecols))
        self.tileij    = np.c_[self.tileij].reshape([2,-1]).T

        self.maxcover = 0.95*self.ntilepix
        self.maxseen  = int(self.accept*self.ntilepix)

    def next(self):
        # randomly selects a tile from the list of pixel/tile offsets
        # while preserving state, allows for sampling with/without replacement
        # returns best tile slice and percent of unmasked pixels for best slice
        # (larger percentages=less overlap with previously-selected tiles)
        
        tijbest,tijseen = None, self.ntilepix 

        if len(self.pixrc)==0 or len(self.tileij)==0:
            warn('no pixel offsets defined, cannot proceed')
            return (tijbest, tijseen)
        
        nsearch = 0
        pixrc  = list(self.pixrc)
        # pick a random row/col pixel offset from our seen pixel list
        r,c = pixrc.pop(randint(len(pixrc)))            
        while nsearch <= self.maxsearch:
            tileij = list(self.tileij)
            # search tiles in random order for current pixel offset
            while tileij != []:
                ti,tj = tileij.pop(randint(len(tileij)))
                i,j = (ti*self.tiledim)+r,(tj*self.tiledim)+c
                if i+self.tiledim>=self.nrows or j+self.tiledim>=self.ncols:
                    #  TODO (BDB, 02/21/17): allow padding here? 
                    continue

                tij = (slice(i,i+self.tiledim,None),
                       slice(j,j+self.tiledim,None))
                
                # select tile with the fewest seen (maskseen==1) pixels
                nseen = np.count_nonzero(self.maskseen[tij])
                if nseen<tijseen:
                    tijbest, tijseen = tij, nseen
                    if nseen<=self.maxseen:
                        # exit early if we meet stopping criteria
                        nsearch = self.maxsearch
                        break

            # found an acceptable tile or all pixels masked inseen (reset or exit)
            if nsearch>=self.maxsearch:                                                
                # reset mask if our best tile is covered by more than maxcover
                if self.reinit_mask and tijseen > self.maxcover:
                    if self.verbose:
                        coverage = tijseen/self.ntilepix
                        msg = "Reinitializing mask (%6.3f%% pixel coverage)"%coverage
                        warn(msg)
                    self.maskseen = self.maskskip.copy()
                    # pick a new offset to increase sampling diversity
                    r,c = pixrc.pop(randint(len(pixrc)))
                    tijbest, tijseen = None, self.ntilepix
                    nsearch = 0
                else:
                    # found a good tile, mask if sampling wo replacement
                    if not self.replacement:
                        self.maskseen[tijbest] = True
                break

            # randomly increment either the row or the column, but not both
            if randint(2)==1:
                rr = self.rowrange[randint(len(self.rowrange))]
                r = (r+rr)%self.rowdim
            else:
                cc = self.colrange[randint(len(self.colrange))]
                c = (c+cc)%self.coldim
                
            # keep track of searches to avoid infinite loop
            nsearch += 1
                    
        return (tijbest, tijseen)

    def __repr__(self):
        ntiles = len(self.tiles)
        outstr = ['%d tiles'%ntiles]
        if ntiles == 0:
            return outstr[0]
        
        outstr.append(tileinfohdr)
        for i,tij in enumerate(self.tiles):
            tijpercent = self.percent_seen[i]
            outstr.append(str(i,tile2str(tij),'%4.3f'%tijpercent))
                
        return '\n'.join(outstr)
    
    @timeit
    def collect(self):
        if self.ul != []:
            return self.ul
        
        tiles = []
        percent_seen = []

        if self.verbose:
            print('Collecting tiles')
            print(tileinfohdr)
        for i in range(self.numtiles):
            tij,tijseen = self.next()
            if tij==None:
                break
            tijpercent = tijseen/self.ntilepix
            if self.verbose:
                print(i,tile2str(tij),'%5.4f'%tijpercent)

            # if strict mode on, discard 'best match' tiles below criteria
            if self.strict and tijseen > self.maxseen:
                if self.verbose:
                    print('skipped %d: tijseen=%d > maxseen=%d'%(i,tijseen,
                                                                 self.maxseen))
                continue
            tiles.append(tij)
            percent_seen.append(tijpercent)

        self.tiles = tiles
        self.percent_seen = percent_seen
        numtiles = len(tiles)
        print('Collected',numtiles,'of',self.numtiles,'requested tiles')
        self.numtiles = numtiles
        self.ul = list(set([(tij[0].start,tij[1].start) for tij in tiles]))
        return self.ul

    def extract(self, img):
        return extract_tiles(img,self.ul,self.tiledim)


class RegionTiler:
    def __init__(self,rcomp,tiledim,numtiles,**kwargs):
        self.ul       = []
        self.rcomp    = rcomp
        self.rclab    = kwargs.pop('rclab',np.unique(rcomp[rcomp!=0]))
        self.tiledim  = tiledim
        self.numtiles = numtiles
        self.kwargs   = kwargs
        
    def collect(self):
        if self.ul != []:
            return self.ul

        ul = []
        for r in self.rclab:
            tiler = MaskTiler((self.rcomp==r),self.tiledim,self.numtiles,
                              **self.kwargs)
            print(r,(self.rcomp==r).sum(),tiler.collect())
            ul.extend(tiler.collect())
        self.ul = ul
        return self.ul
