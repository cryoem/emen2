(function($) {
	
	$.widget('emen2.SimpleRelationshipControl', {
		options: {
			name: null,
			show: true
		},

		_create: function() {
			this.built = 0;
			var self = this;
			if (this.options.show) {this.build()}
			
		},
		
		rebuild: function() {
			this.built = 0;
			this.build();
		},
		
		build: function() {
			if (this.built) {return}
			var self = this;
			var rec = this.cacherec();
			var getrecs = rec.children.concat(rec.parents);
			
			$.jsonRPC.call('getrecord', [getrecs], function(recs) {
				$.each(recs, function(k,v) {caches['record'][v.name] = v});
				
				$.jsonRPC.call('renderview', [getrecs], function(d) {
					$.each(d, function(k,v) {caches['recnames'][k] = v});

					// get the recorddefs..
					var args = {};
					args['record'] = getrecs
					$.jsonRPC.call('findrecorddef', args, function(rds) {
						$.each(rds, function(k,v) {caches['recorddef'][v.name] = v})
						self._build();
					});
				});
			});
		}, 
		
		_build: function() {
			this.built = 1;
			var self = this;
			// Build a simple form
			var rec = this.cacherec();
			var parents = rec.parents;
			var children = rec.children;
			
			var p = this.build_summary(parents)
			var c = this.build_summary(children)
			
			this.element.append('<h4>Relationships</h4>');
			var label = 'parent';
			if (parents.length > 1) {label = 'parents'}		
			this.element.append('<p>This record has '+this.build_summary(parents, 'parents')+' and '+this.build_summary(children, 'children')+'</p>');
			
			$('.e2-relationship-rectype', this.element).click(function() {
				var state = $(this).attr('data-checked');
				if (state=='checked') {
					$(this).attr('data-checked', '');
					state = true;
				} else {
					$(this).attr('data-checked', 'checked');
					state = false
				}
				var rectype = $(this).attr('data-rectype');
				var reltype = $(this).attr('data-reltype');
				$('input[name='+reltype+'][data-rectype='+rectype+']', this.element).attr('checked', state);
			});
			
			var form = $('<form action="'+EMEN2WEBROOT+'/record/'+this.options.name+'/edit/rel/" method="post" name="rel"></form>')
			form.append(this.build_table());
			form.append('<input type="hidden" name="method" value="" />');
			
			var controls = $('<div class="e2l-controls" />');

			var relink = $('<input type="button" class="big e2l-save" value="Move" />');
			relink.click(function() {
				console.log("moving...");
			})

			var pclink = $('<input type="button" class="big e2l-save" value="Remove" />');
			pclink.click(function() {
				$('input[name=method]', this.element).val('pclink')
				$('form[name=rel]', this.element).submit();
			});
			controls.append(relink, ' or &nbsp;', pclink); //, ' selected relationships');

			form.append(controls);
			this.element.append(form);

		},
		
		build_summary: function(value, label) {
			var ct = {}
			$.each(value, function(k,v){
				var r = caches['record'][v] || {};
				if (!ct[r.rectype]){ct[r.rectype]=[]}
				ct[r.rectype].push(this);
			});				

			var ce = [];
			$.each(ct, function(k,v) {
				var rd = caches['recorddef'][k] || {};
				var adds = '';
				if (v.length > 1) {adds='s'}
				ce.push(v.length+' '+rd.desc_short+' <span data-checked="checked" data-reltype="'+label+'" data-rectype="'+k+'" class="small e2l-a e2-relationship-rectype">(select)</span>');
			});
			
			var pstr = '';
			if (!value) {
				pstr = '<span>no '+label+'</span>';
			} else if (ce.length == 1) {
				pstr = '<span>'+ce.join(', ')+' '+label+'</span>';
			} else {
				pstr = '<span>'+value.length+' '+label+'</span>, including '+ce.join(', ')
			}	
			return pstr
		},
		
		build_table: function() {
			var self = this;
			var rec = this.cacherec();
			var table = $('<div />');
			table.append('<br /><h4 class="e2l-clearfix"><input type="button" value="+" /> Parents</h4>');
			table.append('<ul class="e2l-nonlist e2-relationship-parents"></ul><br />');
			table.append('<h4 class="e2l-clearfix"><input type="button" value="+" /> Children</h4>');
			table.append('<ul class="e2l-nonlist e2-relationship-children"></ul><br />');
			for (var i=0;i<rec.parents.length;i++) {
				$('.e2-relationship-parents', table).append(this.build_td(rec.parents[i], 'parents'))
			}
			for (var i=0;i<rec.children.length;i++) {
				$('.e2-relationship-children', table).append(this.build_td(rec.children[i], 'children'))
			}
			return table

			// $('.e2-relationship-toggle', table).click(function(){
			// 	var state = $(this).attr('checked');
			// 	var reltype = $(this).attr('data-reltype');
			// 	$('input[name='+reltype+']', this.element).attr('checked', state || false);
			// 	// self.set_reltype(reltype, state);
			// });
			// return table
		},
		
		build_td: function(q, reltype) {
			if (q == null) {return '<td/><td />'}
			var rec = caches['record'][q];
			var recname = caches['recnames'][q];
			var id = 'e2-relationships-children-'+this.options.name+'-'+q;
			return '<li style="padding-bottom:5px;"><input type="checkbox" name="'+reltype+'" value="'+q+'" data-rectype="'+rec.rectype+'" id="'+id+'"/><label for="'+id+'">'+recname+'</label></li>'
		},
		
		cacherec: function() {
			return caches['record'][this.options.name];
		}
	})
	
	
	
    $.widget("emen2.RelationshipControl", {
		// Relationship BROWSER
		
		options: {
			action: "view",
			attach: false,
			controls: true,
			sitemap: false,
			cb: function(){},
			expandable: true,
			root: null,
			keytype: "record",
			embed: true,
			mode: "children",
			selecttext: "Select",
			cb: function(key){console.log(key)}
		},

		_create: function() {
			var self = this;
			this.built = 0;
			
			this.options.mode = this.element.attr('data-mode') || this.options.mode;
			this.options.root = this.element.attr('data-root') || this.options.root;
			this.options.keytype = this.element.attr('data-keytype') || this.options.keytype;	
										
			if (this.options.attach) {
				this.bind_ul(this.element);
				if (this.options.sitemap) {
					this.build_sitemap()
				}
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
	
		/////////////////////////////////
		// Build the container..	
		/////////////////////////////////
	
		build: function() {
			if (this.built) {
				return
			}
			this.built = 1;			
			
			var self = this;

			this.dialog = $('<div class="e2l-clearfix"></div>');

			// Append the table area to the dialog, then the dialog to the element..
			this.element.append(this.dialog);
					
			if (!this.options.controls) {
				var ul = $('<div class="e2-map e2-map-'+this.options.mode+'"></div>');
				this.dialog.append(ul);
				this.build_ul(ul, this.options.root);
				return
			}
			
			// build the ul.ulm elements, one for parents, and children
			var p = $(' <div class="e2l-clearfix" style="border-bottom:solid 1px #ccc;margin-bottom:6px;"> \
						<div class="e2-browser-parents .e2l-float-left" style="width:249px;"> Parents </div> \
						<div class="e2-browser-action .e2l-float-left" style="width:249px;">&nbsp;</div> \
						<div class="e2-browser-children .e2l-float-left" style="width:249px;"> Children </div> \
					</div>');
						
			var parents = $('<div class="e2-map e2-map-parents .e2l-float-left" style="width:245px"></div>');
			var children = $('<div class="e2-map e2-map-children .e2l-float-left" ></div>');
			this.dialog.append(p, parents, children);

			this.setaction(this.options.action);
			this.build_root(this.options.root);

			if (!this.options.embed) {
				this.dialog.attr("title", "Relationships");
				this.dialog.dialog({
					width: 820,
					height: 700, 
					autoOpen: true,
					modal: true
				});
			}
			
			if (this.options.embed) {
				this.build_addsimple();
			}
		},
		
		build_sitemap: function() {
			var p = $(' <div class="e2l-clearfix" style="border-bottom:solid 1px #ccc;margin-bottom:6px;"> \
						<div class="e2-browser-action .e2l-float-left" style="width:249px;">&nbsp;</div> \
						<div class="e2-browser-children .e2l-float-left" style="width:249px;"> Children </div> \
					</div>');						
			this.element.prepend(p);
			if (this.options.embed) {
				this.build_addsimple();
			}
			this.setaction(this.options.action);
		},
		
		build_addsimple: function() {
			var self = this;
			var cb = function(parent,key){}
			
			// Adding this back to help users..
			var addparents = $('<input type="button" name="addparents" value="+" />').click(function() {
				var cb = function(parent) {self._action_addrel(parent, self.options.root)}
				var i = $('<div></div>');
				i.RelationshipControl({root:self.options.root, embed: false, keytype:self.options.keytype, action:"select", selecttext:"Add Parent", cb:cb});
			});

			var addchildren = $('<input type="button" name="addchildren" value="+" />').click(function() {
				var cb = function(child) {self._action_addrel(self.options.root, child)}
				var i = $('<div></div>');
				i.RelationshipControl({root:self.options.root, embed: false, keytype:self.options.keytype, action:"select", selecttext:"Add Child", cb:cb});
			});			

			$('.e2-browser-parents', this.dialog).prepend(addparents);
			$('.e2-browser-children', this.dialog).prepend(addchildren);		
		},
		
		build_ul: function(elem, key) {
			elem.empty();
			
			// Rebuild the root element
			var root_img = $('<img class="e2-map-expand" src="'+EMEN2WEBROOT+'/static/images/bg-open.'+this.options.mode+'.png" />');
			var root_a = $('<a data-key="'+key+'">'+this.getname(key)+'</a>');
			var root_li = $('<li style="background:none"></li>');

			root_li.append(root_a, root_img);
			var root_ul = $('<ul></ul>');
			root_ul.append(root_li);

			elem.append(root_ul);

			// bind the children ul
			this.bind_ul(elem);

			// build the root node and first level of children
			this.expand(elem.find('li'));			
		},
		
		// Send the RPC request to get info to build (or rebuild) the root element..
		build_root: function(key) {
			var self = this;
			this.options.root = key;
			
			// Set the root..
			$('input[name=root]', this.dialog).val(key);

			var children_ul = $('.e2-map-children', this.dialog);
			var parents_ul = $('.e2-map-parents', this.dialog);

			parents_ul.empty();			
			parents_ul.append('<img class="e2l-spinner" src="'+EMEN2WEBROOT+'/static/images/spinner.gif" />');
			this.build_ul(children_ul, key);

			// get the parents through an RPC call
			$.jsonRPC.call("rel.parent", [key, 1, null, this.options.keytype], function(parents) {
				caches['parents'][key] = parents;
				self.getviews(parents, function(){
					// build the parents..
					parents_ul.empty();				
					var ul = $('<ul></ul>');
					$.each(parents, function() {
						var i = $('<li><a href="'+EMEN2WEBROOT+'/'+self.options.keytype+'/'+this+'" data-key="'+this+'" data-child="'+self.options.root+'">'+self.getname(this)+'</a></li>');
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
			this.options.action = action;
			var self = this;
			
			// Empty action tool box, and unselect any selected records
			$('.e2-browser-action', this.dialog).empty();
			$(".e2-browser-select", this.dialog).each(function(){$(this).removeClass('e2-browser-select')})

			// Tool selector
			var action = $('<select> \
				<option value="view">View</option> \
				<option value="reroot">Navigate</option> \
				<option value="move">Move</option> \
				<option value="delete">Delete</option> \
				<option value="addparent">Add Parent</option> \
				<option value="addchild">Add Child</option> \
				</select>');				
			action.val(this.options.action);
			action.change(function() {
				self.setaction($(this).val());
			});
			
			// Record selector
			var selector1 = $('<input name="root" type="text" size="6" value="'+this.options.root+'" />');
			var selector2 = $('<input name="select" type="button" class="save" value="'+this.options.selecttext+'" />');
			selector1.keypress(function() {
				$('input[name=select]', self.dialog).val("Go To").data("reroot", true).removeClass("save");
			})
			selector2.click(function() {
				var reroot = $(this).data("reroot");
				var key = $("input[name=root]", self.dialog).val();
				if (reroot) {
					$(this).data("reroot", false);
					$(this).addClass("save");
					$(this).val(self.options.selecttext);
					self.build_root(key);
				} else {
					self.dialog.dialog('close');
					self.options.cb(key);
				}
			});

			if (this.options.action == 'select') {
				$('.e2-browser-action', this.dialog).append(selector1, selector2);			
			} else {
				$('.e2-browser-action', this.dialog).append('<span>Current Tool: </span>', action);				
			}

		},
		
		/////////////////////////////////////////
		// Actions
		/////////////////////////////////////////
		
		action: function(e) {
			var self = this;
			var target = $(e.target);
			var key = target.attr('data-key');
			if (this.options.action == null) {return}				

			if (this.options.action == 'view') {
				return
			}
			e.preventDefault();

			// some tool specific behaviors..

			if (this.options.action == "move" || this.options.action == "copy") {

				if (target.attr('data-parent') != null) {							
					target.toggleClass("e2-browser-select");
				}
				
			} else if (this.options.action == "delete") {

				var parent = target.attr('data-parent');
				var child = target.attr('data-child');
				self._action_delete(key, parent, child);
				
			} else if (this.options.action == "addparent") {

				var cb = function(parent) {self._action_addrel(parent, key)}
				var i = $('<div></div>');
				i.RelationshipControl({root:this.options.root, embed: false, keytype:this.options.keytype, action:"select", selecttext:"Add Parent", cb:cb});				

			} else if (this.options.action == "addchild") {

				var cb = function(child) {self._action_addrel(key, child)}
				var i = $('<div></div>');
				i.RelationshipControl({root:this.options.root, embed: false, keytype:this.options.keytype, action:"select", selecttext:"Add Child", cb:cb});

			} else if (this.options.action == "reroot" || this.options.action == "select") {

				// rebuild the root..
				this.build_root(key);

			}
		},
		
		_action_delete: function(key, parent, child) {
			var self = this;
			
			if (child != null) {
				var rmlink = [key, child];
			} else if (parent != null) {
				var rmlink = [parent, key];
			} else {
				return
			}
			
			var d = $('<div title="Confirm"> \
				Do you want to remove this link? \
				<h3>Parent:</h3><a href="'+EMEN2WEBROOT+'/'+this.options.keytype+'/'+rmlink[0]+'/">'+self.getname(rmlink[0])+'</a> \
				<h3>Child:</h3><a href="'+EMEN2WEBROOT+'/'+this.options.keytype+'/'+rmlink[1]+'/">'+self.getname(rmlink[1])+'</a></div>');
				
			d.dialog({
				//height: 350,
				modal: true,
				buttons: {
					"OK": function() {
						$(this).dialog("close");
						$.jsonRPC.call("rel.pcunlink", [rmlink[0], rmlink[1], self.options.keytype], function() {
							self.build_root(self.options.root);			
						});
					},
					Cancel: function() {$(this).dialog("close")}
				}});			

		},
		
		_action_addrel: function(parent, child) {
			//console.log("Adding rel", parent, child);
			var self = this;
			$.jsonRPC.call("rel.pclink", [parent, child, this.options.keytype], function() {
				self.refresh(parent);
			});
		},	
		
		dropaction: function(e, ui) {
			if (this.options.action == "move") {
				this._drop_move(e, ui);
			}
		},
		
		_drop_move: function(e, ui) {
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
						console.log(rels, newrels);
						$.jsonRPC.call("pcrelink", [rels, newrels], function() {
							self.build_root(self.options.root);
							// $.each(refresh, function() {
							// 	self.refresh(this);
							// })
						});
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

			$('a.e2-browser-select', this.dialog).each(function() {
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
			var helper = $('<div class="e2-browser-selecthelper">'+text+'</div>');
			helper.data('keys', keys);
			return helper
		},
		
		// handle type-specific details for caching recnames/desc_short, then execute a callback..
		getviews: function(keys, cb) {
			var self = this;
			if (self.options.keytype == "record") {
				$.jsonRPC.call("record.render", [keys, null, "recname"], function(recnames){
					$.each(recnames, function(k,v) {caches['recnames'][k]=v});
					cb();
				});					
			} else if (self.options.keytype == "recorddef") {
				$.jsonRPC.call("recorddef.get", [keys], function(rds){
					$.each(rds, function() {caches['recorddef'][this.name]=this});
					cb();
				});											
			} else if (self.options.keytype == "paramdef") {
				$.jsonRPC.call("paramdef.get", [keys], function(pds){
					$.each(pds, function() {caches['paramdef'][this.name]=this});
					cb();
				});						
			}			
		},
		
		// more type-specific handling..
		getname: function(item) {
			if (this.options.keytype == 'record') {
				return caches['recnames'][item] || String(item)
			} else if (this.options.keytype == 'paramdef') {
				return caches['paramdef'][item].desc_short || item
			} else if (this.options.keytype == 'recorddef') {
				return caches['recorddef'][item].desc_short || item
			}			
		},
		
		// rebuild all branches for key
		refresh: function(key) {
			var self = this;
			$('a[data-key='+key+']', this.dialog).each(function() {
				self.expand($(this).parent());
			});
		},


		// expand/contract a branch		
		toggle: function(elem) {
			// elem is the expand image element			
			var self = this;
			var elem = $(elem);
		
			// pass the img's parent LI to this.expand
			if (elem.hasClass('e2-map-expanded')) {
				elem.removeClass('e2-map-expanded');
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

			var method = "rel.child.tree";
			if (this.options.mode == "parents") {
				method = "rel.parent.tree";
			}
			
			$.jsonRPC.call(method, [key, 2, null, this.options.keytype], function(tree){
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
			img.addClass('e2-map-expanded');
			img.attr('src', EMEN2WEBROOT+'/static/images/bg-close.'+this.options.mode+'.png');
			
			// lower-case alpha sort...
			var sortby = {};
			$.each(caches[this.options.mode][key], function() {
				sortby[this] = self.getname(this);
			});
			var sortkeys = $.sortstrdict(sortby);
			sortkeys.reverse();			

			if (sortkeys.length == 0) {
				//img.attr('src', EMEN2WEBROOT+'/static/images/bg-close.'+this.options.mode+'.png');
				img.remove();
			}
						
			$.each(sortkeys, function() {
				var line = $('<li> \
					<a data-key="'+this+'" data-parent="'+key+'" href="'+EMEN2WEBROOT+'/'+self.options.keytype+'/'+this+'/">'+self.getname(this)+'</a> \
					</li>');

				if (caches[self.options.mode][this] && self.options.expandable) {
					var expand = $(' \
						<img class="e2-map-expand" alt="'+caches[self.options.mode][this].length+' \
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
			
			$('img.e2-map-expand', root).click(function() {self.toggle(this)});

			// If this is a simple, non-editable map..
			if (!this.options.controls) {
				return
			}

			// this should be made simpler...
			$("a[data-key]", root).droppable({
				tolerance: 'pointer',
				addClasses: false,
				hoverClass: "e2-map-hover",
				activeClass: "e2-map-active",
				drop: function(e, ui) {self.dropaction(e, ui)}
			});	

			$("a", root).click(function(e) {self.action(e)});
			
			$("a[data-parent]", root).draggable({
				addClasses: false,
				helper: function(ui, e){return self.helper(ui, e)}
			});		
		
		}
	});
})(jQuery);

