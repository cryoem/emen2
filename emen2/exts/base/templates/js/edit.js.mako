(function($) {
	
	// Comments Widget
    $.widget("emen2.CommentsControl", {
		options: {
			name: null,
			edit: false,
			title: null,
			controls: null,
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
			this.built = 1;

			// Make a copy of the cached comments and history
			var rec = caches['record'][this.options.name];
			this.comments = rec['comments'].slice() || [];
			this.history = rec['history'].slice() || [];
			
			// Add a "comment" for the record creation time		
			this.comments.push([
				rec['creator'], 
				rec['creationtime'], 
				'Record created']);

			// Check for cached users
			var users = [];
			$.each(this.comments, function(){users.push(this[0])})
			$.each(this.history, function(){users.push(this[0])})
			users = $.checkcache('user', users);

			// Check cached parameters
			var params = $.map(this.history, function(item){return item[2]});
			params = $.checkcache('paramdef', params);

			// If we need users or params, fetch them.
			// Todo: find a nicer way to chain these together
			if (users && params) {
				$.jsonRPC.call('getuser', [users], function(users) {
					$.updatecache(users)
					$.jsonRPC.call('getparamdef', [params], function(params) {
						$.updatecache(params)
						self._build();
					});
				});
			} else if (params) {
				$.jsonRPC.call("getparamdef", [params], function(params) {
					$.updatecache(params)
					self._build();
				});
			} else if (users) {
				$.jsonRPC.call("getuser", [users], function(users) {
					$.updatecache(users)
					self._build();
				});
			} else {
				self._build();
			}
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

			if (this.options.edit && this.options.controls) {
				var controls = $(' \
					<ul class="e2l-controls e2l-fw"> \
						<li><textarea name="comment" rows="2" placeholder="Add a comment"></textarea></li> \
						<li><input type="submit" class="e2l-float-right e2l-save" value="Add Comment" /></li> \
					</ul>');
				$('input:submit', controls).click(function(e) {self.save(e)});
				this.options.controls.append(controls)
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
					var row = ' \
						<tr> \
							<td style="width:16px">'+$.e2image('edit.png')+'</td> \
							<td><a href="'+EMEN2WEBROOT+'/paramdef/'+event[2]+'/">'+pdname+'</a></td> \
						</tr><tr> \
							<td /> \
							<td>Old value: '+event[3]+'</td> \
						</tr>';
					rows.push(row);
				}
			});
			comments = comments.join('');
			if (rows) {
				rows = '<table cellpadding="0" cellspacing="0"><tbody>'+rows.join('')+'</tbody></table>';
			} else { rows = ''}
			return comments + rows;
		},
		
		save: function(e) {	
			var self = this;
			$.jsonRPC.call('addcomment', [this.options.name, $('textarea[name=comment]', this.options.controls).val()], function(rec) {
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
			private: null,
			copy: null,
			show: true
		},
		
		_create: function() {
			this.built = 0;
			this.options.rectype = $.checkopt(this, 'rectype');
			this.options.parent = $.checkopt(this, 'parent');
			this.options.private = $.checkopt(this, 'private');
			this.options.copy = $.checkopt(this, 'copy');
			
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
			this.element.append($.e2spinner(true));
			
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
			
			// Children suggested by RecordDef.typicalchld
			// todo: -> this.build_leve(label, level, items);
			if (rd.typicalchld.length) {
				this.element.append(this.build_level('Suggested protocols for children', 'typicalchld', rd.typicalchld))
			}
			
			// Child protocols
			// if (rd.children.length) {
			var related = rd.children.slice();
			related.push(rd.name);
			this.element.append(this.build_level('Related protocols', 'related', related));
			//}
			
			this.element.append('<p><input type="button" name="other" value="Browse other protocols" /></p>')
			
			$('input[name=other]', this.element).FindControl({
				keytype: 'recorddef',
				value: rd.name,
				selected: function(widget, value) {
					self.add('related', value);
				}
			});
			
			// Options
			var form = $('<form name="e2-newrecord" action="" method="get"></form>')
			form.append(' \
				<ul class="e2l-options"> \
					<li> \
						<input type="checkbox" name="_private" id="e2-newrecord-private" /> \
						<label for="e2-newrecord-private">Private</label> \
					</li> \
					<li> \
						<input type="checkbox" name="_copy" id="e2-newrecord-copy" /> \
						<label for="e2-newrecord-copy">Copy</label> \
					</li>  \
				</ul> \
				<ul class="e2l-controls"> \
					<li><input type="submit" value="New record" /></li> \
				</ul>');

			if (this.options.private) {
				$("input[name=private]", form).attr("checked", "checked");
			}
			if (this.options.copy) {
				$("input[name=copy]", form).attr("checked", "checked");
			}
			
			// Action button
			$('input[type=submit]', form).click(function(e) {
				var rectype = $('input[name=rectype]:checked', this.element).val();
				if (rectype) {
					var uri = EMEN2WEBROOT+'/record/'+self.options.parent+'/new/'+rectype+'/';
					var form = $('form[name=e2-newrecord]', this.element);
					form.attr('action', uri);
				} else {
					e.preventDefault();
				}
			});

			this.element.append(form);
		},
		
		build_level: function(label, level, items) {
			var header = $('<h4>'+label+'</h4>')
			var boxes = $('<div class="e2l-cf"></div>');
			boxes.attr('data-level', level);
			$.each(items, function() {
				var box = $('<div/>').InfoBox({
					keytype: 'recorddef',
					selectable: true,						
					name: this,
					input: ['radio', 'rectype']
				});
				boxes.append(box);
			});
			return $('<div/>').append(header, boxes);
		},
		
		add: function(level, name) {
			var selector = 'div[data-level='+level+']';
			var boxes = $(selector, this.element);
			if (!boxes.length) {
				this.element.prepend(this.build_level('Other protocols', level, []));
				var boxes = $(selector, this.element);
			}
			var box = $('<div/>').InfoBox({
				keytype: 'recorddef',
				selectable: true,						
				name: name,
				input: ['radio', 'rectype']
			});
			box.InfoBox('check');
			boxes.append(box);
		}
	});
	
	
	
	// This control acts on groups of EditControls, editing one or more records.
    $.widget("emen2.MultiEditControl", {		
		options: {
			show: null,
			name: null,
			selector: null,
			controls: null,
			prefix: false
		},
				
		_create: function() {
			this.built = 0;

			// Parse options from element attributes if available
			this.options.name = $.checkopt(this, 'name');
			
			// jQuery selector for this multi-edit control to activate
			this.options.selector = $.checkopt(this, 'selector', '.e2-edit[data-name='+this.options.name+']');

			// Show
			if (this.options.show) {
				this.show();
			}			
		},
		
		show: function() {
			this.build();
			if (this.options.controls) {
				$('input', this.options.controls).hide();
				$('.e2-edit-comments', this.options.controls).show();
				$('.e2-edit-save', this.options.controls).show();
			}			
		},
	
		hide: function() {
			$(this.options.selector).EditControl('hide');
			if (this.options.controls) {
				$('input', this.options.controls).hide();
				$('.e2-edit-show', this.options.controls).show();
			}
		},
		
		build: function() {
			var self = this;
			// Gather records and params to request from server..
			var names = $.map($(this.options.selector), function(elem){return $(elem).attr("data-name")});
			var params = $.map($(this.options.selector), function(elem){return $(elem).attr("data-param")});
			names = $.checkcache('record', names);
			params = $.checkcache('paramdef', params);

			// Request records and params; update caches; show widget on callback
			if (names.length || params.length) {
				$.jsonRPC.call("getrecord", [names], function(recs) {
					$.updatecache(recs);
					$.jsonRPC.call("getparamdef", [params], function(paramdefs) {
						$.updatecache(paramdefs);
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
			
			// Build the individual editing controls
			$(this.options.selector).EditControl({
				prefix: this.options.prefix
			});

			$('input[type=submit]', this.element).click(function(e){self.save(e)});

			// Build overall controls
			if (this.options.controls) {
				var placeholder = 'Reason for changes';
				if (this.options.prefix) {
					placeholder = 'Reason for changes; this comment will be added to all changed records.'
				}
				
				var controls = $(' \
					<textarea class="e2l-fw" name="comments" placeholder="'+placeholder+'"></textarea> \
					<ul class="e2l-controls"> \
						<li><input type="button" class="e2-edit-save" value="Save" /></li> \
					</ul>');
				$('.e2-edit-show', controls).click(function() {self.show()})
				$('.e2-edit-cancel', controls).click(function() {self.hide()})
				$('.e2-edit-save', controls).click(function(e){self.save(e)})
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
				$('input:checked, input.e2-permissions-hidden', this.options.permissions).each(function(){
					var i = $(this);
					var cloned = $('<input type="hidden" />');
					cloned.attr('name', i.attr('name'));
					cloned.val(i.val());
					copied.append(cloned);
				});
			}
			
			// Copy comments
			if (this.options.controls) {
				var comments = $('textarea[name=comments]', this.options.controls);
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
			show: true,
			name: null,
			param: null,
			prefix: null
		},
				
		_create: function() {
			// Parse options from element attributes if available		
			this.options.name = $.checkopt(this, 'name');
			this.options.param = $.checkopt(this, 'param');

			if (this.options.prefix) {
				this.options.prefix = this.options.name + '.';
			} else {
				this.options.prefix = '';
			}
		
			this.built = 0;

			if (this.options.show) {
				this.show();
			}
		},
	
		show: function() {	
			var self = this;
					
			// Get the Record if it isn't cached
			if (caches['record'][this.options.name] == null) {
				$.jsonRPC.call("getrecord", [this.options.name], function(rec) {
					$.updatecache([rec]);
					self.show();
				});
				return
			}

			// Get the ParamDef if it isn't cached
			if (!caches['paramdef'][this.options.param]) {
				$.jsonRPC.call("getparamdef", [this.options.param], function(paramdef){
					$.updatecache([paramdef]);
					self.show();
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
			
			// The edit widget container
			this.dialog = $('<div class="e2-edit-widget" />');
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
			return '<input type="text" name="'+this.options.prefix+pd.name+'" value="'+(val || '')+'" />';
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
				var realedit = '<input class="e2-edit-val" type="hidden" name="'+this.options.prefix+pd.name+'" value="'+(val || '')+'" />';
				var editw = $('<input class="e2-edit-unitsval" type="text" value="'+(val || '')+'" />');
				var units = this.build_units();
				editw.change(function(){self.sethidden()});
				units.change(function(){self.sethidden()});
				container.append(editw, units, realedit);
			} else {
				container.append('<input type="text" name="'+this.options.prefix+pd.name+'" value="'+(val || '')+'" />');
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
			var editw = $('<select name="'+this.options.prefix+this.cachepd().name+'"></select>');
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
			var empty = $('<input type="hidden" name="'+this.options.prefix+this.options.param+'" value="" />');
			this.element.addClass('e2l-fw');
			return $('<div />').append(ul, this.build_add(), empty);
		},

		build_item: function(val) {
			var d = $('<div />');
			d.InfoBox({
				keytype: 'user',
				name: val,
				selectable: true,
				input: ['checkbox', this.options.prefix+this.options.param, true]
			});
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
				selected: function(test, name){self.add_item(name)}
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
			var ul = $('<ul />');
			$.each(choices, function() {
				// grumble..
				var rand = Math.ceil(Math.random()*10000000);
				var id = 'e2-edit-radio-'+rand;
				var input = '<input type="radio" name="'+self.options.prefix+self.options.param+'" value="'+this+'" id="'+id+'"/><label for="'+id+'">'+this+'</label>';
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
