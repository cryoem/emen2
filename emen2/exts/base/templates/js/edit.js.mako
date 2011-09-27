(function($) {
    $.widget("emen2.NewRecordControl", {
		options: {
			// go to new record page instead of popup
			newrecordpage: true,						
			// show selector, show newrecord
			embedselector: true,
			selector: false,
			show: false,
			embed: false,
			// new record options
			rectype: null,
			parent: null,
			private: false,
			copy: false,
			// callbacks
			cb_save: function(recs) {
				window.location = EMEN2WEBROOT + '/record/' + recs[0].name;
			},
			cb_reload: function(recs) {
				window.location = window.location;
			}
			
		},
				
		_create: function() {
			this.typicalchld = [];
			this.built = 0;			
			this.built_selector = false;
			this.options.rectype = this.element.attr('data-rectype') || this.options.rectype;
			this.options.parent = this.element.attr('data-parent') || this.options.parent;
			this.options.private = this.element.attr('data-private') || this.options.private;
			this.options.copy = this.element.attr('data-copy') || this.options.copy;
			this.options.embed = this.element.attr('data-embed') || this.options.embed;			
			
			var self=this;
			if (!this.options.embed) {
				this.element.click(function(e){self.show(e)});
			}			
			if (this.options.show) { // || this.options.showselector) {
				this.show();
			}
		},
		
		show: function() {
			if (this.options.selector) {
				this.build_selector();
			} else {
				if (this.options.newrecordpage) {
					this.action();
				} else {
					this.build_newrecord();
				}
			}	
		},
		
		action: function() {
			var self = this;
			if (this.options.newrecordpage) {
				var link = EMEN2WEBROOT + '/record/'+this.options.parent+'/new/'+this.options.rectype+'/';
				if (this.options.copy && this.options.private) {
					link = link + '?private=1&amp;copy=1';
				} else if (this.options.copy) {
					link = link + '?copy=1';
				} else if (this.options.private) {
					link = link + '?private=1';
				}
				window.location = link;
			} else {
				this.build_newrecord();
			}
		},
		
		build_selector: function() {
			var self = this;
			if (this.built_selector) {
				return
			}
			this.built_selector = true;
			this.selectdialog = $('<div />');

			this.typicalchld = $('<div/>');
			this.typicalchld.append($.spinner())
			
			this.selectdialog.append('<h4>New Record</h4>', this.typicalchld);

			// new record rectype
			var o = $('<div><input type="radio" name="newrecordselect" data-other="1" id="newrecordselectother" /> <label for="newrecordselectother">Other:</label></div>')
			var s = $('<input type="text" name="newrecordselectother" value="" size="8" />');
			s.FindControl({'keytype':'recorddef'});
			s.click(function() {
				$("#newrecordselectother").attr('checked', 'checked');
			});
			o.append(s);
			this.selectdialog.append(o);

			// options
			ob = $('<div class="e2l-controls"><ul class="e2l-nonlist"> \
				<li><input type="checkbox" name="private" id="private" /> <label for="private">Private</label></li> \
				<li><input type="checkbox" name="copy" id="copy" /> <label for="private">Copy values</label></li>  \
				</ul></div>');
				
			if (this.options.private) {
				$("input[name=private]", ob).attr("checked", "checked");
			}
			if (this.options.copy) {
				$("input[name=copy]", ob).attr("checked", "checked");
			}

			$('input[name=private]', ob).click(function() {
				var value = $(this).attr('checked');
				self.options.private = value;
			});
			$('input[name=copy]', ob).click(function() {
				var value = $(this).attr('checked');
				self.options.copy = value;
			});

			// action button
			var b = $('<input type="button" value="New record" />');			
			b.click(function() {
				var b = $('input[name=newrecordselect]:checked', this.selectdialog);
				if (b.attr('data-other')) {
					b = $('input[name=newrecordselectother]').val();
				} else {
					b = b.val();
				}
				if (!b) {return}
				self.options.rectype = b;
				self.action();
			});
			ob.append(b);			
			this.selectdialog.append(ob);

			// embed or popup selector dialog
			if (this.options.embedselector) {
				this.element.append(this.selectdialog);
			} else {			
				var pos = this.element.offset();
				this.selectdialog.attr("title", "New Record");
				this.selectdialog.dialog({
					position: [pos.left, pos.top+this.element.outerHeight()],
					autoOpen: true
				});
			}
			
			// run a request to get the recorddef display names
			$.jsonRPC.call("findrecorddef", {'record':[this.options.parent]}, function(rd) {
				var typicalchld = [];
				$.each(rd, function() {
					self.rectype = this.name;
					caches['recorddef'][this.name] = this;
					typicalchld = this.typicalchld;					
				});
				$.jsonRPC.call("getrecorddef", [typicalchld], function(rd2) {
					$.each(rd2, function() {
						caches['recorddef'][this.name] = this;
					})
					self.build_typicalchld();
				})
			});
		},
		
		build_typicalchld: function() {
			// callback for setting list of typical children
			this.typicalchld.empty();
			var self = this;
			var t = caches['recorddef'][this.rectype].typicalchld;
			$.each(t, function() {
				try {
					var i = $('<div><input type="radio" name="newrecordselect" value="'+this+'" id="newrecordselect_'+this+'"  /> <label class="e2l-a" for="newrecordselect_'+this+'">'+caches['recorddef'][this].desc_short+'</label></div>');
					self.typicalchld.append(i);
				} catch(e) {
					//self.dialog.append('<div><a href="/record/'+self.options.name+'/new/'+this+'/">('+this+')</a></div>');
				}
			});
			var a = $('input[name=newrecordselect]:first', this.typicalchld).attr('checked', 'checked');
		},
		
		build_newrecord: function() {
			var self = this;
			this.newdialog = $('<div/>');
			this.newdialog.append($.spinner());
			
			$.jsonRPC.call('getrecorddef', [this.options.rectype], function(rd) {
				caches['recorddef'][rd.name] = rd;
				
				$.jsonRPC.call("newrecord", [self.options.rectype, self.options.parent], function(rec) {	
					rec.name = 'None';
					caches['record'][rec.name] = rec;
					
					$.jsonRPC.call("renderview", [rec, null, 'defaultview', true], function(data) {
						self.newdialog.empty();

						var header = $('<p style="background:#eee;padding:10px;border:solid 1px #ccc"><strong>Description:</strong></p>');
						header.append(rd.desc_long);
						self.newdialog.append(header);

						var content = $('<form id="newrecord" data-name="None" method="post" action="'+EMEN2WEBROOT+'/record/'+self.options.parent+'/new/'+rd.name+'">');
						content.append(data);
						self.newdialog.append(content);
						$('.e2l-editable', content).EditControl({
							name:'None'
						});

						var controls = $('<div></div>');
						self.newdialog.append(controls);
						$('#newrecord').MultiEditControl({show: true});

					});
				});
			});
					
			this.element.append(this.newdialog);
			var rd = caches['recorddef'][this.options.rectype] || {};
			this.newdialog.attr("title", "New "+(rd.desc_short || this.options.rectype)+", child of "+(caches['recnames'][this.options.parent] || this.options.parent));

			// popup or embed
			if (!this.options.embed) {
				this.newdialog.dialog({
					width: 800,
					height: $(window).height()*0.8,
					modal: true,
					autoOpen: true
				});
			}
		}
	});


	// This control acts on groups of EditControls, editing one or more records.
    $.widget("emen2.MultiEditControl", {		
		options: {
			show: false,
			name: null,
			selector: null,
			controls: false,
			cb_save: function(recs){}
		},
				
		_create: function() {
			var self = this;
			this.built = 0;

			// Parse options from element attributes if available
			this.options.name = this.options.name || parseInt(this.element.attr("data-name"));
			
			// jQuery selector for this multi-edit control to activate
			this.options.selector = this.options.selector || '.e2l-editable[data-name='+this.options.name+']';

			// Bind click
			// this.element.click(function(e){self.event_click()});			
			if (this.options.show) {
				this.event_click();
			}			
		},
		
		event_click: function(e) {
			// Gather records and params to request from server..
			var self=this;
			var names = [];
			var names_toget = $.makeArray($(this.options.selector).map(function(){return $(this).attr("data-name")}));
			for (var i=0;i < names_toget.length;i++) {
				if (caches['record'][names_toget[i]] == null) {
					names.push(names_toget[i]);
				}
			}			
			var params = [];
			var params_toget = $.makeArray($(this.options.selector).map(function(){return $(this).attr("data-param")}));			
			for (var i=0;i < params_toget.length;i++) {
				if (caches['paramdef'][params_toget[i]] == null) {
					params.push(params_toget[i]);
				}
			}
			// Request records and params; update caches; show widget on callback
			$.jsonRPC.call("getrecord", [names], function(recs) {
				$.each(recs, function(k,v) {
					caches['record'][v.name] = v;
				});
				$.jsonRPC.call("getparamdef", [params], function(paramdefs) {
					$.each(paramdefs, function(k,v) {
						caches['paramdef'][v.name] = v;
					});
					self.show();
				});
			});
		},

		build: function() {
			if (this.built) {
				return
			}
			this.built = 1;
			var self = this;			
			
			// Build controls
			this.controls = $('<div class="e2l-controls" />');
			this.controls.append($.spinner());

			if (!this.options.controls) {return}			
			
			var save = $('<input type="submit" name="save" class="e2l-save" value="Save" />');
			save.click(function(e) {self.save()});
			this.controls.append(save);

			if (this.options.name != "None") {
				var cancel = $('<input type="button" value="Cancel" />').bind("click", function(e) {e.stopPropagation();self.hide()});
				this.controls.append(cancel);
			}
			this.element.after(this.controls);
		},
		
		show: function() {
			this.build();
			$(this.options.selector).each(function() {
				var t = $(this);
				t.EditControl({});
				t.EditControl('hide');
				t.EditControl('show');
			});
			this.element.hide();
			this.controls.show();
		},
	
		hide: function() {
			$(this.options.selector).EditControl('hide');
			this.controls.hide();
			this.element.show();
		},
		
		save: function() {
			if (this.options.form) {
				$(this.options.form).submit();
				return
			}
		}
		
		// save: function() {
		// 	var changed = {};
		// 	var self = this;
		// 
		// 	$('input[name=save]', this.controls).val('Saving..');
		// 
		// 	var comment = $('input[name=editsummary]').val();
		// 
		// 	$(this.options.selector).each(function() {
		// 		var t = $(this);
		// 		try {
		// 			var name = t.EditControl('getname');
		// 			var value = t.EditControl('getval');
		// 			var param = t.EditControl('getparam');				
		// 			if (!changed[name]) {changed[name]={}}
		// 			changed[name][param] = value;
		// 			if (comment) {changed[name]['comments'] = comment}
		// 		} catch(e) {
		// 		}
		// 	});
		// 	
		// 	$('input[name=save]', this.controls).val('Saving...');
		// 	$('.e2l-spinner', this.controls).show();
		// 
		// 	// process changed
		// 	var updated = [];
		// 	$.each(changed, function(k,v) {
		// 		if (k == 'None') {
		// 			v = self.applynew(v);
		// 		}
		// 		v['name'] = k;
		// 		updated.push(v);
		// 	});
		// 
		// 	$.jsonRPC.call("putrecord", [updated], function(recs) {
		// 		if (self.options.reload) {
		// 			window.location = window.location
		// 			return
		// 		} else if (self.options.newrecordpage) {
		// 			window.location = EMEN2WEBROOT + '/record/' + recs[0].name + '/';
		// 			return
		// 		}
		// 		$('.e2l-spinner', self.controls).hide();
		// 		$('input[name=save]', self.controls).val('Save');
		// 		$.each(recs, function() {
		// 			$.record_update(this);
		// 		});
		// 		self.hide();
		// 		self.options.cb_save(recs);
		// 	}, function(e) {
		// 		$('input[name=save]', self.controls).val('Retry');
		// 		$('.e2l-spinner', self.controls).hide();
		// 		default_errback(e, function(){})
		// 	});
		// },
		// 
		// applynew: function(newrec) {
		// 	var rec = caches['record']['None'];
		// 	var newrec2 = {};
		// 	$.each(rec, function(k,v) {newrec2[k] = v});
		// 	$.each(newrec, function(k,v) {newrec2[k] = v});
		// 	if ($('#newrecord_permissions').length) {
		// 		newrec2['permissions'] = $('#newrecord_permissions').PermissionControl('getusers');
		// 	}
		// 	if ($('#newrecord_permissions').length) {
		// 		newrec2['groups'] = $('#newrecord_permissions').PermissionControl('getgroups');
		// 	}
		// 	return newrec2
		// }
	});

	// Edit Control Wrapper
	// This class create the actual editing control
	// It will grab the ParamDef if it isn't cached
    $.widget("emen2.EditControl", {
		options: {
			show: false,
			name: null,
			param: null
		},
				
		_create: function() {
			// Parse options from element attributes if available		
			this.options.param = this.options.param || this.element.attr("data-param");
			this.options.name = this.options.name || parseInt(this.element.attr("data-name"));

			// Record name is null or empty, editing a new record..
			if (isNaN(this.options.name)) this.options.name = "None";
			
			this.built = 0;
			this.find_cache = {};

			if (this.options.show) {
				this.show();
			}
		},
	
		show: function(showcontrols) {
			if (showcontrols==null) {showcontrols=1}
			var self = this;

			// Get the Record if it isn't cached
			if (caches['record'][this.options.name] == null) {
				$.jsonRPC.call("getrecord", [this.options.name], function(rec) {
					caches['record'][rec.name] = rec;
					self.show();
				});
				return
			}
			// Get the ParamDef if it isn't cached
			if (!caches['paramdef'][this.options.param]) {
				$.jsonRPC.call("getparamdef", [this.options.param], function(paramdef){
					caches['paramdef'][paramdef.name]=paramdef;
					self.show(showcontrols);
				});
				return
			}

			// Build the control
			this.build();
			
			// .. hide the original element and show the control
			this.element.hide();
			this.dialog.show();
		},

		hide: function() {
			if (!this.built) {
				return
			}
			// Hide the control and show the original element
			this.dialog.hide();
			this.element.show();
		},
		
		build: function() {
			if (this.built){return}
			this.built = 1;
			this.dialog = $('<div class="e2l-edit" />');
			this.element.after(this.dialog);

			// Find the right editor...
			var pd = this.cachepd();
			var cls;
			if (pd.controlhint) {
				cls = $.emen2edit[pd.controlhint];
			} else if ($.emen2edit[pd.vartype]) {
				cls = $.emen2edit[this.controlhints(pd.vartype)];
			}
			if (!cls) {
				cls = $.emen2edit['string'];
			}
			this.editor = new cls(this.options, this.dialog);
		},		

		save: function() {
			var self = this;
			var p = {}
			p[this.options.param] = this.getval();
			$.jsonRPC.call("putrecordvalues", [this.options.name, p], function(rec) {
				$.record_update(rec);
				self.hide();
			}, function(e) {
				$.error_dialog(e.statusText, e.getResponseHeader('X-Error'), this.jsonRPCMethod, this.data);
			});
		},
		
		controlhints: function(vt) {
			var defaults = {
				'html':'text',
				'time':'datetime',
				'date':'datetime',
				'history':'none',
				'uri':'none',
				'recid':'none',
				'acl':'none'
			}
			return defaults[vt] || vt;			
		},		
		
		getname: function() {
			// Return the record name
			return this.options.name
		},

		getparam: function() {
			// Return the param name
			return this.options.param
		},		

		getval: function() {
			//return null;
			return this.editor.getval();
		},
		
		cacheval: function() {
			return caches['record'][this.options.name][this.options.param];
		},
		
		cachepd: function() {
			return caches['paramdef'][this.options.param];	
		}
	});

	// Assumes the Record and ParamDef are already cached
	$.widget('emen2.EditBase', {
		options: {
			name: null,
			param: null,
		},				

		_create: function() {
			this.build_control();
		},
		
		build_control: function() {
			var self = this;
			var pd = this.cachepd();
			var val = this.cacheval();
			this.element.empty();
			if (this.options.block) {
				this.element.addClass('e2l-fw');
			}			
			if (pd.iter) {
				this.element.append(this.build_iter(val));
			} else {
				this.element.append(this.build_item(val));
			}			
		},
		
		build_iter: function(val) {
			val = val || [];
			var ul = $('<ul class="e2-edit-iterul" />');
			for (var i=0;i<val.length;i++) {
				var control = this.build_item(val[i]);
				ul.append($('<li />').append(control));
			}
			this.element.addClass('e2l-fw');
			return $('<div />').append(ul, this.build_add());
		},
		
		build_item: function(val) {
			var pd = this.cachepd();
			return '<input type="text" name="'+pd.name+'" value="'+(val || '')+'" />';
		},
		
		build_add: function(e) {
			return $('<input type="button" value="+" />');
		},
		
		getval: function() {
			return null
		},
		
		cacheval: function() {
			var rec = caches['record'][this.options.name]
			if (!rec) {return null}
			return rec[this.options.param];
		},
		
		cachepd: function() {
			var pd = caches['paramdef'][this.options.param];
			return pd
		}		
	});


	// Not editable
    $.widget("emen2edit.none", $.emen2.EditBase, {
		build_control: function() {
			this.element.append('Not Editable');
		}
	});

	// Basic String editing widget
    $.widget("emen2edit.string", $.emen2.EditBase, {
		build_item: function(val) {
			var self = this;
			var pd = this.cachepd();
			var container = $('<span class="e2-edit-container" />');
			if (pd.property) {
				var realedit = '<input class="e2-edit-val" type="hidden" name="'+pd.name+'" value="'+(val || '')+'" />';
				var editw = $('<input class="e2-edit-unitsval" type="text" value="'+(val || '')+'" />');
				var units = this.build_units();
				editw.change(function(){self.sethidden()});
				units.change(function(){self.sethidden()});
				container.append(editw, units, realedit);
			} else {
				container.append('<input type="text" name="'+pd.name+'" value="'+(val || '')+'" />');
			}
			return container
		},

		build_units: function() {
			var property = this.cachepd().property;
			var defaultunits = this.cachepd().defaultunits;
			var units = $('<select class="e2-edit-units"></select>');
			for (var i=0;i < valid_properties[property][1].length;i++) {
				var sel = "";
				if (defaultunits == valid_properties[property][1][i]) sel = "selected";
				units.append('<option '+sel+'>'+valid_properties[property][1][i]+'</option>');
			}
			return units
		},

		sethidden: function() {
			var self = this;
			$('.e2-edit-container', this.element).each(function(){
				var unitsval = $('.e2-edit-unitsval', this).val();
				var units = $('.e2-edit-units', this).val();
				$('.e2-edit-val', this).val(unitsval+' '+units);
			});
		}
		
	});
	
	// Single-choice widget
    $.widget("emen2edit.choice", $.emen2.EditBase, {
		build_item: function(val) {
			var choices = this.cachepd().choices;
			var editw = $('<select name="'+this.cachepd().name+'"></select>');
			editw.append('<option></option>');
			for (var i=0;i<choices.length;i++){
				var choice = $('<option value="'+choices[i]+'">'+choices[i]+'</option>');
				if (choices[i]==val) {choice.attr('selected', true)}
				editw.append(choice);
			}
			return editw
		}
	});

	// True-False
    $.widget("emen2edit.boolean", $.emen2.EditBase, {
		build_item: function(val) {
			var editw = $('<select name="'+this.cachepd().name+'"><option selected="selected"></option><option>True</option><option>False</option></select>');
			if (val === true) {
				editw.val("True");
			} else if (val === false) {
				editw.val("False");
			}
			return editw
		}
	});	
	
	// User editor
    $.widget("emen2edit.user", $.emen2.EditBase, {
		build_iter: function(val) {
			val = val || [];
			var ul = $('<div class="e2-edit-iterul e2l-clearfix" />');
			for (var i=0;i<val.length;i++) {
				var control = this.build_item(val[i]);
				ul.append(control);
			}
			this.element.addClass('e2l-fw');
			return $('<div />').append(ul, this.build_add());
		},

		build_item: function(val) {
			var d = $('<div />');
			d.InfoBox({
				'keytype': 'user',
				'name': val,
				'deleteable': true
			});
			d.append('<input type="hidden" name="'+this.options.param+'" value="'+val+'" />');
			d.click(function() {
				$(this).remove();
			})
			return d
			
			// var editw = $('<span class="e2-edit-container"></span>');
			// editw.append('User: '+val);
			// editw.append('<input type="hidden" name="'+this.cachepd().name+'" value="'+val+'" />');
			// return editw
		},
		
		sethidden: function() {
			var self = this;
			$('.e2-edit-container', this.element).each(function(){
				$('.e2-edit-val', this).val('');
			});
		},

		build_add: function(e) {
			var self = this;
			var button = $('<input type="button" value="+" />');
			button.FindControl({
				keytype: 'user',
				minimum: 2,
				cb: function(test, name){self.add_item(name)}
			});
			return button			
		},

		add_item: function(val) {
			var ul = $('ul.e2-edit-iterul', this.element);
			ul.append($('<li />').append(this.build_item(val)))
		}
	});	

	// Text editor
    $.widget("emen2edit.text", $.emen2.EditBase, {
		build_item: function(val) {
			var editw = $('<textarea style="width:100%" name="'+this.cachepd().name+'" rows="20">'+(val || '')+'</textarea>');
			this.element.addClass('e2l-fw');
			return editw
		}	
	});
	
	// Binary Editor
    $.widget("emen2edit.binary", $.emen2.EditBase, {
		build_item: function(val) {
			return 'Edit Binary...'
		},
		sethidden: function() {
			var self = this;
			$('.e2-edit-container', this.element).each(function(){
				$('.e2-edit-val', this).val('');
			});
		}
	});	
	
	// Group Editor
    $.widget("emen2edit.groups", $.emen2.EditBase, {
		build_item: function(val) {
			return 'Edit Groups...'
		},
		sethidden: function() {
			var self = this;
			$('.e2-edit-container', this.element).each(function(){
				$('.e2-edit-val', this).val('');
			});
		}
	});	
	
	// Comments
    $.widget("emen2edit.comments", $.emen2.EditBase, {
		build_item: function(val) {
			return 'Edit Comments...'
		}
	});
	
	// Coordinate
    $.widget("emen2edit.coordinate", $.emen2.EditBase, {
		build_item: function(val) {
			return 'Edit Groups...'
		}
	});	

	// Coordinate
    $.widget("emen2edit.percent", $.emen2.EditBase, {
		build_item: function(val) {
			return 'Edit Percent...'
		},
		sethidden: function() {
			var self = this;
			$('.e2-edit-container', this.element).each(function(){
				$('.e2-edit-val', this).val('');
			});
		}		
	});	
	
	// Rectype
    $.widget("emen2edit.rectype", $.emen2.EditBase, {
		build_item: function(val) {
			return 'Edit rectype...'
		}
	});	

	// Datetime
    $.widget("emen2edit.datetime", $.emen2.EditBase, {
		build_item: function(val) {
			return 'Edit datetime...'
		}
	});
	
	// WIDGET HINTS
	$.widget('emen2edit.checkbox', $.emen2.EditBase, {
		build_item: function(val) {
			return '<input type="checkbox" />'
		}
	});
	
	// Radio buttons
    $.widget("emen2edit.radio", $.emen2.EditBase, {
		build_item: function(val) {
			var self = this;
			var rec = caches['record'][self.option.name];
			var val = ''; //rec[this.options.name];
			var pd = this.cachepd();
			var choices = pd.choices || [];
			var ul = $('<ul class="e2l-nonlist" />');
			$.each(choices, function() {
				// grumble..
				var rand = Math.ceil(Math.random()*10000000);
				var id = 'e2-edit-radio-'+rand;
				var input = '<input type="radio" name="'+self.options.param+'" value="'+this+'" id="'+id+'"/><label for="'+id+'">'+this+'</label>';
				ul.append($('<li/>').append(input));
			});
			return ul
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
