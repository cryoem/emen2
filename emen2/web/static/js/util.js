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
caches["colors"] = {};


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


////////////////  JSON Utilities ///////////////////


// Default error message dialog.
// This gives the user some feedback if an RPC request fails.
function error_dialog(title, text, method, data) {
	var error = $('<div class="error" title="'+title+'" />');
	error.append('<p>'+text+'</p>');
		
	var debug = $('<div class="debug shadow_top hide"/>');
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
				$('.debug', this).toggle();
			}
		}
	});
}



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
	$.jsonRPC = function(method, data, callback, errback) {
				
		// Wrap these methods
		if (errback == null) {errback = function(){}}
		var eb = function(xhr, textStatus, errorThrown) {
			error_dialog(xhr.statusText, xhr.getResponseHeader('X-Error'), this.jsonRPCMethod, this.data);
			try {errback(xhr, textStatus, xhr)} catch(e) {}
		}
		
		var cb = function(data, status, xhr) {
			if (xhr.status == 0) {
				error_dialog('Connection refused', 'The server may not be responding, or your internet connection may be down.', this.jsonRPCMethod, this.data);
				return
			}
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



////////////////  Button Switching ///////////////////
// This is pretty old, and a simple top level function, but works well... 

function switchbutton(type,id) {
	$(".button_"+type).each(function() {
		var elem=$(this);
		if (this.id != "button_"+type+"_"+id) {
			elem.removeClass("button_active");
			elem.removeClass("button_"+type+"_active");
		} else {
			elem.addClass("button_active");
			elem.addClass("button_"+type+"_active");
		}
	});
}


var switchedin=new Array();

function switchin(classname, id) {
	switchedin[classname]=id;
	switchbutton(classname,id);
	$(".page_"+classname).removeClass("page_active");
	$(".page_"+classname).removeClass("page_"+classname+"_active");	
	$("#page_"+classname+"_"+id).addClass("page_active");
	$("#page_"+classname+"_"+id).addClass("page_"+classname+"_active");
}




////////////////  Notifications ///////////////////


function notify(msg, fade, error) {
	var msg=$('<li>'+msg+'</li>');

	if (error) {
		msg.addClass("error");
	}

	//var killbutton = $('<img src="'+EMEN2WEBROOT+'/static/images/delete.png" alt="Delete" />');
	var killbutton = $('<span>X</span>');
	killbutton.click(function() {
		$(this).parent().fadeOut(function(){
			//fadeoutcallback; in this context, 'this' is li
			$(this).remove();
			});		
	});
	killbutton.addClass("kill");
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

// ian: todo: fix this sometime...
function notify_post(uri,msgs) {
	// var postform = document.createElement("form");
	// postform.method="post" ;
	// postform.action = uri;
	// for (var i=0;i<msgs.length;i++) {
	// 	var note = document.createElement("input") ;
	// 	note.setAttribute("name", "notify"+i) ;
	// 	note.setAttribute("value", msgs[i]);
	// 	postform.appendChild(note) ;
	// }
	// document.body.appendChild(postform);
	// postform.submit();
	window.location = uri;
}




////////////////  New Record page init ///////////////////

function newrecord_init(rec) {
	rec.name = "None";
	var name = rec.name;
	caches["recs"][name] = rec;

	$(".editbar .tools").EditbarHelper({
		width:400,
		show: true,
		reflow: "#rendered"
	});	

	$('#newrecord_save').MultiEditControl({
		name: name,
		show: true
		});
	
	$('#newrecord_permissions').PermissionControl({
		name:name,
		edit:true,
		embed:true
		});

	$('.editable').EditControl({
		name: name
		});

	// Change the text of file upload elements..
	$('.editable_files .label').html('(The record must be saved before files can be attached)');

	$('.editbar .change select').change(function(){
		var parent = $(this).attr('data-parent');
		notify_post(EMEN2WEBROOT+'/record/'+parent+'/new/'+$(this).val()+'/', []);
	});


}



////////////////  Record page init ///////////////////

function record_init(rec, ptest, edit) {
	var name = rec.name;
	caches["recs"][name] = rec;

	// Bind editable widgets
	$('.editbar .edit .label').MultiEditControl({});
	$('.editable').EditControl({});
	// $('.editable_files').FileControl({});

	$('.editbar .edit').EditbarHelper({
		bind: false,
		reflow: '#rendered',
		init: function(self) {
			var addcomment = $('<span>Comments: <input type="text" name="editsummary" value="" /></span>');
			self.popup.append(addcomment);
		}
	});
	
	if (edit) {
		$('.editbar .edit .label').MultiEditControl('event_click');
	}	

	// Permissions editor
	$('.editbar .permissions').EditbarHelper({
		width: 640,
		cb: function(self){
			self.popup.PermissionControl({
				name: name,
				edit: ptest[3],
				embed: true,
				show: true
				});
			}
	});		


	// Attachments editor
	var showattachments = (window.location.hash.search('showattachments'));
	if (showattachments>-1){showattachments=true}

	$('.editbar .attachments').EditbarHelper({
		width:600,
		cb: function(self) {
			self.popup.AttachmentViewerControl({
				name: name,
				edit: ptest[2] || ptest[3],
				embed: true,
				show: true
				});
			},
		show: showattachments
	});		

	// New record editor
	$('.editbar .newrecord').EditbarHelper({
		width:300,
		cb: function(self){
			self.popup.NewRecordSelect({
				name: name,
				embed: true,
				show: true
				});
			}
	});		

	// Relationship editor
	$(".editbar .relationships").EditbarHelper({		
		width: 750,
		cb: function(self){
			self.popup.RelationshipControl({
				root: name,
				edit: true,
				embed: true,
				show: true
				});
			}
	});	
	
	// Tools menu: e.q. common queries
	$(".editbar .tools").EditbarHelper({width:300});	

	// Change rendered view
	$(".editbar .selectview").EditbarHelper({});	

	$('.selectview [data-viewtype]').click(function(){
		var target=$("#rendered");
		var viewtype=$(this).attr('data-viewtype') || 'recname';
		target.attr("data-viewtype", viewtype);
		rebuildviews("#rendered");
	});

	// Additional detailed information
	$(".editbar .creator").EditbarHelper({});

	// Comments and history
	$("#page_comments_comments").CommentsControl({
		name:name,
		edit:ptest[1] || ptest[2] || ptest[3],
		title:"#button_comments_comments"
		});
		
	$("#page_comments_history").HistoryControl({
		name:name,
		title:"#button_comments_history"
		});


	// Simple handler for browsing siblings...
	var showsiblings = (window.location.hash.search('showsiblings'));
	if (showsiblings>-1){showsiblings=true}
	
	$(".editbar .siblings").EditbarHelper({
		show: showsiblings,
		width:250,
		align: 'right',
		init: function(self) {
			var sibling = self.element.attr('data-sibling') || rec.name;
			self.popup.append('<span class="status">Loading...</span>');
			$.jsonRPC("getsiblings", [rec.name, rec.rectype], function(siblings) {
				$.jsonRPC("renderview", [siblings, null, "recname"], function(recnames) {
					siblings = siblings.sort(function(a,b){return a-b});
					$('.status', self.popup).remove();
					var ul = $('<ul class="nonlist" />');
					$.extend(caches["recnames"], recnames);
					$.each(siblings, function(i,k) {
						if (k != rec.name) {
							ul.append('<li><span style="color:white">&raquo; </span><a href="'+EMEN2WEBROOT+'/record/'+k+'/?sibling='+sibling+'#showsiblings">'+(caches["recnames"][k]||k)+'</a></li>');
						} else {
							ul.append('<li>&raquo; '+(caches["recnames"][k]||k)+'</li>');
						}
					});

					self.popup.append(ul);
				});
			});
		}
	});	
}






////////////////  Record Update callbacks ///////////////////


function record_update(rec) {
	if (typeof(rec)=="number") {
		var name = rec;
	} else {
		caches["recs"][rec.name] = rec;
		var name = rec.name;
	}
	rebuildviews('.view[data-name='+name+']');
	$("#page_comments_comments").CommentsControl('rebuild');
	$("#page_comments_history").HistoryControl('rebuild');
	$('.editbar .attachments').AttachmentViewerControl('rebuild');	
}



function rebuildviews(selector) {
	selector = selector || '.view';
	var self = this;
	$(selector).each(function() {
		var elem = $(this);
		var name = parseInt(elem.attr('data-name'));
		var viewtype = elem.attr('data-viewtype');
		var edit = elem.attr('data-edit');
		$.jsonRPC("renderview", {'names':name, 'viewtype': viewtype, 'edit': edit}, function(view) {
			elem.html(view);
			$('.editable', elem).EditControl({});
			//$('.editable_files', elem).FileControl({});
		},
		function(view){}
		);
	})
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
		$.jsonRPC("approveuser",[approve],
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
			},
			function(data) {
				
			}
		);
	};

	if (reject.length > 0) {
		$.jsonRPC("rejectuser",[reject],
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
			},
			function(data) {
				
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
		$.jsonRPC("enableuser",[enable],
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
		$.jsonRPC("disableuser",[disable],
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



///////////////////////////////////////////////////
// Some simple jquery UI widgets that don't really
//  fit in any other files..
///////////////////////////////////////////////////

////////////////  "Drop-down Menu" ///////////////////


(function($) {
    $.widget("ui.EditbarHelper", {
		options: {
			open: function(self) {},
			close: function(self) {},
			cb: function(self) {},
			init: function(self) {},
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
			this.element.addClass('popup');
			
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
			if (this.element.hasClass('active')) {
				this.hide();
			} else {
				this.show();
			}
		},
		
		show: function() {
			$('.editbar .active').EditbarHelper('hide');
			this.build();
			this.element.addClass('active');
			this.options.cb(this);
			this.options.open(this);
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
			this.options.close(this);
			this.element.removeClass('active');

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
			
			this.popup.css('top', this.element.outerHeight()-4);
			
			if (this.options.width) {
				this.popup.width(this.options.width)
			}
			if (this.options.height) {
				this.popup.height(this.options.height);
			}

			this.options.init(this);			
						
			// ugly horrible hack time...
			var uglydiv = $('<div style="position:absolute;background:white" />');
			uglydiv.width(this.element.outerWidth()-5);
			uglydiv.height(4);
			uglydiv.css('top', -4);
			
			if (this.options.align == 'left') {
				this.popup.css('left', -2);
				uglydiv.css('left', 0);
				uglydiv.width(this.element.outerWidth()-3);
			} else {
				this.popup.css('left', -this.popup.outerWidth()+this.element.outerWidth()-2);
				uglydiv.css('right', 0);
			}

			this.popup.append(uglydiv);
		},
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);


///////////////////////////////////////////////////



// This is at the bottom because my editor's syntax highlighting cracks on it..
function escapeHTML(html) {
	var escaped = html;
	var findReplace = [[/&/g, "&amp;"], [/</g, "&lt;"], [/>/g, "&gt;"], [/"/g, "&quot;"]];
	for (var i=0; i < findReplace.length; i++) {
		item = findReplace[i];
    	escaped = escaped.replace(item[0], item[1]);
	}
	return escaped
}
