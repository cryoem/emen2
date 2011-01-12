$(document).ready(function() {
	$("#calendar").Calendar();
});	

function parsedate(d) {
	var pd = Date.parse(d);
	if (!isNaN(pd)) {
	 	return new Date(pd);
	}
}

function writedate(d) {
	return d.getFullYear() + '/' + (d.getMonth()+1) + '/' + d.getDate() + ' ' + d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds();
}


function dayid(d) {
	return d.getFullYear() + '-' + (d.getMonth()+1) + '-' + d.getDate();
}

(function($) {
    $.widget("ui.Calendar", {
		options: {
			'recid': null,
			'start': null,
			'end': null
		},
				
		_create: function() {
			this.element.css('position','relative');
			this.options.recid = this.options.recid || parseInt(this.element.attr('data-recid'));
			this.options.start = parsedate(this.element.attr('data-start'));
			this.options.end = parsedate(this.element.attr('data-end'));
			this.counter = -1;
			this.built = 0;
			this.build();
		},
				
		build: function() {
				
			if (this.built) {return}
			this.build = 1;
			
			var self = this;
			var newevent = $('<button>Add Event</button>');
			newevent.click(function(){self.addevent()})
			this.element.append(newevent);
						
			var table = $(' \
				<table cellpadding="0" cellspacing="0"> \
					<thead> \
					<tr class="calendar_header"> \
						<th style="width:50px"></th> \
					</tr> \
					</thead> \
					<tbody> \
						<tr class="calendar_body"> \
							<td class="calendar_hours" style="width:40px;padding:0px;margin:0px;"></td> \
						</tr> \
					</tbody> \
				</table> \
			');
			for (var i=0;i<24;i++) {
				var text = i+"am";
				if (i==0){
					text = "12am";
				} else if (i==12) {
					text = "12pm";
				} else if (i>12) {
					text = i%12 + "pm"
				}
				$('.calendar_hours', table).append('<div style="text-align:right;font-size:8pt;color:#666;padding:2px;height:35px;border-right:solid 1px #ccc;border-bottom:solid 1px #ccc">'+text+' </div>');
			}
			this.element.append(table);
			
			this.makedays(this.options.start, this.options.end);			
			
			$('.event', this.element).CalendarEvent();
			$('.event', this.element).CalendarEvent('draw');
			
		},
		
		makedays: function(start, end) {
			var day = new Date(start);
			while (day < end) {
				$('.calendar_header', this.element).append('<th style="text-align:center">'+(day.getMonth()+1)+'/'+day.getDate()+'</th>');
				var newday = new Date(day.getTime() + 24*60*60*1000);
				var daydiv = $('<div style="padding:0px;margin:0px;position:relative;" class="day" data-dayid="'+dayid(day)+'" data-start="'+day+'" data-end="'+newday+'" />');
				var datediff = new Date()-day
				if (datediff <= (24*60*60*1000) && datediff > 0) {
					// is today..
					daydiv.addClass('today');
				}
				for (var i=0;i<48;i++) {
					var color = "#eee";
					if (i%2) {color="#ccc"}
					daydiv.append('<div style="height:19px;border-right:solid 1px #ccc;border-bottom:solid 1px '+color+';"></div>')
				}	
				var daytd = $('<td style="padding:0px;margin:0px"></td>');
				daytd.append(daydiv);
				$('.calendar_body', this.element).append(daytd);
				day = newday;		
			}
		},
				
		addevent: function(event) {
			var e = $('<div class="event" data-recid="'+this.counter+'">Test!</div>');
			e.CalendarEvent({
				'recid': this.counter,
				'parent': this.options.recid,
				'start': this.options.start,
				'end': new Date(this.options.start.getTime() + 60*60*1000)
			});
			this.counter -= 1;
			e.CalendarEvent('draw');
			this.element.append(e);
		},			
				
		destroy: function() {

		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);





(function($) {
    $.widget("ui.CalendarEvent", {
		options: {
			'start': null,
			'end': null,
			'recid': null,
			'parent': null
		},
				
		_create: function() {
			var self = this;
			this.indent = 0;
			this.opacity = 1.0;
			this.view = '';
			this.element.hide();
			this.options.recid = parseInt(this.options.recid || this.element.attr('data-recid'));
			this.built = 0;
			if (this.options.recid >= 0) {
				$.jsonRPC("getrecord", [this.options.recid], function(rec) {
					self.rec = rec;
					self.build();
					self.renderview();
				})
			} else {
				$.jsonRPC("newrecord", ["folder", this.options.parent], function(rec) {
					rec['recid'] = self.options.recid;
					self.rec = rec;
					self.build();
				})
			}

		},
		
		formathour: function(d) {
			var h = d.getHours();
			var s = '';
			var m = d.getMinutes();
			var p = '';
			if (m==0) {m = ''} else {m = ':'+m}
			if (h==0) {
				s = '12';				
			} else if (h < 12) {
				s = h;
			} else if (h == 12) {
				s = '12';
				p = 'p'
			} else {
				s = h%12
				p = 'p';
			}
			return s+m+p
		},
		
		build: function() {
			var self = this;
			if (this.built) {
				return
			}
			this.built = 1;			
			this.options.start = parsedate(this.rec['date_start']) || this.options.start;
			this.options.end = parsedate(this.rec['date_end']) || this.options.end;
			this.original_start = this.options.start;
			this.original_end = this.options.end;
			this.collisions();
			this.draw();
		},
		
		draw: function() {
			var self = this;

			// hide any boxes with important events bound to preserve start/drag/stop -- and remove others
			$('.event_bound[data-recid='+this.options.recid+']').hide();			
			$('.event_box[data-recid='+this.options.recid+']:not(.event_bound)').remove();			

			$('.day').each(function() {
				var endstoday = false;
				var thisday = new Date($(this).attr('data-start'));
				var width = $(this).width();
				var y_offset = (self.options.start - thisday) / (3600 * 1000);				
				var duration = (self.options.end - self.options.start) / (3600 * 1000);
				height = duration;

				// offset + height exceeds max column height
				if (duration+y_offset>24) {
					height = 24 - y_offset;
				}

				// ending this day
				if (duration + y_offset <= 24 && duration >= 24) {
					height = duration + y_offset;
					y_offset = 0;
					endstoday = true;
				}			
				if (duration + y_offset <= 24) {
					endstoday = true;
				}
								
				// began before this day
				if (y_offset < 0) {
					height = duration + y_offset;
					y_offset = 0;
				}

				// max column height
				if (height >= 24) {
					height = 24;
				}
				
				if (height <= 0) {
					return
				}
			
				var e = $('<div style="position:absolute;top:0px;"><div class="label">'+self.formathour(self.options.start)+' - '+self.formathour(self.options.end)+'</div><div class="indent">'+self.indent+'</div></div>');
				var view = $('<div class="view" data-recid="'+self.options.recid+'" data-viewtype="recname">'+self.view+'</div>');
				e.append(view);
				
				e.addClass('event_box');
				if (endstoday) {
					e.addClass('endstoday');
				}
				e.attr('data-recid', self.options.recid);
				e.css('top', y_offset*40);
				e.css('height', height*40-4);
				e.css('width', width-4);
				e.css('opacity', self.opacity);
				$(this).append(e);
				self.makedraggable(e);
			});
		},
		
		timewindow: function(d1, d2, t1, t2) {
			return t1 <= d2 && t2 >= d1;
		},
		
		makedraggable: function(box) {
			var self = this;

			box.draggable({
				'helper': function(){return '<div></div>'},
				'start': function(event, ui) {
					var offset = $('.day').offset();
					self._sub = 4
					self._width = $('.day').width();
					self._height = $('.day').height() / 24;
					self._ox = event.pageX;
					self._oy = event.pageY;
					self._cellx = (event.pageX - offset.left) % self._width;
					self._celly = (event.pageY - offset.top) % self._height;
					self._day = 0;
					self._hour = 0;
					self.original_start = self.options.start;
					self.original_end = self.options.end;
					$(event.target).addClass('event_bound');
					self.indent = 0;
					self.opacity = 0.5;			
					},
				'stop': function(event, ui) {
					// we hide the event target to keep the 'stop' handler alive, but now we can kill it..
					$(event.target).remove();
					self.save();
					},
				'drag': function(event, ui) {
					// transform to calendar origin
					var hour = Math.floor((self._celly - (self._oy - event.pageY)) / self._height*self._sub)/self._sub;
					var day = Math.floor((self._cellx - (self._ox - event.pageX)) / self._width);
					if (day != self._day || hour != self._hour) {
						self.settime_offset(hour,day);
					}
					self._hour = hour;
					self._day = day;
					}
			});

			if (!box.hasClass("endstoday")) {
				return
			}

			box.resizable({
				'handles': 's',
				'containment': 'parent',
				'start': function(event, ui) {
					self._d_ox = event.pageY;
					self._height = $('.day').height() / 24;	
				},
			    'resize': function(event, ui) {
			        ui.size.width = ui.originalSize.width;
			    },
				'stop': function(event, ui) {
					var hour = Math.floor(4*((event.pageY - self._d_ox)/self._height))/4;
					self.setduration_offset(hour);
					self.save();
				}
			});
			var helper = $('<div style="text-align:center;position:absolute;bottom:0px;width:100%;font-size:8pt;color:#ccc">=</div>');
			box.append(helper);			

		},
		
		setduration_offset: function(hour) {
			var self = this;
			var duration = 3600 * 1000 * hour;
			var newend = new Date(this.options.end.getTime() + duration);
			if (newend <= this.options.start) {
				return
			}
			this.options.end = newend;
			this.draw();
		},
		
		settime_offset: function(hour, day) {
			var self = this;
			var duration = this.options.end - this.options.start;
			var offset = (24*3600*1000*day) + (3600*1000*hour);
			var newstart = new Date(self.original_start.getTime() + offset);
			var newend = new Date(newstart.getTime() + duration);
			this.options.start = newstart;
			this.options.end = newend;
			this.draw();
		},
		
		reindent: function(level) {
			if (this.indent == level) {
				return
			}
			this.indent = level;
			var self = this;
			$('.event_box[data-recid='+this.options.recid+']').each(function() {
				var e = $(this)
				e.css('left', self.indent*20+"%");
				e.css('width', 100-(self.indent*20)+"%");
				e.css('z-index', self.indent*10);
			});
		},
		
		checkcollisions: function() {
			var self = this;
			var cs = [];
			$('.event').each(function() {
				var e = $(this);
				var eid = e.CalendarEvent('option', 'recid');
				var ds = e.CalendarEvent('option', 'start');
				var de = e.CalendarEvent('option', 'end');
				if (eid == self.options.recid) {return}			
				if (self.timewindow(ds, de, self.options.start, self.options.end)) {
					cs.push(eid);
				}
			});
			return cs
		},
		
		collisions: function() {
			// find all overlapping items
			var current = this.options.recid;
			var result = [this.options.recid];
			var stack = [];
			while (current != null) {
				var cs = this.checkcollisions();
				for (var i=0; i<cs.length; i++) {
					if ($.inArray(cs[i], result) < 0) {
						result.push(cs[i]);
						stack.push(cs[i]);
					}
				}
				if (stack.length > 0) {
					current = stack.pop(); 
				} else {
					current = null;
				}
			}
			//console.log("Total overlaps: ", result);			
			// sort by length, then indent appropriately
			lengths = {}
			for (var i=0; i<result.length; i++) {
				var e = $('.event[data-recid='+result[i]+']');
				var ds = e.CalendarEvent('option', 'start');
				var de = e.CalendarEvent('option', 'end');
				lengths[result[i]] = de-ds;
			}
			var sorted = $.sortdict(lengths);
			for (var i=0; i<sorted.length; i++) {
				var e = $('.event[data-recid='+sorted[i]+']');
				e.CalendarEvent('reindent', i);
			}
		},
		
		setrecid: function(recid) {
			//console.log("updating recid..", this.options.recid, recid);
			$('[data-recid='+this.options.recid+']').each(function() {
				$(this).attr('data-recid', recid);
			});
			this.options.recid = recid;
		},
		
		save: function() {
			this.opacity = 1.0;
			this.draw();
			this.collisions();			
			return
			var self = this;
			if (this.rec['recid'] >= 0) {
				var rec = {};
				rec['date_start'] = writedate(this.options.start);
				rec['date_end'] = writedate(this.options.end);
				$.jsonRPC('putrecordvalues', [this.options.recid, rec], function(updrec) {
					//console.log("saved!");
					self.rec = updrec;
					self.renderview();
				});
			} else {
				this.rec['date_start'] = writedate(this.options.start);
				this.rec['date_end'] = writedate(this.options.end);
				$.jsonRPC('putrecord', [this.rec], function(updrec) {
					//console.log("saved new record!");
					self.rec = updrec;
					self.setrecid(updrec['recid']);
					self.renderview();
				});				
			}
		},
		
		renderview: function() {
			var self = this;
			$.jsonRPC('renderview', [this.options.recid, null, 'recname'], function(view) {
				self.view = view;
				if (view==null) {
					view = "Record "+self.options.recid;
				}
				self.draw();
			});
		},
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);










