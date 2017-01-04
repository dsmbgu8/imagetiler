from __future__ import absolute_import, print_function, division

from .util import *
from .imagetiler import *

from skimage.io.collection import ImageCollection

class TileCollection:
    """
    TileCollection: collections of subimage tiles extracted from a directory
    of large base images
    """

    def __init__(self,imgdir,imgext,tiledir,tiledim,maxtiles,
                 loadfunc,savefunc,maskfunc,**kwargs):
        self.imgdir  = imgdir
        self.imgext  = imgext
        self.outdir  = tiledir
        self.tiledim  = tiledim
        self.maxtiles = maxtiles
        self.loadfunc = loadfunc
        self.savefunc = savefunc        
        self.maskfunc = maskfunc
        self.tileext  = kwargs.pop('tileext','.jpg')
        self.verbose  = kwargs.pop('verbose',False)
        
        self.masked_reject=kwargs.pop('masked_reject',0.75)
        self.with_replacement=kwargs.pop('with_replacement',False)

        if not pathexists(self.outdir):
            os.makedirs(outdir)

        self.tiles = {}

    def extract(self,**kwargs):
        """
        extracts randomly selected image tiles for each of a set of base images
        in a specified directory

        Output: directory for each base image containing the image tiles and
        tile extraction log file
        """
        from glob import glob
        overwrite = kwargs.pop('overwrite',False)
        loadpattern = pathjoin(self.imgdir,'*%s'%self.imgext)
        imgfiles = glob(loadpattern)
        nimg = len(imgfiles)
        print('Extracting tiles for',nimg,'images')
        for i,imgf in enumerate(imgfiles):
            tiledir = pathjoin(self.outdir,splitext(basename(imgf))[0])

            img = np.atleast_3d(self.loadfunc(imgf))
            imgmask = self.maskfunc(imgf=imgf,img=img)
            if self.verbose:
                print("Image %d of %d"%(i+1,nimg),basename(imgf),'dims=',img.shape)
            tg = ImageTiler(img,imgmask,self.tiledim,self.maxtiles,
                            masked_reject=self.masked_reject,
                            with_replacement=self.with_replacement,
                            verbose=self.verbose)
            tg.write(tiledir,self.savefunc,overwrite=overwrite,
                     outext=self.tileext)
    @timeit
    def load(self,**kwargs):
        """
        returns dictionary contanining tiles, with each tile set
        represented as an imagecollection, for each base image
        (i.e., each subdirectory of self.outdir)
        """
        regen = kwargs.pop('regen',False)
        if not pathexists(self.outdir) or regen:
            self.extract(overwrite=regen)
        
        tiles = {}
        tilef_regex = '[0-9]*'+self.tileext
        basedirs = os.listdir(self.outdir)
        print('Loading image tile collections for',len(basedirs),'images')
        for basedir in basedirs:
            loadpattern = pathjoin(self.outdir,basedir,tilef_regex)
            tiles[basedir] = ImageCollection(loadpattern,
                                             conserve_memory=True,
                                             load_func=self.loadfunc)
        self.tiles = tiles
        return self.tiles
