/*
Date Input 1.1.6
Requires jQuery version: 1.2.6

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
  this.bindMethodsToObj("show", "hide", "hideIfClickOutside", "selectDate", "prevMonth", "nextMonth");
  
  this.build();
  this.selectDate();
  this.hide();
};
DateInput.DEFAULT_OPTS = {
  month_names: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
  short_month_names: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  short_day_names: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
  start_of_week: 1,
	save_button: 0,
	cancel_button: 0
};
DateInput.prototype = {
  build: function() {
	
		this.timeSpan = $('<span class="time_name"></span>');
		var hournav = $('<select></select>');
		for (var i=0;i<24;i++) {
			hournav.append('<option>'+i+'</option>');
		}
		var minnav = $('<select></select>');
		for (var i=0;i<60;i++) {
			minnav.append('<option>'+i+'</option>');
		}
		var secnav = $('<select></select>');
		for (var i=0;i<60;i++) {
			secnav.append('<option>'+i+'</option>');
		}	
		this.timeSpan.append(hournav,minnav,secnav);
	
	
    this.monthNameSpan = $('<div class="month_name"></div>');
    var monthNav = $('<p class="month_nav"></p>').append(
      $('<a href="#" class="prev">&laquo;</a>').click(this.prevMonth),
      " ", this.monthNameSpan, " ",
      $('<a href="#" class="next">&raquo;</a>').click(this.nextMonth)
    );
    
    var tableShell = "<table><thead><tr>";
    $(this.adjustDays(this.short_day_names)).each(function() {
      tableShell += "<th>" + this + "</th>";
    });
    tableShell += "</tr></thead><tbody></tbody></table>";
    
		this.dateSelectorDay = $('<div/>').append(monthNav,tableShell);
    this.dateSelector = this.rootLayers = $('<div class="date_selector"></div>').append(this.timeSpan, this.dateSelectorDay).appendTo(document.body);
    
    if ($.browser.msie && $.browser.version < 7) {
      this.ieframe = $('<iframe class="date_selector_ieframe" frameborder="0" src="#"></iframe>').insertBefore(this.dateSelector);
      this.rootLayers = this.rootLayers.add(this.ieframe);
    };
    
    this.tbody = $("tbody", this.dateSelector);
    
    // The anon function ensures the event is discarded
    this.input.change(this.bindToObj(function() { this.selectDate(); }));
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
    
    this.monthNameSpan.empty().append(this.monthName(date) + " " + date.getFullYear());
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
      this.selectMonth(date);
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
    $([window, document.body]).click(this.hideIfClickOutside);
  },
  
  hide: function() {
    this.rootLayers.css("display", "none");
    $([window, document.body]).unbind("click", this.hideIfClickOutside);
    this.input.focus(this.show);
  },
  
  hideIfClickOutside: function(event) {
    if (event.target != this.input[0] && !this.insideSelector(event)) {
      this.hide();
    };
  },
  
//   stringToDate: function(string) {
//     var matches;
//     if (matches = string.match(/^(\d{1,2}) ([^\s]+) (\d{4,4})$/)) {
//       return new Date(matches[3], this.shortMonthNum(matches[2]), matches[1]);
//     } else {
//       return null;
//     };
//   },
//   
//   dateToString: function(date) {
//     return date.getDate() + " " + this.short_month_names[date.getMonth()] + " " + date.getFullYear();
//   },

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

		//console.log(Date(date[0],date[1] - 1,date[2],time[0],time[1],time[2]));
		return new Date(date[0],date[1] - 1,date[2],time[0],time[1],time[2])
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
  
  prevMonth: function() {
    this.moveMonthBy(-1);
    return false;
  },
  
  nextMonth: function() {
    this.moveMonthBy(1);
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
