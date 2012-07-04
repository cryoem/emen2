(function($) {
	
	$.widget('emen2.PermissionsControl', {
		options: {
			keytype: 'record',
			name: null,
			edit: false,
			show: true,
			controls: null,
			groups: true,
			summary: false,
			help: false,
		},
		
		_create: function() {
			var self = this;
			this.built = 0;
			if (this.options.show) {
				this.show();
			}
		},
		
		show: function() {
			this.build();
		},
		
		build: function() {
			// Cache items before real build..
			if (this.built) {return}
			var self = this;

			// Add the e2-permissions class
			this.element.empty();
			this.element.addClass('e2-permissions');
			this.element.append(emen2.template.spinner());

			// Complicated callback chain...
			// 1. Get the item...
			var item = emen2.caches[this.options.keytype][this.options.name];
			if (!item) {
				emen2.db('get', {'keytype':this.options.keytype, 'names':this.options.name}, function(item) {
					emen2.cache.update([item]);

					// 2. Get all the users before we draw the infoboxes
					var users = [];
					$.each(item['permissions'] || [], function(k, v) {users = users.concat(v)});
					users = emen2.cache.check('user', users);
					emen2.db('user.get', [users], function(users) {
						emen2.cache.update(users);

						// 3. ... also get groups ...
						var groups = item['groups'] || [];
						groups = emen2.cache.check('group', groups);
						emen2.db('group.get', [groups], function(groups) {					
							emen2.cache.update(groups)

							// 4. Finally call real build method
							self._build();
						});	
					});
				});
			} else {

				// This should be broken down into a separate callback method
				// for each step of the chain
				var users = [];
				$.each(item['permissions'] || [], function(k, v) {users = users.concat(v)});
				users = emen2.cache.check('user', users);
				emen2.db('user.get', [users], function(users) {
					emen2.cache.update(users);

					// 3. ... also get groups ...
					var groups = item['groups'] || [];
					groups = emen2.cache.check('group', groups);
					emen2.db('group.get', [groups], function(groups) {					
						emen2.cache.update(groups)

						// 4. Finally call real build method
						self._build();
					});	
				});
				
			}
		},
		
		_build: function() {
			// Real build method
			this.built = 1;
			var self = this;
			var permissions = emen2.caches[this.options.keytype][this.options.name]['permissions'] || [];
			var groups = emen2.caches[this.options.keytype][this.options.name]['groups'] || [];

			// Remove anything that is bound
			this.element.empty();

			// Build the controls
			if (this.options.controls && this.options.edit) {
				this.build_controls();
			}
			if (this.options.summary || this.options.help) {
				this.element.append('<h4 class="e2l-cf">Permissions</h4>');
			}
			if (this.options.help) {
				var help = (' \
				<div class="e2l-help" role="help"><p> \
					There are four types of permissions: \
				</p><ul><li><strong>Read-only</strong>: can access record</li> \
					<li><strong>Comment</strong>: can access record and add comments</li> \
					<li><strong>Write</strong>: can access record, add comments, and change values</li> \
					<li><strong>Owner</strong>: can access record, add comments, change values, and change permissions</li> \
				</ul><p>You can also assign <strong>Group</strong> permissions. The permissions of each specified group will be added to the record. \
					For example, say user "John" is a member of the group "Technicians," and he has write permission in that group. If you added "Technicians" \
					to this record, "John" would then have write access to this record. \
					There are also a few special groups. <em>Authenticated</em> group will permit <em>all</em> logged-in users to access the record. \
					<em>Anonymous</em> will make the record publicly accessible to anyone. \
				</p><p>To <strong>add users or groups</strong>, click one of the <strong>+</strong> buttons below. \
					This will show a chooser. Search for the user or group you wish to add, and click their name. \
					They will be added to the list of users or groups. The changes will take effect when you click <strong>Save permissions</strong>. \
				</p><p>To <strong>remove users or groups</strong>, uncheck their name, and click <strong>Save permissions</strong>. \
				</p><p> \
					Additional information is available at the <a href="http://blake.grid.bcm.edu/emanwiki/EMEN2/Help/Permissions">EMEN2 Wiki</a>. \
				</p></div>');
				this.element.append(help);
				var helper = $('<span class="e2-button e2l-float-right">Help</span>');
				helper.click(function(e){$('[role=help]', self.element).toggle()})
				$('h4', this.element).append(helper);
			}
			if (this.options.summary) {
				var summary = $('<p />');			
				summary.append(this.build_summary());
				this.element.append(summary);
			}

			// Build the permissions levels
			if (this.options.groups) {
				this.element.append(this.build_level('Groups', 'groups', groups, 'group'));
			}
			this.element.append(this.build_level('Read-only', 'read', permissions[0]));
			this.element.append(this.build_level('Comment', 'comment', permissions[1]));
			this.element.append(this.build_level('Write', 'write', permissions[2]));
			this.element.append(this.build_level('Owners', 'admin', permissions[3]));
			
			// Show all the infoboxes...
			$('.e2-permissions-infobox', this.element).InfoBox('show');
			
		},
		
		build_summary: function() {
			var permissions = emen2.caches[this.options.keytype][this.options.name]['permissions'] || [];
			var groups = emen2.caches[this.options.keytype][this.options.name]['groups'] || [];
			var total = permissions[0].length + permissions[1].length + permissions[2].length + permissions[3].length;
			var ret = '<p>This record is accessible by '+groups.length+' groups and '+total+' users.</p>';
			return ret
		},
		
		build_controls: function() {
			var self = this;
			var controls = $(' \
				<ul class="e2l-options"> \
					<li class="e2-select"></li> \
					<li><span class="e2-permissions-advanced e2l-a">'+emen2.template.caret('up')+'Advanced</span></li> \
			 	</ul> \
				<ul class="e2l-advanced e2l-hide"> \
			 		<li><input type="button" name="add" value="Add selection to children" /></li> \
		 			<li><input type="button" name="remove" value="Remove selection from children" /></li> \
			 		<li><input type="button" name="overwrite" value="Overwrite children with selection" /></li> \
				 	<li><input type="checkbox" name="filt" value="filt" checked id="e2-permissions-filt"><label for="e2-permissions-filt">Ignore failures</label><br /></li> \
				</ul> \
				<ul class="e2l-controls"> \
					<li><input type="button" name="save" value="Save permissions" /></li> \
				</ul>');

			// Selection control
			$('.e2-select', controls).SelectControl({root: this.element});
			
			// Show/hide advanced options
			$('.e2-permissions-advanced', controls).click(function(){
				emen2.template.caret('toggle', self.options.controls);
				$('.e2l-controls', self.options.controls).toggle();
				$('.e2l-advanced', self.options.controls).toggle();
			});
			
			// Action buttons
			$('input[name=add]', controls).click(function(){self.save('add')})
			$('input[name=remove]', controls).click(function(){self.save('remove')})
			$('input[name=overwrite]', controls).click(function(){self.save('overwrite')})
			$('input[name=save]', controls).click(function(){self.save()});
			
			this.options.controls.append(controls);			
		},

		build_level: function(lab, level, items, keytype) {
			// Build a header, controls, and infoboxes for a group of items
			var self = this;
			var keytype = (level == 'groups') ? 'group' : 'user';
			var param = (level == 'groups') ? 'groups' : 'permissions.'+level;

			var ret = $('<div></div>')			
			var header = $('<h4 class="e2l-cf">'+lab+'</h4>');
			if (this.options.edit) {
				var add = $('<input type="button" data-level="'+level+'" data-keytype="'+keytype+'" value="+" /> ');
				// Find control. Callback adds item to the correct box.
				// var minimum = 0;
				// if (keytype=='group'){minimum=0}
				add.FindControl({
					keytype: keytype,
					minimum: 0,
					selected: function(w, value) {
						var level = w.element.attr('data-level');
						self.add(level, value);
					}
				});
				header.prepend(add, ' ');
			}

			var div = $('<div class="e2l-cf"></div>');
			div.attr('data-level', level);
			
			// Add the infoboxes
			for (var i=0;i<items.length;i++) {
				div.append(this.build_item(level, items[i], keytype));
			}

			// We have to put in one last empty element
			div.append('<input type="hidden" name="'+param+'" value="" class="e2-permissions-hidden" />');
			ret.append(header, div);
			return ret
		},
		
		build_item: function(level, name) {
			// Build the infobox for an item
			var self = this;
			var keytype = (level == 'groups') ? 'group' : 'user';
			var param = (level == 'groups') ? 'groups' : 'permissions.'+level;

			// Update the select count when built or checked..
			var cb = function() {$('.e2-select', self.options.controls).SelectControl('update')}

			// User infobox
			// Show is false -- we need to attach to DOM before
			// the built() callback will work correctly.
			var d = $('<div class="e2-permissions-infobox"></div>');
			d.InfoBox({
				show: false,
				keytype: keytype,
				name: name,
				selectable: this.options.edit,
				input: ['checkbox', param, true],
				selected: cb,
				built: cb
			});
			return d
		},
		
		add: function(level, name) {
			var self = this;
			var lvl = $('div[data-level='+level+']');
			if ($('div[data-name='+name+']', lvl).length) {
				return
			}
			var item = this.build_item(level, name);
			lvl.append(item);
			item.InfoBox('show');
		},
		
		save: function(action) {
			var self = this;
			
			// Copy options into the form...
			if (action) {
				$('.e2-permissions-copied', this.element).remove();
				var copied = $('<div class="e2-permissions-copied e2l-hide"></div>');
				var filt = $('input[name=filt]:checked', this.options.controls).val();
				copied.append('<input type="hidden" name="action" value="'+action+'" />');
				copied.append('<input type="hidden" name="filt" value="'+filt+'" />');
				this.element.append(copied);
			}
			
			// Submit the actual form
			this.element.submit();			
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