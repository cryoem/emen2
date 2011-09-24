<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  />
<%
import time
import datetime
import collections
import dateutil.rrule
import jsonrpc.jsonutil
import emen2.db.vartypes

# today = datetime.datetime.today().replace(year=2010, month=12, day=13, hour=0, minute=0, second=0, microsecond=0)

def isoformat(t):
	dt = emen2.db.vartypes.parse_datetime(t)[0]
	if dt:
		return dt.isoformat()

def convertevent(e, dtstart=None, dtend=None):
	r = {}
	r['start'] = isoformat(e.get('date_start'))
	r['end'] = isoformat(e.get('date_end'))
	
	if r.get('date_duration'):
		pass
	if r.get('date_recurrence'):
		pass
	
	r['id'] = e.name
	r['title'] = recnames.get(e.name, e.name)
	r['allDay'] = False
	return r


%>


<%block name="javascript_ready">
	$('.e2-event-repeat').DateRepeatControl({});
	
	$('#calendar').fullCalendar({
		events: ${jsonrpc.jsonutil.encode([convertevent(e) for e in events])},
		header: {
			left: 'prev,next today',
			center: 'title',
			right: 'month,agendaWeek,agendaDay'
		},
	    dayClick: function() {
	        alert('a day has been clicked!');
	    }
	});
});
</%block>


<div class="e2-event-repeat">New Event</div>

<div id="calendar" />

