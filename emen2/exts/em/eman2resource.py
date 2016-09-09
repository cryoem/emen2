# # $Id: eman2resource.py,v 1.4 2012/10/18 09:41:40 irees Exp $
# import re
# import os
# import pickle
# import traceback
# import time
# import random
# import cStringIO
# import tempfile
# import subprocess
# import atexit
# import signal
# 
# import jsonrpc.jsonutil
# 
# # Twisted Imports
# from twisted.internet import threads
# from twisted.python import failure, filepath
# from twisted.internet import threads
# from twisted.internet import defer
# from twisted.web.resource import Resource
# from twisted.web.static import *
# 
# import emen2.db.config
# 
# 
# 
# def loadEMAN():
#     # Try to import EMAN2..
#     try:
#         import EMAN2
#         # We need to steal these handlers from EMAN2...
#         # signal.signal(2, signal.SIG_DFL)
#         # signal.signal(15, signal.SIG_DFL)
#         # atexit.register(emen2.db.database.DB_Close)
#     except ImportError:
#         EMAN2 = None
#     return EMAN2
# 
# 
# 
# class RingDict(dict):
# 
#     def __init__(self, *args, **kwargs):
#         self.maxlen = kwargs.pop('maxlen', None)
#         self.order = [] # collections.deque()
#         dict.__init__(self, *args, **kwargs)
# 
# 
#     def __getitem__(self, key):
#         if key in self.order:
#             self.order.remove(key)
#         self.order.insert(0, key)
#         return dict.__getitem__(self, key)
# 
# 
#     def __delitem__(self, key):
#         if key in self.order:
#             self.order.remove(key)
#         dict.__delitem__(self, key)
# 
# 
#     def __setitem__(self, key, value):
#         if key in self.order:
#             self.order.remove(key)
# 
#         self.order.insert(0, key)
#         self.order = self.order[:self.maxlen]
# 
#         for i in self.keys():
#             if i not in self.order:
#                 del self[i]
# 
#         dict.__setitem__(self, key, value)
# 
# 
#     # def _check_compress(self, bdo):
#     #     compress = False
#     #     filepath = bdo.get('filepath')
#     #     workfile = bdo.get('filepath')
#     #
#     #     fs = bdo.get('filename').split(".")
#     #     if fs[-1] == "gz":
#     #         compress = "gzip"
#     #     elif fs[-1] == "bz2":
#     #         compress = "bzip2"
#     #
#     #     if compress:
#     #         fs.pop()
#     #         workfile = os.path.join(g.paths.tmp, "%s.%s"%(bdo.name.replace(":","."), fs[-1]))
#     #         if not os.access(workfile, os.F_OK):
#     #             print "Decompressing %s to %s"%(filepath, workfile)
#     #             a = subprocess.Popen("%s -d -c %s > %s"%(compress, filepath, workfile), shell=True)
#     #             a.wait()
#     #
#     #     return workfile
#     #
#     #
#     # def _open(self, bdo, ctxid=None):
#     #     key = bdo.name
#     #     emd = EMEN2RING.get(key)
#     #     if emd:
#     #         return emd
#     #
#     #     workfile = str(self._check_compress(bdo))
#     #
#     #     emd = EMAN2.EMData()
#     #     emd.read_image(workfile)
#     #     emd.process_inplace("normalize")
#     #     rmin = emd.get_attr("mean") - emd.get_attr("sigma") * 3.0
#     #     rmax = emd.get_attr("mean") + emd.get_attr("sigma") * 3.0
#     #     emd.set_attr("render_min", rmin)
#     #     emd.set_attr("render_max", rmax)
#     #     EMEN2RING[key] = emd
#     #     return emd
# 
# 
# 
# 
# ##########################################
# # Download Resource
# 
# 
# class EMAN2BoxResource(Resource, File):
#     """This class keeps an internal ring buffer of open EMData objects, and renders boxes cut out from them"""
# 
#     isLeaf = True
#     defaultType="application/octet-stream"
#     ring = RingDict(maxlen=10)
# 
#     def render(self, request):
#         host = request.getClientIP()
#         args = request.args
#         request.postpath = filter(bool, request.postpath)
#         ctxid = request.getCookie("ctxid")
# 
#         if request.args.get("ctxid"):
#             ctxid = request.args.get("ctxid",[None])[0]
# 
#         bdo = request.postpath[0]
#         method = request.postpath[1]
#         d = threads.deferToThread(self.action, bdo, method, request.args, ctxid, host)
#         d.addErrback(self._ebRender, request)
# 
#         if method == "box":
#             d.addCallback(self._boxRender, request)
#         else:
#             d.addCallback(self._cbRender, request)
# 
#         return server.NOT_DONE_YET
# 
# 
#     def _check_compress(self, bdo):
# 
#         compress = False
#         filepath = bdo.get('filepath')
#         workfile = bdo.get('filepath')
# 
#         fs = bdo.get('filename').split(".")
#         if fs[-1] == "gz":
#             compress = "gzip"
#         elif fs[-1] == "bz2":
#             compress = "bzip2"
# 
#         if compress:
#             fs.pop()
#             tmppath = emen2.db.config.get('paths.tmp')
#             workfile = os.path.join(tmppath, "%s.%s"%(bdo.name.replace(":","."), fs[-1]))
#             if not os.access(workfile, os.F_OK):
#                 # print "Decompressing %s to %s"%(filepath, workfile)
#                 a = subprocess.Popen("%s -d -c %s > %s"%(compress, filepath, workfile), shell=True)
#                 a.wait()
# 
#         return workfile
# 
# 
#     def _open(self, bdo, ctxid=None):
#         import EMAN2
# 
#         key = bdo.name
#         emd = self.ring.get(key)
#         if emd:
#             return emd
# 
#         workfile = str(self._check_compress(bdo))
# 
#         emd = EMAN2.EMData()
#         emd.read_image(workfile)
#         emd.process_inplace("normalize")
#         rmin = emd.get_attr("mean") - emd.get_attr("sigma") * 3.0
#         rmax = emd.get_attr("mean") + emd.get_attr("sigma") * 3.0
#         emd.set_attr("render_min", rmin)
#         emd.set_attr("render_max", rmax)
#         self.ring[key] = emd
#         return emd
# 
# 
# 
#     def method_auto_contrast(self, bdo, args):
#         emd = self._open(bdo)
#         rmin = emd.get_attr("mean") - emd.get_attr("sigma") * 3.0
#         rmax = emd.get_attr("mean") + emd.get_attr("sigma") * 3.0
#         emd.set_attr("render_min", rmin)
#         emd.set_attr("render_max", rmax)
#         return emd.get_attr_dict()
# 
# 
#     def method_get_attr_dict(self, bdo, args):
#         emd = self._open(bdo)
#         return emd.get_attr_dict()
# 
# 
#     def method_get_range(self, bdo, args):
#         emd = self._open(bdo)
#         return emd.get_attr("render_min"), emd.get_attr("render_max")
# 
# 
#     def method_set_range(self, bdo, args):
#         rmin = int(args.get("min", [0])[0])
#         rmax = int(args.get("max", [0])[0])
#         emd = self._open(bdo)
#         emd.set_attr("render_min", rmin)
#         emd.set_attr("render_max", rmax)
#         return emd.get_attr("render_min"), emd.get_attr("render_max")
# 
# 
# 
#     def method_autobox(self, bdo, args):
#         # particle_diameter=128
# 
#         emd = self._open(bdo)
#         boxertools.set_idd_image_entry(bdo.get(name), boxertools.FLCFImage.DB_NAME, emd)
# 
# 
# 
#         boxes = [[1024,1024], [512, 1024], [2048, 2048]]
#         boxer = e2boxer.SwarmBoxer()
#         boxer.handle_file_change(filename)
#         boxer_vitals = emboxerbase.EMBoxerModuleVitals(file_names=[filename])
#         boxer_vitals.current_idx=0
#         boxer.target = weakref.ref(boxer_vitals)
#         boxer.clear_all()
#         for box in boxes:
#             boxer.add_ref(box[0], box[1], filename)
# 
#         ret = boxer.auto_box(filename, True, True, cache=False)
#         return ret
# 
# 
# 
#     def method_box(self, bdo, args):
#         import EMAN2
# 
#         size = float(args.get("size",[128])[0])
#         scale = float(args.get("scale",[1])[0])
#         x = float(args.get("x", [0])[0])
#         y = float(args.get("y", [0])[0])
#         fill = args.get("fill", [None])[0]
#         emd = self._open(bdo)
# 
# 
#         region = EMAN2.Region(x, y, size, size)
#         if fill:
#             cutout = emd.get_clip(region, fill=emd.get_attr('maximum'))
#         else:
#             cutout = emd.get_clip(region)
# 
# 
#         # print "imgsize: %s size: %s scale: %s x: %s y: %s"%(emd.get_attr('nx'), size, scale, x, y)
# 
#         if scale > 1:
#             #cutout.process_inplace("math.meanshrink", {"n":scale})
#             cutout.process_inplace("xform.scale", {"scale":1/scale})
# 
#         # rmin, rmax = emd.get_attr("render_min"), emd.get_attr("render_max")
#         if args.has_key("min") or args.has_key("max"):
#             rmin = float(args.get("min", [0])[0])
#             rmax = float(args.get("max", [0])[0])
#             cutout.set_attr("render_min", rmin)
#             cutout.set_attr("render_max", rmax)
# 
#         outfile = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
# 
#         f = outfile.name
#         outfile.close()
#         cutout.write_image(f)
#         return f
# 
# 
#     def action(self, bdo, method, args, ctxid, host, db=None):
# 
#         with db:
#             db._setContext(ctxid,host)
#             bdo = db.binary.get(bdo)
# 
#         if not bdo:
#             raise IOError
# 
#         if method == "box":
#             return self.method_box(bdo, args)
# 
#         elif method == "set_range":
#             return self.method_set_range(bdo, args)
# 
#         elif method == "get_range":
#             return self.method_get_range(bdo, args)
# 
#         elif method == "get_attr_dict":
#             return self.method_get_attr_dict(bdo, args)
# 
#         elif method == "auto_contrast":
#             return self.method_auto_contrast(bdo, args)
# 
# 
# 
#     def cbRender(self, result, request):
#         result = jsonrpc.jsonutil.encode(result).encode("utf-8")
#         request.write(result)
#         request.finish()
# 
# 
#     def _boxRender(self, result, request):
#         """You know what you doing."""
#         request.setHeader('content-type', 'image/png')
#         fsize = size = os.stat(result).st_size
#         f = open(result)
#         FileTransfer(f, size, request)
#         # f.close()
# 
# 
#     def dbRender(self,failure,request):
# 
#         errmsg = "Unspecified Error"
#         errcode = 500
# 
#         try:
#             failure.raiseException()
#         except IOError,e:
#             errcode = 404
#             errmsg = "File Not Found"
#         except Exception,e:
#             errmsg = str(e)
#             raise
# 
#         data = errmsg
# 
#         request.setResponseCode(errcode)
#         request.setHeader("content-type", "text/html; charset=utf-8")
#         request.setHeader('content-length',len(data))
#         request.write(data)
# 
#         request.finish()
# 
# 
# 
# __version__ = "$Revision: 1.4 $".split(":")[1][:-1].strip()
