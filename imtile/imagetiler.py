from __future__ import absolute_import, print_function, division

from .util import *

from warnings import warn, filterwarnings
filterwarnings("ignore", message='.*is a low contrast image.*')

tileinfof = 'tileinfo.txt'
tileinfohdr = 'tileid row_start row_stop col_start col_stop percent_valid'
def imslice2str(imslice):
    """
    converts 2d slice ((row_start,row_stop,None),(col_start,col_stop,None)) to
    output string format='row_start row_stop col_start col_stop'
    """
    return ' '.join(['%d %d'%(si.start,si.stop) for si in imslice])

class MaskTiler:
    """
    MaskTiler(mask,tiledim,masked_reject=0.75,maxsearch=100,reinit_mask=True)
    
    Summary: generates randomly selected tiledim x tiledim subtiles given
    initial mask of valid pixel locations
    
    Arguments:
    - tiledim: tile dimension
    - mask: [nrows x ncols] bool mask indicating valid regions of img
    
    Keyword Arguments:
    - masked_reject: max percentage of masked pixels/tile to warrant rejection
    
    Output:
    - tileij = tiledim x tiledim tile extracted from img at position i,j
    """

    def __init__(self,mask,tiledim,numtiles,**kwargs):
        self.tiledim  = tiledim
        self.numtiles = numtiles

        self.maxsearch = kwargs.pop('maxsearch',100)
        self.masked_reject = kwargs.pop('masked_reject',0.75)
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
        self.maskinit  = np.bool8(mask)
        self.mask      = self.maskinit.copy()                
        
        # get pixel offsets from tile dim
        self.rowdim    = self.tiledim-(self.nrows%self.tiledim)-1
        self.coldim    = self.tiledim-(self.ncols%self.tiledim)-1
        self.pixrc     = np.meshgrid(range(0,self.rowdim,5),
                                     range(0,self.coldim,5))
        self.pixrc     = np.c_[self.pixrc].reshape([2,-1]).T
        self.ntilepix  = self.rowdim*self.coldim

        # compute number of rows/cols of tiledim tiles
        self.tilerows  = self.nrows//tiledim
        self.tilecols  = self.ncols//tiledim
        self.tileij    = np.meshgrid(range(self.tilerows),range(self.tilecols))
        self.tileij    = np.c_[self.tileij].reshape([2,-1]).T
        self.ntiles    = self.tileij

        # keep track of tiles we've already collected
        self.tiles = []        
        self.minvalid  = (1.0-self.masked_reject)*self.ntilepix

    def next_tile(self):
        # randomly selects a tile from the list of valid pixel/tile offsets
        # while preserving state, allows for sampling with/without replacement
        # returns best tile slice and percent of valid pixels for best slice
        # (larger percentages=less overlap with previously-selected tiles)
        
        tijbest = None # 
        tijvalid = 0.0 # 

        if len(self.pixrc)>0 and len(self.tileij)>0:
            # randomly select next tile
            nsearch = 0
            pixrc  = list(self.pixrc)            
            while pixrc != []:
                # pick a random row/col pixel offset from our valid pixel list
                r,c = pixrc.pop(np.random.randint(len(pixrc)))
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
                        tijbest = tij
                        tijvalid = nvalid                        
                        if nvalid>self.minvalid:
                            # exit early if we meet stopping criteria
                            nsearch = self.maxsearch
                            break

                # found an acceptable tile or all pixels masked invalid
                if nsearch>=self.maxsearch:
                    # reset mask if we run out of valid pixels
                    coverage = 100*(1-tijvalid/self.ntilepix)
                    if self.reinit_mask and coverage > 95:
                        if self.verbose:
                            msg = "Reinitializing mask (%5.3f%% pixel coverage)"%coverage
                            warn(msg)
                        self.mask = self.maskinit.copy()
                        tijbest = None
                        tijvalid = 0.0
                        nsearch = 0
                    else:
                        # found a good tile, mask if sampling wo replacement
                        if not self.with_replacement:
                            self.mask[tijbest] = False
                        break

                # need to keep track of searches to avoid infinite loop
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
            tij,tijvalid = self.next_tile()
            if tij==None:
                break
            tijpercent = tijvalid/self.ntilepix
            if self.verbose:
                print(i,imslice2str(tij),'%4.3f'%tijpercent)
                
            tiles.append(tij)
            percent_valid.append(tijpercent)

        self.tiles = tiles
        self.percent_valid = percent_valid
        numtiles = len(tiles)
        print('Collected',numtiles,'of',self.numtiles,'requested tiles')
        self.numtiles = numtiles

    @timeit
    def generate(self,img):
        self.collect()
        for tij in self.tiles:
            yield img[tij]
    
    @timeit
    def save_tiles(self,savefunc,tiledir,basename,**kwargs):
        overwrite = kwargs.pop('overwrite',False)
        outext = kwargs.pop('outext','.jpg')

        outfile = None
        imgtiles = self.extract()        
        logmsg = [tileinfohdr]
        for i,tij in enumerate(self.tiles):
            tijid,tijslstr = 'tile%d'%i,imslice2str(tij)
            tijimg,tijvalid = imgtiles[i],self.percent_valid[i]
            logmsg.append(' '.join([tijid,tijslstr,'%4.3f'%tijvalid]))
            outfile = savefunc(tiledir,tileid,basename,outext,tijimg)

        if outfile:
            outdir = dirname(outfile)
            print('Saved',self.numtiles,'tiles to',outdir)
            masku8 = 255*self.mask.astype(np.uint8)
            maskinitu8 = 255*self.maskinit.astype(np.uint8)
            savefunc(tiledir,'mask',basename,outext,masku8)
            savefunc(tiledir,'maskinit',basename,outext,maskinitu8)
            with open(pathjoin(outdir,tileinfof),'w') as fid:
                print('\n'.join(logmsg),file=fid)

