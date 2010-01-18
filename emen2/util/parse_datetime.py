"""This file is placed in the public domain by Paul Harrison, 2006; modified by Ian"""


import time, datetime

time_formats = [
	'%H:%M:%S',
	'%H:%M',
	'%H'
	]

date_formats = [
	'%Y %m %d',
	'%Y %m',
	'%Y'
	]

# ian: todo: high priority: think about this more.
# Foramts to check [0] and return [1] in order of priority
# (the return value will be used for the internal database value for consistency)
# The DB will return the first format that validates.

datetime_formats = [
	['%Y %m %d %H:%M:%S','%Y/%m/%d %H:%M:%S'],
	['%Y %m %d %H:%M','%Y/%m/%d %H:%M'],
	['%Y %m %d %H', '%Y/%m/%d %H'],
	['%Y %m %d', '%Y/%m/%d'],
	['%Y %m','%Y/%m'],
	['%Y','%Y'],
	['%m %Y','%Y/%m'],
	['%d %m %Y','%Y/%m/%d'],
	['%d %m %Y %H:%M:%S','%Y/%m/%d %H:%M:%S'],
	['%m %d %Y','%Y/%m/%d'],
	['%m %d %Y %H:%M:%S','%Y/%m/%d %H:%M:%S']
	]



def parse_datetime(string):
	string = string.strip()
	if not string:
		return None

	string = string.replace('/',' ').replace('-',' ').replace(',',' ').split(".")
	msecs = 0
	if len(string) > 1:
		msecs = int(string.pop().ljust(6,'0'))
	string = ".".join(string)

	for format, output in datetime_formats:
		try:
			string = datetime.datetime.strptime(string, format)
			return datetime.datetime.strftime(string, output)
		except ValueError, inst:
			#print inst
			pass

	raise ValueError()



def parse_time(string):
	string = string.strip()

	string = string.split(".")
	msecs = 0
	if len(string) > 1:
		msecs = int(string.pop().ljust(6,'0'))
	string = ".".join(string)

	for format in time_formats:
		try:
			return datetime.datetime.strptime(string, format).time()
		except ValueError, inst:
			#print inst
			pass

	raise ValueError()



def parse_date(string):
	string = string.strip()
	if not string: return None

	string = string.replace('/',' ').replace('-',' ').replace(',',' ')

	for format in date_formats:
		try:
			return datetime.datetime.strptime(string, format).date()
		except ValueError:
			pass

	raise ValueError()


if __name__ == '__main__':
	print parse_datetime("2009")



