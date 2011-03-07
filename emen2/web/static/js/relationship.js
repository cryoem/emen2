/////////////////////////////////////////////
//////// Relationship Editor    /////////////
/////////////////////////////////////////////


(function($) {
    $.widget("ui.RelationshipControl", {

		options: {
			action: "reroot",
			attach: false,
			cb: function(){},
			expandable: true,
			build: false,
			root: null,
			keytype: "record",
			embed: true,
			mode: "children"
		},

		_create: function() {
			var self = this;
			this.built = 0;
			
			this.options.mode = this.element.attr('data-mode') || this.options.mode;
			this.options.root = this.element.attr('data-root') || this.options.root;
			this.options.keytype = this.element.attr('data-keytype') || this.options.keytype;	
				
			console.log(this.options);	
				
			if (this.options.attach) {
				this.bind_ul(this.element);
			} else {			
				this.element.click(function() {
					self.event_click();
				});	
				this.event_click();
			}
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
			
			// build the ul.ulm elements, one for parents, and children
			// header
			var p = $('<div class="clearfix" style="border-bottom:solid 1px #ccc;padding-bottom:6px;margin-bottom:6px;"> \
						<div class="floatleft" style="width:262px;">Parents</div> \
						<div class="floatleft" style="width:262px;"> \
							<input name="root" type="text" size="6" class="floatleft" style="font-size:10pt" /> \
							<div class="action floatleft" style="font-size:10pt"></div> \
							</div> \
						<div class="floatleft" style="width:262px;">Children</div> \
					</div>');
				
			var action = $('<select> \
				<option value="reroot">Navigate</option> \
				<option value="select">Select</option> \
				<option value="move">Move</option> \
				<option value="copy">Copy</option> \
				<option value="delete">Delete</option> \
				<option value="addparent">Add Parent</option> \
				<option value="addchild">Add Child</option> \
				</select>');
			action.val(this.options.action);
			action.change(function() {
				self.setaction($(this).val());
			});
			
			$('.action', p).append(action);

			var parents = $('<div class="ulm parents" style="float:left;width:262px"></div>');
			var children = $('<div class="ulm children"style="float:left"></div>');

			this.tablearea.append(p, parents, children);
			this.build_root(this.options.root);

		},
		
		// Send the RPC request to get info to build (or rebuild) the root element..
		build_root: function(key) {
			var self = this;

			// Set the root..
			$('input[name=root]', this.element).val(key);


			var children_ul = $('.ulm.children', this.element);
			var parents_ul = $('.ulm.parents', this.element);
			parents_ul.empty();			
			parents_ul.append('<img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" />');
			children_ul.empty();
			//children_ul.append('<img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" />');

			// Rebuild the root element
			var root_img = $('<img class="expand" src="'+EMEN2WEBROOT+'/static/images/bg-open.'+self.options.mode+'.png" />');
			var root_a = $('<a data-key="'+key+'">'+this.getname(key)+'</a>');
			var root_li = $('<li></ul>');
			root_li.append(root_a, root_img);
			var root_ul = $('<ul></ul>');
			root_ul.append(root_li);
			children_ul.append(root_ul);

			// bind the children ul
			this.bind_ul(children_ul);

			// build the root node and first level of children
			this.expand(children_ul.find('li'));
			
			// get the parents through an RPC call
			$.jsonRPC("getparents", [key, 1, null, this.options.keytype], function(parents) {
				caches['parents'][key] = parents;
				self.getviews(parents, function(){

					// build the parents..
					parents_ul.empty();				
					var ul = $('<ul></ul>');
					$.each(parents, function() {
						var i = $('<li><a href="'+EMEN2WEBROOT+'/'+self.options.keytype+'/'+this+'" data-key="'+this+'">'+self.getname(this)+'</a></li>');
						ul.append(i);
					});
					parents_ul.append(ul);
					
					// grumble... needs this to keep from collapsing
					parents_ul.append('&nbsp;');
					
					// rebind!
					self.bind_ul(parents_ul);

				});
			})

		},

		setaction: function(action) {
			//var oldaction = this.options.action;
			//if (oldaction == this.options.action) {return}
			// var select_actions = ['move', 'copy', 'delete'];
			// var add_actions = ['addparent', 'addchild']
			// if ($.inArray(oldaction, select_actions) == $.inArray(action, add_actions)) {
			// 	console.log("changing tool from", oldaction, newaction);
			// }
			this.options.action = action;
			$(".mapselect", this.element).each(function(){$(this).removeClass('mapselect')})
		},
		
		action: function(e) {
			var self = this;
			var target = $(e.target);
			var key = target.attr('data-key')
			if (this.options.action == null) {return}				
			e.preventDefault();

			// some tool specific behaviors..
			var parent = target.attr('data-parent');
			if (this.options.action == "move" || this.options.action == "copy" || this.options.action == "delete" || this.options.action == "select") {
				if (parent != null) {							
					target.toggleClass("mapselect");
				}
			} else if (this.options.action == "addparent" || this.options.action == "addchild") {

			} else if (this.options.action == "reroot") {
				// rebuild the root..
				this.build_root(key);
			}
		},
		
		dropaction: function(e, ui) {
			var self = this;
			var target = $(e.target);
			var rels = $(ui.helper).data('keys');
			var newparent = target.data('key');
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
						$(this).dialog( "close" );
						// console.log(rels, newrels);
						// $.jsonRPC("pcrelink", [rels, newrels], function() {
						// 	$.each(refresh, function() {
						// 		self.refresh(this);
						// 		// needs a fade-out effect......
						// 	})
						// });
					},
					Cancel: function() {
						$(this).dialog( "close" );
					}
				}
			});			
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
		
		// create a helper element for drag-and-drop
		helper: function(ui, e) {
			var self = this;
			var keys = this.getselected(ui.target);
			if (this.options.action == "copy") {
				var text = "Adding a parent to "+keys.length+" items";
			} else if (this.options.action == "move") {
				var text = "Moving "+keys.length+" items";
			} else {
				return
			}			
			var helper = $('<div class="mapselect_helper">'+text+'</div>');
			helper.data('keys', keys);
			return helper
		},
		
		// handle type-specific details for caching recnames/desc_short, then execute a callback..
		getviews: function(keys, cb) {
			var self = this;
			if (self.options.keytype == "record") {
				$.jsonRPC("renderview", [keys, null, "recname"], function(recnames){
					$.each(recnames, function(k,v) {caches['recnames'][k]=v});
					cb();
				});					
			} else if (self.options.keytype == "recorddef") {
				$.jsonRPC("getrecorddef", [keys], function(rds){
					$.each(rds, function() {caches['recorddefs'][this.name]=this});
					cb();
				});											
			} else if (self.options.keytype == "paramdef") {
				$.jsonRPC("getparamdef", [keys], function(pds){
					$.each(pds, function() {caches['paramdefs'][this.name]=this});
					cb();
				});						
			}			
		},
		
		// more type-specific handling..
		getname: function(item) {
			if (this.options.keytype == 'record') {
				return caches['recnames'][item] || String(item)
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
				this.expand(elem.parent());
			}			
		},
		
		// rebuild a branch
		expand: function(elem) {
			// elem is the LI			
			var self = this;
			var key = elem.children('a').attr('data-key');
			var img = elem.children('img');
			img.attr('src', EMEN2WEBROOT+'/static/images/spinner.gif'); 

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
				
				self.getviews(tree[key], function(){self.drawtree(elem)});
			
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
				sortby[this] = self.getname(this);
			});
			var sortkeys = $.sortstrdict(sortby);
			sortkeys.reverse();			
						
			$.each(sortkeys, function() {
				var line = $('<li> \
					<a data-key="'+this+'" data-parent="'+key+'" href="'+EMEN2WEBROOT+'/'+self.options.keytype+'/'+this+'/">'+self.getname(this)+'</a> \
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

			if (this.options.attach) {
				return
			}

			// this should be made simpler...
			$("a[data-key]", root).droppable({
				tolerance: 'pointer',
				addClasses: false,
				hoverClass: "maphover",
				activeClass: "mapactive",
				drop: function(e, ui) {self.dropaction(e, ui)}
			});	

			$("a", root).click(function(e) {self.action(e)});
			
			$("a[data-parent]", root).draggable({
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


$(document).ready(function() {
	$('.ulm').RelationshipControl({
		"attach":true
	});
});	






















