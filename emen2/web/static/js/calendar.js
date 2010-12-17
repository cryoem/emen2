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
			var table = $(' \
				<table cellpadding="0" cellspacing="0"> \
					<tbody> \
						<tr class="calendar_body"> \
							<td class="calendar_hours" style="width:40px;padding:0px;margin:0px;"></td> \
						</tr> \
					</tbody> \
				</table> \
			');
			for (var i=0;i<24;i++) {
				$('.calendar_hours', table).append('<div style="height:39px;border-right:solid 1px #ccc;border-bottom:solid 1px #ccc">'+i+'</div>');
			}
			this.element.append(table);
		},
		
		makedays: function(start, end) {
			var day = new Date(start);
			while (day <= end) {
				// $('.calendar_header', this.element).append('<th>'+day.getUTCDate()+'/'+(day.getUTCMonth()+1)+'</th>');
				var newday = new Date(day.getTime() + 24*60*60*1000);
				var daydiv = $('<div style="padding:0px;margin:0px;position:relative;" class="day" data-dayid="'+dayid(day)+'" data-start="'+day+'" data-end="'+newday+'" />');
				for (var i=0;i<24;i++) {
					daydiv.append('<div style="height:39px;border-right:solid 1px #ccc;border-bottom:solid 1px #ccc"></div>')
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
			this.element.hide();
			this.eventid = this.element.attr('data-eventid');
			this.date_start = parsedate(this.element.attr('data-start'));
			this.date_end = parsedate(this.element.attr('data-end'));
			this.days = [];
		},
		
		draw: function() {
			this.checkdays();
			this.collisions();			
			var self = this;
			$.each(this.days, function() {
				var p = $('.day[data-dayid='+this+']');
				var thisday = new Date(p.attr('data-start'));
				var y_offset = (self.date_start - thisday) / (3600 * 1000);				
				var duration = (self.date_end - self.date_start) / (3600 * 1000);
				height = duration;

				// offset + height exceeds max column height
				if (duration+y_offset>24) {
					height = 24 - y_offset;
				}

				// ending this day
				if (duration + y_offset < 24 && duration > 24) {
					height = duration + y_offset;
					y_offset = 0;
				}
				
				// began before this day
				if (y_offset < 0) {
					height = duration + y_offset;
					y_offset = 0;
				}

				// max column height
				if (height > 24) {
					height = 24;
				}

				var e = $('<div style="position:absolute;top:0px;width:100%;opacity:0.5">'+self.eventid+'</div>');
				e.css('background', 'red');
				// e.css('border', 'solid blue 1px');
				e.css('left', self.indent*20+"%");
				e.css('width', 100-(self.indent*20)+"%")
				e.css('top', y_offset*40);
				e.css('height', height*40);			
				p.append(e);
			});
			
		},
		
		move: function() {
		},
		
		checkdays: function() {
			this.days = [];
			var day = new Date(this.date_start);
			while (day <= this.date_end) {
				var p = $('.day[data-dayid='+dayid(day)+']');
				if (p.length) {this.days.push(dayid(day))}
				day = new Date(day.getTime() + 24*60*60*1000); // add 24 hours
			}
		},
		
		geteventid: function() {
			return this.eventid;
		},
		
		getstart: function() {
			return this.date_start
		},
		
		getend: function() {
			return this.date_end
		},
		
		timewindow: function(d1, d2, t1, t2) {
			// console.log("---");
			// console.log(t1, "<=", d2, t1 <= d2);
			// console.log(t2, ">=", d1, t2 >= d1);
			return t1 <= d2 && t2 >= d1;
		},
		
		collisions: function() {
			var self = this;
			this.indent = 0;
			var cs = [];
			$('.event').each(function() {
				var eid = $(this).CalendarEvent('geteventid');
				if (eid == self.eventid) {return}
				var ds = $(this).CalendarEvent('getstart');
				var de = $(this).CalendarEvent('getend');
				if (self.timewindow(ds, de, self.date_start, self.date_end)) {
					cs.push(eid);
					var l1 = self.date_end - self.date_start;
					var l2 = de - ds;
					if (l2 > l1) {
						self.indent += 1
					}
				}
			});
			console.log("Collions: ", this.eventid, " with ", cs, " ... indent is", this.indent);
		},
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);










