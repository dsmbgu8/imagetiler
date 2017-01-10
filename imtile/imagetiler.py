from __future__ import absolute_import, print_function, division

from .util import *

from warnings import warn, filterwarnings
filterwarnings("ignore", message='.*is a low contrast image.*')

tileinfof = 'tileinfo.txt'
tileinfohdr = 'tileid row_start row_stop col_start col_stop percent_valid'
def tile2str(tileslice):
    """
    converts 3d tile slice ((row_start,row_stop,None),(col_start,col_stop,None)) to
    output string format='row_start row_stop col_start col_stop'
    """
    return ' '.join(['%d %d'%(si.start,si.stop) for si in tileslice])

class MaskTiler:
    """
    MaskTiler(mask,tiledim,reject=0.75,maxsearch=100,reinit_mask=True)
    
    Summary: generates randomly selected tiledim x tiledim subtiles given
    initial mask of valid pixel locations
    
    Arguments:
    - tiledim: tile dimension
    - mask: [nrows x ncols] bool mask indicating valid regions of img
    
    Keyword Arguments:
    - reject: max percentage of (mask==0)/ntilepix to warrant rejection
    
    Output:
    - tileij = tiledim x tiledim tiles extracted from img at position i,j
    """

    def __init__(self,mask,tiledim,numtiles,**kwargs):
        self.tiledim  = tiledim
        self.numtiles = numtiles

        self.maxsearch = kwargs.pop('maxsearch',1000)
        self.minvalid = kwargs.pop('min_valid',0.75)
        self.with_replacement = kwargs.pop('with_replacement',False)
        self.reinit_mask = kwargs.pop('reinit_mask',True) # reset mask if we run out of valid pixels
        self.verbose = kwargs.pop('verbose',False)
        
        self.nrows = mask.shape[0]
        self.ncols = mask.shape[1] 
        
        if self.nrows<tiledim or self.ncols<tiledim:
            msg='tiledim %d too large for shape (%dx%d)'%(tiledim,
                                                          self.nrows,
                                                          self.ncols)
            raise Exception(msg)

        # assign initial mask pixels + threshold
        self.maskinit  = np.bool8(mask.copy())
        self.mask      = self.maskinit.copy()
        
        # get pixel offsets from tile dim
        self.rowdim    = self.nrows-(self.nrows%self.tiledim)
        self.coldim    = self.ncols-(self.ncols%self.tiledim)
        self.rowrange  = range(0,self.rowdim,5)
        self.colrange  = range(0,self.coldim,5)
        self.pixrc     = np.meshgrid(self.rowrange,self.colrange)
        self.pixrc     = np.c_[self.pixrc].reshape([2,-1]).T
        self.ntilepix  = self.rowdim*self.coldim

        # compute number of rows/cols of tiledim tiles
        self.tilerows  = int(np.ceil(self.nrows/tiledim))
        self.tilecols  = int(np.ceil(self.ncols/tiledim))
        self.tileij    = np.meshgrid(range(self.tilerows),range(self.tilecols))
        self.tileij    = np.c_[self.tileij].reshape([2,-1]).T
        self.ntiles    = self.tileij

        # keep track of tiles we've already collected
        self.tiles = []
        if self.minvalid < 1.0:
            self.minvalid  = int(round(self.minvalid*self.ntilepix))

        self.collect()

    def next(self):
        # randomly selects a tile from the list of valid pixel/tile offsets
        # while preserving state, allows for sampling with/without replacement
        # returns best tile slice and percent of valid pixels for best slice
        # (larger percentages=less overlap with previously-selected tiles)
        
        tijbest = None # 
        tijvalid = 0.0 # 

        tr,tc = self.tilerows,self.tilecols
        pr,pc = self.rowdim,self.coldim
        if len(self.pixrc)==0 or len(self.tileij)==0:
            warn('no pixel offsets defined, cannot proceed')
            return (tijbest, tijvalid)
        
        nsearch = 0
        pixrc  = list(self.pixrc)
        r,c = pixrc.pop(np.random.randint(len(pixrc)))            
        while nsearch <= self.maxsearch:
            # pick a random row/col pixel offset from our valid pixel list

            tileij = list(self.tileij)
            # search tiles in random order for current pixel offset
            while tileij != []:
                ti,tj = tileij.pop(np.random.randint(len(tileij)))
                i,j = (ti*self.tiledim)+r,(tj*self.tiledim)+c
                if i+self.tiledim>=self.nrows or j+self.tiledim>=self.ncols:
                    continue

                tij = (slice(i,i+self.tiledim,None),
                       slice(j,j+self.tiledim,None))

                # select tile with the most valid (mask==True) pixels
                nvalid = np.count_nonzero(self.mask[tij])
                if nvalid>tijvalid:
                    tijbest, tijvalid = tij, nvalid
                    if nvalid>self.minvalid:
                        # exit early if we meet stopping criteria
                        nsearch = self.maxsearch
                        break

            # found an acceptable tile or all pixels masked invalid (reset or exit)
            if nsearch>=self.maxsearch:
                # reset mask if we run out of valid pixels
                coverage = (100*(1.0-tijvalid))/self.ntilepix
                if self.reinit_mask and coverage > 95:
                    if self.verbose:
                        msg = "Reinitializing mask (%5.3f%% pixel coverage)"%coverage
                        warn(msg)
                    self.mask = self.maskinit.copy()
                    tijbest, tijvalid = None, 0.0
                    nsearch = 0
                    r,c = pixrc.pop(np.random.randint(len(pixrc)))
                else:
                    # found a good tile, mask if sampling wo replacement
                    if not self.with_replacement:
                        self.mask[tijbest] = False
                break

            # update either the row or the column, but not both
            if np.random.rand() > 0.5:
                rr = self.rowrange[np.random.randint(len(self.rowrange))]
                r = (r+rr)%self.rowdim
            else:
                cc = self.colrange[np.random.randint(len(self.colrange))]
                c = (c+cc)%self.coldim
                
            # keep track of searches to avoid infinite loop
            nsearch += 1
                    
        return (tijbest, tijvalid)

    @timeit
    def collect(self):
        if self.tiles != []:
            return
        
        tiles = []
        percent_valid = []

        if self.verbose:
            print(tileinfohdr)
        for i in range(self.numtiles):
            tij,tijvalid = self.next()
            if tij==None:
                break
            tijpercent = tijvalid/self.ntilepix
            if self.verbose:
                print(i,tile2str(tij),'%4.3f'%tijpercent)
                
            tiles.append(tij)
            percent_valid.append(tijpercent)

        self.tiles = tiles
        self.percent_valid = percent_valid
        numtiles = len(tiles)
        print('Collected',numtiles,'of',self.numtiles,'requested tiles')
        self.numtiles = numtiles
    
    @timeit
    def save_tiles(self,img,savefunc,outdir,**kwargs):
        import pylab as pl
        import matplotlib.patches as patches
        overwrite = kwargs.pop('overwrite',False)
        outfile = None
        logmsg = [tileinfohdr]
        figi = pl.figure()
        axi = figi.add_subplot(111)
        axi.imshow(img)
        figm = pl.figure()
        axm = figm.add_subplot(111)
        axm.imshow(np.uint8(self.maskinit))        
        for i,tij in enumerate(self.tiles):
            tijid,tijslstr = 'tile%d'%i,tile2str(tij)
            tijimg,tijvalid = img[self.tiles[i]],self.percent_valid[i]
            print(tijimg[:,:,0].min(),tijimg[:,:,0].max(),tijimg.shape)
            logmsg.append(' '.join([tijid,tijslstr,'%4.3f'%tijvalid]))
            savefunc(pathjoin(outdir,tijid),tijimg)
            pi = patches.Rectangle((tij[1].start,tij[0].start),
                                  self.tiledim,self.tiledim,
                                  fill=False,edgecolor='g',
                                  linewidth=2)
            pm = patches.Rectangle((tij[1].start,tij[0].start),
                                  self.tiledim,self.tiledim,
                                  fill=False,edgecolor='g',
                                  linewidth=2)            
            axi.add_patch(pi)
            axm.add_patch(pm)

        print('Saved',self.numtiles,'tiles to',outdir)
        savefunc(pathjoin(outdir,'mask'),self.mask)
        savefunc(pathjoin(outdir,'maskinit'),self.maskinit)
        with open(pathjoin(outdir,tileinfof),'w') as fid:
            print('\n'.join(logmsg),file=fid)


        pl.figure()
        pl.imshow(np.uint8(self.mask))

        pl.show()
                
