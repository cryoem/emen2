(function($) {
	
	
	// Comments Widget
	
    $.widget("emen2.CommentsControl", {
		options: {
			name: null,
			edit: false,
			title: null,
			historycount: false,
			commentcount: false
		},
				
		_create: function() {
			this.built = 0;
			this.element.addClass('e2-comments');
			this.build();
		},
		
		rebuild: function() {
			this.built = 0;
			this.build();
		},
	
		build: function() {	
			var self = this;	
			if (this.built) {return}

			this.comments = caches['record'][this.options.name]["comments"].slice() || [];
			this.history = caches['record'][this.options.name]['history'].slice() || [];			
			this.comments.push([caches['record'][this.options.name]['creator'], caches['record'][this.options.name]['creationtime'], 'Record created']);

			// Check to see if we need any users or parameters
			var users = [];
			$.each(this.comments, function(){users.push(this[0])})
			$.each(this.history, function(){users.push(this[0])})
			users = $.map(users, function(user){if (!caches['user'][user]){return user}})

			var params = [];
			$.each(this.history, function(){
				if (!caches['paramdef'][this[2]]) {
					params.push(this[2])
				}
			});

			// If we need users or params, fetch them.
			// Todo: find a nice way to chain these together, server side
			if (users && params) {

				$.jsonRPC.call('getuser', [users], function(users) {
						$.each(users, function() {caches['user'][this.name] = this});
						$.jsonRPC.call('getparamdef', [params], function(params) {
							$.each(params, function() {caches['paramdef'][this.name] = this});
							self._build();
						});
					});
			
			} else if (params.length) {

				$.jsonRPC.call("getparamdef", [params], 
					function(params) {
						$.each(params, function() {caches['paramdef'][this.name] = this});
						self._build();
					});
					
			} else if (users.length) {

				$.jsonRPC.call("getuser", [users], 
					function(users) {
						$.each(users, function() {caches['user'][this.name] = this});
						self._build();
					});

			} else {
				self._build();
			}
			this.built = 1;
		},
	
		_build: function() {
			// Build after all data is cached
			var self = this;
			this.element.empty();			
			var total = this.comments.length + this.history.length
			var all = [];
			$.each(this.comments, function(){all.push(this)})
			$.each(this.history, function(){all.push(this)})
			// Break each log event out by date
			var bydate = {};
			$.each(all, function() {
				var user = this[0];
				var date = this[1];
				// Emulate Python collections.defaultdict
				if (!bydate[date]) {bydate[date] = {}}
				if (!bydate[date][user]) {bydate[date][user] = []}
				bydate[date][user].push(this);
			});

			// Sort the keys. JS doesn't support sorted(dict, key=..)
			var keys = [];
			$.each(bydate, function(k,v){keys.push(k)})
			keys.sort();
			// keys.reverse();
			
			$.each(keys, function(i, date) {
				$.each(bydate[date], function(user, events) {
					// var events = $.map(events, self.makebody);
					var d = $('<div />');
					d.InfoBox({
						'keytype':'user',
						'name': user,
						'time': date,
						'autolink': true,
						'body': self.makebody(events) || ' '
					});
					self.element.append(d);
				});
			})

			// var comments_text = caches['record'][this.options.name]["comments_text"];
			// if (comments_text) {
			// 	this.element.append('<strong>Additional comments:</strong><p>'+comments_text+'</p>');
			// }			

			if (this.options.edit) {
				var controls = $('<div><textarea class="e2l-fw" name="comment" rows="2" placeholder="Add a comment"></textarea><input type="submit" class="e2l-float-right e2l-save" value="Add Comment" /></div>');
				$('input[name=save]', controls).click(function(e) {self.save()});
				this.element.append(controls);
			}
		},
		
		makebody: function(events) {
			var comments = [];
			var rows = [];
			$.each(events, function(i, event) {
				if (event.length == 3) {'<p>'+comments.push(event[2])+'</p>'}
				if (event.length == 4) {
					var pdname = event[2];
					if (caches['paramdef'][pdname]){pdname=caches['paramdef'][pdname].desc_short}
					var row = '<tr><td style="width:16px"><img src="'+EMEN2WEBROOT+'/static/images/edit.png" /></td><td><a href="'+EMEN2WEBROOT+'/paramdef/'+event[2]+'/">'+pdname+'</a></td></tr><tr><td /><td>Old value: '+event[3]+'</td></tr>';
					rows.push(row);
				}
			});
			comments = comments.join('');
			if (rows) {
				rows = '<table cellpadding="0" cellspacing="0"><tbody>'+rows.join('')+'</tbody></table>';
			} else { rows = ''}
			return comments + rows;
		},
		
		////////////////////////////
		save: function() {	
			var self = this;
			$.jsonRPC.call('addcomment', [this.options.name, $('textarea[name=comment]', this.element).val()], function(rec) {
				$.record_update(rec)
				$.notify('Comment Added');
			});
		}
	});	
	
	
	// Select a Protocol for a new record
	$.widget('emen2.NewRecordControl', {
		options: {
			parent: null,
			rectype: null,
			private: false,
			copy: false,
			embed: true,
			show: true
		},
		
		_create: function() {
			this.built = 0;
			this.options.rectype = this.element.attr('data-rectype') || this.options.rectype;
			this.options.parent = this.element.attr('data-parent') || this.options.parent;
			this.options.private = this.element.attr('data-private') || this.options.private;
			this.options.copy = this.element.attr('data-copy') || this.options.copy;
			this.options.embed = this.element.attr('data-embed') || this.options.embed;			
			if (this.options.show) {
				this.show();
			}
		},
		
		show: function() {
			var self = this;
			this.build();
		},
		
		build: function() {
			var self = this;
			// Provide some loading feedback
			this.element.empty();
			this.element.append($.spinner(true));
			
			// Get the RecordDef for typicalchildren and prettier display
			$.jsonRPC.call("findrecorddef", {'record':[this.options.parent]}, function(rd) {
				var typicalchld = [];
				$.each(rd, function() {
					self.options.rectype = this.name;
					caches['recorddef'][this.name] = this;
					typicalchld = this.typicalchld;					
				});
				$.jsonRPC.call("getrecorddef", [typicalchld], function(rd2) {
					$.each(rd2, function() {
						caches['recorddef'][this.name] = this;
					})
					self._build();
				})
			});			
		},
		
		_build: function() {
			if (this.built) {return}
			this.built = 1;
			var self = this;
			var rd = caches['recorddef'][this.options.rectype];

			this.element.empty();
			this.dialog = $('<div />');			
			
			// Children suggested by RecordDef.typicalchld
			if (rd.typicalchld.length) {
				this.dialog.append('<h4>Suggested protocols for children</h4>');
				var c = $('<div class="e2l-cf"></div>');
				$.each(rd.typicalchld, function() {
					var d = $('<div></div>').InfoBox({
						keytype: 'recorddef',
						selectable: true,						
						name: this,
						input: ['radio', 'rectype']
					});
					c.append(d);				
				});
				this.dialog.append(c);
			}
			
			// Child protocols
			if (rd.children.length) {
				this.dialog.append('<h4>Related protocols</h4>');
				var c = $('<div class="e2l-cf"></div>');
				var related = rd.children; //.concat(rd.parents);
				$.each(related, function() {
					var d = $('<div></div>').InfoBox({
						keytype: 'recorddef',
						selectable: true,
						name: this,
						input: ['radio', 'rectype']
					});
					c.append(d);				
				});
				this.dialog.append(c);
			}
			
			this.dialog.append('<p><input type="button" name="other" value="Browse other protocols" /></p>')
			
			$('input[name=other]', this.dialog).FindControl({
				keytype: 'recorddef',
				value: rd.name
			});
			
			// Options
			var form = $('<form name="e2-newrecord" action="" method="get"></form>')
			form.append('<div class="e2l-options"><ul class="e2l-nonlist"> \
				<li><input type="checkbox" name="_private" id="e2-newrecord-private" /> <label for="e2-newrecord-private">Private</label></li> \
				<li><input type="checkbox" name="_copy" id="e2-newrecord-copy" /> <label for="e2-newrecord-copy">Copy values</label></li>  \
				</ul></div>');
			form.append('<div class="e2l-controls"><input type="submit" value="New record" /></div>');

			if (this.options.private) {
				$("input[name=private]", form).attr("checked", "checked");
			}
			if (this.options.copy) {
				$("input[name=copy]", form).attr("checked", "checked");
			}
			
			// Action button
			$('input[type=submit]', form).click(function(e) {
				var rectype = $('input[name=rectype]:checked', this.dialog).val();
				console.log(rectype);
				if (rectype) {
					var uri = EMEN2WEBROOT+'/record/'+self.options.parent+'/new/'+rectype+'/';
					var form = $('form[name=e2-newrecord]', this.element);
					form.attr('action', uri);
				} else {
					e.preventDefault();
				}
			});

			this.dialog.append(form);

			// Create the dialog...
			this.element.append(this.dialog);
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
			this.built = 0;

			// Parse options from element attributes if available
			this.options.name = this.options.name || this.element.attr("data-name");
			
			// jQuery selector for this multi-edit control to activate
			this.options.selector = this.options.selector || '.e2l-editable[data-name='+this.options.name+']';

			// Show
			if (this.options.show) {
				this.show();
			}			
		},
		
		show: function() {
			this.build();
			if (this.options.controls) {
				$('input', this.options.controls).hide();
				$('input[name=comments]', this.options.controls).show();
				$('input[name=save]', this.options.controls).show();
			}			
		},
	
		hide: function() {
			$(this.options.selector).EditControl('hide');
			if (this.options.controls) {
				$('input', this.options.controls).hide();
				$('input[name=show]', this.options.controls).show();
			}
		},
		
		build: function() {
			var self = this;
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
			if (names || params) {
				$.jsonRPC.call("getrecord", [names], function(recs) {
					$.each(recs, function(k,v) {
						caches['record'][v.name] = v;
					});
					$.jsonRPC.call("getparamdef", [params], function(paramdefs) {
						$.each(paramdefs, function(k,v) {
							caches['paramdef'][v.name] = v;
						});
						self._build();
					});
				});
			} else {
				this._build();
			}
		},
		
		_build: function() {
			if (this.built) {
				$(this.options.selector).EditControl('show');				
				return
			}
			this.built = 1;
			var self = this;			
			
			$(this.options.selector).EditControl({show:true})

			$('input[type=submit]', this.element).click(function(e){self.save(e)});

			// Build controls
			if (this.options.controls) {
				var controls = $('<div class="e2l-controls e2l-fw"></div>');
				controls.append('<input type="button" name="show" value="Edit" class="e2l-hide" />');
				controls.append('<textarea class="e2l-fw" type="text" name="comments" placeholder="Reason for changes" /></textarea>');				
				controls.append('<input class="e2l-float-right" type="button" name="save" value="Save"/>');
				$('input[name=show]', controls).click(function() {self.show()})
				$('input[name=cancel]', controls).click(function() {self.hide()})
				$('input[name=save]', controls).click(function(e){self.save(e)})
				this.options.controls.append(controls);
			}
		},
		
		save: function(e) {
			e.preventDefault();
			
			// We need to import values from some other forms..
			$("#e2-edit-copied", this.element).remove();
			var copied = $('<div id="e2-edit-copied" style="display:none"></div>');
			this.element.append(copied);

			// Copy permissions
			if (this.options.permissions) {
				$('input:checked', this.options.permissions).each(function(){
					var i = $(this);
					var cloned = $('<input type="hidden" />');
					cloned.attr('name', i.attr('name'));
					cloned.val(i.val());
					copied.append(cloned);
				});
			}
			
			// Copy comments
			if (this.options.controls) {
				var comments = $('input[name=comments]', this.options.controls);
				var cloned = $('<input type="hidden" name="comments" />')
				cloned.val(comments.val());
				copied.append(cloned);
			}

			// Submit form
			this.element.submit();
		}
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
			iterwrap: '<li />'
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
			for (var i=0;i<val.length+1;i++) {
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
			var self = this;
			var b = $('<input type="button" value="+" />');
			b.click(function() {self.add_item('')});
			return b
		},

		add_item: function(val) {
			var ul = $('.e2-edit-iterul', this.element);
			ul.append($(this.options.iterwrap).append(this.build_item(val)));
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
			var ul = $('<div class="e2-edit-iterul e2l-cf" />');
			for (var i=0;i<val.length;i++) {
				var control = this.build_item(val[i]);
				ul.append(control);
			}
			// Add a final empty element to detect empty result..
			var empty = $('<input type="hidden" name="'+this.options.param+'" value="" />');
			this.element.addClass('e2l-fw');
			return $('<div />').append(ul, this.build_add(), empty);
		},

		build_item: function(val) {
			var d = $('<div />');
			d.InfoBox({
				'keytype': 'user',
				'name': val,
				'selectable': true,
				'input': ['checkbox', this.options.param, true]
			});
			// d.append('<input type="hidden" name="'+this.options.param+'" value="'+val+'" />');
			// d.click(function() {
			// 	$(this).remove();
			// })
			return d
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
