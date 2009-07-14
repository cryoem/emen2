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

datetime_formats = [
	'%Y %m %d %H:%M:%S',
	'%Y %m %d %H:%M',
	'%Y %m %d %H',
	'%Y %m %d',
	'%Y %m',
	'%Y'
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

	for format in datetime_formats:
		try:
			return datetime.datetime.strptime(string, format)
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



