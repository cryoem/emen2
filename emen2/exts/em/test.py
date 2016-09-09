import os
import sys
import collections
import operator
import getpass
import math
import json    

# import emen2.clients
import emen2.db.admin


PROJECT  = EMAN2.db_open_dict("bdb:project")
APIX = PROJECT.get('global.apix')

    
def open_refine_classes(refine, classes, prefix=None, mappings=None, db=None):
    if not mappings:
        mappings = {}
        
    cmd_dict = EMAN2.db_open_dict("bdb:%s#register"%refine).get('cmd_dict',{})
    classes = EMAN2.db_open_dict("bdb:%s#%s"%(refine,classes))

    input_set = cmd_dict.get('input')
    input_set = EMAN2.db_open_dict(input_set)
    
    source_uri = {}
    ptcl_source = {}
    ptcl_by_class = {}
    ptcl_excl_by_class = {}

    ptcl_source = collections.defaultdict(set)
    included = set()
    excluded = set()
    
    print "Reading input set (%s particles)"%input_set['maxrec']
    for i in range(0,input_set['maxrec']+1):
        src = input_set.get_header(i).get('data_source')
        ptcl_source[src].add(i)
        
    
    print "Reading refinement classes (%s classes)"%classes['maxrec']
    for i in range(0,classes['maxrec']+1):
        included |= set(classes[i].get_attr_default('class_ptcl_idxs') or [])
        excluded |= set(classes[i].get_attr_default('exc_class_ptcl_idxs') or [])

    included -= excluded


    print "Reading particle sets to get source_uris"
    for k in ptcl_source:
        d = EMAN2.db_open_dict(k)
        s = d[0].get_attr_default('source_uri')
        if s: source_uri[k] = s
            
    print source_uri
    
    scores = {}
    
    # Create a score for each micrograph
    print "Calculating score"
    for k,v in ptcl_source.items():
        incl = v & included
        excl = v & excluded
        scores[k] = len(incl)/float(len(v)) #1.0 - 


    source_map = collections.defaultdict(list)    
    total = float(len(scores))
    for count, k in enumerate(sorted(scores, key=scores.get)):
        # print k, scores[k]
        srcbin = int((count/total)*10)
        # srcbin = int(scores[k]*20)
        source_map[srcbin].append(k)


    #putrecs = []
    # for k,v in scores.items():
    #     s = source_uri.get(k)
    #     if not s:
    #         continue
    #     bdo = db.binary.get(s.split("/")[-1])    
    #     recid = bdo.get('name')
    #     rec = db.record.get(recid)
        # gi = db.rel.parents(recid, rectype='grid_imaging')
        # if len(gi) == 1:
        #     source_map[gi.pop()].append(k)
        # else:
        #     print "Ambigous/no grid_imaging:", gi
    #     rec['percent_included'] = v
    #     putrecs.append(rec)
    # 
    # if putrecs:
    #     db.record.put(putrecs)

        
    # print source_map
    if prefix:
        f = open("test_%s.json"%prefix, 'w')
        json.dump(source_map, f)
        f.close()    
        make_plots(source_map, prefix=prefix)
        
    
    

def plot_processed_snr(prefix="ctfp", db=None, apix=None):
    f = open('source2_gi.json')
    source_gi = json.load(f)
    f.close()

    source_ctf = {}
    print "Reading e2ctfparms"
    for k,v in EMAN2.db_open_dict("bdb:e2ctf.parms").items():
        ctf = EMAN2.EMAN2Ctf()
        ctf.from_string(v[0])
        source_ctf[k] = ctf.snr
        print ctf.snr


    for k,v in source_gi.items():
        print "\n==", k
        outfile = open("%s_%s.plot"%(prefix, k), 'w')
        for v2 in v:
            for x,y in peaks(source_ctf[v2], apix=APIX):
                outfile.write("%s\t%s\n"%(x,y))
        outfile.close()

        
    
    
def peaks(y, apix=1.0):
    # get x axis
    dx = 1.0 / (2.0 * apix * (len(y)+1))
    x = [dx*(i+1) for i in range(len(y))]
    
    p = []
    for i in range(1, len(y)-1):
        if y[i-1] < y[i] > y[i+1]:
            p.append((x[i], y[i]))
    
    return p
    
        
    
def make_plots(source, prefix=None):
    for k,v in source.items():
        print "\n=== Processing GI", k
        outfile = open("%s_%s.plot"%(prefix, k), 'w')
        for v2 in v:
            d = EMAN2.db_open_dict(v2)
            ctf = d.get_attr(0, 'ctf')
            for x,y in peaks(ctf.snr, apix=APIX):
                outfile.write("%s\t%s\n"%(x,y))
        outfile.close()
                


if __name__ == "__main__":
    pass
    # plot_processed_snr(db=db)
    #open_refine_classes("refine_08", "classes_04", prefix="decbin", db=db)
    #make_plots("test_bin.json", prefix="bin2")


