# stock.py  01/28/2006  Steven Ludtke
# This set of sample routines allows you to use EMEN2 to establish a mineable database
# of historical stock prices
import Database
from Database import ParamDef
from Database import RecordDef
from DBUtil import *
import os
import urllib2
from stockdates import datelist

try:
	import pylab
except:
	pylab=None

DB=Database
db=DB.Database(os.getenv("HOME")+"/stockdb")
ctx=db.login("root","foobar")
print db.checkcontext(ctx,None)

monthnames={"Jan":"01","Feb":"02","Mar":"03","Apr":"04","May":"05","Jun":"06","Jul":"07","Aug":"08","Sep":"09","Oct":"10","Nov":"11","Dec":"12"}

def dbinit():
	db.addparamdef(ParamDef("eventdate","date","Date event occured","Date event occured"),ctx)
	db.addparamdef(ParamDef("eventdateseq","int","Market date sequence","Stock market day sequence starting from Jan 1962"),ctx)
	db.addparamdef(ParamDef("stock_volume","int","Stock volume","Stock trading volume"),ctx)
	db.addparamdef(ParamDef("price_day_open","float","Stock open","Stock price at market open","currency","dollars"),ctx)
	db.addparamdef(ParamDef("price_day_close","float","Stock close","Stock price at market close","currency","dollars"),ctx)
	db.addparamdef(ParamDef("price_day_adjclose","float","Stock adj close","Adjusted stock price at market close","currency","dollars"),ctx)
	db.addparamdef(ParamDef("price_day_low","float","Stock low","Day low stock price","currency","dollars"),ctx)
	db.addparamdef(ParamDef("price_day_high","float","Stock high","Day high stock price","currency","dollars"),ctx)
	db.addparamdef(ParamDef("name","text","name of the object","name of the object"),ctx)
	db.addparamdef(ParamDef("symbol_stock","string","Stock market symbol","Stock market symbol"),ctx)
	db.addparamdef(ParamDef("name_company","string","Comany name","Company name"),ctx)
	
	rd=RecordDef()
	rd.name="company"
	rd.mainview="$$symbol_stock<br>$$name_company<br>This represents a company as traded on some stock market"
	db.addrecorddef(rd,ctx)
	
	rd=RecordDef()
	rd.name="quote_stock"
	rd.mainview="""<pre>A single price quote for <b>$$symbol_stock</b>
On: $$eventdate ($$eventdateseq)
Open: $$price_day_open
Close: $$price_day_close ($$price_day_adjclose)
High: $$price_day_high
Low: $$price_day_low
</pre>"""
	db.addrecorddef(rd,ctx)
	
def dateconv(yd):
	"convert a yahoo date 23-May-86 to a EMEN2 date 19860523"
	if yd[1]=='-' : yd="0"+yd
	try:
		if int(yd[-2:])>50 : nd="19"+yd[-2:]+monthnames[yd[3:6]]+yd[:2]
		else : nd="20"+yd[-2:]+monthnames[yd[3:6]]+yd[:2]
	except:
		print yd
	return nd
	
def gethistory(symbol):
	"""Connect to Yahoo and get the stock price history for the named symbol"""
	fin=urllib2.urlopen("http://ichart.finance.yahoo.com/table.csv?s=%s&a=00&b=2&c=1962&d=00&e=29&f=2006&g=d&ignore=.csv"%symbol)
	data=fin.readlines()
	fin.close()
	n=len(data)
	data=[j.strip().split(',')+[n-i-2] for i,j in enumerate(data[1:])]
	off=11094-datelist[data[-1][0]]
	print off
	data=[{"eventdate":dateconv(i[0]),"price_day_open":float(i[1]),"price_day_high":float(i[2]),"price_day_low":float(i[3]),
		"price_day_close":float(i[4]),"stock_volume":int(i[5]),"price_day_adjclose":float(i[6]),"eventdateseq":i[7]+off} for i in data]
	
	return data

def setupnewstock(symbol):
	d=gethistory(symbol)
	for i in d:
		r=db.newrecord("quote_stock",ctx)
		for j in i.keys(): r[j]=i[j]
		r["symbol_stock"]=symbol.upper()
		db.putrecord(r,ctx)

def plotstock(symbol):
	a=db.query("plot price_day_open vs eventdateseq symbol_stock==%s"%symbol,ctx)
	b=db.query("plot price_day_close vs eventdateseq symbol_stock==%s"%symbol,ctx)
	pylab.plot(a["data"]["x"],a["data"]["y"])
	pylab.plot(b["data"]["x"],b["data"]["y"])
	pylab.show()
	