/////////////////////////////////////////////
//////// Relationship Editor    /////////////
/////////////////////////////////////////////


(function($) {
    $.widget("ui.RelationshipControl", {

		options: {
			tool: "select",
			expandable: true,
			build: false,
			root: null,
			keytype: "record",
			embed: false,
			mode: "children"
		},

		_create: function() {
			console.log("building relationship control, root is", this.options.root);
			var self = this;
			this.built = 0;
			this.element.click(function() {
				self.event_click();
			});	
			this.event_click();
			// 	this.bind_ul(this.element);
		},
	
		event_click: function() {
			var self = this;
			this.build();
		},
			
		// Build the container..	
		build: function() {
			if (this.built) {
				return
			}
			this.built = 1;			
			
			var self = this;
			this.dialog = $('<div class="browser" />');
			this.tablearea = $('<div class="clearfix"/>');
			this.dialog.append(this.tablearea);
			
			if (this.options.embed) {
				this.element.append(this.dialog);
			} else {
				var pos = this.element.offset();
				this.dialog.attr("title", "Relationships");
				this.dialog.dialog({
					position:[pos.left, pos.top+this.element.outerHeight()],				
					autoOpen: false
					//modal: this.options.modal
				});			
			}
			
			// build the table area to reflect the current ID
			this.build_root(this.options.root);
		},
		
		// Send the RPC request to get info to build (or rebuild) the root element..
		build_root: function(key) {
			var self = this;
			this.tablearea.empty();

			// build the ul.ulm elements, one for parents, and children
			// the parents will be filled in with a callback,
			// the children will use this.expand to take care of event handlers

			// container
			var p = $('<div class="clearfix" style="padding-bottom:4px;border-bottom:solid 1px #ccc;"> \
						<div class="floatleft" style="width:262px;">Parents</div> \
						<div class="floatleft" style="width:262px;">This Record</div> \
						<div class="floatleft" style="width:262px;">Children</div> \
					</div>');

			var parents = $('<div class="ulm parents" style="float:left;width:262px"><ul></ul></div>');
			var children = $('<div class="ulm children"style="float:left"><ul><li><a href="" data-key="'+this.options.root+'"></a></li></ul></div>');
		
			this.tablearea.append(p, parents, children);
			// it seems it needs to be in the DOM before .wrap will work..

			this.expand(children.find('li'));
		},

		
		event_select: function(elem) {
			var self = this;
			var key = $(elem).attr('data-key');
			self.rebuild(key);
		},
	
		///////////////////
		// Map Select...
		///////////////////

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
			var keys = this.getselected(ui.target);
			var helper = $('<div class="mapselect_helper">Moving '+keys.length+' items</div>');
			helper.data('keys', keys);
			return helper
		},
		
		getname: function(item) {
			if (this.options.keytype == 'record') {
				return caches['recnames'][item] || item
			} else if (this.options.keytype == 'paramdef') {
				return caches['paramdefs'][item].desc_short || item
			} else if (this.options.keytype == 'recorddef') {
				return caches['recorddefs'][item].desc_short || item
			}
			
		},
		
		// rebuild all branches for key
		refresh: function(key) {
			var self = this;
			$('a[data-key='+key+']').each(function() {
				self.expand($(this).parent());
			});
		},


		// expand/contract a branch		
		toggle: function(elem) {
			// elem is the expand image element			
			var self = this;
			var elem = $(elem);
		
			// pass the img's parent LI to this.expand
			if (elem.hasClass('expanded')) {
				elem.removeClass('expanded');
				elem.siblings('ul').remove();
				elem.attr('src', EMEN2WEBROOT+'/static/images/bg-open.'+this.options.mode+'.png');
			} else {
				elem.attr('src', EMEN2WEBROOT+'/static/images/spinner.gif'); 
				this.expand(elem.parent());
			}			
		},
		
		// rebuild a branch
		expand: function(elem) {
			// elem is the LI			
			var self = this;
			var key = elem.children('a').attr('data-key');

			// remove current ul..
			elem.find('ul').remove();

			var method = "getchildtree";
			if (this.options.mode == "parents") {
				method = "getparenttree";
			}
		
			$.jsonRPC(method, [key, 2, null, this.options.keytype], function(tree){
				// put these in the cache..
				$.each(tree, function(k,v) {
					caches[self.options.mode][k]=v;
				});
				
				// we also need to get the recnames..
				if (self.options.keytype == "record") {
					$.jsonRPC("renderview", [tree[key], null, "recname"], function(recnames){
						$.each(recnames, function(k,v) {caches['recnames'][k]=v});
						self.drawtree(elem);						
					});					
				} else if (self.options.keytype == "recorddef") {
					$.jsonRPC("getrecorddef", [tree[key]], function(rds){
						$.each(rds, function() {caches['recorddefs'][this.name]=this});
						self.drawtree(elem);						
					});											
				} else if (self.options.keytype == "paramdef") {
					$.jsonRPC("getparamdef", [tree[key]], function(pds){
						$.each(pds, function() {caches['paramdefs'][this.name]=this});
						self.drawtree(elem);						
					});						
				}
			
			});				
		},

		// draw a branch.. elem is the LI
		drawtree: function(elem) {
			var self = this;
			var newl = $('<ul></ul>');
			var key = elem.find('a').attr('data-key');
			var img = elem.find('img');

			img.addClass('expanded');
			img.attr('src', EMEN2WEBROOT+'/static/images/bg-close.'+this.options.mode+'.png');
			
			// lower-case alpha sort...
			var sortby = {};
			$.each(caches[this.options.mode][key], function() {
				sortby[this] = "test";//self.getname(this);
			});
			var sortkeys = $.sortstrdict(sortby);
			sortkeys.reverse();			
						
			$.each(sortkeys, function() {
				var line = $('<li> \
					<a class="draggable" data-key="'+this+'" data-parent="'+key+'" href="'+EMEN2WEBROOT+'/'+self.options.keytype+'/'+this+'/">'+self.getname(this)+'</a> \
					</li>');

				if (caches[self.options.mode][this] && self.options.expandable) {
					var expand = $(' \
						<img class="expand" alt="'+caches[self.options.mode][this].length+' \
						children" src="'+EMEN2WEBROOT+'/static/images/bg-open.'+self.options.mode+'.png" />');
					line.append(expand);
				}
				newl.append(line);
			});
			elem.find('ul').remove();
						
			// don't forget to adjust top
			elem.append(newl);
			var h = newl.siblings('a').height();
			newl.css('margin-top', -h);
			newl.css('min-height', h);
			this.bind_ul(newl);
		},
	
		// add the event handlers to a UL and its LI children
		bind_ul: function(root) {
			var self = this;
			
			// height adjustment
			$('ul', root).each(function() {
				var elem = $(this);
				var h = elem.siblings('a').height();
				elem.css('margin-top', -h);
				elem.css('min-height', h);
			})
			
			$('img.expand', root).click(function() {self.toggle(this)});

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

			// parents mode is currently not supported -- a little too complicated..
			if (this.options.mode=="parents") {
				return
			}

			$("a[data-parent]", root).click(function(e) {
				if (self.options.tool==null) {return}
				e.preventDefault();
				$(this).toggleClass("mapselect");
			}).draggable({
				addClasses: false,
				helper: function(ui, e){return self.helper(ui, e)}
			});		
		
		},
	
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);


// $(document).ready(function() {
// 	$('.ulm').MapSelect();
// });	






















