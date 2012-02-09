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
			var rec = emen2.caches['record'][this.options.name];
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
			users = emen2.cache.check('user', users);

			// Check cached parameters
			var params = $.map(this.history, function(item){return item[2]});
			params = emen2.cache.check('paramdef', params);

			// If we need users or params, fetch them.
			// Todo: find a nicer way to chain these together
			if (users && params) {
				emen2.db('getuser', [users], function(users) {
					emen2.cache.update(users)
					emen2.db('getparamdef', [params], function(params) {
						emen2.cache.update(params)
						self._build();
					});
				});
			} else if (params) {
				emen2.db("getparamdef", [params], function(params) {
					emen2.cache.update(params)
					self._build();
				});
			} else if (users) {
				emen2.db("getuser", [users], function(users) {
					emen2.cache.update(users)
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
					if (emen2.caches['paramdef'][pdname]){pdname=emen2.caches['paramdef'][pdname].desc_short}
					var row = ' \
						<tr> \
							<td style="width:16px">'+emen2.template.image('edit.png')+'</td> \
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
			emen2.db('addcomment', [this.options.name, $('textarea[name=comment]', this.options.controls).val()], function(rec) {
				$.record_update(rec)
				$.notify('Comment Added');
			});
		}
	});	
	
	// Create a new record in a dialog box
	$.widget('emen2.RecordControl', {
		options: {
			parent: null,
			rectype: null,
			show: false,
			action: null,
			modal: true,
			redirect: null,
			name: null,
			mode: 'new'
		},
		
		_create: function() {
			// Todo: If self.options.rectype is null, 
			//		show the NewRecordChooserControl
			//		based on the parent
			var self = this;
			this.built = 0;
			this.options.rectype = emen2.util.checkopt(this, 'rectype');
			this.options.parent = emen2.util.checkopt(this, 'parent');
			this.options.name = emen2.util.checkopt(this, 'name');
			if (this.options.name != null) {
				this.options.mode = 'edit';
			}
			
			if (this.options.show) {
				this.show();
			} else {
				this.element.click(function(e){self.show(e)})
			}
		},
		
		show: function(e) {
			if (e) {e.preventDefault()}
			this.build();
			if (this.options.modal) {
				this.dialog.dialog('open');
			}
		},
		
		build: function() {
			if (this.built) {return}
			this.built = 1;
			
			var self = this;
			this.dialog = $('<div>Loading...</div>');
			this.dialog.attr('title','Loading...');
			
			if (this.options.modal) {
				// grumble... get the viewport dimensions..
				// 'auto' won't work because the content
				// is added by the callbacks
				var w = $(window).width() * 0.8;
				var h = $(window).height() * 0.8;

				this.dialog.dialog({
					modal: this.options.modal,
					autoOpen: false,
					width: w,
					height: h
				});
			} else {
				this.element.append(this.dialog);
			}			
			
			if (this.options.mode=='new') {
				this._record_new();
			} else {
				this._record_edit();
			}

		},
		
		_record_new: function() {
			var self = this;
			emen2.db('getrecorddef', [[self.options.rectype]], function(rds) {
				emen2.cache.update(rds);
				emen2.db('newrecord', {'rectype':self.options.rectype, 'inherit':self.options.parent}, function(rec) {
					// console.log("New record:", rec);
					emen2.caches['record']['None'] = rec;
					emen2.db('renderview', {'names':rec, 'viewname':'mainview', 'edit':true}, function(rendered) {
						self._build(rendered);
					});				
				});
			});			
		},
		
		_record_edit: function() {
			var self = this;
			emen2.db('getrecord', [self.options.name], function(rec) {
				emen2.cache.update([rec]);
				
				self.options.rectype = rec['rectype']
				emen2.db('getrecorddef', [rec['rectype']], function(rds) {
					emen2.cache.update([rds]);
					emen2.db('renderview', {'names':self.options.name, 'viewname':'mainview', 'edit':true}, function(rendered) {
						self._build(rendered);
					});				
				});			
			});
		},
				
		_build: function(rendered) {
			this.dialog.empty();

			// Show the recorddef long description
			var rd = emen2.caches['recorddef'][this.options.rectype];

			// Set the dialog title to show the record type and parent recname
			if (this.options.modal) {
				this.dialog.dialog('option', 'title', this.options.mode+' '+rd.desc_short);
			}

			// Create the form
			var form = $('<form enctype="multipart/form-data"  action="" method="post" data-name="'+this.options.name+'" />');

			if (this.options.mode == 'new') {
				var desc = $.trim(rd.desc_long).replace('\n','<br /><br />'); // hacked in line breaks
				var desc = $('<p class="e2-newrecord-desc_long">'+desc+'</p>');
				this.dialog.append(desc);
				// Add the parent for a new record
				form.attr('data-name', 'None');
				// Add the rectype
				form.append('<input type="hidden" name="parents" value="'+this.options.parent+'" /><input type="hidden" name="rectype" value="'+this.options.rectype+'" />')				
			}
			
			// ...redirect after submission
			if (this.options.redirect) {
				form.append('<input type="hidden" name="_location" value="'+this.options.redirect+'"/>');
			}
			// ...content
			form.append(rendered);
			// ...controls
			form.append('<ul class="e2l-controls"><li><input type="submit" value="Save" /></li></ul>');

			// Set the form action
			var action_alt = EMEN2WEBROOT+'/record/'+this.options.parent+'/new/'+this.options.rectype+'/';
			if (this.options.mode == 'edit') {
				var action_alt = EMEN2WEBROOT+'/record/'+this.options.name+'/edit/';
			}
			var action = this.options.action || this.element.attr('data-action') || action_alt;
			form.attr('action',action);
		
			// Add the editing control after it's in the DOM
			this.dialog.append(form);
			form.MultiEditControl({
				show: true				
			});
		}
	});
	
	
	// Select a Protocol for a new record
	$.widget('emen2.NewRecordChooserControl', {
		options: {
			parent: null,
			rectype: null,
			private: null,
			copy: null,
			show: true,
			help: false,
			summary: false
		},
		
		_create: function() {
			this.built = 0;
			this.options.rectype = emen2.util.checkopt(this, 'rectype');
			this.options.parent = emen2.util.checkopt(this, 'parent');
			this.options.private = emen2.util.checkopt(this, 'private');
			this.options.copy = emen2.util.checkopt(this, 'copy');
			
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
			this.element.append(emen2.template.spinner(true));
			
			// Get the RecordDef for typicalchildren and prettier display
			emen2.db("findrecorddef", {'record':[this.options.parent]}, function(rd) {
				var typicalchld = [];
				$.each(rd, function() {
					self.options.rectype = this.name;
					emen2.caches['recorddef'][this.name] = this;
					typicalchld = this.typicalchld;					
				});
				emen2.db("getrecorddef", [typicalchld], function(rd2) {
					$.each(rd2, function() {
						emen2.caches['recorddef'][this.name] = this;
					})
					self._build();
				})
			});			
		},
		
		_build: function() {
			if (this.built) {return}
			this.built = 1;
			var self = this;
			var rd = emen2.caches['recorddef'][this.options.rectype];
			this.element.empty();

			if (this.options.help || this.options.summary) {
				var header = $('<h4 class="e2l-cf">New record</h4>');				
				this.element.append(header);
			}
			if (this.options.help) {
				var help = $(' \
					<div class="e2l-hide e2l-help" role="help"><p> \
						The suggested protocols are those that are commonly \
						used as children of this record\'s protocol. Related protocols are the \
						child protocols of this record\'s protocol. \
						To select a protocol that is not displayed, click "Browse other protocols" \
						and use the protocol chooser to select a different protocol. \
					</p><p> \
						By default, child records will inherit permissions from the parent. \
						If you want the new record to have an empty permissions list, click the \
						"Private" checkbox. If you would like to create the child record as a copy \
						of this record, click the "Copy" checkbox. \
					</p><p> \
						Additional information is available at the <a href="http://blake.grid.bcm.edu/emanwiki/EMEN2/Help/NewRecord">EMEN2 wiki</a>. \
					</p></div>');
				this.element.append(help);
				var helper = $('<span class="e2-button e2l-float-right">Help</span>');
				helper.click(function(e){$('[role=help]', self.element).toggle()})
				$('h4', this.element).append(helper);
			}			
			if (this.options.summary) {
				var summary = $('<p></p>');
				summary.append('Select one of the protocols below and click "New record" to begin creating a new child record.');
				this.element.append(summary);
			}
			
			// Children suggested by RecordDef.typicalchld
			if (rd.typicalchld.length) {
				this.element.append(this.build_level('Suggested protocols', 'typicalchld', rd.typicalchld))
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
				if (!rectype) {
					e.preventDefault();
					return false
				}			
				var asd = $('<input type="hidden" />');
				self.element.append(asd);
				asd.RecordControl({
					parent: self.options.parent,
					rectype: rectype,
					show: true
				});
				return false
				
				var uri = EMEN2WEBROOT+'/record/'+self.options.parent+'/new/'+rectype+'/';
				var form = $('form[name=e2-newrecord]', this.element);
				form.attr('action', uri);
				var f = $('<div />');
				this.element.append(f);
				f.RecordControl({
					rectype: rectype,
					parent: self.options.parent,
					show: true,
				});
				return false
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
			this.options.name = emen2.util.checkopt(this, 'name');
			
			// jQuery selector for this multi-edit control to activate
			this.options.selector = emen2.util.checkopt(this, 'selector', '.e2-edit[data-name='+this.options.name+']');
			
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
			names = emen2.cache.check('record', names);
			params = emen2.cache.check('paramdef', params);

			// Request records and params; update caches; show widget on callback
			if (names.length || params.length) {
				emen2.db("getrecord", [names], function(recs) {
					emen2.cache.update(recs);
					emen2.db("getparamdef", [params], function(paramdefs) {
						emen2.cache.update(paramdefs);
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
				var placeholder = 'Please provide a reason for the changes.';
				if (this.options.prefix) {
					placeholder = 'Please provide a reason for the changes. This comment will be added to all changed records.'
				}
				
				// Add 10px padding to the hide button b/c aarrgghh.
				var controls = $(' \
					<textarea class="e2l-fw" name="comments" placeholder="'+placeholder+'"></textarea> \
					<ul class="e2l-controls e2l-fw"> \
						<li><a style="padding-top:10px" class="e2l-float-left e2l-small" href="'+EMEN2WEBROOT+'/record/'+self.options.name+'/hide/">(Hide this record?)</a><input type="submit" class="e2-edit-save e2l-float-right" value="Save" /></li> \
					</ul>');
				$('.e2-edit-show', controls).click(function() {self.show()})
				$('.e2-edit-cancel', controls).click(function() {self.hide()})
				$('.e2-edit-save', controls).click(function(e){self.save(e)})
				this.options.controls.append(controls);
			}
		},
		
		save: function(e) {
			// Check if we need to copy other values into the form...
			if (!(this.options.permissions || this.options.controls)) {
				return false
			}

			// Setup an area to copy the values
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
			e.preventDefault();			
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
			this.options.name = emen2.util.checkopt(this, 'name');
			this.options.param = emen2.util.checkopt(this, 'param');
			this.options.required = emen2.util.checkopt(this, 'required');

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
			if (emen2.caches['record'][this.options.name] == null) {
				emen2.db("getrecord", [this.options.name], function(rec) {
					emen2.cache.update([rec]);
					self.show();
				});
				return
			}

			// Get the ParamDef if it isn't cached
			if (!emen2.caches['paramdef'][this.options.param]) {
				emen2.db("getparamdef", [this.options.param], function(paramdef){
					emen2.cache.update([paramdef]);
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
			} else {
				cls = $.emen2edit[this.controlhints(pd.vartype)];
			}
			if (!cls) {
				cls = $.emen2edit['string'];
			}
			this.editor = new cls(this.options, this.dialog);
		},		
		
		controlhints: function(vt) {
			var defaults = {
				'text':'textarea',
				'html':'textarea',
				'history':'none',
				'uri':'none',
				'recid':'none',
				'acl':'not_ready',
				'links':'not_ready',
				'groups':'not_ready',
				'binary':'binary',
				'comments':'textarea'
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
			return emen2.caches['record'][this.options.name][this.options.param];
		},
		
		cachepd: function() {
			return emen2.caches['paramdef'][this.options.param];	
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
			this.element.append(this.build_add());	
		},
		
		build_iter: function(val) {
			if (!val) {val == []}
			var pd = this.cachepd();
			var ul = $('<ul class="e2-edit-iterul" />');
			for (var i=0; i<val.length+1; i++) {
				var control = this.build_item(val[i], i);
				ul.append($('<li />').append(control));
			}
			// Must append a hidden element...
			// var hidden = '';
			// $('<input type="hidden" name="'+this.options.prefix+pd.name+'" value="" />');
			this.element.addClass('e2l-fw');
			return $('<div />').append(ul);
		},
		
		build_item: function(val, index) {
			var pd = this.cachepd();
			var editw = $('<input type="text" name="'+this.options.prefix+pd.name+'" value="'+val+'" autocomplete="off" />');
			if (this.options.required && !index) {editw.attr('required',true)}			
			return editw
		},
		
		build_add: function(e) {
			// var self = this;
			// var b = $('<input type="button" value="+" />');
			// b.click(function() {self.add_item('')});
			// return b
			return $('')
		},

		add_item: function(val) {
			var ul = $('.e2-edit-iterul', this.element);
			ul.append($(this.options.iterwrap).append(this.build_item(val, -1)));
		},
		
		getval: function() {
			return null
		},
		
		cacheval: function() {
			var rec = emen2.caches['record'][this.options.name];
			if (!rec) {return null}
			var val = rec[this.options.param];
			if (val==null) {val=''}
			return val
		},
		
		cachepd: function() {
			var pd = emen2.caches['paramdef'][this.options.param];
			return pd
		}		
	});


	// Not editable
    $.widget("emen2edit.none", $.emen2.EditBase, {
		build_control: function() {
			this.element.append('Not Editable');
		}
	});

	// Use other widget
    $.widget("emen2edit.not_ready", $.emen2.EditBase, {
		build_control: function() {
			this.element.append('(Use toolbar to edit this)');
		}
	});

	// Basic String editing widget
    $.widget("emen2edit.string", $.emen2.EditBase, {
		build_item: function(val, index) {
			var self = this;
			var pd = this.cachepd();
			var container = $('<span class="e2-edit-container" />');
			if (val==null){val=""}
		
			var editw = $('<input type="text" name="'+this.options.prefix+pd.name+'" value="'+val+'" autocomplete="off" />');
			if (this.options.required && !index) {editw.attr('required',true)}
			
			if (pd.property) {
				var realedit = '<input class="e2-edit-val" type="hidden" name="'+this.options.prefix+pd.name+'" value="'+val+'" />';
				var editw = $('<input class="e2-edit-unitsval" type="text" value="'+val+'" />');
				var units = this.build_units();
				editw.change(function(){self.sethidden()});
				units.change(function(){self.sethidden()});
				container.append(editw, units, realedit);
			} else {
				container.append(editw);
			}
			
			var param = pd.name;
			editw.autocomplete({
				minLength: 0,
				source: function(request, response) {
					emen2.db("findvalue", [param, request.term], function(ret) {
						var r = $.map(ret, function(item) {
							return {
								label: item[0] + " (" + item[1] + " records)",
								value: item[0]
							}
						});
						response(r);			
					});
				}
			});
			//editw.click(function() {
			//	$(this).autocomplete('search');
			//});			
			
			return container
		},

		build_units: function() {
			var property = this.cachepd().property;
			var defaultunits = this.cachepd().defaultunits;
			var units = $('<select class="e2-edit-units"></select>');
			var u = valid_properties[property][1];
			// Add all the known units to the select
			for (var i=0;i < valid_properties[property][1].length;i++) {
				units.append('<option>'+valid_properties[property][1][i]+'</option>');
			}
			// Make sure the defaultunits for this paramdef is in the select
			if ($.inArray(defaultunits, u)==-1) {
				units.append('<option>'+defaultunits+'</option>');				
			}
			units.val(defaultunits);
			return units
		},

		sethidden: function() {
			var self = this;
			$('.e2-edit-container', this.element).each(function(){
				var unitsval = $('.e2-edit-unitsval', this).val();
				var units = $('.e2-edit-units', this).val();
				if (!unitsval) {units=""}
				$('.e2-edit-val', this).val(unitsval+' '+units);
			});
		}
	});
	
	// Single-choice widget
    $.widget("emen2edit.choice", $.emen2.EditBase, {
		build_item: function(val, index) {
			var choices = this.cachepd().choices;
			var editw = $('<select name="'+this.options.prefix+this.cachepd().name+'"></select>');
			if (this.options.required && !index) {editw.attr('required',true)}
			
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
		build_item: function(val, index) {
			var editw = $('<select name="'+this.cachepd().name+'"><option selected="selected"></option><option>True</option><option>False</option></select>');
			if (this.options.required && !index) {editw.attr('required',true)}
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
		build_iter: function(val, index) {
			val = val || [];			
			var ul = $('<div class="e2-edit-iterul e2l-cf" />');
			for (var i=0;i<val.length;i++) {
				var control = this.build_item(val[i], i);
				ul.append(control);
			}
			// Add a final empty element to detect empty result..
			var empty = $('<input type="hidden" name="'+this.options.prefix+this.options.param+'" value="" />');
			this.element.addClass('e2l-fw');
			return $('<div />').append(ul, empty);
		},

		build_item: function(val, index) {
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
	$.widget("emen2edit.textarea", $.emen2.EditBase, {
		build_item: function(val, index) {
			var editw = $('<textarea style="width:100%" name="'+this.options.prefix+this.cachepd().name+'" rows="10">'+val+'</textarea>');
			if (this.options.required && !index) {editw.attr('required',true)}			
			this.element.addClass('e2l-fw');
			return editw
		}
	});
	
	// Binary Editor
	$.widget("emen2edit.binary", $.emen2.EditBase, {
		build_iter: function(val, index) {
			val = val || [];			
			var ul = $('<div class="e2-edit-iterul e2l-cf" />');
			for (var i=0;i<val.length;i++) {
				var control = this.build_item(val[i], i);
				ul.append(control);
			}
			// Add a final empty element to detect empty result..
			var empty = $('<input type="hidden" name="'+this.options.prefix+this.options.param+'" value="" />');
			this.element.addClass('e2l-fw');
			return $('<div />').append(ul, empty);
		},

		build_item: function(val, index) {
			var d = $('<div class="e2-attachments-infobox" />').InfoBox({
				name: val,
				keytype: 'binary',
				selectable: true,
				input: ['checkbox', this.options.prefix+this.cachepd().name, true]
			});
			return d
		},
		
		build_add: function(e) {
			return $('<input type="file" name="'+this.options.prefix+this.options.param+'"/>')
		}
		// build_iter: function(val, index) {
		// 	var editw = $('<input type="file" name="'+this.options.prefix+this.cachepd().name+'" />')
		// 	if (this.options.required && !index) {editw.attr('required',true)}			
		// 	this.element.addClass('e2l-fw');
		// 	return editw
		// }
	});
	
	// Group Editor
	//     $.widget("emen2edit.groups", $.emen2.EditBase, {
	// 	build_item: function(val, index) {
	// 		return 'Edit Groups...'
	// 	},
	// 	sethidden: function() {
	// 		var self = this;
	// 		$('.e2-edit-container', this.element).each(function(){
	// 			$('.e2-edit-val', this).val('');
	// 		});
	// 	}
	// });	
	
	// Comments
	//     $.widget("emen2edit.comments", $.emen2.EditBase, {
	// 	build_item: function(val, index) {
	// 		return 'Edit Comments...'
	// 	}
	// });

	// Coordinate
	//     $.widget("emen2edit.coordinate", $.emen2.EditBase, {
	// 	build_item: function(val, index) {
	// 		return 'Edit coordinates...'
	// 	}
	// });
	
	// Rectype
	//     $.widget("emen2edit.rectype", $.emen2.EditBase, {
	// 	build_item: function(val, index) {
	// 		return 'Rectype is not editable!'
	// 	}
	// });	

	// Percent
    $.widget("emen2edit.percent", $.emen2.EditBase, {
		build_item: function(val, index) {
			return 'Edit Percent...'
		},
		sethidden: function() {
			var self = this;
			$('.e2-edit-container', this.element).each(function(){
				$('.e2-edit-val', this).val('');
			});
		}		
	});	

	// Date Time
    $.widget("emen2edit.datetime", $.emen2.EditBase, {
		build_item: function(val, index) {
			var e = $('<input type="text" name="'+this.options.prefix+this.options.param+'" value="'+val+'" />');
			if (this.options.required && !index) {e.attr('required',true)}
			e.datetimepicker({
				showButtonPanel: true,
				changeMonth: true,
				changeYear: true,
				showAnim: '',
				yearRange: 'c-100:c+100',
				dateFormat: 'yy-mm-dd',
				separator: 'T',
			});
			return e
		}
	});	

	// Date
    $.widget("emen2edit.date", $.emen2.EditBase, {
		build_item: function(val, index) {
			var e = $('<input type="text" name="'+this.options.prefix+this.options.param+'" value="'+val+'" />');
			if (this.options.required && !index) {e.attr('required',true)}
			e.datepicker({
				showButtonPanel: true,
				changeMonth: true,
				changeYear: true,
				showAnim: '',
				yearRange: 'c-100:c+100',
				dateFormat: 'yy-mm-dd'
			});
			return e
		}
	});
		
	// WIDGET HINTS
	$.widget('emen2edit.checkbox', $.emen2.EditBase, {
		build_item: function(val, index) {
			var n = this.options.prefix+this.options.param;
			var edit = $('<input type="checkbox" name="'+n+'" value="True" />');
			if (this.options.required && !index) {editw.attr('required',true)}
			
			//<input type="hidden" name="'+n+'" value="" />');
			if (val) {
				$('input:checkbox', edit).attr('checked',true);
			}
			return edit
		}
	});
	
	// Radio buttons
    $.widget("emen2edit.radio", $.emen2.EditBase, {
		build_item: function(val, index) {
			var self = this;
			var pd = this.cachepd();
			var choices = pd.choices || [];
			var ul = $('<ul />');
			$.each(choices, function(k,v) {
				// grumble..
				var rand = Math.ceil(Math.random()*10000000);
				var id = 'e2-edit-radio-'+rand;
				var input = $('<input type="radio" name="'+self.options.prefix+self.options.param+'" value="'+v+'" id="'+id+'"/>');
				if (self.options.required && !index) {input.attr('required',true)}
				if (val == v) {
					input.attr('checked',true);
				}
				var label = '<label for="'+id+'">'+v+'</label>';
				ul.append($('<li/>').append(input, label));
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
