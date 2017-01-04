from __future__ import absolute_import, print_function, division

from .util import *

from warnings import filterwarnings
filterwarnings("ignore", message='.*is a low contrast image.*')

class ImageTiler:
    """
    tilegen(imgshape,tiledim,mask=[],masked_reject=0.75)
    
    Summary: generates randomly selected tiledim x tiledim subtiles given imgshape
    
    Arguments:
    - img: extract subtile from this [nrows x ncols x nbands] image
    - tiledim: tile dimension
    - mask: [nrows x ncols] bool mask indicating valid regions of img
    
    Keyword Arguments:
    - masked_reject: max percentage of masked pixels/tile to warrant rejection
    
    Output:
    - tileij = tiledim x tiledim tile extracted from img at position i,j
    """

    def __init__(self,img,mask,tiledim,maxtiles,**kwargs):
        nrows,ncols,nbands = img.shape[0],img.shape[1],img.shape[2]
        npix = nrows*ncols
        assert(mask.shape[0]==nrows and mask.shape[1]==ncols)
        if nrows<tiledim or ncols<tiledim:
            msg='tiledim %d too large for shape (%dx%d)'%(tiledim,nrows,ncols)
            raise Exception(msg)

        self.img = img
        self.rowstride = kwargs.pop('rowstep',int(10*nrows/ncols))
        self.colstride = kwargs.pop('colstep',int(10*ncols/nrows))
        
        self.masked_reject = kwargs.pop('masked_reject',0.75)
        self.with_replacement = kwargs.pop('with_replacement',False)
        self.verbose = kwargs.pop('verbose',False)

        # get pixel offsets from tile dim
        self.tiledim   = tiledim
        self.ntilepix  = self.tiledim*self.tiledim   
        self.nrows     = nrows
        self.ncols     = ncols
        self.pixoff    = np.meshgrid(range(0,self.tiledim,self.rowstride),
                                     range(0,self.tiledim,self.colstride))
        self.pixoff    = np.c_[self.pixoff].reshape([2,-1]).T

        # compute number of rows/cols of tdim tiles
        self.tilerows  = nrows//tiledim
        self.tilecols  = ncols//tiledim
        self.tileoff   = np.meshgrid(range(self.tilerows),range(self.tilecols))
        self.tileoff   = np.c_[self.tileoff].reshape([2,-1]).T
        self.ntiles    = len(self.tileoff)

        # assign initial mask pixels + threshold
        self.mask     = np.bool8(mask.copy())
        self.nminkeep = self.masked_reject*self.ntilepix
        self.numtiles = maxtiles

        # keep track of tiles we've already collected
        self.tiles    = []

    def getnext(self):
        # randomly selects the next tile from the list of pixel/tile offsets
        # allows for sampling with/without replacement
        pixoff  = list(self.pixoff)
        tileoff = list(self.tileoff)

        tijbest = None # best tile slice
        tijmask = 1.0 # percent of masked pixels for best tile (lower=less overlap)

        while pixoff != [] and tileoff != []:
            pixi,pixj = pixoff.pop(np.random.randint(len(pixoff)))
            nmaskmax = 0
            while tileoff != []:
                tilei,tilej = tileoff.pop(np.random.randint(len(tileoff)))
                ii,jj = (tilei*self.tiledim)+pixi,(tilej*self.tiledim)+pixj
                if ii+self.tiledim>=self.nrows or jj+self.tiledim>=self.ncols:
                    continue
                
                tij = (slice(ii,ii+self.tiledim,None),
                       slice(jj,jj+self.tiledim,None))
                
                # select tile if it doesn't have too many masked (zero) pixels
                nmask = np.count_nonzero(self.mask[tij])
                tijmask = 1-nmask/float(self.ntilepix)
                if nmask>self.nminkeep:
                    tijbest = tij
                    break
                elif nmask>nmaskmax:
                    tijbest = tij                
                    nmaskmax = nmask

            if tijbest: # found a tile 
                if not self.with_replacement:
                    self.mask[tijbest] = False
                break
        return tijbest, tijmask

    @timeit
    def collect(self):
        if self.tiles != []:
            return self.tiles
        
        tiles = []
        percent_masked = []
        
        for i in range(self.numtiles):
            tij,tijmask = self.getnext()
            if tij==None:
                break
            if self.verbose:
                if i==0:
                    print(tileposhdr)
                print('Tile',i,imslice2str(tij),'%4.3f'%tijmask)
                
            tiles.append(tij)
            percent_masked.append(tijmask)

        self.tiles = tiles
        self.percent_masked = percent_masked
        numtiles = len(tiles)
        print('Collected',numtiles,'of',self.numtiles,'tiles')
        self.numtiles = numtiles
        return tiles

    @timeit
    def write(self,outdir,savefunc,**kwargs):
        overwrite = kwargs.pop('overwrite',False)
        outext = kwargs.pop('outext','.jpg')

        if not pathexists(outdir):
            os.makedirs(outdir)

        tiles = self.collect()
        print('Writing',self.numtiles,'tiles to',outdir)
        with open(pathjoin(outdir,tileposf),'w') as fid:
            print(tileposhdr,file=fid)
            for i,tij in enumerate(tiles):
                tijimg,tijmask = self.img[tij],self.percent_masked[i]
                outf = '%d%s'%(i,outext)
                if overwrite or not pathexists(pathjoin(outdir,outf)):
                    savefunc(pathjoin(outdir,outf),tijimg)
                    print('Wrote',outf,imslice2str(tij),'%4.3f'%tijmask,file=fid)
                else:
                    print('Skipped',outf,'- file already exists')
        savefunc(pathjoin(outdir,'mask%s'%outext),self.mask.astype(np.uint8)*255)


