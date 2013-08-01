#!/usr/bin/env python


import subprocess
import twitter
import twitter.cmdline
import twitter.oauth
import twitter.oauth_dance



# Run a process, get the standard out
def check_output(args, **kwds):
    kwds.setdefault("stdout", subprocess.PIPE)
    kwds.setdefault("stderr", subprocess.STDOUT)
    p = subprocess.Popen(args, **kwds)
    return p.communicate()[0]



def gettokens():
    OAUTH_TOKEN = ''
    OAUTH_SECRET = ''
    CONSUMER_KEY = ''
    CONSUMER_SECRET = ''
    return {"OAUTH_TOKEN": OAUTH_TOKEN, "OAUTH_SECRET": OAUTH_SECRET, "CONSUMER_KEY": CONSUMER_KEY, "CONSUMER_SECRET": CONSUMER_SECRET}


def getapi():
    tk = gettokens()
    
    if not tk.get('OAUTH_TOKEN') or not tk.get('OAUTH_SECRET'):
        tk['OAUTH_TOKEN'], tk['OAUTH_SECRET'] = twitter.oauth_dance.oauth_dance("EMEN2", tk.get('CONSUMER_KEY'), tk.get('CONSUMER_SECRET'))
        print "Got auth tokens: ", tk

    t = twitter.Twitter(
        auth=twitter.oauth.OAuth(tk['OAUTH_TOKEN'], tk['OAUTH_SECRET'], tk['CONSUMER_KEY'], tk['CONSUMER_SECRET']),
        secure=1,
        api_version='1',
        domain='api.twitter.com')

    return t


def tweet(status, t=None):
    if not t:
        t = getapi()
    t.statuses.update(status=status)
    
    
def uptime():
    b = emdash.check_output("uptime").strip()
    tweet("NCMIDB status: %s"%b)
    
    
if __name__ == "__main__":
    uptime()
    
    
__version__ = "$Revision$".split(":")[1][:-1].strip()