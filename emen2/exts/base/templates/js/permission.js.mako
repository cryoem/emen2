(function($) {
	
	$.widget('emen2.PermissionsControl', {
		options: {
			keytype: 'record',
			name: null,
			edit: false,
			show: false,
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
				var options = $('<div class="e2l-options">');
				options.append(' \
					Select <span class="e2l-a e2-permissions-all">all</span> / <span class="e2l-a e2-permissions-none">none</span><br /> \
					<input type="checkbox" name="recurse" value="recurse" id="e2-permissions-mode"><label for="e2-permissions-mode">Recurse</label><br /> \
					<ul class="e2l-nonlist e2l-hide"> \
						<li><input type="checkbox" name="filt" value="filt" checked id="e2-permissions-filt"><label for="e2-permissions-filt">Ignore failures</label><br /></li> \
				 		<li><input type="radio" name="recurse_mode" value="add" id="e2-permissions-mode-add" checked><label for="e2-permissions-mode-add">Add to children</label></li> \
			 			<li><input type="radio" name="recurse_mode" value="remove" id="e2-permissions-mode-remove"><label for="e2-permissions-mode-remove">Remove from children</label></li> \
				 		<li><input type="radio" name="recurse_mode" value="overwrite" id="e2-permissions-mode-overwrite"><label for="e2-permissions-mode-overwrite">Overwrite children</label></li> \
				 	</ul>');
				
				$('.e2-permissions-all', options).click(function(){$('input:checkbox', self.element).attr('checked', 'checked')});
				$('.e2-permissions-none', options).click(function() {$('input:checkbox', self.element).attr('checked', null)});
				
				$('input[name=recurse]', options).click(function(){
					var t = $(this);
					var state = t.attr('checked');
					if (state) {
						$('ul', options).show();
						// $('ul input, ul label', controls).attr('disabled', false);
					} else {
						$('ul', options).hide();
						// $('ul input, ul label', controls).attr('disabled', true);						
					}
				})

				var controls = $('<div class="e2l-controls"></div>');
				controls.append('<input type="button" name="save" value="Save permissions" />');
				$('input[name=save]', controls).click(function(e){self.save(e)})
				this.options.controls.append(options, controls);
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
						console.log(w, value);
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
		
		save: function(e) {
			e.preventDefault();
			var self = this;

			// Copy options into the form...
			$('.e2-edit-copied', this.element).remove();
			var copied = $('<div class="e2-edit-copied e2l-hide"></div>');

			var recurse = $('input[name=recurse]:checked', this.options.controls).val();
			var recurse_mode = $('input[name=recurse_mode]:checked', this.options.controls).val();
			var filt = $('input[name=filt]:checked', this.options.controls).val();
			if (recurse) {
				copied.append('<input type="hidden" name="recurse" value="'+recurse+'" />');
				copied.append('<input type="hidden" name="recurse_mode" value="'+recurse_mode+'" />');
				copied.append('<input type="hidden" name="filt" value="'+filt+'" />');
			}
			this.element.append(copied);
			
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