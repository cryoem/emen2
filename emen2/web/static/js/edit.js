(function($) {
    $.widget("emen2.NewRecordControl", {
		options: {
			// go to new record page instead of popup
			newrecordpage: true,						
			// show selector, show newrecord
			embedselector: true,
			showselector: false,
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
			if (this.options.show || this.options.showselector) {
				this.show();
			}
		},
		
		show: function() {
			if (this.options.showselector) {
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
			this.typicalchld = $('<div><img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /></div>')
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
			ob = $('<div class="controls"><ul class="nonlist"> \
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
					caches["recorddefs"][this.name] = this;
					typicalchld = this.typicalchld;					
				});
				$.jsonRPC.call("getrecorddef", [typicalchld], function(rd2) {
					$.each(rd2, function() {
						caches["recorddefs"][this.name] = this;
					})
					self.build_typicalchld();
				})
			});
		},
		
		build_typicalchld: function() {
			// callback for setting list of typical children
			this.typicalchld.empty();
			var self = this;
			var t = caches["recorddefs"][this.rectype].typicalchld;
			$.each(t, function() {
				try {
					var i = $('<div><input type="radio" name="newrecordselect" value="'+this+'" id="newrecordselect_'+this+'"  /> <label class="clickable" for="newrecordselect_'+this+'">'+caches["recorddefs"][this].desc_short+'</label></div>');
					self.typicalchld.append(i);
				} catch(e) {
					//self.dialog.append('<div><a href="/record/'+self.options.name+'/new/'+this+'/">('+this+')</a></div>');
				}
			});
			var a = $('input[name=newrecordselect]:first', this.typicalchld).attr('checked', 'checked');
		},
		
		build_newrecord: function() {
			var self = this;
			this.newdialog = $('<div><img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /></div>');
			$.jsonRPC.call("newrecord", [this.options.rectype, this.options.parent], function(rec) {	
				rec.name = 'None';
				caches['recs'][rec.name] = rec;
					
				$.jsonRPC.call("renderview", [rec, null, 'defaultview', true], function(data) {
					self.newdialog.empty();

					var content = $('<div></div>');
					content.append(data);
					self.newdialog.append(content);
					$('.editable', content).EditControl({
						name:'None'
					});

					var controls = $('<div></div>');
					self.newdialog.append(controls);
					controls.MultiEditControl({
						name: 'None',
						show: true,
						cb_save: function(recs){
							self.newdialog.dialog('close');
							self.options.cb_save(recs);
						}
					});

				});
			});
					
			this.element.append(this.newdialog);
			this.newdialog.attr("title", "New "+this.options.rectype+", child of "+caches['recnames'][this.options.parent]);

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
			reload: false,
			newrecordpage: false,
			cb_save: function(recs){}
		},
				
		_create: function() {
			// Parse options from element attributes if available
			this.options.name = this.options.name || parseInt(this.element.attr("data-name"));
			// jQuery selector for this multi-edit control to activate
			this.options.selector = this.options.selector || '.editable[data-name='+this.options.name+']';
			
			this.built = 0;
			this.backup = this.element.html();

			// this.element.click(function(e){self.event_click(e)});
			var self = this;
			this.element.click(function(e){self.event_click()});
			
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
				if (caches['recs'][names_toget[i]] == null) {
					names.push(names_toget[i]);
				}
			}			
			var params = [];
			var params_toget = $.makeArray($(this.options.selector).map(function(){return $(this).attr("data-param")}));			
			for (var i=0;i < params_toget.length;i++) {
				if (caches['paramdefs'][params_toget[i]] == null) {
					params.push(params_toget[i]);
				}
			}

			// Request records and params; update caches; show widget on callback
			$.jsonRPC.call("getrecord", [names], function(recs) {
				$.each(recs, function(k,v) {
					caches["recs"][v.name] = v;
				});
				$.jsonRPC.call("getparamdef", [params], function(paramdefs) {
					$.each(paramdefs, function(k,v) {
						caches["paramdefs"][v.name] = v;
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
			this.controls = $('<div class="controls" />');

			var spinner = $('<img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" class="spinner hide" alt="Loading" />');
			this.controls.append(spinner);

			var save = $('<input class="save" type="submit" name="save" value="Save" />');
			save.click(function(e) {self.save()});
			this.controls.append(save);
			
			if (this.options.name != "None") {
				var cancel = $('<input class="cancel" type="button" value="Cancel" />').bind("click", function(e) {e.stopPropagation();self.hide()});
				this.controls.append(cancel);
			}			
			this.element.after(this.controls);
		},
		
		rebind_save: function() {
			var self = this;
			var t = $('input[name=save]', this.controls);
			t.val("Retry...");
			t.one(function(e) {self.save()});
		},
	
		show: function() {
			this.build();
			$(this.options.selector).each(function() {
				var t = $(this);
				t.EditControl({});
				t.EditControl('hide');
				t.EditControl('show', 0);
			});
			this.element.hide();
			this.controls.show();
			this.element.EditbarControl('show');
		},
	
		hide: function() {
			$(this.options.selector).EditControl('hide');
			this.controls.hide();
			this.element.show();
			this.element.EditbarControl('hide');			
		},
		
		save: function() {
			var changed = {};
			var self = this;

			$('input[name=save]', this.controls).val('Saving..');

			var comment = $('input[name=editsummary]').val();

			$(this.options.selector).each(function() {
				var t = $(this);
				try {
					var name = t.EditControl('getname');
					var value = t.EditControl('getval');
					var param = t.EditControl('getparam');				
					if (!changed[name]) {changed[name]={}}
					changed[name][param] = value;
					if (comment) {changed[name]['comments'] = comment}
				} catch(e) {
				}
			});
			
			$('input[name=save]', this.controls).val('Saving...');
			$('.spinner', this.controls).show();

			// process changed
			var updated = [];
			$.each(changed, function(k,v) {
				if (k == 'None') {
					v = self.applynew(v);
				}
				v['name'] = k;
				updated.push(v);
			});

			$.jsonRPC.call("putrecord", [updated], function(recs) {
				if (self.options.reload) {
					window.location = window.location
					return
				} else if (self.options.newrecordpage) {
					window.location = EMEN2WEBROOT + '/record/' + recs[0].name + '/';
					return
				}
				$('.spinner', self.controls).hide();
				$('input[name=save]', self.controls).val('Save');
				$.each(recs, function() {
					record_update(this);
				});
				self.hide();
				self.options.cb_save(recs);
			}, function(e) {
				$('input[name=save]', self.controls).val('Retry');
				$('.spinner', self.controls).hide();
				default_errback(e, function(){})
			});
		},

		applynew: function(newrec) {
			var rec = caches['recs']['None'];
			var newrec2 = {};
			$.each(rec, function(k,v) {newrec2[k] = v});
			$.each(newrec, function(k,v) {newrec2[k] = v});
			if ($('#newrecord_permissions').length) {
				newrec2['permissions'] = $('#newrecord_permissions').PermissionControl('getusers');
			}
			if ($('#newrecord_permissions').length) {
				newrec2['groups'] = $('#newrecord_permissions').PermissionControl('getgroups');
			}
			return newrec2
		}
	});

	$.widget('emen2.Edit')

	// Basic Edit Control
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

			if (caches['recs'][this.options.name] == null) {
				$.jsonRPC.call("getrecord", [this.options.name], function(rec) {
					caches["recs"][rec.name] = rec;
					self.show();
				});
				return
			}

			if (!caches["paramdefs"][this.options.param]) {
				$.jsonRPC.call("getparamdef", [this.options.param], function(paramdef){
					caches["paramdefs"][paramdef.name]=paramdef;
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
			this.dialog = $('<div class="e2-layout-edit" />');
			this.build_control();
		},		

		build_control: function() {
			// Build the editing control			
		},

		rebind_save: function() {
			var self = this;
		},

		save: function() {
			var self = this;
			var p = {}
			p[this.options.param] = this.getval();
			$.jsonRPC.call("putrecordvalues", [this.options.name, p], function(rec) {
				record_update(rec);
				self.hide();
			}, function(e) {
				error_dialog(e.statusText, e.getResponseHeader('X-Error'), this.jsonRPCMethod, this.data);
				self.rebind_save();
			});
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
			return null
		},
		
		cacheval: function() {
			return caches["recs"][this.options.name][this.options.param];
		},
		
		cachepd: function() {
			return caches["paramdefs"][this.options.param];	
		},
	});

	// Basic String editing widget
    $.widget("emen2.Edit_string", $.emen2.EditControl, {
		build_control: function() {
			this.dialog.append('<input size="20" type="text" name="value" value="'+this.cacheval()+'" />');
			this.build_units();		
		},
		
		build_units: function() {
			var property = this.cachepd().property;
			var defaultunits = this.cachepd().defaultunits;
			if (!property) { return }

			var units = $('<select name="units"></select>');
			for (var i=0;i < valid_properties[property][1].length;i++) {
				var sel = "";
				if (defaultunits == valid_properties[property][1][i]) sel = "selected";
				units.append('<option '+sel+'>'+valid_properties[property][1][i]+'</option>');
			}
			this.dialog.append(units);
		},

		getval: function() {
			var ret = $('[name=value]', this.dialog).val() || '';
			var units = $('select[name=units]', this.dialog).val() || '';
			if (!ret) {return null}
			return ret + units
		}
	});
	
	// Single-choice widget
    $.widget("emen2.Edit_choice", $.emen2.EditControl, {
		build_control: function() {
			// Get the choices and the current value
			var choices = this.cachepd().choices;
			var editw = $('<select name="value"></select>');
			for (var i=0;i<choices.length;i++){
				var choice = $('<option value="'+choices[i]+'" />');
				if (choices[i]==this.cacheval()) {choice.attr('selected', true)}
				editw.append(choice);
			}
			this.dialog.append(editw);
		}
	});

	// True-False
    $.widget("emen2.Edit_boolean", $.emen2.EditControl, {
		build_control: function() {
			var editw = $('<select name="value"><option selected="selected"></option><option>True</option><option>False</option></select>');
			if (this.cacheval() === true) {
				editw.val("True");
			} else if (this.cacheval() === false) {
				editw.val("False");
			}
			this.dialog.append(editw);
		}
	});	
	
	// User editor
    $.widget("emen2.Edit_user", $.emen2.EditControl, {
		build_control: function() {
			this.dialog.append('<div>User</div>');	
		}	
	});	

	// Text editor
    $.widget("emen2.Edit_text", $.emen2.EditControl, {
		build_control: function() {
			this.dialog.append('<textarea name="value" cols="80" rows="10">'+this.cacheval()+'</textarea>');	
			this.dialog.addClass('e2-layout-fw');			
		}	
	});
	
	// Date controls
    $.widget("emen2.Edit_datetime", $.emen2.EditControl, {
		build_control: function() {
			this.dialog.append('<input name="value" size="18" type="text" value="'+this.cacheval()+'" />');
		}	
	});		
	
    $.widget("emen2.Edit_date", $.emen2.EditControl, {
		build_control: function() {
			this.dialog.append('<input name="value" size="10" type="text" value="'+this.cacheval()+'" />');
		}	
	});
	
    $.widget("emen2.Edit_time", $.emen2.EditControl, {
		build_control: function() {
			this.dialog.append('<input name="value" size="10" type="text" value="'+this.cacheval()+'" />');
		}	
	});	
		
})(jQuery);


