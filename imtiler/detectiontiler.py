from __future__ import absolute_import, print_function, division

from .util import *
from .classmasktiler import *

from numpy.random import randint, permutation as randperm

class DetectionTiler(ClassMaskTiler):
    def __init__(self,detmask,tiledim,**kwargs):
        """
        __init__(self,detmask,tiledim,**kwargs)
        
        Summary: given a mask of detections, return tiles covering the positive detections, 
        along with tiles covering negative detections.
        
        Arguments:
        - detmask: detmask
        - tiledim: tiledim
        
        Keyword Arguments:

        
        Output:
        - output
        """
        tpmask,tnmask,fpmask = detmask,~detmask,np.zeros_like(detmask)
        kwargs.setdefault('ntprand',0)
        kwargs.setdefault('tp_conn',0)
        kwargs.setdefault('ntn',MATCH_POS)
        kwargs['tpcomp'] = kwargs.pop('detcomp',[])
        kwargs['fpcomp'] = fpmask.copy()
        super(DetectionTiler,self).__init__(tpmask,tnmask,fpmask,
                                            tiledim,**kwargs)

    def collect(self):
        ul = super(DetectionTiler,self).collect()
        return dict(pos=ul['tp'],neg=ul['tn'])
