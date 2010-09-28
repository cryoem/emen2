(function($) {
    $.widget("ui.MapSelect", {
		options: {
			show: true,
			recid: null,
			status: null,
			cb: function(self, selected){}
		},
				
		_create: function() {
			if (this.options.show) {
				this.build();
			}
		},

		build: function() {
			var self = this;
		
			$('a.map', this.element).each(function() {
				var t = $(this);
				var recid = parseInt(t.attr('data-recid'));
				var i = $('<input type="checkbox" name="recordselect" />');
				if ($.inArray(recid, self.options.status) > -1) {
					i.attr('checked', 'checked');
					t.addClass('add');
				} else {
					i.attr('checked', null);
				}
				i.attr('data-recid', recid);
				t.before(i);
			});
		
			$('input[name=recordselect]', this.element).click(function() {
				var c = self.bfs($(this).attr('data-recid'), caches['children']);
				var state = $(this).attr('checked');
				$.each(c, function() {
					$('input[data-recid='+this+']').attr('checked', state);
				});

			});
			
			this.element.prepend('<div class="controls bigbutton"><img class="spinner" style="display:none" src="'+EMEN2WEBROOT+'/static/images/spinner.gif"><input type="button" value="Save" name="save" /></div>');
			$('input[name=save]', this.element).click(function() {
				self.save();
			})

		},
		
		save: function() {
			var self = this;
			var recids = $.makeArray($('input[name=recordselect]:checked').map(function(){return parseInt($(this).attr('data-recid'))}));
			var collapsed = [];
			$.each(recids, function() {
				var c = caches['collapsed'][this] || [];
				for (var i=0;i<c.length;i++) {
					collapsed.push(c[i]);
				}				
			});
			
			var selected = this.unique(recids.concat(collapsed));
			this.default_cb(this, selected);
			//this.options.cb(this, selected);
		},
		
		default_cb: function(self, selected) {
			$('.spinner', this.element).show();
			var remove = [];
			var add = [];

			for (var i=0;i<selected.length;i++) {
				if ($.inArray(selected[i], this.options.status)==-1) {
					add.push(selected[i]);
				}
			}
			
			if (this.options.status.length > 0) {			
				for (var i=0;i<this.options.status.length;i++) {
					if ($.inArray(this.options.status[i], selected)==-1) {
						remove.push(this.options.status[i]);
					}
				}
			}
			//console.log("Add: ", add.length);
			//console.log("Remove: ", remove.length);
			//return

			

			$.jsonRPC("addgroups", [add, ['publish']], function(){ 
				$.jsonRPC("removegroups", [remove, ['publish']], function() {
					$('.spinner', self.element).hide();
					window.location = window.location;
				});
			});
		},
			
		// JS has no sets
		unique: function(li) {
			var o = {}, i, l = li.length, r = [];
			for(i=0; i<l;i++) o[li[i]] = li[i];
			for(i in o) r.push(o[i]);
			return r;
		},
		
	
		bfs: function(root, tree) {
			root = parseInt(root);
			var stack = tree[root] || [];
			stack = stack.slice();
			var seen = stack.slice();
			seen.push(root);
			while (stack.length) {
				var cur = stack.pop();
				var c = tree[cur] || [];
				for (var i=0; i < c.length; i++) {
		                        stack.push(c[i]);
					seen.push(c[i]);
				}
			}
			return seen
		},

				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);