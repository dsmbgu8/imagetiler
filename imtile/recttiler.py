from __future__ import absolute_import, print_function, division

from .util import *
from .basetiler import *

class RectTiler(BaseTiler):
    def __init__(self,rcomp,tiledim,**kwargs):
        '''
        conn=1: only center tile
        conn=4: center tile + 4 quad offsets
        conn=8: center tile + 8 octal offsets
        '''
        self.rclab = kwargs.pop('rclab',np.unique(rcomp[rcomp!=0]))
        self.conn = kwargs.pop('conn',8)
        self.maskskip = kwargs.pop('mask',[])
        if len(self.maskskip) != 0:
            self.maskskip = np.atleast_3d(self.maskskip)
        
        self.ul = []
        self.rcomp = rcomp
        self.tiledim = tiledim

    def collect(self):
        if self.ul != []:
            return self.ul

        t2,t4,t8 = self.tiledim//2,self.tiledim//4,self.tiledim//8
        toff = []
        if self.conn == 4:
            toff.extend([-t4,t4])
        elif self.conn == 8:
            toff.extend([-t4,-t8,t8,t4])
            
        ul = []
        for r in self.rclab:
            c = np.uint32(map(np.mean,np.where(self.rcomp==r)))
            print('lab',r,c)
                         
            # get center tile
            cul = (c[0]-t2,c[1]-t2)
            if len(self.maskskip)!=0:
                tmask = extract_tile(self.maskskip,cul,self.tiledim)
                if tmask.any():
                    print(cul,'overlaps',tmask.sum(),'masked pixels')
                    continue   
            
            ul.append(cul)

            # get quad/octal offset tiles
            for ti in toff:
                for tj in toff:
                    tul = (cul[0]+ti,cul[1]+tj)
                    if len(self.maskskip)!=0:
                        tmask = extract_tile(self.maskskip,tul,self.tiledim)
                        if tmask.any():
                            print(tul,'overlaps',tmask.sum(),'masked pixels')
                            continue 
                    ul.append(tul)        

        self.ul = ul
        return self.ul
