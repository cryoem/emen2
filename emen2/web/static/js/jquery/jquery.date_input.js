/*
Date Input 1.1.5
Requires jQuery version: 1.2
Requires plugins:
  * Dimensions - http://plugins.jquery.com/files/dimensions_1.2.zip

Copyright (c) 2007-2008 Jonathan Leighton & Torchbox Ltd

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
*/

DateInput = (function($) { // Localise the $ function

function DateInput(el, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, DateInput.DEFAULT_OPTS, opts);
  
  this.input = $(el);
  this.bindMethodsToObj("show", "hide", "hideIfClickOutside", "selectDate", "prevMonth", "nextMonth", "prevYear", "nextYear");
  
	this.currentDate = new Date();

  this.build();
  this.selectDate();
  this.hide();
};
DateInput.DEFAULT_OPTS = {
  month_names: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
  short_month_names: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  short_day_names: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
	time_rows: 12,
	start_hour: 7,
	min_interval: 5,
	sec_interval: 5,
	disp_hour: 8,
	disp_min: 0,
	disp_sec: 0,
  start_of_week: 1
};
DateInput.prototype = {
  build: function() {
	
		this.currentHour=null;
		this.currentMin=null;
		this.currentSec=null;
		
		this.timecont = $('<div class="time_cont"></div>');
		this.timeNav = $('<table class="time_nav"></table>');

		this.timeNav.append($(
			$("<thead></thead>").append(
				$('<th>H </th>').append(
					$('<a href="#">+</a>').click(this.bindToObj(function(event) {this.incrTime("hour",1)})),
					$('<a href="#">-</a>').click(this.bindToObj(function(event) {this.incrTime("hour",-1)}))
					),
				$('<th>M </th>').append(
					$('<a href="#">+</a>').click(this.bindToObj(function(event) {this.incrTime("min",1)})),
					$('<a href="#">-</a>').click(this.bindToObj(function(event) {this.incrTime("min",-1)}))
					),
				$('<th>S </th>').append(
					$('<a href="#">+</a>').click(this.bindToObj(function(event) {this.incrTime("sec",1)})),
					$('<a href="#">-</a>').click(this.bindToObj(function(event) {this.incrTime("sec",-1)}))
					)
				)
			)
		);
		
		this.hourNav = $('<td class="hour_nav"></td>');
		this.minNav = $('<td class="min_nav"></td>');
		this.secNav = $('<td class="sec_nav"></td>');	
		this.timeNav.append(this.hourNav,this.minNav,this.secNav);
		this.timecont.append(this.timeNav);
	
    this.monthNameSpan = $('<span class="month_name"></span>');
    var monthNav = $('<p class="month_nav"></p>').append(
      $('<a href="#" class="prev">&laquo;</a>').click(this.prevMonth), " ",
      $('<a href="#" class="next">&raquo;</a>').click(this.nextMonth), " ",
      this.monthNameSpan
    );

		this.yearNameSpan = $('<p class="month_name"></p>');
		var yearNav = $('<p class="month_nav"></p>').append(this.yearNameSpan, $('<a href="#" class="prev">&laquo;</a>').click(this.prevYear), " ", $('<a href="#" class="next">&raquo;</a>').click(this.nextYear));
    
    var tableShell = "<table><thead><tr>";
    $(this.adjustDays(this.short_day_names)).each(function() {
      tableShell += "<th>" + this + "</th>";
    });
    tableShell += "</tr></thead><tbody></tbody></table>";
    
		var datecont = $('<div class="date_cont"></div>');
		datecont.append(monthNav,yearNav,tableShell);
    this.dateSelector = this.rootLayers = $('<div class="date_selector"></div>').append(this.timecont, datecont).appendTo(document.body);
    
    if ($.browser.msie && $.browser.version < 7) {
      this.ieframe = $('<iframe class="date_selector_ieframe" frameborder="0" src="#"></iframe>').insertBefore(this.dateSelector);
      this.rootLayers = this.rootLayers.add(this.ieframe);
    };
    
    this.tbody = $("tbody", this.dateSelector);
    // this.selectTime();
    // The anon function ensures the event is discarded
    this.input.change(this.bindToObj(function() { this.selectDate(); }));
  },
  
	selectTime: function(date) {

		//this.checktimebounds();

		//console.log("selectTime: "+date);

		if (date.getHours() == 0 && date.getMinutes() == 0 && date.getSeconds() == 0) {
			this.disp_hour = 8;
			this.disp_min = 1;
			this.disp_sec = 1;
		} else {
			this.disp_hour = date.getHours();
			this.disp_min = date.getMinutes();
			this.disp_sec = date.getSeconds();
		}

		this.hourNav.empty();
		this.minNav.empty();
		this.secNav.empty();
		
		this.start_hour = this.disp_hour - this.time_rows / 2;
		if (this.start_hour < 0) {this.start_hour=0}
		if (this.start_hour > 24-this.time_rows) {this.start_hour = 24-this.time_rows}
		
		var secs=Array();
		var mins=Array();

		for (var i =0; i < 60; i=i+this.sec_interval) {	secs.push(i);	}
		if (secs.indexOf(this.disp_sec) < 0) {
			secs.push(this.disp_sec);
			secs.sort(sortNumber);
		} 
		
		for (var i =0; i < 60; i=i+this.min_interval) {	mins.push(i);	}
		if (mins.indexOf(this.disp_min) < 0) {
			mins.push(this.disp_min);
			mins.sort(sortNumber);
		}
	
		for (var i = 0; i < this.time_rows; i++) {
			var ti=this.start_hour+i;
			var t=$('<tr time="'+ti+'"><a href="#">'+ti+'</a></tr>').click(this.bindToObj(function(event) {this.selectHour(event)}));
			if (ti==this.disp_hour) {t.addClass("selected")};
			this.hourNav.append(t);			
		}
		for (i in mins) {
			var t=$('<tr time="'+mins[i]+'"><a href="#">'+mins[i]+'</a></tr>').click(this.bindToObj(function(event) {this.selectMin(event)}));
			if (mins[i]==this.disp_min) {t.addClass("selected")};
			this.minNav.append(t);			
		}
		for (i in secs) {
			var t=$('<tr time="'+secs[i]+'"><a href="#">'+secs[i]+'</a></tr>').click(this.bindToObj(function(event) {this.selectSec(event)}));
			if (secs[i]==this.disp_sec) {t.addClass("selected")};
			this.secNav.append(t);			
		}

		//console.log("wtf");
		this.changeTimeField(date);
		this.selectMonth(date);
		
	},
	
	incrTime: function(type,value) {
		if (type=="hour") {
			this.currentDate.setHours(this.disp_hour + value);
		} else if (type=="min") {
			this.currentDate.setMinutes(this.disp_min + value);
		} else if (type=="sec") {
			this.currentDate.setSeconds(this.disp_sec + value);
		}
		this.selectTime(this.currentDate);	
		return false;
	},
	
	selectHour: function(e) {
		//console.log(e);
		this.currentDate.setHours(parseInt($(e.target).parent().attr('time')));
		//console.log("e");
		this.selectTime(this.currentDate);
	},
	
	selectMin: function(e) {
		this.currentDate.setMinutes(parseInt($(e.target).parent().attr('time')));
		this.selectTime(this.currentDate);
	},

	selectSec: function(e) {
		this.currentDate.setSeconds(parseInt($(e.target).parent().attr('time')));
		this.selectTime(this.currentDate);
	},
	
	changeTimeField: function(date) {
		//console.log("setfield");
		this.input.val(this.dateToString(date));	
	},

  selectMonth: function(date) {
    this.currentMonth = new Date(date.getFullYear(), date.getMonth(), 1);
    
    var rangeStart = this.rangeStart(date), rangeEnd = this.rangeEnd(date);
    var numDays = this.daysBetween(rangeStart, rangeEnd);
    var dayCells = "";
    
    for (var i = 0; i <= numDays; i++) {
      var currentDay = new Date(rangeStart.getFullYear(), rangeStart.getMonth(), rangeStart.getDate() + i);
      
      if (this.isFirstDayOfWeek(currentDay)) dayCells += "<tr>";
      
      if (currentDay.getMonth() == date.getMonth()) {
        dayCells += '<td date="' + this.dateToString(currentDay) + '"><a href="#">' + currentDay.getDate() + '</a></td>';
      } else {
        dayCells += '<td class="unselected_month" date="' + this.dateToString(currentDay) + '">' + currentDay.getDate() + '</td>';
      };
      
      if (this.isLastDayOfWeek(currentDay)) dayCells += "</tr>";
    };
    
    this.monthNameSpan.empty().append(this.monthName(date));
		this.yearNameSpan.empty().append(date.getFullYear());
    this.tbody.empty().append(dayCells);
    
    $("a", this.tbody).click(this.bindToObj(function(event) {
      this.selectDate(this.stringToDate($(event.target).parent().attr("date")));
      //this.hide();
      return false;
    }));
    
    $("td[date=" + this.dateToString(new Date()) + "]", this.tbody).addClass("today");
  },
  
  selectDate: function(date) {
    if (typeof(date) == "undefined") {
      date = this.stringToDate(this.input.val());
    };
    
    if (date) {
      this.selectedDate = date;
			this.currentDate = date;
      this.selectMonth(date);
			this.selectTime(date);
      var stringDate = this.dateToString(date);
      $('td[date=' + stringDate + ']', this.tbody).addClass("selected");
      
      if (this.input.val() != stringDate) {
        this.input.val(stringDate).change();
      };
    } else {
      this.selectMonth(new Date());
    };
  },

  show: function() {
    this.rootLayers.css("display", "block");
    this.setPosition();
    this.input.unbind("focus", this.show);
    //$([window, document.body]).click(this.hideIfClickOutside);
  },
  
  hide: function() {
    this.rootLayers.css("display", "none");
    //$([window, document.body]).unbind("click", this.hideIfClickOutside);
    this.input.focus(this.show);
  },
  
  hideIfClickOutside: function(event) {
    if (event.target != this.input[0] && !this.insideSelector(event)) {
      this.hide();
    };
  },
  
  stringToDate: function(string) {
		// this is ugly because js regex support isn't great
		//return null;
		var dt=$.trim(string).split(" ");
		var date=[0,0,0];
		var time=[0,0,0];
		if (dt.length>0) {
			var z=dt[0].split("/");
			for (i in z) {date[i]=parseInt(z[i])}
		}
		if (dt.length>1) {
			var z=dt[1].split(":");
			for (i in z) {time[i]=parseInt(z[i])}
		}

		console.log(Date(date[0],date[1] - 1,date[2],time[0],time[1],time[2]));
		return new Date(date[0],date[1] - 1,date[2],time[0],time[1],time[2])
//     var matches;
//     if (matches = string.match(/^(\d{4,4})\/(\d{2,2})\/(\d{2,2})$/)) {
//       return new Date(matches[1], matches[2] - 1, matches[3]);
//     } else {
//       return null;
//     };
  },

  dateToString: function(date) {
    var month = (date.getMonth() + 1).toString();
    var dom = date.getDate().toString();

		var hours = date.getHours().toString();
		var mins = date.getMinutes().toString();
		var secs = date.getSeconds().toString();

    if (month.length == 1) month = "0" + month;
    if (dom.length == 1) dom = "0" + dom;

		if (hours == 0 && mins == 0 && secs == 0) {
	    return date.getFullYear() + "/" + month + "/" + dom;
		}

    if (hours.length == 1) hours = "0" + hours;
    if (mins.length == 1) mins = "0" + mins;
    if (secs.length == 1) secs = "0" + secs;

    return date.getFullYear() + "/" + month + "/" + dom + " " + hours + ":" + mins + ":" + secs;
  },
  
  setPosition: function() {
    var offset = this.input.offset();
    this.rootLayers.css({
      top: offset.top + this.input.outerHeight(),
      left: offset.left
    });
    
    if (this.ieframe) {
      this.ieframe.css({
        width: this.dateSelector.outerWidth(),
        height: this.dateSelector.outerHeight()
      });
    };
  },
  
  moveMonthBy: function(amount) {
    this.selectMonth(new Date(this.currentMonth.setMonth(this.currentMonth.getMonth() + amount)));
  },

	moveYearBy: function(amount) {
		var year = this.currentDate.getFullYear() + amount;
		this.currentDate.setFullYear(year);
		this.selectDate(this.currentDate);
	},
  
  prevMonth: function() {
    this.moveMonthBy(-1);
    return false;
  },
  
  nextMonth: function() {
    this.moveMonthBy(1);
    return false;
  },

	prevYear: function() {
    this.moveYearBy(-1);
    return false;
	},
	
	nextYear: function() {
		this.moveYearBy(1);
		return false;
	},
  
  monthName: function(date) {
    return this.month_names[date.getMonth()];
  },
  
  insideSelector: function(event) {
    var offset = this.dateSelector.offset();
    offset.right = offset.left + this.dateSelector.outerWidth();
    offset.bottom = offset.top + this.dateSelector.outerHeight();
    
    return event.pageY < offset.bottom &&
           event.pageY > offset.top &&
           event.pageX < offset.right &&
           event.pageX > offset.left;
  },
  
  bindToObj: function(fn) {
    var self = this;
    return function() { return fn.apply(self, arguments) };
  },
  
  bindMethodsToObj: function() {
    for (var i = 0; i < arguments.length; i++) {
      this[arguments[i]] = this.bindToObj(this[arguments[i]]);
    };
  },
  
  indexFor: function(array, value) {
    for (var i = 0; i < array.length; i++) {
      if (value == array[i]) return i;
    };
  },
  
  monthNum: function(month_name) {
    return this.indexFor(this.month_names, month_name);
  },
  
  shortMonthNum: function(month_name) {
    return this.indexFor(this.short_month_names, month_name);
  },
  
  shortDayNum: function(day_name) {
    return this.indexFor(this.short_day_names, day_name);
  },
  
  daysBetween: function(start, end) {
    start = Date.UTC(start.getFullYear(), start.getMonth(), start.getDate());
    end = Date.UTC(end.getFullYear(), end.getMonth(), end.getDate());
    return (end - start) / 86400000;
  },
  
  changeDayTo: function(to, date, direction) {
    var difference = direction * (Math.abs(date.getDay() - to - (direction * 7)) % 7);
    return new Date(date.getFullYear(), date.getMonth(), date.getDate() + difference);
  },
  
  rangeStart: function(date) {
    return this.changeDayTo(this.start_of_week, new Date(date.getFullYear(), date.getMonth()), -1);
  },
  
  rangeEnd: function(date) {
    return this.changeDayTo((this.start_of_week - 1) % 7, new Date(date.getFullYear(), date.getMonth() + 1, 0), 1);
  },
  
  isFirstDayOfWeek: function(date) {
    return date.getDay() == this.start_of_week;
  },
  
  isLastDayOfWeek: function(date) {
    return date.getDay() == (this.start_of_week - 1) % 7;
  },
  
  adjustDays: function(days) {
    var newDays = [];
    for (var i = 0; i < days.length; i++) {
      newDays[i] = days[(i + this.start_of_week) % 7];
    };
    return newDays;
  }
};

$.fn.date_input = function(opts) {
  return this.each(function() { new DateInput(this, opts); });
};
$.date_input = { initialize: function(opts) {
  $("input.date_input").date_input(opts);
} };

return DateInput;
})(jQuery); // End localisation of the $ function
