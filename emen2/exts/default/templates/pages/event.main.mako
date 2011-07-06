<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  />
<%
import time
import datetime
import collections
import emen2.db.vartypes

today = datetime.datetime.today().replace(year=2010, month=12, day=13, hour=0, minute=0, second=0, microsecond=0)

timemap = {}
eventmap = {}
for event in events:
	ds = emen2.db.vartypes.parse_datetime(event.get('date_start'))[0]
	de = emen2.db.vartypes.parse_datetime(event.get('date_end'))[0]
	timemap[event.name] = ds, de
	eventmap[event.name] = event


def timewindow(d, t, inclusive=False):
	# if inclusive, this entire time slice exists within event
	# else, there is any overlap of time slice with event
	if inclusive:
		return t[0] <= d[0] and t[1] >= d[1]
	return t[0] <= d[1] and t[1] >= d[0]



def findconflicts(emap):
	conflicts = collections.defaultdict(set)
	indents = collections.defaultdict(int)

	for eventid1, t1 in emap.items():
		for eventid2, t2 in emap.items():
			if eventid1 == eventid2:
				continue
			if timewindow(t1, t2):
				print "CONFLICT!", eventid1, eventid2
				conflicts[eventid1].add(eventid2)
				conflicts[eventid2].add(eventid1)
				# assign an indent...
				l1 = t1[1] - t1[0]
				l2 = t2[1] - t2[0]
				if l2 > l1:
					indents[eventid1] += 1
				else:
					indents[eventid2] += 1


	return conflicts, indents
	

DAYSTART = 0
DAYEND = 24
		
conflicts, indents = findconflicts(timemap)
weekwindow = today-datetime.timedelta(days=today.isoweekday()), today+datetime.timedelta(days=7-today.isoweekday())

dayevents = {}
for i in range(7):
	daywindow = weekwindow[0] + datetime.timedelta(days=i), weekwindow[0] + datetime.timedelta(days=i+1)
	daye = []
	print "day:", 1, daywindow
	for event in events:
		if timewindow(daywindow, timemap.get(event.name)):
			daye.append(event)
	dayevents[daywindow[0]] = daye


COLORS = ["orange", "blue", "green", "red", "#ccc", "yellow"]
colormap = {}
for color, event in enumerate(events):
	colormap[event.name] = COLORS[color%len(COLORS)]
	
%>



<%def name="drawday(e)">
% for event in e:
	<%
	eventlength = (timemap.get(event.name)[1] - timemap.get(event.name)[0]).seconds / 3600.0
	height = int(eventlength * 40.0)

	top = int((timemap.get(event.name)[0] - today - datetime.timedelta(hours=DAYSTART)).seconds / 3600.0 * 40.0)
	if top < 0:
		height += top
		top = 0
		
	width = 100 - len(conflicts.get(event.name, [])) * 20
	left = indents.get(event.name, 0) * 10
	%>
	<div class="event" style="position:absolute;width:${width}%;height:${height}px;left:${left}%;top:${top}px;background:${colormap.get(event.name)};z-index:${left*10}">
		${recnames.get(event.name)}
	</div>
% endfor
</%def>		




<h1>${recnames.get(rec.name)}</h1>

<ul>
<li>Availability: ${rec.get('date_start')} - ${rec.get('date_end')}</li>
<li>Contact: ${rec.get('name_contact')}</li>
</ul>

<div id="calendar" data-name="${rec.name}" data-start="${weekwindow[0].strftime(TIMESTR)}" data-end="${weekwindow[1].strftime(TIMESTR)}">
	<div class="events" style="position:absolute;border:solid red 1px;">
	% for event in events:
		<div class="event" data-name="${event.name}">${recnames.get(event.name)}</div>
	% endfor
	</div>
</div>


<h1>Events</h1>

<ul>
% for i in events:
	<li>${i.get('date_start', '')} - ${i.get('date_end', '')}: ${recnames.get(i.name)}</li>
%endfor
</ul>