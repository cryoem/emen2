# $Id: handlers.py,v 1.6 2013/02/28 00:49:55 irees Exp $
'''File handlers.'''

import time
import math
import os
import signal
import struct
import json
import sys
import cPickle as pickle

# For file writing
import tempfile

# EMEN2 imports
# Provide a dummy handler if EMEN2 cannot be imported.
class DummyHandler(object):
    @classmethod
    def register(cls, *args, **kwargs):
        def f(o):
            return o
        return f
  
try:
    import emen2.db.handlers
    BinaryHandler = emen2.db.handlers.BinaryHandler
except:
    BinaryHandler = DummyHandler
    

# EMAN2 can only be imported in the main thread.
try:
    import EMAN2
    # We need to steal these handlers back from EMAN2...
    signal.signal(2, signal.SIG_DFL)
    signal.signal(15, signal.SIG_DFL)
except ImportError:
    EMAN2 = None


class EMDataBuilder(object):
    '''Helper class to build tiles and thumbnails for EMAN2-readable files.
    
    Ex:
    builder = EMDataBuilder()
    tile = builder.build("test.dm3", "test.dm3.tile")

    There is a kludge to write out some additional scaled images:
    
    copyout = {
        128: "thumb.jpg",
        512: "small.jpg"
    }
    builder = EMDataBuilder()
    tile = builder.build("test.dm3", "test.dm3.tile", copyout=copyout)

    '''
    
    def build(self, workfile, outfile, copyout=None):
        '''Main build function.'''
        # print "Building: %s -> %s"%(workfile, outfile)
        self.workfile = workfile
        self.outfile = outfile

        # Temporary directory
        self.tmpdir = tempfile.mkdtemp(prefix='emen2thumbs.')

        # Number of images in the file
        self.nimg = EMAN2.EMUtil.get_image_count(workfile)

        # Awful hack to write out regular thumbs
        self.copyout = copyout or {}

        # Build each image in the file
        ret = []        
        for index in range(self.nimg):
            ret.append(self._build(index))
        
        # Combine all the files into the tile file
        self._build_compile(ret, outfile)
        
        # CLeanup
        try:
            # print "Removing tmpdir:", self.tmpdir
            os.rmdir(self.tmpdir)
        except:
            # print "Couldn't remove tmpdir: ", self.tmpdir
            pass
        
        # print ret
        return ret
        

    def _build(self, index):
        '''Build a single image in the file.'''
        # print "...index:", index
        header = {}

        # Read the header
        img = EMAN2.EMData()
        img.read_image(self.workfile, 0, True)
        h = img.get_attr_dict()
        
        # Copy basic header information
        header['nx'] = h['nx']
        header['ny'] = h['ny']
        header['nz'] = h['nz']
        header['slices'] = []
        
        if header['nz'] == 1:
            # 2D Image
            img2 = EMAN2.EMData()
            img2.read_image(self.workfile, index, False)
            img2.process_inplace("normalize")
            if self.nimg > 1:
                # ... stack of 2D images.
                header['slices'].append(self.build_slice(img2, index=index, fixed=[128,512,1024]))
            else:
                # regular old 2D image -- also generate power spectrum and tiles.
                header['slices'].append(self.build_slice(img2, index=index, tile=True, pspec=True, fixed=[128,512,1024]))
        
        else:        
            # 3D Image -- read region for each Z slice
            for i in range(header['nz']):
                region = EMAN2.Region(0, 0, i, header['nx'], header['ny'], 1)
                img2 = EMAN2.EMData()
                img2.read_image(self.workfile, 0, False, region)
                header['slices'].append(self.build_slice(img2, index=index, nz=i, fixed=[128,512,1024]))
        
        return header
        

    def _build_compile(self, ret, outfile):
        '''Combine the results into a single tile file.'''
        # print "...compiling"    
        # Get items to pack
        self.pos = 0
        self.packed = []
        def pack(items):
            for i,j in sorted(items.items()):
                f = j[0]
                j[0] = self.pos
                j[1] = os.stat(f).st_size
                self.pos += j[1]
                self.packed.append(f)
        
        for index in ret:
            for sl in index.get('slices', []):
                pack(sl.get('tiles', {}))
                pack(sl.get('fixed', {}))
                pack(sl.get('pspec', {}))
                pack(sl.get('pspec1d', {}))
        
        # Move all the packed files into the archive
        tf = file(outfile, "wb")
        pickle.dump(ret, tf)
        for filename in self.packed:
            a = open(filename, "r")
            b = a.read()
            a.close()
            tf.write(b)
            os.remove(filename)

        tf.close()        


    def build_slice(self, img, nz=1, index=0, tile=False, pspec=False, fixed=None):
        '''Build a single 2D slice from a 2D or 3D image.'''
        header = {}

        h = img.get_attr_dict()
        header['nx'] = h['nx']
        header['ny'] = h['ny']
        header['nz'] = h['nz']
        
        if tile:
            # print "...tiles"
            header['tiles'] = self.build_tiles(img, nz=nz, index=index)

        if pspec:
            # print "...pspec"
            header['pspec'], header['pspec1d'] = self.build_pspec(img, nz=nz, index=index)

        if fixed:
            # print "...fixed"
            header['fixed'] = {}
            for f in fixed:
                header['fixed'][f] = self.build_fixed(img, tilesize=f, nz=nz, index=index)

        return header
        
        
    def build_tiles(self, img, nz=1, index=0, tilesize=256):
        '''Build tiles for a 2D slice.'''
        # Work with a copy of the EMData
        img2 = img.copy()        

        # Calculate the number of zoom levels based on the tile size
        levels = math.ceil( math.log( max(img.get_xsize(), img.get_ysize()) / tilesize) / math.log(2.0) )

        # Tile header
        header = img.get_attr_dict()
        tile_dict = {}

        # Step through shrink range creating tiles
        for level in range(int(levels)):
            scale = 2**level
            rmin = img2.get_attr("mean") - img2.get_attr("sigma") * 3.0
            rmax = img2.get_attr("mean") + img2.get_attr("sigma") * 3.0
            for x in range(0, img2.get_xsize(), tilesize):
                for y in range(0, img2.get_ysize(), tilesize):
                    i = img2.get_clip(EMAN2.Region(x, y, tilesize, tilesize), fill=rmax)
                    i.set_attr("render_min", rmin)
                    i.set_attr("render_max", rmax)
                    i.set_attr("jpeg_quality", 80)
                    # Write output
                    fsp = "tile.index-%d.scale-%d.z-%d.x-%d.y-%d.jpg"%(index, scale, nz, x/tilesize, y/tilesize)
                    fsp = os.path.join(self.tmpdir, fsp)
                    i.write_image(fsp)
                    tile_dict[(scale, x/tilesize, y/tilesize)] = [fsp, None, 'jpg', tilesize, tilesize]
                    
            # Shrink by 2 for next round.
            img2.process_inplace("math.meanshrink",{"n":2})

        return tile_dict

        
    def build_fixed(self, img, tilesize=256, nz=1, index=0):
        """Build a thumbnail of a 2D EMData."""
        # Output files
        fsp = "fixed.index-%d.z-%d.size-%d.jpg"%(index, nz, tilesize)
        fsp = os.path.join(self.tmpdir, fsp)

        # The scale factor
        thumb_scale = img.get_xsize() / float(tilesize), img.get_ysize() / float(tilesize)
        sc = 1 / max(thumb_scale)

        if tilesize == 0 or sc >= 1.0:
            # Write out a full size jpg
            img2 = img.copy()
        else:
            # Shrink the image
            # print "shrink to thumbnail with scale factor:", sc, 1/sc, math.ceil(1/sc)
            # img2 = img.process("xform.scale", {"scale":sc, "clip":tilesize})
            img2 = img.process("math.meanshrink", {'n':math.ceil(1/sc)})

        # Adjust the brightness for rendering
        rmin = img2.get_attr("mean") - img2.get_attr("sigma") * 3.0
        rmax = img2.get_attr("mean") + img2.get_attr("sigma") * 3.0
        img2.set_attr("render_min", rmin)
        img2.set_attr("render_max", rmax)
        img2.set_attr("jpeg_quality", 80)        
        img2.write_image(fsp)
        
        # Awful hack to write out regular thumbs
        if index == 0 and nz == 1 and tilesize in self.copyout:
            # print "...copy thumb:", tilesize, self.copyout[tilesize]
            img2.write_image(self.copyout[tilesize])

        return [fsp, None, 'jpg', img2.get_xsize(), img2.get_ysize()]

    
    def build_pspec(self, img, tilesize=512, nz=1, index=0):
        """Build a 2D FFT and 1D rotationally averaged power spectrum of a 2D EMData."""
        
        # Return dictionaries
        pspec_dict = {}
        pspec1d_dict = {}

        # Output files
        outfile = "pspec.index-%d.z-%d.size-%d.png"%(index, nz, tilesize)
        outfile = os.path.join(self.tmpdir, outfile)        

        outfile1d = "pspec1d.index-%d.z-%d.size-%d.json"%(index, nz, tilesize)
        outfile1d = os.path.join(self.tmpdir, outfile1d)        

        # Create a new image to hold the 2D FFT
        nx, ny = img.get_xsize() / tilesize, img.get_ysize() / tilesize
        a = EMAN2.EMData()
        a.set_size(tilesize, tilesize)
        
        # Image isn't big enough..
        if (ny<2 or nx<2):
            return pspec_dict, pspec1d_dict
            
        # Create FFT
        for y in range(1,ny-1):
            for x in range(1,nx-1):
                c = img.get_clip(EMAN2.Region(x*tilesize, y*tilesize, tilesize, tilesize))
                c.process_inplace("normalize")
                c.process_inplace("math.realtofft")
                c.process_inplace("math.squared")
                a += c

        # Reset the center value
        a.set_value_at(tilesize/2, tilesize/2, 0, .01)

        # Adjust brightness
        a -= a.get_attr("minimum") - a.get_attr("sigma") * .01
        a.process_inplace("math.log")
        a.set_attr("render_min", a.get_attr("minimum") - a.get_attr("sigma") * .1)
        a.set_attr("render_max", a.get_attr("mean") + a.get_attr("sigma") * 4.0)

        # Write out the PSpec png
        a.write_image(outfile)

        # Add to dictionary
        pspec_dict[tilesize] = [outfile, None, 'png', a.get_xsize(), a.get_ysize()]

        # Calculate
        t = (tilesize/2)-1
        y = a.calc_radial_dist(t, 1, 1, 0) # radial power spectrum (log)
        f = open(outfile1d, "w")
        json.dump(y,f)
        f.close()
        pspec1d_dict[tilesize] = [outfile1d, None, 'json', t]
        
        # Return both the 2D and 1D files
        return pspec_dict, pspec1d_dict


##### Cryo-EM file format handlers #####

class EMDataHandler(BinaryHandler):
    _allow_gzip = True

    def _thumbnail_build(self, workfile):
        outfile = self._outfile('eman2')
        copyout = {
            128: self._outfile('thumb.jpg'),
            512: self._outfile('small.jpg')
        }
        builder = EMDataBuilder()
        tile = builder.build(str(workfile), outfile, copyout=copyout)            
        


@BinaryHandler.register(['dm3', 'mrc', 'tif', 'tiff', 'hdf'])
class MicrographHandler(EMDataHandler):
    _allow_gzip = True
    


# IMPORTANT -- Do not change this.
if __name__ == "__main__":
    emen2.db.handlers.main(globals())

    
