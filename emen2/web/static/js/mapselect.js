(function($) {
    $.widget("ui.MapSelect", {

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
				elem.siblings('ul').remove();
				elem.attr('src', EMEN2WEBROOT+'/static/images/bg-open.'+this.mode+'.png');
			} else {
				elem.attr('src', EMEN2WEBROOT+'/static/images/spinner.gif'); 
				this.expand(elem.parent());
			}
			
		},
		
		expand: function(elem) {
			// elem is the LI			
			var self = this;
			var key = elem.children('a').attr('data-key');

			// remove current ul..
			elem.find('ul').remove();

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
			var img = elem.find('img');
			
			img.addClass('expanded');
			img.attr('src', EMEN2WEBROOT+'/static/images/bg-close.'+this.mode+'.png');
			
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
					line.append(expand);
				}
				newl.append(line);
			});
			elem.find('ul').remove();
			
			// don't forget to adjust top
			elem.append(newl);
			var h = newl.siblings('a.draggable').height();
			newl.css('margin-top', -h);
			newl.css('min-height', h);
			this.bind_ul(newl);
		},
	
		bind_ul: function(root) {
			var self = this;
			
			// height adjustment
			$('ul', root).each(function() {
				var elem = $(this);
				var h = elem.siblings('a.draggable').height();
				elem.css('margin-top', -h);
				elem.css('min-height', h);
			})
			
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
	$('.ulm').MapSelect();
});	













