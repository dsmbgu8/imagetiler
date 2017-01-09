from __future__ import absolute_import, print_function, division

from .util import *
from .imagetiler import *

from skimage.io.collection import ImageCollection

class TileCollection:
    """
    TileCollection: collections of subimage tiles extracted from a directory
    of larger base images
    """

    def __init__(self,loadpattern,tileext,tiledir,tiledim,maxtiles,**kwargs):
        self.loadpattern = loadpattern # e.g., pathjoin(imgdir,'*.jpg')
        self.tileext     = tileext # e.g., '.jpg'
        self.tiledir     = tiledir
        self.tiledim     = tiledim
        self.maxtiles    = maxtiles
        self.loadfunc    = kwargs.pop('loadfunc',DefaultLoader())
        self.maskfunc    = kwargs.pop('maskfunc',DefaultMasker())
        self.savefunc    = kwargs.pop('savefunc',DefaultSaver())       

        self.verbose     = kwargs.pop('verbose',False)
        
        self.masked_reject=kwargs.pop('masked_reject',0.75)
        self.with_replacement=kwargs.pop('with_replacement',False)

        self.outdir = pathjoin(self.tiledir,str(self.tiledim))

        self.collect()

    def collect(self):
        """
        extracts randomly selected image tiles for each of a set of base images
        in a specified directory

        Output: directory for each base image containing the image tiles and
        tile extraction log file
        """
        from glob import glob
        imgfiles = sorted(glob(self.loadpattern))
        nimg = len(imgfiles)
        print('Collecting tiles for',nimg,'images')
        tilers = {}
        for i,imgf in enumerate(imgfiles):
            if self.verbose:
                print("Image %d of %d"%(i+1,nimg))
            mask = self.maskfunc(imgf)
            tilers[imgf] = ImageTiler(imgf,mask,self.tiledim,self.maxtiles,
                                      loadfunc=self.loadfunc,
                                      savefunc=self.savefunc,
                                      masked_reject=self.masked_reject,
                                      with_replacement=self.with_replacement,
                                      verbose=self.verbose)
            
        self.tilers = tilers
        self.imgfiles = imgfiles        
        self.nimg = nimg
        
    def extract(self):
        imgtiles = {}
        for i,imgf in enumerate(self.imgfiles):
            tiler = self.tilers[imgf]
            if self.verbose:
                print("Image %d of %d"%(i+1,self.nimg))
            imgtiles[imgf] = tiler.extract()
        return imgtiles

    def write(self,**kwargs):
        overwrite = kwargs.pop('overwrite',False)
        if len(self.tilers)==0:
            self.collect()
        if not pathexists(self.outdir):
            os.makedirs(self.outdir)
        if self.verbose:
            print('Saving tiles to %s'%self.outdir)            
        for i,imgf in enumerate(self.imgfiles):
            tiler = self.tilers[imgf]
            if self.verbose:
                print("Image %d of %d"%(i+1,self.nimg))
            tiler.write(self.outdir,outext=self.tileext,overwrite=overwrite)
        
    @timeit
    def load(self,**kwargs):
        """
        returns dictionary contanining tiles, with each tile set
        represented as an imagecollection, for each base image
        (i.e., each subdirectory of self.outdir)
        """
        tiles = {}
        if not pathexists(self.outdir):
            warn('Tile directory %s does not exist'%self.outdir)
        
        tilef_regex = 'tile[0-9]*'+self.tileext
        basedirs = os.listdir(self.outdir)
        print('Loading image tile collections for',len(basedirs),'images')
        for basedir in basedirs:
            loadpattern = pathjoin(self.outdir,basedir,tilef_regex)
            tiles[basedir] = ImageCollection(loadpattern,
                                             conserve_memory=True,
                                             load_func=DefaultLoader())
        self.tiles = tiles
        return self.tiles
