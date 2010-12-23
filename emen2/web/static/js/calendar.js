$(document).ready(function() {
	$("#calendar").Calendar();
});	

function parsedate(d) {
	var dt = new Date(Date.parse(d));
	return dt
}


function dayid(d) {
	return d.getUTCFullYear() + '-' + (d.getUTCMonth()+1) + '-' + d.getUTCDate();
}

(function($) {
    $.widget("ui.Calendar", {
		options: {
		},
				
		_create: function() {
			this.element.css('position','relative');
			this.date_start = parsedate(this.element.attr('data-start'));
			this.date_end = parsedate(this.element.attr('data-end'));
			this.maketable();
			this.makedays(this.date_start, this.date_end);
			$('.event', this.element).CalendarEvent();
			$('.event', this.element).CalendarEvent('draw');
		},

		// <thead> \
		// 	<tr class="calendar_header"> \
		// 		<th style="width:50px"></th> \
		// 	</tr> \
		// </thead> \
				
		maketable: function() {
			
			// var header = $(' \
			// 	<table cellpadding="0" cellspacing="0"> \
			// 		<tbody> \
			// 			<tr class="calendar_header"> \
			// 				<th style="width:40px;padding:0px;margin:0px;"></th> \
			// 			</tr> \
			// 		</tbody> \
			// 	</table> \
			// ');
			// this.element.append(header);
						
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
		},
		
		makedays: function(start, end) {
			var day = new Date(start);
			while (day < end) {
				$('.calendar_header', this.element).append('<th style="text-align:center">'+day.getUTCDate()+'/'+(day.getUTCMonth()+1)+'</th>');
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
		},
				
		_create: function() {
			var self = this;
			this.indent = 0;
			this.element.hide();
			this.recid = this.element.attr('data-recid');
			this.date_start = parsedate(this.element.attr('data-start'));
			this.date_end = parsedate(this.element.attr('data-end'));
			this.original_date_start = parsedate(this.element.attr('data-start'));
			this.original_date_end = parsedate(this.element.attr('data-end'));
		},
		
		draw: function() {
			this.collisions();
			var self = this;
			$('.event_box[data-recid='+this.recid+']').remove();			
			$('.day').each(function() {
				var endstoday = false;
				var thisday = new Date($(this).attr('data-start'));
				var y_offset = (self.date_start - thisday) / (3600 * 1000);				
				var duration = (self.date_end - self.date_start) / (3600 * 1000);
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
				if (duration <= 24) {
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

				var e = $('<div style="position:absolute;top:0px;width:100%;opacity:0.5">'+self.recid+'</div>');
				e.addClass('event_box');
				if (endstoday) {
					e.addClass('endstoday');
				}
				e.attr('data-recid', self.recid);
				e.css('background', 'red');
				e.css('top', y_offset*40);
				e.css('height', height*40);	
				$(this).append(e);
				self.makedraggable(e);		
			});
		},
		
		// checkdays: function() {
		// 	this.days = [];
		// 	var day = new Date(this.date_start);
		// 	while (day <= this.date_end) {
		// 		var p = $('.day[data-dayid='+dayid(day)+']');
		// 		if (p.length) {this.days.push(dayid(day))}
		// 		day = new Date(day.getTime() + 24*60*60*1000); // add 24 hours
		// 	}
		// },
		
		getrecid: function() {
			return this.recid;
		},
		
		getstart: function() {
			return this.date_start
		},
		
		getend: function() {
			return this.date_end
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
					self._sub = 2
					self._width = $('.day').width();
					self._height = $('.day').height() / 24;
					self._ox = event.pageX;
					self._oy = event.pageY;
					self._cellx = (event.pageX - offset.left) % self._width;
					self._celly = (event.pageY - offset.top) % self._height;
					self._day = 0;
					self._hour = 0;
					self.original_date_start = self.date_start;
					self.original_date_end = self.date_end;
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
					},
				'stop': function(event, ui) {}
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
					console.log("height?", self._height)				
				},
			    'resize': function(event, ui) {
			        ui.size.width = ui.originalSize.width;
			    },
				'stop': function(event) {
					var hour = Math.floor(4*((event.pageY - self._d_ox)/self._height))/4;
					self.setduration_offset(hour);
				}
			})
			
			var helper = $('<div style="text-align:center;position:absolute;bottom:0px;width:100%;font-size:8pt;color:#fff">=</div>');
			box.append(helper);			
			// helper.draggable({
			// 	'helper': function(){return '<div></div>'},
			// 	'start': function(event, ui){
			// 		self._d_ox = event.pageY;
			// 		self._duration = 0;
			// 		self._height = $('.day').height() / 24;
			// 	},
			// 	'drag': function(event, ui){
			// 		var duration = Math.floor(4 * (event.pageY - self._d_ox) / self._height) / 4;
			// 		if (self._duration != duration) {
			// 			self.setduration_offset(duration);
			// 		}
			// 		self._duration = duration;
			// 	},
			// 	'stop': function(event, ui) {}
			// });
		},
		
		setduration_offset: function(hour) {
			console.log("adding time", hour)
			var self = this;
			var duration = 3600 * 1000 * hour;
			var newend = new Date(this.date_end.getTime() + duration);
			if (newend <= this.date_start) {
				return
			}
			this.date_end = newend;
			this.draw();
		},
		
		settime_offset: function(hour, day) {
			var self = this;
			var duration = this.date_end - this.date_start;
			var offset = (24*3600*1000*day) + (3600*1000*hour);
			var newstart = new Date(self.original_date_start.getTime() + offset);
			var newend = new Date(newstart.getTime() + duration);
			this.date_start = newstart;
			this.date_end = newend;
			this.draw();
		},
		
		reindent: function(level) {
			if (this.indent == level) {
				return
			}
			this.indent = level;
			var self = this;
			$('.event_box[data-recid='+this.recid+']').each(function() {
				var e = $(this)
				e.css('left', self.indent*20+"%");
				e.css('width', 100-(self.indent*20)+"%")				
			});	
		},		
		
		collisions: function() {
			var self = this;
			var cs = [];
			var levels = {};
			$('.event').each(function() {
				var eid = $(this).CalendarEvent('getrecid');
				if (eid == self.recid) {return}
				var ds = $(this).CalendarEvent('getstart');
				var de = $(this).CalendarEvent('getend');
				if (self.timewindow(ds, de, self.date_start, self.date_end)) {
					cs.push(eid);
					var l1 = self.date_end - self.date_start;
					var l2 = de - ds;
					if (l2 > l1) {
						self.indent += 1;
					}
				}
			});
			//console.log("Collisions: ", this.recid, " with ", cs, " ... indent is", this.indent);
		},		
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);










