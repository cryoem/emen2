// Log wrapper to keep everything from crashing horribly
//		if I forget to comment out a Firebug console.log()
// http://paulirish.com/2009/log-a-lightweight-wrapper-for-consolelog/
window.log = function(){
  log.history = log.history || [];   // store logs to an array for reference
  log.history.push(arguments);
  if(this.console){
    console.log( Array.prototype.slice.call(arguments) );
  }
};

// Time localize format
$.localize.format = 'mm/dd/yyyy';

// EMEN2 helper methods
var emen2 = {};

// EMEN2 time functions
emen2.time = {};

emen2.time.pad = function(n) {
    return n<10 ? '0'+n : n
};

// Print an ISO Date String in UTC time
emen2.time.UTCISODateString = function(d) {
    return d.getUTCFullYear()+'-'
    + emen2.time.pad(d.getUTCMonth()+1)+'-'
    + emen2.time.pad(d.getUTCDate())+'T'
    + emen2.time.pad(d.getUTCHours())+':'
    + emen2.time.pad(d.getUTCMinutes())+':'
    + emen2.time.pad(d.getUTCSeconds())+'Z'
}

// Print an ISO Date String
emen2.time.ISODateString = function(d) {
	var sep = '-';
	var offset = d.getTimezoneOffset();
	if (offset < 0) {
		sep = '+';
		offset = Math.abs(offset);
	}
	var hours = Math.floor(offset/60);
	var minutes = offset % 60;
    return d.getFullYear() + '-'
	+ emen2.time.pad(d.getMonth()+1) +'-'
    + emen2.time.pad(d.getDate()) + 'T'
    + emen2.time.pad(d.getHours()) + ':'
    + emen2.time.pad(d.getMinutes()) + ':'
    + emen2.time.pad(d.getSeconds()) + sep
	+ emen2.time.pad(hours) + ':'
	+ emen2.time.pad(minutes)
}

emen2.time.now = function() {
	return emen2.time.ISODateString(new Date());
}

emen2.time.range = function(t1, t2, width) {
	var t2 = t2 || new Date();
	var width = width || 'month';
	var f = emen2.time.interval[width];
	var start = f(t1)[0];
	var end = f(t2)[1];
	var cur = start;
	var ret = [];
	var i = 0;
	while (cur<end) {
		var d = f(cur);
		ret.push(d[0]);
		cur = d[1];
	}
	ret.push(end);
	return ret
};
emen2.time.start = function(t1, width) {
	var t1 = t1 || new Date();
	var width = width || 'month';
	return emen2.time.interval[width](t1)[0]
};

// EMEN2 Time interval helpers
emen2.time.interval = {};


// Return year interval
emen2.time.interval.year = function(t1) {
	var t1 = t1 || new Date();
	var start = new Date(t1.getFullYear(), 0, 1, 0, 0, 0, 0);
	var end = new Date(t1.getFullYear()+1, 0, 1, 0, 0, 0, 0);
	return [start, end]
};

emen2.time.interval.month = function(t1) {
	var t1 = t1 || new Date();
	var start = new Date(t1.getFullYear(), t1.getMonth(), 1, 0, 0, 0, 0);
	var end = new Date(t1.getFullYear(), t1.getMonth()+1, 1, 0, 0, 0, 0);
	return [start, end]
};

emen2.time.interval.day = function(t1) {
	var t1 = t1 || new Date();
	var start = new Date(t1.getFullYear(), t1.getMonth(), t1.getDate(), 0, 0, 0, 0);
	var end = new Date(t1.getFullYear(), t1.getMonth(), t1.getDate()+1, 0, 0, 0, 0);
	return [start, end]	
};

emen2.time.interval.hour = function(t1) {
	var t1 = t1 || new Date();
	var start = new Date(t1.getFullYear(), t1.getMonth(), t1.getDate(), t1.getHours(), 0, 0, 0);
	var end = new Date(t1.getFullYear(), t1.getMonth(), t1.getDate(), t1.getHours()+1, 0, 0, 0);
	return [start, end]	
};

emen2.time.interval.minute = function(t1) {
	var t1 = t1 || new Date();
	var start = new Date(t1.getFullYear(), t1.getMonth(), t1.getDate(), t1.getHours(), t1.getMinutes(), 0, 0);
	var end = new Date(t1.getFullYear(), t1.getMonth(), t1.getDate(), t1.getHours(), t1.getMinutes()+1, 0, 0);
	return [start, end]	
};

emen2.time.interval.second = function(t1) {
	var t1 = t1 || new Date();
	var start = new Date(t1.getFullYear(), t1.getMonth(), t1.getDate(), t1.getHours(), t1.getMinutes(), t1.getSeconds(), 0);
	var end = new Date(t1.getFullYear(), t1.getMonth(), t1.getDate(), t1.getHours(), t1.getMinutes(), t1.getSeconds()+1, 0);
	return [start, end]
};



// EMEN2 cache handling
emen2.cache = {};

emen2.caches = {
	'user': {},
	'group': {},
	'record': {'None':{}},
	'paramdef': {},
	'recorddef': {},
	'binary': {},
	'children': {},
	'parents': {},
	'recnames': {}
};

emen2.cache.get = function(key, keytype) {
	var keytype = keytype || 'record';
	return emen2.caches[keytype][key]
};

emen2.cache.update = function(items) {
	$.each(items, function() {
		if (!this.keytype) {return}
		emen2.caches[this.keytype][this.name] = this;
	})
};

emen2.cache.check = function(keytype, items) {
	var ret = [];
	$.each(items, function(i,v) {
		if (v == 'None' || v == null) {
			return
		}
		var item = emen2.caches[keytype][v];
		if (item==null && $.inArray(v,ret)==-1) {ret.push(v)}
	});
	return ret
};

emen2.db = function(method, args, cb, eb) {
	return $.jsonRPC.call(method, args, cb, eb);
};

// EMEN2 template functions
emen2.template = {};

emen2.template.random = function() {
	return ""
};

emen2.template.caret = function(state, elem) {
	// Create or toggle a caret up/down icon
	var caret = [];
	if (elem) {
		var caret = $('.e2l-caret', elem);
	}
	if (!elem || !caret.length) {
		caret = $(emen2.template.image('caret.up.png', '^', 'e2l-caret'));
	}
	state = state || 'down';
	if (state == 'toggle') {
		if (caret.attr('data-state')=='up') {state='down'} else {state='up'}
	}		
	caret.attr('src', emen2.template.static('images/caret.'+state+'.png'));
	caret.attr('data-state', state);
	if (elem){return}
	return $('<div />').append(caret).html()
};

emen2.template.static = function(name) {
	return EMEN2WEBROOT+'/static-'+VERSION+'/'+name
};

emen2.template.image = function(name, alt, cls) {
	alt = alt || '';
	cls = cls || '';
	return '<img src="'+emen2.template.static('images/'+name)+'" class="'+cls+'" alt="'+alt+'" />'		
};

emen2.template.spinner = function(show) {
	var cls = 'e2l-spinner e2l-hide';
	if (show) {cls = 'e2l-spinner'}
	return emen2.template.image('spinner.gif', 'Loading', cls);
};

emen2.template.notify = function(msg, error, fade) {
	var msg=$('<li>'+msg+'</li>');
	if (error!=null) {
		msg.addClass("e2l-error");
	}
	var killbutton = $('<span class="e2l-float-right">X</span>');
	killbutton.click(function() {
		$(this).parent().fadeOut(function(){
			$(this).remove();
		});		
	});
	msg.append(killbutton);
	$("#container .e2-alert").append(msg); //.fadeIn();	
};

emen2.template.poll_notifications = function(freq) {
   $.jsonRPC.call('poll', {}, function(result) {
      emen2.template.notify(result, false);
      console.log('found_notification');
      emen2.template.poll_notifications();
   }, function(result) {
      emen2.template.notify(result, true);
      console.log('found_error');
   });
};

// Default error message dialog.
// This gives the user some feedback if an RPC request fails.
emen2.template.error = function(title, text, method, data) {
	var error = $('<div title="'+title+'" />');
	error.append('<p>'+text+'</p>');
	var debug = $('<div class="e2-error-debug e2l-hide"/>');
	debug.append('<p><strong>JSON-RPC Method:</strong></p><p>'+method+'</p>');
	debug.append('<p><strong>Data:</strong></p><p>'+data+'</p>');
	error.append(debug);
	error.dialog({
		width: 400,
		height: 300,
		modal: true,
		buttons: {
			'OK':function() {
				$(this).dialog('close')
			},
			'More Info': function() {
				$('.e2-error-debug', this).toggle();
			}
		}
	});
};

emen2.ui = {};

emen2.ui.buttonfeedback = function(elem) {
	var elem = $(elem);
	$('.e2l-spinner', elem).show();
	elem.addClass('e2l-disabled');
}


// Convert a byte count to human friendly
emen2.template.prettybytes = function(bytes) {
	var b = 0;
	if (bytes >= 1099511627776) {
		b = bytes / 1099511627776;
		return b.toFixed(2) + " TB"
	} else if (bytes >= 1073741824) {
		b = bytes / 1073741824;
		return b.toFixed(2) + " GB"
	} else if (bytes >= 1048576) {
		b = bytes / 1048576;
		return b.toFixed(2) + " MB"
	} else if (bytes >= 1024) {
		b = bytes / 1024;
		return b.toFixed(2) + " KB"
	} else if (bytes != null) {
		return bytes + " bytes"
	} else {
		return "Unknown"
	}
};


// EMEN2 Utility functions
emen2.util = {};

// For EMEN2 widgets, check this.options first, then
// this.element.attr('data-'+key)
// This includes a check so that record ID = 0 works
emen2.util.checkopt = function(self, key, dfault) {
	var value = self.options[key];
	if (value == 0) {
		//  && key == 'name') {
		return value
	}
	value = value || self.element.attr('data-'+key) || dfault;
	return value
};

// Sort a dict's keys based on integer values
// >>> var sortable = [];
// >>> for (var vehicle in maxSpeed)
//       sortable.push([vehicle, maxSpeed[vehicle]])
// >>> sortable.sort(function(a, b) {return a[1] - b[1]})
// [["bike", 60], ["motorbike", 200], ["car", 300],
// ["helicopter", 400], ["airplane", 1000], ["rocket", 28800]]
emen2.util.sortdict = function(o) {
	var sortable = [];
	for (var i in o) {
		sortable.push([i, o[i]])
	}
	var s = sortable.sort(function(a, b) {return b[1] - a[1]})
	result = [];
	for (var i=0;i<s.length;i++) {
		result.push(s[i][0]);
	}
	return result
};

// Sort a dict's keys based on lower-case string values
emen2.util.sortdictstr = function(o) {
	var sortable = [];
	for (var i in o) {
		sortable.push([i, o[i]])
	}
	var s = sortable.sort(function(a, b) {
		return b[1].toLowerCase() > a[1].toLowerCase()
		});
	result = [];
	for (var i=0;i<s.length;i++) {
		result.push(s[i][0]);
	}
	return result
};


emen2.util.set_add = function(i, l) {
	var pos = $.inArray(i, l);
	if (pos == -1) {
		l.push(i);
	}
	return l
};


emen2.util.set_remove = function(i, l) {
	var pos = $.inArray(i, l);
	if (pos > -1) {
		l.splice(pos, 1);
	}
	return l
};



// $.getFromURL = function(args, data, callback, errback, dataType){
// 	$.get_url(args.name, args.args, args.kwargs)(function(url) {
// 		$.getJSON(EMEN2WEBROOT+url, data, callback, errback, dataType)
// 	})
// }
// 
// $.get_urls = function(args) {
// 	return function(cb) {
// 		$.post(reverse_url, {'arg___json':$.toJSON(args)}, cb, 'json');
// 	}
// }
// 
// $.execute_url = function(name, args, kwargs) {
// 	return function(cb) {
// 		$.post(reverse_url+name+'/execute/', {'arguments___json':$.toJSON(args), 'kwargs___json':$.toJSON(kwargs)}, cb, 'json');
// 	}
// }


// Utility classes
(function($){

	// These two methods are deprecated.
	// Update controls when a record has changed
	$.record_update = function(rec) {
		if (typeof(rec)=="number") {
			var name = rec;
		} else {
			emen2.caches['record'][rec.name] = rec;
			var name = rec.name;
		}
		$.rebuild_views('.e2-view[data-name='+name+']');
		$('.e2-comments').CommentsControl('rebuild');
		$('.e2-attachments').AttachmentControl('rebuild');	
	}

	// Rebuild a rendered view
	$.rebuild_views = function(selector) {
		selector = selector || '.view';
		var self = this;
		$(selector).each(function() {
			var elem = $(this);
			var name = parseInt(elem.attr('data-name'));
			var viewname = elem.attr('data-viewname');
			var edit = elem.attr('data-edit');
			emen2.db("record.render", {'names':name, 'viewname': viewname, 'edit': edit}, function(view) {
				elem.html(view);
				$('time', elem).localize();
				//$('.e2-edit', elem).EditControl({});
			},
			function(view){}
			);
		})
	}

	///////////////////////////////////////////////////
	// Some simple jquery UI widgets that don't really
	//  fit in any other files..
	///////////////////////////////////////////////////
 
	// Select utility
	$.widget('emen2.SelectControl', {
		options: {
			root: null,
			selected: 'input[name]:checkbox:checked',
			all: 'input[name]:checkbox',
			show: true
		},
		
		_create: function() {
			this.built = 0;
			if (this.options.show) {
				this.build();
			}
		},
		
		build: function() {
			if (this.built) {return}
			this.built = 1;
			var self = this;
			
			this.element.empty();			
			var controls = $(' \
				<li> \
					Select \
					<span class="e2l-a e2-select-all">all</span> \
					 or \
					<span class="e2l-a e2-select-none">none</span> \
					<span class="e2-select-count"></span> \
				</li>');
				
			$('.e2-select-all', controls).click(function() {
				$('input:checkbox', self.options.root).attr('checked', 'checked');
				self.update();
			});
			$('.e2-select-none', controls).click(function() {
				$('input:checkbox', self.options.root).attr('checked', null);
				self.update();
			});
				
			this.element.append(controls);
		},
		
		selectnone: function() {
			
		},
		
		selectall: function() {
		},
		
		update: function() {
			var selected = $(this.options.selected, this.options.root);
			var all = $(this.options.all, this.options.root);
			var txt = '('+selected.length+' of '+all.length+' selected)';
			$('.e2-select-count', this.element).html(txt);
		}
	});

	// EMEN2 Tabs
	// Works somewhat like jQuery-UI Tabs -- uses
	//		basically the same markup
	// This control uses the role= attribute to identify components
	// roles: tablist, tabpanel
	$.widget('emen2.TabControl', {
		options: {
			active: 'e2-tab-active',
			absolute: false,
			cbs: {},
			hidecbs: {},
			tabgroup: null
		},
		
		_create: function() {
			this.built = 0;
			this.options.tabgroup = emen2.util.checkopt(this, 'tabgroup');
			this.tablist = this.element.children('ul');
			this.tabpanel = this.element;
			var tablist = $('[data-tabgroup='+this.options.tabgroup+'][role=tablist]');
			var tabpanel = $('[data-tabgroup='+this.options.tabgroup+'][role=tabpanel]');
			if (tablist.length) {this.tablist = tablist}
			if (tabpanel.length) {this.tabpanel = tabpanel}
			this.build();
		},

		// Check the window hash (e.g. "#permissions")
		// and open that tab if it exists
		checkhash: function() {
			var active = window.location.hash.replace("#","")
			if (active) {
				this.show(active);
			}			
		},
		
		build: function() {
			if (this.built){return}
			var self = this;
			$('li[data-tab]', this.tablist).click(function(e){
				var tab = $(this).attr('data-tab');
				var hc = $(this).hasClass(self.options.active);
				if (hc) {
					e.preventDefault();
					self.hide(tab);
				} else {
					self.hide(tab);
					self.show(tab);
				}
			});
			this.built = 1;
		},
		
		setcb: function(tab, cb) {
			this.options.cbs[tab] = cb;
		},
		
		sethidecb: function(tab, cb) {
			this.options.hidecbs[tab] = cb;			
		},
		
		hide: function(tab) {
			var self = this;
			$('li.'+this.options.active, this.tablist).each(function() {
				var t = $(this);
				var tab = t.attr('data-tab');
				var p = $('[data-tab='+tab+']', self.tabpanel);
				t.removeClass(self.options.active);
				p.removeClass(self.options.active);
				var cb = self.options.hidecbs[tab];
				if (cb) {cb(p)}
			});
			var active = window.location.hash.replace("#","")
			if (tab==active) {
				window.location.hash = '';
			}
		},

		show: function(tab) {
			var t = $('li[data-tab='+tab+']', this.tablist);
			if (!t.length) {
				return
			}
			var p = $('div[data-tab='+tab+']', this.tabpanel);
			if (!p.length) {
				var p = $('<div data-tab="'+tab+'"></div>');
				this.tabpanel.append(p);
			}
			
			p.addClass('e2l-cf');

			// Menu-style -- float above content
			// if (this.options.absolute) {
			// 	// Set the position
			// 	var pos = t.position();
			// 	var height = t.height();
			// 	var width = t.width();
			// 	p.css('position', 'absolute');
			// 	p.css('top', pos.top + height);
			// 
			// 	// Is it right aligned?
			// 	var align = t.css('float');				
			// 	if (align=='left') {
			// 		p.css('left', pos.left-1);					
			// 	} else {
			// 		var parentwidth = p.parent().width();
			// 		p.css('right', parentwidth-(width+pos.left)-2);
			// 	}
			// }
			
			// Run any callbacks
			var cb = this.options.cbs[tab];
			if (cb) {
				cb(p);
			}

			t.addClass(this.options.active);
			p.addClass(this.options.active);
		},
		
		switch: function(tab) {
		}
		
	});

	// View and edit bookmarks
    $.widget("emen2.BookmarksControl", {
		options: {
			mode: null,
			parent: null
		},
				
		_create: function() {
			this.options.parent = emen2.util.checkopt(this, 'parent');
			this.options.mode = emen2.util.checkopt(this, 'mode');
			this.options.name = emen2.util.checkopt(this, 'name');
			this.built_bookmarks = 0;
			var self = this;
			if (this.options.mode) {
				this.element.click(function() {self._action(self.options.mode, self.options.name)})
			}			
		},
		
		showbookmarks: function() {
			if (this.built_bookmarks) {
				return
			}
			//this.built_bookmarks = 1;
						
			var self = this;
			var bookmarks = [];
			emen2.db('rel.children', [this.options.parent, 1, 'bookmarks'], function(children) {
				children.sort();
				var brec = null;
				if (children.length > 0) {
					brec = children[children.length-1];
				}
				emen2.db('record.get', [brec], function(rec) {
					var brecs = [];
					if (rec != null) {
						var brecs = rec['bookmarks'] || [];
					}
					emen2.db('record.render', [brecs], function(recnames) {
						$.each(recnames, function(k,v) {
							emen2.caches['recnames'][k] = v;
						});
						self._build_bookmarks(brecs);
					});	
				});
			});
		},
				
		_build_bookmarks: function(bookmarks) {
			$('ul#bookmarks', this.element).remove();
			var ul = $('<ul id="bookmarks"></ul>');
			bookmarks.reverse();			
			if (bookmarks.length == 0) {
				ul.append('<li><a href="">No bookmarks</a></li>');
			}
			$.each(bookmarks, function() {
				var li = $('<li><a href="'+EMEN2WEBROOT+'/record/'+this+'/">'+emen2.caches['recnames'][this]+'</a></li>');
				ul.append(li);
			});			
			this.element.append(ul);
		},
		
		add_bookmark: function(name) {
			this._action('add', name);
		},
		
		remove_bookmark: function(name) {
			this._action('remove', name);			
		},
		
		toggle_bookmark: function(name) {
			this._action('toggle', name);
		},
		
		_action: function(action, name) {
			var self = this;
			
			if (this.options.parent == null) {
				alert("Can't add bookmark without user preferences record");
				return
			}
			
			//$('img.star', this.element).
			this.element.empty();
			this.element.append(emen2.template.spinner(false));
			
			emen2.db('rel.children', [this.options.parent, 1, 'bookmarks'], function(children) {
				emen2.db('record.get', [children], function(recs) {
					if (recs.length == 0) {
						var rec = {'rectype':'bookmarks', 'bookmarks': [], 'parents': [self.options.parent]};
					} else {
						var rec = recs[0];
					}
					var bookmarks = rec['bookmarks'] || [];
					name = parseInt(name);
					var pos = $.inArray(name, bookmarks);

					if (action == 'remove') {
						if (pos > -1) {
							bookmarks.splice(pos, 1);
						}
					} else if (action == 'add') {
						if (pos == -1) {
							bookmarks.push(name);
						}
					} else if (action == 'toggle') {
						if (pos == -1) {
							bookmarks.push(name);
						} else {
							bookmarks.splice(pos, 1);
						}
					}
					//var pos = $.inArray(name, bookmarks);
					rec['bookmarks'] = bookmarks;
					var pos = $.inArray(name, bookmarks);
					emen2.db('record.put', [rec], function(updrec) {
						if (pos == -1) {
							var star = $(emen2.template.image('star.open.png', 'Add Bookmark'))
						} else {
							var star = $(emen2.template.image('star.closed.png', 'Bookmarked'))
						}
						self.element.empty();
						self.element.append(star);
					});
				});
			});			
		}
	});

	// Siblings control
	$.widget('emen2.SiblingsControl', {
		options: {
			name: null,
			prev: null,
			next: null
		},
		
		_create: function() {
			var self = this;
			this.options.name = emen2.util.checkopt(this, 'name');
			this.options.sibling = emen2.util.checkopt(this, 'sibling');
			this.options.prev = emen2.util.checkopt(this, 'prev');
			this.options.next = emen2.util.checkopt(this, 'next');
			this.build();
		},
		
		build: function() {
			var self = this;
			var rec = emen2.cache.get(this.options.name);
			var sibs = $('<div class="e2-siblings">'+emen2.template.spinner(true)+' Loading siblings...</div>');

			this.element.empty();
			this.element.append(sibs);
			emen2.db("rel.siblings", [rec.name, rec.rectype], function(siblings) {
				emen2.db("record.render", [siblings], function(recnames) {
					siblings = siblings.sort(function(a,b){return a-b});
					$.each(recnames, function(k,v) {
						emen2.caches['recnames'][k] = v;
					});
					self._build_siblings(siblings);
				});			
			});
		},
		
		_build_siblings: function(siblings) {
			var self = this;
			var rec = emen2.cache.get(this.options.name);

			this.element.empty();

			var prevnext = $('<h4 class="e2l-cf" style="text-align:center">Siblings</h4>');
			if (this.options.prev) {
				prevnext.append('<div class="e2l-float-left"><a href="'+EMEN2WEBROOT+'/record/'+this.options.prev+'/#siblings">&laquo; Previous</a></div>');
			}
			if (this.options.next) {
				prevnext.append('<div class="e2l-float-right"><a href="'+EMEN2WEBROOT+'/record/'+this.options.next+'/#siblings">Next &raquo;</a></div>');
			}					
			this.element.append(prevnext);
			
			var ul = $('<ul />');
			$.each(siblings, function(i,k) {
				var rn = emen2.cache.get(k, 'recnames') || k;
				if (k != rec.name) {
					ul.append('<li><a href="'+EMEN2WEBROOT+'/record/'+k+'/?sibling='+self.options.name+'">'+rn+'</a></li>');
				} else {
					ul.append('<li class="e2-siblings-active">'+rn+'</li>');
				}
			});
			this.element.append(ul);
		}

	});

	// A simple widget for counting words in a text field
	$.widget("emen2.WordCount", {
		options: {
			min: null,
			max: null,
		},	

		_create: function() {
			var self = this;
			this.options.max = emen2.util.checkopt(this, 'max');
			
			this.wc = $('<div class="e2-wordcount-count"></div>');
			this.element.after(this.wc);
			self.update();
			this.element.bind('keyup click blur focus change paste', function() {
				self.update();
			});
		},

		update: function() {
			var wc = jQuery.trim(this.element.val()).split(' ').length;
			var t = wc+' Words';
			if (this.options.max) {
				t = t + ' (Maximum: '+this.options.max+')';
			}
			var fault = false;
			if (wc > this.options.max) {fault=true}
			if (fault) {
				this.wc.addClass('e2l-error');
			} else {
				this.wc.removeClass('e2l-error')
			}
			this.wc.text(t);	
		}
	});
})(jQuery);

<%!
public = True
headers = {
	'Content-Type': 'application/javascript',
	'Cache-Control': 'max-age=86400'
}
%>
