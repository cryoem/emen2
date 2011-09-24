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

// Utility Methods
(function($){
	
	$.setadd = function(arr, item) {
		if ($.inArray(item, arr) == -1) {
			arr.push(item);
		}
	}

	$.spinner = function() {
		return '<img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" class="e2l-spinner hide" alt="Loading" />'
	}
	
	// Update controls when a record has changed
	$.record_update = function(rec) {
		if (typeof(rec)=="number") {
			var name = rec;
		} else {
			caches['record'][rec.name] = rec;
			var name = rec.name;
		}
		$.rebuild_views('.e2-view[data-name='+name+']');
		$(".e2-comments").CommentsControl('rebuild');
		$('.e2-attachments').AttachmentControl('rebuild');	
	}

	// Rebuild a rendered view
	$.rebuild_views = function(selector) {
		selector = selector || '.view';
		var self = this;
		$(selector).each(function() {
			var elem = $(this);
			var name = parseInt(elem.attr('data-name'));
			var viewtype = elem.attr('data-viewtype');
			var edit = elem.attr('data-edit');
			$.jsonRPC.call("renderview", {'names':name, 'viewtype': viewtype, 'edit': edit}, function(view) {
				elem.html(view);
				//$('.editable', elem).EditControl({});
			},
			function(view){}
			);
		})
	}
	

	// Notifications
	$.notify = function(msg, fade, error) {
		var msg=$('<li>'+msg+'</li>');
		if (error) {
			msg.addClass("error");
		}
		var killbutton = $('<span class="e2l-float-right">X</span>');
		killbutton.click(function() {
			$(this).parent().fadeOut(function(){
				$(this).remove();
			});		
		});
		msg.append(killbutton);
		$("#e2-alert").append(msg); //.fadeIn();	
	}
	
	// Convert a byte count to human friendly
	$.convert_bytes = function(bytes) {
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
	}

	// Similar to RPC, but POST to a view.
	$.postJSON = function(url, data, callback, errback) {
		return $.ajax({
			url: url,
			data: $.toJSON(data), 
			type: "POST",
			success: callback
			//error: function(jqXHR, textStatus, errorThrown) {console.log(errorThrown)}
			//dataType: "json"
			});
	}

	$.get_url = function(name, args, kwargs) {
		if (args === undefined) {args = []};
		if (kwargs === undefined) {kwargs = {}};
		return function(cb) {
			$.post(reverse_url+name+'/', {'arguments___json':$.toJSON(args), 'kwargs___json':$.toJSON(kwargs)}, cb, 'json');
		}
	}

	$.getFromURL = function(args, data, callback, errback, dataType){
		$.get_url(args.name, args.args, args.kwargs)(function(url) {
			$.getJSON(EMEN2WEBROOT+url, data, callback, errback, dataType)
		})
	}

	$.get_urls = function(args) {
		return function(cb) {
			$.post(reverse_url, {'arg___json':$.toJSON(args)}, cb, 'json');
		}
	}

	$.execute_url = function(name, args, kwargs) {
		return function(cb) {
			$.post(reverse_url+name+'/execute/', {'arguments___json':$.toJSON(args), 'kwargs___json':$.toJSON(kwargs)}, cb, 'json');
		}
	}
	
	// Sort a dict's keys based on integer values
	// >>> var sortable = [];
	// >>> for (var vehicle in maxSpeed)
	//       sortable.push([vehicle, maxSpeed[vehicle]])
	// >>> sortable.sort(function(a, b) {return a[1] - b[1]})
	// [["bike", 60], ["motorbike", 200], ["car", 300],
	// ["helicopter", 400], ["airplane", 1000], ["rocket", 28800]]
	$.sortdict = function(o) {
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
	}

	// Sort a dict's keys based on lower-case string values
	$.sortstrdict = function(o) {
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
	}
	
	// Default error message dialog.
	// This gives the user some feedback if an RPC request fails.
	$.error_dialog = function(title, text, method, data) {
		var error = $('<div title="'+title+'" />');
		error.append('<p>'+text+'</p>');
		var debug = $('<div class="e2-error-debug hide"/>');
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
	}	

	// Tab switching
	// This is pretty old, but works well... 
	$.switchin = function(classname, id) {
		$('#buttons_'+classname+' *').each(function() {
			if (this.id == 'button_'+classname+'_'+id) {
				$(this).addClass('e2l-tab-active');
			} else {
				$(this).removeClass('e2l-tab-active');
			}
		});
		$('#pages_'+classname+' *').each(function() {
			if (this.id == 'page_'+classname+'_'+id) {
				$(this).addClass('e2l-tab-active');
			} else {
				$(this).removeClass('e2l-tab-active');
			}
		});
	}

	///////////////////////////////////////////////////
	// Some simple jquery UI widgets that don't really
	//  fit in any other files..
	///////////////////////////////////////////////////
 
	// View and edit bookmarks
    $.widget("emen2.BookmarksControl", {
		options: {
			mode: null,
			parent: null
		},
				
		_create: function() {
			this.options.parent = this.element.attr('data-parent') || this.options.parent;
			this.options.mode = this.element.attr('data-mode') || this.options.mode;
			this.options.name = this.element.attr('data-name') || this.options.name;			
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
			$.jsonRPC.call('rel.child', [this.options.parent, 1, 'bookmarks'], function(children) {
				children.sort();
				var brec = null;
				if (children.length > 0) {
					brec = children[children.length-1];
				}
				$.jsonRPC.call('record.get', [brec], function(rec) {
					var brecs = [];
					if (rec != null) {
						var brecs = rec['bookmarks'] || [];
					}
					$.jsonRPC.call('record.render', [brecs], function(recnames) {
						$.each(recnames, function(k,v) {
							caches['recnames'][k] = v;
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
				var li = $('<li><a href="'+EMEN2WEBROOT+'/record/'+this+'/">'+caches['recnames'][this]+'</a></li>');
				ul.append(li);
			});			
			// ul.append('<li class="divider"><a href="">Bookmark Manager</a></li>');			
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
			var spinner = $('<img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" class="e2l-spinner hide" alt="Loading" />');
			this.element.append(spinner);
			
			$.jsonRPC.call('rel.child', [this.options.parent, 1, 'bookmarks'], function(children) {
				$.jsonRPC.call('record.get', [children], function(recs) {
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
					$.jsonRPC.call('record.put', [rec], function(updrec) {
						if (pos == -1) {
							var star = $('<img src="'+EMEN2WEBROOT+'/static/images/star-open.png" alt="Add Bookmark" />');
						} else {
							var star = $('<img src="'+EMEN2WEBROOT+'/static/images/star-closed.png" alt="Bookmarked" />');							
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
		// $("#e2l-editbar-record-siblings").EditbarControl({
		// 	show: showsiblings,
		// 	width:300,
		// 	align: 'right',
		// 	cb: function(self) {
		// 		self.popup.empty();
		// 		var sibling = self.element.attr('data-sibling') || rec.name;
		// 		var prev = self.element.attr('data-prev') || null;
		// 		var next = self.element.attr('data-next') || null;
		// 		if ($('#siblings', self.popup).length) {
		// 			return
		// 		}
		// 		var sibs = $('<div class="e2-siblings"><img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /></div>');
		// 		self.popup.append(sibs);
		// 		$.jsonRPC.call("getsiblings", [rec.name, rec.rectype], function(siblings) {
		// 			$.jsonRPC.call("renderview", [siblings, null, "recname"], function(recnames) {
		// 				siblings = siblings.sort(function(a,b){return a-b});
		// 				sibs.empty();
		// 				var prevnext = $('<h4 class="e2l-clearfix e2l-editbar-sibling-prevnext"></h4>');
		// 				if (prev) {
		// 					prevnext.append('<div class=".e2l-float-left"><a href="'+EMEN2WEBROOT+'/record/'+prev+'/#siblings">&laquo; Previous</a></div>');
		// 				}
		// 				if (next) {
		// 					prevnext.append('<div class="e2l-float-right"><a href="'+EMEN2WEBROOT+'/record/'+next+'/#siblings">Next &raquo;</a></div>');
		// 				}					
		// 				sibs.append(prevnext);
		// 
		// 				var ul = $('<ul class="e2l-nonlist"/>');
		// 				$.extend(caches["recnames"], recnames);
		// 				$.each(siblings, function(i,k) {
		// 					if (k != rec.name) {
		// 						// color:white here is a hack to have them line up
		// 						ul.append('<li><a href="'+EMEN2WEBROOT+'/record/'+k+'/?sibling='+sibling+'#siblings">'+(caches["recnames"][k]||k)+'</a></li>');
		// 					} else {
		// 						ul.append('<li class="e2-siblings-active">'+(caches["recnames"][k]||k)+'</li>');
		// 					}
		// 				});
		// 				sibs.append(ul);
		// 			});
		// 		});
		// 	}
		// });	
	});

	// A simple widget for counting words in a text field
	$.widget("emen2.WordCount", {
		options: {
			min: null,
			max: null,
		},	

		_create: function() {
			var self = this;
			this.options.max = this.options.max || parseInt(this.element.attr('data-max'));
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
				this.wc.addClass('e2-wordcount-error');
			} else {
				this.wc.removeClass('e2-wordcount-error')
			}
			this.wc.text(t);	
		}
	});


	// "Drop-down Menu"
    $.widget("emen2.EditbarControl", {
		options: {
			cb: function(self) {},
			bind: true,
			show: false,
			reflow: false,
			align: 'left',
			width: null,
			height: null
		},
				
		_create: function() {
			this.built = 0;
			var self = this;
			this.cachepadding = null;
			this.element.addClass('e2l-tab-active');
			
			if (this.options.bind) {
				$('.label', this.element).click(function(e) {
					e.stopPropagation();
					self.toggle();
				});
			}
			
			if (this.options.show==true) {
				this.toggle();
			}
			
		},
		
		toggle: function() {
			if (this.element.hasClass('e2l-hover')) {
				this.hide();
			} else {
				this.show();
			}
		},
		
		show: function() {
			$('.e2l-editbar .e2l-hover').EditbarControl('hide');
			this.build();
			this.element.addClass('e2l-hover');
			this.options.cb(this);
			this.popup.show();
			if (this.options.reflow) {
				this.cachepadding = $(this.options.reflow).css('padding-top');
				$(this.options.reflow).css('padding-top', this.popup.outerHeight());
			}
			
		},
		
		hide: function() {
			if (!this.built) {return}
			this.popup.hide();
			this.options.cb(this);
			this.element.removeClass('e2l-hover');
			if (this.options.reflow) {
				$(this.options.reflow).css('padding-top', this.cachepadding);
			}
			
		},		
		
		build: function() {
			if (this.built) {
				return
			}
			this.built = 1;			
			
			var pos = this.element.position();

			this.popup = $('.e2l-menu-hidden', this.element);
			if (!this.popup.length) {
				this.popup = $('<div class="e2l-menu-hidden" />');
				this.element.append(this.popup);
			}
			
			if (this.options.width) {
				this.popup.css('width','auto');
				this.popup.css('min-width', this.options.width);
			}
			if (this.options.height) {
				this.popup.height(this.options.height);
			}
			
			if (this.options.align == 'left') {
				this.popup.css('left', -1);
			} else {
				this.popup.css('left', -this.popup.outerWidth()+this.element.outerWidth());
			}			
		}
	});
})(jQuery);
