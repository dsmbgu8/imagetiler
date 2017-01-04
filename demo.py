from __future__ import absolute_import, print_function, division
import pylab as pl
from imtile import *
from imtile.util import *

# either use default loader+saver+mask functions
loadfunc = DefaultLoader()
savefunc = DefaultSaver()
maskfunc = DefaultMasker()

# or override defaults like this:
class FiniteMasker:
    """
    Summary: marks pixels with elts that are all finite as valid
    
    Arguments:
    - img: image array
    
    Keyword Arguments:
    None
    
    Output:
    - boolean mask with the same number of pixels as img
    """
    def __call__(self, img, **kwargs):
        import numpy as np
        return np.isfinite(np.atleast_3d(img)).all(axis=2)
maskfunc = FiniteMasker()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Image tiler')
    parser.add_argument('-e','--imgext', type=str, default='.jpg',
                       help='Image file extension')
    parser.add_argument('-d','--tiledim', type=int, default=250,
                       help='Tile dimension')
    parser.add_argument('-n','--numtiles', type=int, default=10,
                       help='Max number of tiles to extract from each image')
    parser.add_argument('-o','--overlap', type=float, default=0.75,
                       help='% value to reject tiles that overlap mask')
    parser.add_argument('-w','--with-replacement', action='store_true',
                       help='Sample image tiles with replacement')
    parser.add_argument('-r','--regen-tiles', action='store_true',
                       help='Regenerate image tiles if they already exist')

    parser.add_argument('-v','--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('imgdir', type=str, metavar='IMGDIR',
                       help='Image directory')
    parser.add_argument('outdir', metavar='OUTDIR', default='./tiles/',
                       type=str, help='Output directory for image tiles')    
    args = parser.parse_args()
    
    imgdir = args.imgdir
    imgext = args.imgext    
    verbose = args.verbose

    # output dir / extension for tile images
    tiledir = args.outdir
    tileext = imgext

    # tile parameters
    tiledim = args.tiledim
    maxtiles = args.numtiles
    masked_reject = args.overlap
    with_replacement = args.with_replacement
    regen_tiles = args.regen_tiles
    tc = TileCollection(imgdir,imgext,tiledir,tiledim,maxtiles,
                        loadfunc,savefunc,maskfunc,masked_reject=masked_reject,
                        with_replacement=with_replacement,tileext=tileext,
                        verbose=verbose)
    
    tiles = tc.load(regen=regen_tiles)
    for imgkey in tiles:
        imgtiles = tiles[imgkey]
        print(imgkey+':',len(imgtiles),'tiles of shape',imgtiles[-1].shape)
        pl.imshow(imgtiles[-1],cmap='gray')
        pl.show()
