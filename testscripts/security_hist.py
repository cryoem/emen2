import os
import sys
import collections
import re
logfile = sys.argv[1]
start = '2012-01-01'
end = '2012-12-31'

parse = "(?P<date>[\d-]+)\s(?P<time>[\d\:\-]+)\s\[(?P<event>.+)\]\s(?P<details>.*)"
parse = re.compile(parse, re.VERBOSE)
events = collections.defaultdict(list)
events_failed = collections.defaultdict(list)
hist = collections.defaultdict(list)

for i in open(logfile):
    match = parse.search(i)
    if match.group('date') >= start and match.group('date') <= end:
        if match.group('details').startswith('Login succeeded'):
            user = match.group('details').split(" ")[2]
            events[user].append(match.group('date'))
        if match.group('details').startswith('Login failed'):
            user = match.group('details').split(" ")[-1]
            events_failed[user].append(match.group('date'))

for k,v in sorted(events.items(), key=lambda x:len(x[1])):
    print "User", k, "logged in", len(v), "times"

events_failed_total = sum(map(len, events_failed.values()))
print "Also, in total, bad auth for for %s users, %s times"%(len(events_failed), events_failed_total)
