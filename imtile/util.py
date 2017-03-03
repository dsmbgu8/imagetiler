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

tileinfof = 'tileinfo.txt'
tileinfohdr = 'tileid row_start row_stop col_start col_stop percent_valid'
def tile2str(tileslice):
    """
    converts 3d tile slice ((row_start,row_stop,None),(col_start,col_stop,None)) to
    output string format='row_start row_stop col_start col_stop'
    """
    return ' '.join(['%d %d'%(si.start,si.stop) for si in tileslice])

def extract_tile(img,ul,tdim,verbose=False):
    '''
    extract a tile of dims (tdim,tdim,img.shape[2]) offset from upper-left 
    coordinate ul in img, zero pads when tile overlaps image extent 
    '''
    assert(len(img.shape)==3)
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
def save_tiles(tiledict,outdir,outext,savefunc,**kwargs):
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
        
    outfiles = []
    for tul in sorted(tiledict.keys()):
        timg = tiledict[tul]
        outf = abspath(pathjoin(outdir,outprefix+'%d_%d'%tul)+outext)
        savefunc(outf,timg,overwrite=overwrite)
        outfiles.append(outf)
    print('Saved',len(outfiles),'tiles to',outdir)
    return outfiles

@timeit
def plot_tiles(tiledict,img,**kwargs):
    import pylab as pl
    from matplotlib.patches import Rectangle as rect
    patchkw = dict(edgecolor=kwargs.pop('color','g'),linewidth=1,fill=False)
    ax = kwargs.get('ax',None)
    if ax is None:
        fig,ax = pl.subplots(1,1,sharex=True,sharey=True)
        ax.imshow(img)
        
    for tul in sorted(tiledict.keys()):
        timg = tiledict[tul]
        tdim = (timg.shape[0],timg.shape[1])
        ax.add_patch(rect(tul[::-1],tdim[0],tdim[1],**patchkw))
    return ax

