from __future__ import absolute_import, print_function, division
import pylab as pl
from imtiler import *
from imtiler.util import *

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
        if isinstance(img,str) and pathexists(img):
            img = loadfunc(img)
        return np.isfinite(np.atleast_3d(img)).all(axis=2)

maskfunc = DefaultMasker()

if __name__ == '__main__':
    import argparse
    import numpy as np
    
    parser = argparse.ArgumentParser(description='Image tiler')
    parser.add_argument('-t','--tiledim', type=int, default=256,
                       help='Tile dimension')
    parser.add_argument('-n','--numtiles', type=int, default=10,
                       help='Max number of tiles to extract from each image')
    parser.add_argument('-a','--accept', type=float, default=0.75,
                       help='% of valid pixels neccessary to accept tiles')
    parser.add_argument('-r','--replacement', action='store_true',
                       help='Sample image tiles with replacement')
    parser.add_argument('-s','--seed', type=int, default=42,
                        help='Random seed value')    
    parser.add_argument('-o','--outdir', default='./tile_cache/',
                        type=str, help='Output directory for image tiles')    
    parser.add_argument('-c','--clobber', action='store_true',
                       help='Overwrite image tiles if they already exist')
    parser.add_argument('-e','--ext', type=str, default='.png',
                       help='Output file extension')    
    parser.add_argument('-v','--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('image', type=str, metavar='IMAGE',
                       help='Image to tile')
    args = parser.parse_args()

    np.random.seed(args.seed)

    verbose = args.verbose
    
    imagef = args.image
    imagebase,imageext = splitext(imagef)
    
    # output dir / extension for tile images
    tiledir = args.outdir
    tileext = args.ext 

    # tile parameters
    tiledim  = args.tiledim
    numtiles = args.numtiles
    accept   = args.accept
    replace  = args.replacement

    image = loadfunc(imagef)
    mask  = maskfunc(image)

    imggrid = bands2grid(image,1,orientation='square')
    pl.imshow(imggrid.squeeze())
    pl.show()
    
    tiledir = pathjoin(tiledir,splitext(basename(imagef))[0])
    if not pathexists(tiledir):
        os.makedirs(tiledir)
    
    tiler = MaskTiler(mask,tiledim,numtiles,accept=accept,
                      replacement=replace,verbose=verbose)

    ul = tiler.collect()
    save_tiles(image,ul,tiledim,tiledir,tileext,savefunc,outprefix='tile')

    sys.exit(0)
