#!/bin/env python
# This is designed to (eventually) import (some) XML schema and produce 
# a set of RecordDef and ParamDef entries


import sys
import xml.sax
from xml.sax.handler import ContentHandler

class myhandler(ContentHandler):
	def startDocument(self):
		self.parsed=[]
		self.level=0
		self.close={}
	
	def startElement(self,name,attrs):
		self.level+=1
		
		if self.level==2 and name=="xs:element" : 
			print attrs["name"], " {"
			self.close[self.level]="}\n"
		if self.level>2 and name=="xs:element" : 
			if attrs.has_key("name") : 
				print "  %s"%(attrs["name"]),
				if attrs.has_key("type") : print "(%s)"%attrs["type"],
			if attrs.has_key("ref") : 
				print "  --> %s"%(attrs["ref"]),
				if attrs.has_key("minOccurs") : print "(%s or more)"%attrs["minOccurs"],
				else : print "(1)",
			self.close[self.level]="\n"
		if self.level>2 and name=="xs:restriction" : 
			print "(%s)"%attrs["base"],
		
#		print "  "*self.level,self.level,name
#		for i in attrs.getNames():
#			print "  "*self.level,"  %s = %s"%(i,attrs[i])
	
	def endElement(self,name):
		if self.close.has_key(self.level) :
			print self.close[self.level],
			del self.close[self.level]
		self.level-=1

	def startElementNS(name, qname, attrs):
		print "NS",name,qname
		print attrs
			
handler=myhandler()
xml.sax.parse(sys.argv[1],handler)
