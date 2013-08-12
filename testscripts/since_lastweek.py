import operator
import collections
import datetime
import dateutil.relativedelta
import getpass
import jsonrpc.proxy

HOST = "http://ncmidb.bcm.edu"
USER = "ianrees"

# Open JSON-RPC
db = jsonrpc.proxy.JSONRPCProxy(HOST)
db.login(USER, getpass.getpass())

# Find all records in the past week.
weekago = datetime.datetime.now() - dateutil.relativedelta.relativedelta(days=7)
newrecords = db.query([['creationtime', '>', weekago.isoformat()]])['names']

# Group the records by their parent projects.
newrecords_parents = db.rel.parents(newrecords, recurse=-1)
find = reduce(operator.concat, newrecords_parents.values())
newrecords_byproject = collections.defaultdict(set)
newrecords_byrectype = db.record.groupbyrectype(find)
projects = newrecords_byrectype.get('project', [])
projects = set(projects)
for rec,parents in newrecords_parents.items():
    for i in projects & set(parents):
        newrecords_byproject[i].add(rec)
        
recnames = db.view(newrecords_byproject.keys())
for project,recs in newrecords_byproject.items():
    print recnames.get(project, project), " -> ", len(recs)