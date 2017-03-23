from __future__ import absolute_import, print_function, division
import sys,os

from os.path import exists as pathexists, join as pathjoin, split as pathsplit
from os.path import splitext, basename, dirname, abspath

import numpy as np
from warnings import warn


class ScikitImageLoader:
    """
    demo imageloader function class (necessary for skimage collections)
    """    
    def __call__(self, imgf, **kwargs):
        from skimage.io import imread
        return imread(imgf,plugin='matplotlib')

class ScikitImageSaver:
    """
    demo imagesaver function class 
    """
    def __call__(self, outf, outimg, **kwargs):
        from skimage.io import imsave
        overwrite = kwargs.pop('overwrite',False)
        if pathexists(outf) and not overwrite:
            warn('File %s exists, skipping'%outf)
        else:
            imsave(outf,outimg.squeeze())
            
class DefaultMasker:
    """        
    Summary: demo mask function, marks all pixels in image img as valid
    
    Arguments:
    - imgf: image file
    - loadfunc: image loader function
    
    Keyword Arguments:
    - img: image array (default None)
    
    Output:
    - all true boolean mask with the same number of pixels as img
    """
    def __call__(self, img, **kwargs):
        if isinstance(img,str) and pathexists(img):
            img = loadfunc(img)
            
        return np.ones([img.shape[0],img.shape[1]],dtype=np.bool8)

loadfunc = ScikitImageLoader()
savefunc = ScikitImageSaver()
maskfunc = DefaultMasker()

def timeit(func):
    '''
    Decorator to time the invocation of a function
    '''
    import time
    gettime = time.time
    
    outstr = '%s.%s elapsed time: %0.3f seconds'
    def wrapper(*args,**kwargs):
        starttime  = gettime()
        res = func(*args,**kwargs)
        print(outstr%(func.__module__,str(func).split()[1], gettime()-starttime))
        return res
    return wrapper

def tile2str(tileslice):
    """
    converts 3d tile slice ((row_start,row_stop,None),(col_start,col_stop,None)) to
    output string format='row_start row_stop col_start col_stop'
    """
    return ' '.join(['%d %d'%(si.start,si.stop) for si in tileslice])

def summarize_tiles(ul_list,tdim):
    tileinfof = 'tileinfo.txt'
    tileinfohdr = 'tileid,row_start,row_stop,col_start,col_stop'
    tstr = [tileinfohdr]
    for i,ul in enuemerate(ul_list):
        tstr.append(' '.join(map(str,(i,ul[0],ul[0]+tdim,ul[1],ul[1]+tdim))))
    tstr = '\n'.join(tstr)
    with open(tileinfof,'w') as fid:
        print(tstr,file=fid)

def bands2grid(img,gb,orientation='columnwise'):
    """
    bands2grid(img,gb,orientation='columnwise')
    
    Summary: converts a [r x c x b] multiband image to a [r x gc x gb]
    image grid
    
    Arguments:
    - img: [r x c x b] multiband image to split into grid
    - gb: number of bands for each image in grid
          (must be a multiple of img.shape[2])
    
    Keyword Arguments:
    - orientation: 'columnwise', 'rowwise', 'square'
    
    Output:
    - [r x gc x gb] image grid
    """
    assert((img.ndim==3) and (img.shape[2]>=2*gb) and (img.shape[2]%gb)==0)
    nr,nc,nb = img.shape
    gcell = int(nb/gb)
    if orientation=='columnwise':
        gr,gc = 1,gcell
    elif orientation=='rowwise':
        gr,gc = gcell,1
    elif orientation=='square':
        gsq = np.sqrt(gcell)
        if gsq-int(gsq)!=0:
            gsq = np.ceil(gsq)
            warn('gridded image contains %d empty cells'%((gsq**2)-gcell))
        gsq = int(gsq)
        gr,gc = gsq,gsq

    def gridslice(gidx):
        # return the whole image by default
        gri,gci = int(gidx/gc),gidx%gc
        sl = (slice(gri*nr,(gri+1)*nr,None),
              slice(gci*nc,(gci+1)*nc,None))
        return sl
            
    gimg = np.zeros([gr*nr,gc*nc,gb],dtype=img.dtype)
    for gi in range(gcell):
        gimg[gridslice(gi)] = img[...,gi:gi+gb]
    return gimg

def disk(radius):
    from skimage.morphology import disk as _disk
    return _disk(radius)

def bwdilate(bwimg,**kwargs):
    from skimage.morphology import binary_dilation as _bwd
    kwargs.setdefault('selem',disk(3))
    return _bwd(bwimg,**kwargs)

def randperm(a):
    return np.random.permutation(a)

def blockpermute(a,blen=25):
    b = min(a.shape[0]//2,blen)
    nb = a.shape[0]//b
    bmax = nb*b
    for i in range(0,bmax,b):
        a[i:i+b] = randperm(a[i:i+b])
    a[bmax:] = randperm(a[bmax:])
    return a

def extract_tile(img,ul,tdim,verbose=False):
    '''
    extract a tile of dims (tdim,tdim,img.shape[2]) offset from upper-left 
    coordinate ul in img, zero pads when tile overlaps image extent 
    '''
    assert(img.ndim==3)
    nr,nc,nb = img.shape
    
    lr = (ul[0]+tdim,ul[1]+tdim)
    padt,padb = abs(max(0,-ul[0])), tdim-max(0,lr[0]-nr)
    padl,padr = abs(max(0,-ul[1])), tdim-max(0,lr[1]-nc)
    
    ibeg,iend = max(0,ul[0]),min(nr,lr[0])
    jbeg,jend = max(0,ul[1]),min(nc,lr[1])

    if verbose:
        print(ul,nr,nc)
        print(padt,padb,padl,padr)
        print(ibeg,iend,jbeg,jend)

    imgtile = np.zeros([tdim,tdim,nb],dtype=img.dtype)
    imgtile[padt:padb,padl:padr] = img[ibeg:iend,jbeg:jend]
    return imgtile

@timeit
def extract_tiles(img,ul_list,tdim):
    tiledict = {}
    for ul in ul_list:
        tiledict[ul] = extract_tile(img,ul,tdim)
    return tiledict

@timeit
def save_tiles_dict(img,ul_dict,tdim,outdir,outext,savefunc,**kwargs):    
    # ul_dict = dict of (key0,[coord00, ..., coord0N]) pairs
    outf = {}
    for key in ul_dict:
        # save tiles in 'outdir/key' directory
        outf[key] = save_tiles_list(img,ul_dict[key],tdim,pathjoin(outdir,key),
                                    outext,savefunc,**kwargs)
    
    return outf

@timeit
def save_tiles_list(img,ul_list,tdim,outdir,outext,savefunc,**kwargs):
    # ul_list = list of [coord0, ..., coordN] ul coordinates
    if len(ul_list)==0:
        print('empty ul_list: no tiles saved to',outdir)
        return []
    
    overwrite = kwargs.pop('overwrite',False)
    outprefix = kwargs.pop('outprefix','tile')
    if pathexists(outdir) and overwrite:
        import glob
        outregex = outprefix+'*'+outext
        rmfiles = glob.glob(pathjoin(outdir,outregex))
        for rmf in rmfiles:
            os.remove(rmf)
        msg = 'removed %d existing files '%len(rmfiles)
        msg += 'matching pattern "%s" in directory %s'%(outregex,outdir)
        print(msg)
    elif not pathexists(outdir):
        print('created directory %s'%outdir)
        os.makedirs(outdir)

    tiledict = extract_tiles(img,ul_list,tdim)
    outfiles = []
    for tul in sorted(tiledict.keys()):
        timg = tiledict[tul]
        outf = abspath(pathjoin(outdir,outprefix+'%d_%d'%tul)+outext)
        savefunc(outf,timg,overwrite=overwrite)
        outfiles.append(outf)
    print('Saved',len(outfiles),'tiles to',outdir)
    return outfiles

# alias for convenience sake
def save_tiles(img,ul,tdim,outdir,outext,savefunc,**kwargs):
    if isinstance(ul,list):
        func = save_tiles_list
    elif isinstance(ul,dict):
        func = save_tiles_dict
    return func(img,ul,tdim,outdir,outext,savefunc,**kwargs)

@timeit
def plot_tiles(img,ul_list,tdim,**kwargs):
    import pylab as pl
    from matplotlib.patches import Rectangle as rect
    patchkw = dict(edgecolor=kwargs.pop('color','g'),linewidth=1,fill=False)
    mask = kwargs.pop('mask',np.ones_like(img))
    show = kwargs.pop('show',True)

    fig,ax = pl.subplots(1,2,sharex=True,sharey=True)
    ax[0].imshow(img.squeeze())
    ax[1].imshow(mask.squeeze())
        
    for ul in ul_list:
        ax[0].add_patch(rect(ul[::-1],tdim,tdim,**patchkw))
        ax[1].add_patch(rect(ul[::-1],tdim,tdim,**patchkw))

    if show:
        pl.show()
            
    return ax

