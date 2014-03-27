#!/usr/bin/env python
# Written by Stephen Murray, Mary Daoud, and Ian Rees
import argparse
import getpass
import codecs
import collections
import pprint
import sys
from datetime import *

from Bio import Entrez
from Bio import Medline
import jsonrpc.proxy

def format_pub(pub):
    """Format the PUBMED record."""
    return """<a href="http://www.ncbi.nlm.nih.gov/pubmed/%s/">%s (%s) %s. <em>%s</em></a>"""%(
        pub['pmid'],
        pub['title_publication'],
        pub['journal_date'][:4],
        ", ".join(pub['author_list']),
        pub['name_journal']
    )

def medline_find(pmid): 
    """Find a PUBMED record given a PUBMED ID."""
    # Use the more complex XML return because it includes the abstract
    # and additional information. Summary format is simpler but omits
    # key details.
    handle = Entrez.efetch(db="pubmed", id=str(pmid), retmode="xml")
    records = Entrez.read(handle)
    if records:
        return records.pop()


def medline_map(pubmed_pub):
    """Map the values of PUBMED MedlineCitation record to EMEN2 parameters."""    
    p = pubmed_pub['MedlineCitation']
    article = p['Article']
    ret = {}
    
    print "=================="
    # print article
    
    # Dates are awful.
    try:
        d = article['Journal']['JournalIssue']['PubDate']
        d_month = {'Jan': 1,
                'Feb': 2,
                'Mar': 3,
                'Apr': 4,
                'May': 5,
                'Jun': 6,
                'Jul': 7,
                'Aug': 8,
                'Sep': 9,
                'Oct': 10,
                'Nov': 11,
                'Dec': 12
                }
        ret['journal_date'] = "%04d-%02d-%02dT00:00:00+00:00"%(int(d.get('Year', 1)), int(d_month.get(d.get('Month'), 1)), int(d.get('Day',1)))
    except Exception, e:
        print "Could not find the date, because evil:", e
    
    if article.get('Journal'):
        ret['name_journal'] = article['Journal'].get('Title')
        if article['Journal'].get('JournalIssue'):
            ret['journal_volume'] = article['Journal']['JournalIssue'].get('Volume')
            # Backup method to get year...
            # if not ret.get('journal_date') and article['Journal']['JournalIssue'].get('PubDate'):
            #    ret['journal_date'] = '%s-01-01T00:00:00+00:00'%article['Journal']['JournalIssue']['PubDate'].get('Year')
            #    print "---- SET journal_date from Article/Journal/JournalIssue/PubDate/Year", ret['journal_date']

    if article.get('Pagination'):
        ret['page_range'] = article['Pagination'].get('MedlinePgn')

    if article.get('Abstract'):
        ret['abstract'] = article['Abstract'].get('AbstractText', [""])[0]

    if article.get('ArticleTitle'):
        ret['title_publication'] = article['ArticleTitle']

    a = []
    for i in article.get('AuthorList', []): 
        a.append('%s, %s'%(i['LastName'], i['Initials']))
    ret['author_list'] = a
    
    return ret
    
def summary_find(pmid):
    handle = Entrez.esummary(db="pubmed", id=str(pmid))
    records = Entrez.read(handle)
    if records:
        return records.pop()   
    
def summary_map(pubmed_pub):
    """Map the values of PUBMED summary record to EMEN2 parameters."""
    ret = {}
    ret['title_publication']  =  pubmed_pub['Title']
    ret['name_journal']  =  pubmed_pub['Source']
    ret['journal_volume'] = pubmed_pub['Volume']
    ret['author_list']  =  pubmed_pub['AuthorList']
    ret['page_range'] = pubmed_pub['Pages']
    ret['author_corresponding'] = pubmed_pub['LastAuthor']
    return ret


# Email address to give to PUBMED
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Print or update publications')
    parser.add_argument('commands', nargs=1, help='Command: print or update')
    parser.add_argument('--host', '-H', help="Hostname", default="http://ncmidb.bcm.edu")
    parser.add_argument('--email', help="Email for Entrez query", default="webadmin@blake.grid.bcm.edu")
    parser.add_argument('--user', help='User')
    parser.add_argument('--password', help='Password')

    args = parser.parse_args()
    
    # EMEN2 login information
    user = args.user or raw_input("Username: ")
    pw = args.password or getpass.getpass()

    # Entrez login information
    Entrez.email = args.email

    # Connect to EMEN2
    db = jsonrpc.proxy.JSONRPCProxy(args.host)
    db.login(user, pw)
    print "Logged in as: ", db.checkcontext()[0]

    # Query EMEN2 for applications
    # ... find all "publication" records: db.record.findbyrectype
    publications = db.record.findbyrectype("publication")
    # ... and retreive records: db.record.get
    publications = db.record.get(publications)
    # ... filter out deleted items (this is kind of a bug..)
    publications = filter(lambda x:not x.get("hidden"), publications)
    # ... filter out items that do not have a PUBMED ID (pmid)
    publications = filter(lambda y: y.get("pmid"), publications)

    # publications is now a list of publication records that are not hidden and have a valid PUBMED ID
    # (a list of dictionaries)
    print "Got %s valid publications"%(len(publications))

    if "print" in args.commands:
        for pub in sorted(publications, key=lambda x:x.get('journal_date')):
            # print "========"
            # for k,v in pub.items(): print k,v
            print "\n"
            try: 
                print format_pub(pub)
            except Exception, e:
                print "Could not print %s: "%pub.get('name'), e
                print "\tRecord ->", pub

    if "update" in args.commands:
        commit = []
        for count,pub in enumerate(publications):
            # For each publication found in EMEN2, find the PUBMED record and map the values back to the NCMIDB record
            print "\n===== (%s / %s) %s ====="%(count+1, len(publications), pub['pmid'])

            # This returns the record from PubMed publication with the passed pmid to map it with the recond from pubmed DB
            try:
                pubmed_pub = medline_find(pub['pmid']) 
                if not pubmed_pub:
                    raise Exception
            except:
                print "Did not find PUBMED record for:", pub['pmid']
                continue
        
            try:
                r = medline_map(pubmed_pub)
            except Exception, e:
                print "Could not map %s:"%pub['pmid'], e
                continue
            
            pub.update(r)
            commit.append(pub)
            
        # Write results
        for rec in commit:
            print "SAVING:", commit
            try:
                db.record.put(rec)
            except Exception, e:
                print "Couldnt save: ", e
    
    
    