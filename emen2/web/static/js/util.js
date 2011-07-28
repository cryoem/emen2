// Note: any global methods or variables should be in this file //

////////////////  Global Cache ///////////////////
// cache for items of interest
// the usage pattern is:
//		If I need an item, check the cache. If not found, send an RPC request
//		with a callback that will add it to the cache, then re-enter the method, which will now succeed.
var caches = {};
caches["paramdefs"] = {};
caches["recorddefs"] = {};
caches["displaynames"] = {};
caches["groupnames"] = {};
caches["users"] = {};
caches["groups"] = {};
caches["recs"] = {};
caches["recnames"] = {};
caches["children"] = {};
caches["parents"] = {};


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



(function($){
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
		} else {
			return bytes + " bytes"
		}
	}

	// RPC request. Important!
	$.jsonRPC2 = function(method, data, callback, errback) {
				
		// Wrap these methods
		if (errback == null) {errback = function(){}}
		var eb = function(xhr, textStatus, errorThrown) {
			//console.log(xhr, textStatus, errorThrown);
			if (xhr.status == 0) {
				error_dialog('Connection refused', 'The server may not be responding, or your internet connection may be down.', this.jsonRPCMethod, this.data);
				return
			}
			error_dialog(xhr.statusText, xhr.getResponseHeader('X-Error'), this.jsonRPCMethod, this.data);
			try {
				errback(xhr, textStatus, xhr)
			} catch(e) {}
		}		
		var cb = function(data, status, xhr) {
			callback(data, status, xhr);
		}
				
		$.ajax({
			jsonRPCMethod:method,
		    type: "POST",
		    url: EMEN2WEBROOT+"/json/"+method,
		    data: $.toJSON(data),
		    success: cb,
		    error: eb,
			dataType: "json"
	    });
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
	
})(jQuery)


////////////////  JSON Utilities ///////////////////

// Default error message dialog.
// This gives the user some feedback if an RPC request fails.
function error_dialog(title, text, method, data) {
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



////////////////  Approve / Reject Users ///////////////////
// These should be replaced eventually

function admin_approveuser_form(elem) {
	var approve=[];
	var reject=[];
	var form=$(elem.form);
	$('input:checked', form).each(function() {
		if ($(this).val() == "true") {
			approve.push($(this).attr("name"));
		} else {
			reject.push($(this).attr("name"));
		}
	});

	if (approve.length > 0) {
		$.jsonRPC2("approveuser",[approve],
			function(names) {
				//var names = [];
				//$.each(data, function(){names.push(this.name)});
				notify("Approved users: "+names);
				for (var i=0;i<names.length;i++) {
					$(".userqueue_"+names[i]).remove();
				}
				var count=parseInt($("#admin_userqueue_count").html());
				count -= names.length;
				$("#admin_userqueue_count").html(String(count))
			}
		);
	};

	if (reject.length > 0) {
		$.jsonRPC2("rejectuser",[reject],
			function(names) {
				//var names = [];
				//$.each(data, function(){names.push(this.name)});				
				notify("Rejected users: "+names);
				for (var i=0;i<names.length;i++) {
					$(".userqueue_"+names[i]).remove();
				}
				var count=parseInt($("#admin_userqueue_count").html());
				count -= names.length;
				$("#admin_userqueue_count").html(String(count));							
			}
		);
	};
}




function admin_userstate_form(elem) {
	var enable=[];
	var disable=[];
	var form=$(elem.form);
	$('input:checked', form).each(function() {
		var un=$(this).attr("name");
		var unv=parseInt($(this).val());
		if (unv == 0 &&  admin_userstate_cache[un] != unv) {
			enable.push(un);
		}
		if (unv == 1 &&  admin_userstate_cache[un] != unv) {
			disable.push(un);
		}
	});
	
	if (enable.length > 0) {
		$.jsonRPC2("enableuser",[enable],
			function(data) {
				if (data) {
					notify("Enabled users: "+data);
					for (var i=0;i<data.length;i++) {
						admin_userstate_cache[data[i]]=0;
					}
				}
			}
		)
	}

	if (disable.length > 0) {
		$.jsonRPC2("disableuser",[disable],
			function(data) {
				if (data) {
					notify("Disabled users: "+data);
					for (var i=0;i<data.length;i++) {
						admin_userstate_cache[data[i]]=1;
					}					
				}
			}
		);
	}	
}


////////////////  Button Switching ///////////////////
// This is pretty old, and a simple top level function, but works well... 

function switchin(classname, id) {
	$('#buttons_'+classname+' *').each(function() {
		if (this.id == 'button_'+classname+'_'+id) {
			$(this).addClass('active');
		} else {
			$(this).removeClass('active');
		}
	});
	$('#pages_'+classname+' *').each(function() {
		if (this.id == 'page_'+classname+'_'+id) {
			$(this).addClass('active');
		} else {
			$(this).removeClass('active');
		}
	});
}

////////////////  Notifications ///////////////////


function notify(msg, fade, error) {
	var msg=$('<li class="notify">'+msg+'</li>');

	if (error) {
		msg.addClass("error");
	}

	//var killbutton = $('<img src="'+EMEN2WEBROOT+'/static/images/delete.png" alt="Delete" />');
	var killbutton = $('<span class="floatright">X</span>');
	killbutton.click(function() {
		$(this).parent().fadeOut(function(){
			//fadeoutcallback; in this context, 'this' is li
			$(this).remove();
			});		
	});
	msg.append(killbutton);
	// auto fade if given time value
	//if (!fade) {
	//	setTimeout(function(){msg.fadeOut()},3000)
	//}
	//if (fade > 0) {
	//	setTimeout(function(){msg.fadeOut()},fade*1000)
	//}
	$("#alert").append(msg); //.fadeIn();	
}



///////////////////////////////////////////////////
// Some simple jquery UI widgets that don't really
//  fit in any other files..
///////////////////////////////////////////////////

(function($) {
    $.widget("ui.Bookmarks", {
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
			$.jsonRPC2('getchildren', [this.options.parent, 1, 'bookmarks'], function(children) {
				children.sort();
				var brec = null;
				if (children.length > 0) {
					brec = children[children.length-1];
				}
				$.jsonRPC2('getrecord', [brec], function(rec) {
					var brecs = [];
					if (rec != null) {
						var brecs = rec['bookmarks'] || [];
					}
					$.jsonRPC2('renderview', [brecs], function(recnames) {
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
			var spinner = $('<img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" class="spinner hide" alt="Loading" />');
			this.element.append(spinner);
			
			$.jsonRPC2('getchildren', [this.options.parent, 1, 'bookmarks'], function(children) {
				$.jsonRPC2('getrecord', [children], function(recs) {
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
					$.jsonRPC2('putrecord', [rec], function(updrec) {
						if (pos == -1) {
							var star = $('<img src="'+EMEN2WEBROOT+'/static/images/star-open.png" alt="Add Bookmark" />');
						} else {
							var star = $('<img src="'+EMEN2WEBROOT+'/static/images/star-closed.png" alt="Bookmarked" />');							
						}
						self.element.empty();
						self.element.append(star);
					});
					// // console.log(rec);
					// console.log('updated bookmarks:', rec['bookmarks']);
				});
			});			
		},
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);


$(document).ready(function() {
	$('#bookmarks').hover(
		function() {
			$(this).Bookmarks();
			$(this).Bookmarks('showbookmarks')
		}, 
		function(){}
	);
});



////////////////  "Drop-down Menu" ///////////////////
(function($) {
    $.widget("ui.EditbarHelper", {
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
			this.element.addClass('active');
			
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
			if (this.element.hasClass('hover')) {
				this.hide();
			} else {
				this.show();
			}
		},
		
		show: function() {
			$('.editbar .hover').EditbarHelper('hide');
			this.build();
			this.element.addClass('hover');
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
			this.element.removeClass('hover');
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

			this.popup = $('.hidden', this.element);
			if (!this.popup.length) {
				this.popup = $('<div class="hidden" />');
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
		},
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);

