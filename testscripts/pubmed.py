#!/usr/bin/env python
# Written by Stephen Murray, Mary Daoud, and Ian Rees

from Bio import Entrez
from Bio import Medline
from datetime import *
import jsonrpc.proxy
import getpass
import codecs
import collections
import pprint

def format_pub(pub):
    """Format the PUBMED record."""
    return """<a href="http://www.ncbi.nlm.nih.gov/pubmed/%s/">%s (%s) %s. <em>%s</em></a>\n"""%(
        pub['Id'],
        pub['Title'],
        pub['PubDate'][:4],
        ", ".join(pub['AuthorList']),
        pub['Source']
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
    
    # Make sure to check each key exists...
    d = article.get('ArticleDate')
    if d:
        d = d[0]
        ret['journal_date'] = "%s-%s-%sT00:00:00+00:00"%(d.get('Year', '0000'), d.get('Month', '00'), d.get('Day','00'))
    
    if article.get('Journal'):
        ret['name_journal'] = article['Journal'].get('Title')
        if article['Journal'].get('JournalIssue'):
            ret['journal_volume'] = article['Journal']['JournalIssue'].get('Volume')

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


# START OF SCRIPT
# DEBUG mode?
DEBUG = False
if DEBUG:
    print "DEBUG Mode!"

# Email address to give to PUBMED
Entrez.email = "webadmin@blake.grid.bcm.edu"

if __name__ == "__main__":
    # EMEN2 login information
    user = raw_input("NCMIDB username: ")
    pw = getpass.getpass()

    # Connect to EMEN2
    db = jsonrpc.proxy.JSONRPCProxy("http://ncmidb.bcm.edu")
    db.login(user, pw)
    print "Logged in as: ", db.checkcontext()[0]

    # Query EMEN2 for applications
    # ... find all "publication" records: db.record.findbyrectype
    publications = db.record.findbyrectype("publication")
    # ... and retreive records: db.record.get
    publications = db.record.get(publications)
    # ... filter out deleted items (this is kind of a bug..)
    publications = filter(lambda x:not x.get("deleted"), publications)
    # ... filter out items that do not have a PUBMED ID (pmid)
    publications = filter(lambda y: y.get("pmid"), publications)

    # So we don't overload PUBMED... use just the first 3 in DEBUG mode.
    if DEBUG:
        publications = publications[:3]

    # publications is now a list of publication records that are not deleted and have a valid PUBMED ID
    # (a list of dictionaries)
    print "Got %s valid publications"%(len(publications))

    commit = []
    for count,pub in enumerate(publications):
        # For each publication found in EMEN2, find the PUBMED record and map the values back to the NCMIDB record
        print "\n===== (%s / %s) %s ====="%(count+1, len(publications), pub['pmid'])

        # This returns the record from PubMed publication with the passed pmid to map it with the recond from pubmed DB
        pubmed_pub = medline_find(pub['pmid']) 
        if not pubmed_pub:
            print "Did not find PUBMED record for:", pub['pmid']
            continue
        
        try:
            r = medline_map(pubmed_pub)
        except Exception, e:
            print "Couldn't map %s:"%pub['pmid'], e
            continue
            
        print r
        pub.update(r)
        commit.append(pub)
            
    # Write results
    db.record.put(commit)
    
    
    