(function($) {
    $.widget("ui.MapSelect", {
		options: {
			show: true,
			recid: null,
			status: null,
			ext_save: null,
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
			
			if (!this.options.ext_save) {
				this.options.ext_save = $('<div class="controls save"><img class="spinner" src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /><input type="button" value="Save" name="save" /></div>');
				this.element.prepend(this.options.ext_save);				
			}
			$('input[name=save]', this.options.ext_save).click(function() {self.save()});
			

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
			$('.spinner', this.options.ext_save).show();
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
			
			$.jsonRPC("addgroups", [add, ['publish']], function(){ 
				$.jsonRPC("removegroups", [remove, ['publish']], function() {
					$('.spinner', self.options.ext_save).hide();
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





////////////////////


(function($) {
    $.widget("ui.MapDrag", {

		_create: function() {
			this.root = $(this.element).attr('data-root');
			this.keytype = $(this.element).attr('data-keytype');
			this.mode = $(this.element).attr('data-mode');
			this.bind_ul(this.element);
			this.recids = [];
		},

		getselected: function(target) {
			var keys = [];

			$('a.mapselect', this.element).each(function() {
				var parent = $(this).attr('data-parent');
				var key = $(this).attr('data-key');
				keys.push([parent,key]);
			});
			
			if (keys.length == 0 && target != null) {
				var parent = $(target).attr('data-parent');
				var key = $(target).attr('data-key');
				keys.push([parent,key]);
			}
						
			return keys
		},
		
		helper: function(ui, e) {
			var self = this;
			var keys = self.getselected(ui.target);
			var helper = $('<div class="mapselect_helper">Moving '+keys.length+' items</div>');
			helper.data('keys', keys);
			return helper
		},
		
		getname: function(item) {
			if (this.keytype == 'record') {
				return caches['recnames'][item] || item
			} else if (this.keytype == 'paramdef') {
				return caches['paramdefs'][item].desc_short || item
			} else if (this.keytype == 'recorddef') {
				return caches['recorddefs'][item].desc_short || item
			}
			
		},
		
		refresh: function(key) {
			// takes a key and refreshes all currently open LIs
			var self = this;
			$('a[data-key='+key+']').each(function() {
				self.expand($(this).parent());
			});
		},

		toggle: function(elem) {
			// elem is the expand image element			
			var self = this;
			var elem = $(elem);
		
			if (elem.hasClass('expanded')) {
				elem.removeClass('expanded');
				elem.siblings('ul').hide();
				elem.attr('src', EMEN2WEBROOT+'/static/images/bg-open.'+this.mode+'.png');
			} else {
				elem.addClass('expanded');
				elem.attr('src', EMEN2WEBROOT+'/static/images/bg-close.'+this.mode+'.png');				
				this.expand(elem.parent());
			}
			
		},
		
		expand: function(elem) {
			// elem is the LI			
			var self = this;
			var key = elem.children('a').attr('data-key');

			// remove current ul..
			elem.find('ul').remove();

			// build loading... don't forget to adjust top!
			var loading = $('<ul><li><img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" class="spinner" style="display:inline" alt="Loading" /></li></ul>')
			elem.append(loading);
			// var height = p.find('a.draggable').height();
			// loading.css('top', -height);
						
			var method = "getchildtree";
			if (this.mode == "parents") {
				method = "getparenttree";
			}
		
			$.jsonRPC(method, [key, 2, null, this.keytype], function(tree){
				// we also need to get the recnames..
				if (self.keytype == "record") {
					$.jsonRPC("renderview", [tree[key], null, "recname"], function(recnames){
						$.each(recnames, function(k,v) {caches['recnames'][k]=v});
						self.drawtree(elem, tree);						
					});					
				} else if (self.keytype == "recorddef") {
					$.jsonRPC("getrecorddef", [tree[key]], function(rds){
						$.each(rds, function() {caches['recorddefs'][this.name]=this});
						self.drawtree(elem, tree);						
					});											
				} else if (self.keytype == "paramdef") {
					$.jsonRPC("getparamdef", [tree[key]], function(pds){
						$.each(pds, function() {caches['paramdefs'][this.name]=this});
						self.drawtree(elem, tree);						
					});						
				}
			
			});				
		},

		drawtree: function(elem, tree) {
			var self = this;
			var newl = $('<ul></ul>');
			var key = elem.find('a.draggable').attr('data-key');
			
			// lower-case alpha sort...
			var sortby = {};
			$.each(tree[key], function() {
				sortby[this] = self.getname(this);
			});
			var sortkeys = $.sortstrdict(sortby);
			sortkeys.reverse();
		
			$.each(sortkeys, function() {
				var line = $('<li><a class="draggable" data-key="'+this+'" data-parent="'+key+'" href="'+EMEN2WEBROOT+'/'+self.keytype+'/'+this+'/">'+self.getname(this)+'</a></li>');
				if (tree[this]) {
					var expand = $('<img class="expand" alt="'+tree[this].length+' children" src="'+EMEN2WEBROOT+'/static/images/bg-open.'+self.mode+'.png" />');
					//expand.click(function() {self.toggle(this)});
					line.append(expand);
				}
				newl.append(line);
			});
			elem.find('ul').remove();
			
			// don't forget to adjust top
			var h = elem.find('a.draggable').height();
			elem.append(newl);
			newl.css('top', -h);
			// var h2 = newl.height();
			// var h3 = elem.parent().height();
			// elem.parent().css('height', h3-h2);
			
			this.bind_ul(newl);
		},
	
		bind_ul: function(root) {
			var self = this;
			
			$('ul', root).each(function() {
				var elem = $(this);
				var h = elem.siblings('a.draggable').height();
				elem.css('top', -h);
				if (self.mode=="parents") {
					// var h2 = elem.height();
					// var h3 = elem.parent().height();
					// console.log(elem, h, h2, h3);
					//elem.parent().css('height', h3-16);
				}
			});

			
			$('img.expand', root).click(function() {self.toggle(this)});

			// parents mode is currently not supported -- a little too complicated..
			if (this.mode=="parents") {
				return
			}

			$("a.draggable[data-parent]", root).click(function(e) {
				if (!e.shiftKey) {return}
				e.preventDefault();
				$(this).toggleClass("mapselect");
			}).draggable({
				addClasses: false,
				helper: function(ui, e){return self.helper(ui, e)}
			});
			
			// this should be made simpler...
			$("a[data-key]", root).droppable({
				tolerance: 'pointer',
				addClasses: false,
				hoverClass: "maphover",
				activeClass: "mapactive",
				drop: function(event, ui) {
					var rels = $(ui.helper).data('keys');
					var newparent = $(this).data('key');
					var newrels = [];
					var refresh = [newparent];
					$.each(rels, function() {
						newrels.push([newparent, this[1]]);
						if ($.inArray(this[0], refresh)==-1) {refresh.push(this[0])}
					});
					
					// confirm...
					$('<div title="Confirm">Do you want to move these '+rels.length+' items?</div>').dialog({
						resizable: false,
						height: 200,
						modal: true,
						buttons: {
							"OK": function() {
								$( this ).dialog( "close" );
								$.jsonRPC("pcrelink", [rels, newrels], function() {
									$.each(refresh, function() {
										self.refresh(this);
										// needs a fade-out effect......
									})
								});
							},
							Cancel: function() {
								$( this ).dialog( "close" );
							}
						}
					});
				}
			});			
		},
	
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);




$(document).ready(function() {
	$('.ulm').MapDrag();
});	













