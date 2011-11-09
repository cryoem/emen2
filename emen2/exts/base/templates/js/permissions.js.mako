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
			this.element.append($.e2spinner());

			// Complicated callback chain...
			// 1. Get the item...
			var item = caches[this.options.keytype][this.options.name];
			$.jsonRPC.call('get', {'keytype':this.options.keytype, 'names':this.options.name}, function(item) {
				$.updatecache([item]);

				// 2. Get all the users before we draw the infoboxes
				var users = [];
				$.each(item['permissions'] || [], function(k, v) {users = users.concat(v)});
				users = $.checkcache('user', users);
				$.jsonRPC.call('getuser', [users], function(users) {
					$.updatecache(users);
					
					// 3. ... also get groups ...
					var groups = item['groups'] || [];
					groups = $.checkcache('group', groups);
					$.jsonRPC.call('getgroup', [groups], function(groups) {					
						$.updatecache(groups)

						// 4. Finally call real build method
						self._build();
					});	
				});
			});
		},
		
		_build: function() {
			// Real build method
			this.built = 1;
			var self = this;
			var permissions = caches[this.options.keytype][this.options.name]['permissions'] || [];
			var groups = caches[this.options.keytype][this.options.name]['groups'] || [];

			// Remove anything that is bound
			this.element.empty();

			// Build the controls
			if (this.options.controls) {
				this.build_controls();
			}
			if (this.options.summary || this.options.help) {
				this.element.append('<h4>Permissions</h4>');
			}
			if (this.options.summary) {
				var summary = $('<p />');			
				summary.append(this.build_summary());
				this.element.append(summary);
			}
			if (this.options.help) {
				var help = ('<p> \
					There are four increasing levels of permission: read (access record), comment (add comments), write (change values), and owner (change permissions). \
					To add a new user or group, click the "+" button next to that permissions level. \
					Group members will also be granted access, based on their permissions in that group. \
				 	Saving this form will keep checked users and groups; unchecked users and groups will be removed.</p>');
				this.element.append(help);
			}

			// Build the permissions levels
			this.element.append(this.build_level('Groups', 'groups', groups, 'group'));
			this.element.append(this.build_level('Read-only', 'read', permissions[0]));
			this.element.append(this.build_level('Comment', 'comment', permissions[1]));
			this.element.append(this.build_level('Write', 'write', permissions[2]));
			this.element.append(this.build_level('Owners', 'admin', permissions[3]));
			
			// Show all the infoboxes...
			$('.e2-permissions-infobox', this.element).InfoBox('show');
			
		},
		
		build_summary: function() {
			var permissions = caches[this.options.keytype][this.options.name]['permissions'] || [];
			var groups = caches[this.options.keytype][this.options.name]['groups'] || [];
			var total = permissions[0].length + permissions[1].length + permissions[2].length + permissions[3].length;
			var ret = '<p>This record is accessible by '+groups.length+' groups and '+total+' users.</p>';
			return ret
		},
		
		build_controls: function() {
			var self = this;
			var controls = $(' \
				<ul class="e2l-options"> \
					<li class="e2-select"></li> \
					<li><span class="e2-permissions-advanced e2l-a">'+$.e2caret('up')+'Advanced</span></li> \
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
				$.e2caret('toggle', self.options.controls);
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
				var minimum = 2;
				if (keytype=='group'){minimum=0}
				add.FindControl({
					keytype: keytype,
					minimum: minimum,
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
				selectable: true,
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