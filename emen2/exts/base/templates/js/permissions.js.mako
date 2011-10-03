(function($) {
	
	$.widget('emen2.PermissionsControl', {
		options: {
			keytype: 'record',
			name: null,
			edit: false,
			show: true,
			controls: null,
			groups: true
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
			var self = this;
			var item = caches[this.options.keytype][this.options.name];
			if (!item) {
				var args = {}
				args['keytype'] = this.options.keytype;
				args['names'] = this.options.name;
				$.jsonRPC.call('get', {'keytype':this.options.keytype, 'names':this.options.name}, function(item) {
					caches[item.keytype][item.name] = item;
					self._build();
				});
			} else {
				this._build();
			}
		},
		
		_build: function() {
			var self = this;
			var permissions = caches[this.options.keytype][this.options.name]['permissions'] || [];
			var groups = caches[this.options.keytype][this.options.name]['groups'] || [];
			this.element.empty();

			this.element.append(this._build_level('Groups', 'groups', groups, 'group'));
			this.element.append(this._build_level('Read-only', 'read', permissions[0]));
			this.element.append(this._build_level('Comment', 'comment', permissions[1]));
			this.element.append(this._build_level('Write', 'write', permissions[2]));
			this.element.append(this._build_level('Owners', 'admin', permissions[3]));
			
			if (this.options.controls) {
				var controls = $(' \
					<ul class="e2l-options"> \
						<li>Select <span class="e2l-a e2-permissions-all">all</span> or <span class="e2l-a e2-permissions-none">none</span><br /></li> \
						<li><span class="e2-permissions-advanced e2l-a">'+$.caret('up')+'Advanced</span></li> \
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


				$('.e2-permissions-advanced', controls).click(function(){
					$.caret('toggle', self.options.controls);
					$('.e2l-controls', self.options.controls).toggle();
					$('.e2l-advanced', self.options.controls).toggle();
				});
				
				$('.e2-permissions-all', controls).click(function(){$('input:checkbox', self.element).attr('checked', 'checked')});
				$('.e2-permissions-none', controls).click(function() {$('input:checkbox', self.element).attr('checked', null)});				

				$('input[name=add]', controls).click(function(){self.save('add')})
				$('input[name=remove]', controls).click(function(){self.save('remove')})
				$('input[name=overwrite]', controls).click(function(){self.save('overwrite')})
				$('input[name=save]', controls).click(function(){self.save()});
				
				this.options.controls.append(controls);
			}			
		},
		
		_build_level: function(lab, level, l, keytype) {
			var self = this;
			var param = 'permissions.'+level;
			var keytype = (keytype || 'user');
			if (level == 'groups') {
				param = 'groups'
			}

			var ret = $('<div></div>')
			
			var header = $('<h4>'+lab+'</h4>');
			if (this.options.edit) {
				var add = $('<input type="button" data-level="'+level+'" data-keytype="'+keytype+'" value="+" class="e2l-float-left" style="margin-right:10px" /> ');
				var minimum = 2;
				if (keytype=='group'){minimum=0}
				add.FindControl({
					keytype: keytype,
					minimum: minimum,
					cb: function(w, value) {
						var level = w.element.attr('data-level');
						self.add(level, value);
					}
				});
				header.append(add);
			}

			var div = $('<div class="e2l-cf"></div>');
			div.attr('data-level', level);
			for (var i=0;i<l.length;i++) {
				var d = $('<div></div>');
				d.InfoBox({
					keytype: keytype,
					name: l[i],
					selectable: true,
					input: ['checkbox', param, true]
				});
				div.append(d);
			}
			
			// We have to put in one last empty element
			div.append('<input type="hidden" name="'+param+'" value="" class="e2-permissions-hidden" />');

			ret.append(header, div);
			return ret
		},
		
		add: function(level, name) {
			var keytype = 'user';
			var param = 'permissions.'+level;
			if (level=='groups') {
				keytype = 'group';
				param = 'groups';
			}

			var level = $('div[data-level='+level+']');
			var d = $('<div></div>');
			d.InfoBox({
				keytype: keytype,
				name: name,
				selectable: true,
				input: ['checkbox', param, true]
			});
			level.append(d);
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