(function($) {
	
	$.widget('emen2.RelationshipControl', {
		options: {
			name: null,
			keytype: null,
			edit: null,
			show: true,
			summary: false,
			help: false,
			// events: saved
		},

		_create: function() {
			this.built = 0;
			var self = this;
			this.options.name = emen2.util.checkopt(this, 'name');
			this.options.keytype = emen2.util.checkopt(this, 'keytype', 'record');
			this.options.edit = emen2.util.checkopt(this, 'edit')
			this.options.summary = emen2.util.checkopt(this, 'summary')
			if (this.options.show) {this.show()}			
		},
		
		rebuild: function() {
			// Clear out and rebuild
			this.built = 0;
			this.build();
		},
		
		show: function() {
			this.build();
		},
		
		build: function() {
			// Cache items before real build..
			if (this.built) {return}
			var self = this;

			// Always empty the element before a rebuild, and place a spinner
			this.element.empty();
			this.element.addClass('e2-relationships');
			this.element.append(emen2.template.spinner(true));
			
			// Load all the parents and children
			var item = emen2.caches[this.options.keytype][this.options.name];
			var names = item.children.concat(item.parents);
			names = emen2.cache.check(this.options.keytype, names);
			
			// Cache rendered views for all the items
			// 1. Get the related items
			emen2.db('get', {names:names, keytype:this.options.keytype}, function(items) {
				emen2.cache.update(items)
				var found = $.map(items, function(k){return k.name});
				
				// 2a. Records need a second callback for pretty rendered text
				if (self.options.keytype == 'record') {
					emen2.db('record.render', [found], function(recnames) {
						$.each(recnames, function(k,v) {emen2.caches['recnames'][k] = v})
						self._build();
					});
				} else {
					// 2b. No additional items needed.
					self._build();
				}
			});
		}, 
		
		_build: function() {
			// Real build method
			this.built = 1;
			var self = this;

			// Remove the spinner
			this.element.empty();
			
			// Get the parents and children from cache
			var rec = emen2.caches[this.options.keytype][this.options.name];
			var parents = rec.parents;
			var children = rec.children;
			
			if (this.options.summary || this.options.help) {
				this.element.append('<h4 class="e2l-cf">Relationships</h4>');
			}
			if (this.options.help) {
				var help = $(' \
				<div class="e2l-help" role="help"><p> \
					Records can have an arbitrary number of parent and child relationships. \
				</p><p>To <strong>add parent or child relationships</strong>, click one of the <strong>+</strong> buttons below. \
					This will show a record chooser. You can either navigate to the record you want to add, or type \
					the record ID directly into the input box. This will add the chosen record to the list of parents or children. \
					The changes will take effect when you click <strong>Save relationships</strong>. \
				</p><p>To <strong>remove parent or child relationships</strong>, uncheck the relationships you want to remove and click <strong>Save relationships</strong>. \
				</p><p> \
					Additional information is available at the <a href="http://blake.grid.bcm.edu/emanwiki/EMEN2/Help/Relationships">EMEN2 Wiki</a>. \
				</p></div>');
				this.element.append(help);
				var helper = $('<span class="e2-button e2l-float-right">Help</span>');
				helper.click(function(e){$('[role=help]', self.element).toggle()})
				$('h4', this.element).append(helper);
			}
			// Build a textual summary
			if (this.options.summary && this.options.keytype == 'record') {
				this.element.append(this.build_summary(parents, children));
			}
			
			// Add the items
			this.element.append(this.build_level('Parents', 'parents', parents));
			this.element.append(this.build_level('Children', 'children', children));
			
			if (this.options.controls && this.options.edit) {
				this.build_controls();
			}

			// Show all the infoboxes...
			$('.e2-relationships-infobox', this.element).InfoBox('show');
		},
		
		build_summary: function(parents, children) {
			// Make a descriptive summary of the parent and child relationships
			var summary = $('<div class="e2-relationships-summary"></div>')
			var p = this.build_summary_label(parents);
			var c = this.build_summary_label(children);
			var label = 'parent';
			if (parents.length > 1) {label = 'parents'}		

			summary.append('<p>This record has '+
				this.build_summary_label(parents, 'parents')+
				' and '+
				this.build_summary_label(children, 'children')+
				'. Click to <a href="'+EMEN2WEBROOT+'/sitemap/'+this.options.name+'/">view the sitemap starting at this record</a>.</p>');
			// '. Select <span class="e2l-a e2-permissions-all">all</span>
			//	or <span class="e2l-a e2-permissions-none">none</span>.

			// Select by rectype
			$('.e2-relationships-rectype', summary).click(function() {
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
				$('.e2-infobox[data-rectype='+rectype+'] input', self.element).attr('checked', state);
			});
			return summary		
		},
		
		build_summary_label: function(value, label) {
			// Ugly text and markup manipulation to build descriptive summaries of records/rectypes
			var ct = {}
			$.each(value, function(k,v){
				var r = emen2.caches['record'][v] || {};
				if (!ct[r.rectype]){ct[r.rectype]=[]}
				ct[r.rectype].push(this);
			});				

			var ce = [];
			$.each(ct, function(k,v) {
				var rd = emen2.caches['recorddef'][k] || {};
				var rddesc = rd['desc_short'] || k;
				var adds = '';
				if (v.length > 1) {adds='s'}
				ce.push(v.length+' '+rddesc+
					' <span data-checked="checked" data-reltype="'+label+
					'" data-rectype="'+k+
					'" class="e2l-small e2l-a e2-relationships-rectype">(toggle)</span>');
			});

			var pstr = '';
			if (ce.length == 0) {
				pstr = '<span>no '+label+'</span>';
			} else if (ce.length == 1) {
				pstr = '<span>'+ce.join(', ')+' '+label+'</span>';
			} else {
				pstr = '<span>'+value.length+' '+label+'</span>, including '+ce.join(', ')
			}	
			return pstr
		},
		
		build_level: function(label, level, items) {
			var self = this;
			var header = $('<h4 class="e2l-cf">'+label+'</h4>');
			if (this.options.edit) {
				header.prepend('<input data-level="'+level+'" type="button" value="+" /> ');
			}

			$('input:button', header).TreeBrowseControl({
				root: this.options.name,
				selectable: this.options.edit,
				keytype: this.options.keytype,
				selected: function(browse, name) {
					self.add(level, name);
				}
			}).click(function(){
				$(this).TreeBrowseControl('show');
			})

			var d = $('<div data-level="'+level+'"></div>');
			for (var i=0;i<items.length;i++) {
				d.append(this.build_item(level, items[i], false))
			}
			
			d.append('<input type="hidden" name="'+level+'" value="" class="e2-relationships-hidden" />');
			
			return $('<div></div>').append(header, d);
		},
		
		build_item: function(level, name, retry) {
			var self = this;
			// Retry parameter indiciates try again to find item if not in cache.			
			// Do not show immediately -- need to be in DOM for built() callback

			// Update the select count when built or checked..
			var cb = function() {$('.e2-select', self.options.controls).SelectControl('update')}

			return $('<div class="e2-relationships-infobox"></div>').InfoBox({
				show: false,
				keytype: this.options.keytype,
				name: name,
				selectable: this.options.edit,
				retry: retry,
				input: ['checkbox', level, true],
				selected: cb,
				built: cb
			});
		},
		
		build_controls: function() {
			var self = this;
			// ian: todo: move "Select all or none" to a template function (utils.js)
			var controls = $(' \
				<ul class="e2l-options"> \
					<li class="e2-select" /> \
				</ul> \
				<ul class="e2l-controls"> \
					<li><input type="submit" value="Save relationships" /></li> \
				</ul>');

			// Selection control
			$('.e2-select', controls).SelectControl({root: this.element});

			// Save form
			$('input:submit', controls).click(function(e){self.save(e)});

			// Show/hide advanced options
			$('.e2-relationships-advanced', controls).click(function(){
				emen2.template.caret('toggle', self.options.controls);
				$('.e2l-controls', self.options.controls).toggle();
				$('.e2l-advanced', self.options.controls).toggle();
			});
			
			this.options.controls.append(controls);
		},
		
		add: function(level, name) {
			var boxes = $('div[data-level='+level+']', this.element);
			if ($('.e2-infobox[data-name='+name+']', boxes).length) {
				return
			}
			var box = this.build_item(level, name, true);
			boxes.prepend(box);
			box.InfoBox('show');
		},
		
		save: function(e) {
			e.preventDefault();
			var parents = $('input[type=checkbox][name=parents]', this.element);
			var checkedparents = $('input[type=checkbox][name=parents]:checked', this.element);			
			if (parents.length && !checkedparents.length) {
				var ok = confirm("You are attempting to remove all parents of this record. This will not delete the record, but might make it difficult to find. Continue?");
				if (!ok) {return false}
			}
			this.element.submit();
		},
		
		cache: function() {
			return emen2.caches[this.options.keytype][this.options.name];
		}
	});
	
	
	////////////////////////////
	// Browse for an item
	$.widget('emen2.TreeBrowseControl', {
		options: {
			root: null,
			keytype: null,
			embed: false,
			// events
			selected: function(self, name) {},
			moved: function() {},
		},
		
		_create: function() {
			var self = this;
			this.built = 0;

			this.options.mode = emen2.util.checkopt(this, 'mode');
			this.options.root = emen2.util.checkopt(this, 'root');
			this.options.keytype = emen2.util.checkopt(this, 'keytype', 'record');
	
			this.element.click(function(e){self.show(e)});
			if (this.options.show) {
				this.show();
			}			
		},
		
		show: function(e) {
			this.build();
			if (this.options.embed) {
				// pass
			} else {
				this.dialog.dialog('open');
			}
		},

		build: function() {
			if (this.built) {return}
			this.built = 1;
			var self = this;

			// Build the dialog
			this.dialog = $('<div class="e2-browse" />');
			this.dialog.append(' \
				<div class="e2-browse-controls"></div> \
				<div class="e2l-cf e2-browse-header" style="border-bottom:solid 1px #ccc;margin-bottom:6px;"> \
					<div class="e2-browse-parents e2l-float-left" style="width:299px;"> Parents </div> \
					<div class="e2-browse-action e2l-float-left" style="width:299px;">&nbsp;</div> \
					<div class="e2-browse-children e2l-float-left" style="width:299px;"> Children </div> \
				</div> \
				<div class="e2l-cf e2-browse-tree" style="position:relative" />');

			// Refresh the map area
			this.reroot(this.options.root);

			// Build the browser controls
			this.build_browse();

			// Embed or show the dialog
			if (this.options.embed) {
				this.element.append(this.dialog);
			} else {
				// Show the dialog
				this.dialog.attr("title", "Relationship Browser");
				this.dialog.dialog({
					modal: true,
					width: 1000,
					height: 600,
					draggable: false,
					resizable: false,					
				});			
			}
		},

		build_browse: function() {
			var self = this;
			var controls = $(' \
				<span> \
					<input style="margin-left:16px;width:120px;" type="text" name="value" value="" /> \
					<input style="margin-right:16px" type="submit" name="submit" value="Select" /> \
				</span>');
			
			$('input[name=value]', controls).bind('keyup', function(e) {
				$('input[name=submit]', self.dialog).val('Go To');
			});
			
			$('input[name=submit]', controls).click(function(e) {
				var val = $('input[name=value]', self.dialog).val();
				if (val.toString() == self.options.root.toString()) {
					self.options.selected(self, val);
					self.dialog.dialog('close');
				} else {
					self.reroot(val);
				}
			});

			var action = $('.e2-browse-action', this.dialog);
			action.append(controls);
		},
		
		reroot: function(name) {
			var self = this;
			this.options.root = name;
			$('input[name=value]', this.dialog).val(name);
			
			// Selected callback is an "outer callback" to pass off to this.mapselect
			var cb = function(w, elem, name) {self.reroot(name)}
			
			var parents = $('<div class="e2-tree e2l-float-left" style="position:absolute;left:0px;width:300px;">&nbsp;</span>');
			parents.TreeControl({
				root: name, 
				keytype: this.options.keytype, 
				mode: 'parents',
				skiproot: true,
				show: true,
				selected: cb
			});			
			
			// The parents needs a spinner -- the TreeControl one doesn't work right
			parents.append(emen2.template.spinner(true));

			var children = $('<div class="e2-tree e2l-float-left" style="position:absolute;left:300px;" />');
			children.TreeControl({
				root: name, 
				keytype: this.options.keytype, 
				mode: 'children',
				show: true,
				selected: cb
			});
			
			$('.e2-browse-tree', this.dialog).empty();
			$('.e2-browse-tree', this.dialog).append(parents, children);
		}		
	});
	
	
	////////////////////////////	
	// Relationship tree control
	
    $.widget("emen2.TreeControl", {		
		options: {
			root: null,
			keytype: null,
			mode: null,
			expandable: true,
			show: false,
			attach: false,
			skiproot: false,
			selected: null
		},

		_create: function() {
			var self = this;
			this.built = 0;
			
			// Selected/unselected item states
			this.state = {};
			
			// Get options from data- attributes
			this.options.mode = emen2.util.checkopt(this, 'mode', 'children');
			this.options.root = emen2.util.checkopt(this, 'root');
			this.options.keytype = emen2.util.checkopt(this, 'keytype', 'record');

			this.element.addClass('e2-tree-'+this.options.mode);			
			if (this.options.attach) {
				this.bind(this.element);
			} else if (this.options.show) {
				this.build();
			}
			this.init();
		},
		
		init: function() {
			
		},
	
		build: function() {
			var self = this;
			this.element.empty();
			if (this.options.skiproot) {
				// Expand directly off this.element
				this.element.attr('data-name', this.options.root);
				this.expand(this.element, this.options.root);
			} else {
				// Build a root element, then expand it
				this.build_root(this.element, this.options.root);
			}
		},
		
		// Build a tree root
		build_root: function(elem, name) {
			var self = this;
			var name = (name == null) ? elem.attr('data-name') : name;
			if (!emen2.caches[this.options.keytype][name]) {
				// make a pass through this.getnames if we don't have this cached already
				this.getviews([name], function(){self.build_root(elem, name)});
				return
			}

			var root = $('<ul></ul>');
			root.append(' \
				<li data-name="'+name+'"> \
					<a href="#">'+this.getname(this.options.root)+'</a>'+
					emen2.template.image('bg.open.'+this.options.mode+'.png', '+', 'e2-tree-expand')+
				'</li>');
			this.element.append(root);
			this.bind(root);
			this.expand(root.find('li'));			
		},
		
		// Draw a branch
		build_tree: function(elem, name) {
			// elem is usually an li that will have the new ul added
			// name can be specified, or parsed from data-name			
			var self = this;
			var name = (name == null) ? elem.attr('data-name') : name; 
			
			// Remove any spinners
			elem.find('img.e2l-spinner').remove();
						
			// Set the image to expanded
			var img = elem.find('img.e2-tree-expand');
			img.addClass('e2-tree-expanded');
			img.attr('src', EMEN2WEBROOT+'/static-'+VERSION+'/images/bg.close.'+this.options.mode+'.png');
			
			// The new ul
			var ul = $('<ul data-name="'+name+'"></ul>');

			// Lower-case alpha sort...
			var sortby = {};
			$.each(emen2.caches[this.options.mode][name], function() {
				sortby[this] = self.getname(this);
			});
			var sortkeys = emen2.util.sortdictstr(sortby);
			sortkeys.reverse();			
	
			// If there are no children, hide the expand image
			if (sortkeys.length == 0) {
				img.remove();
			}
			
			// Build each child item
			$.each(sortkeys, function() {
				var li = $(' \
					<li data-name="'+this+'"> \
						<a href="'+EMEN2WEBROOT+'/'+self.options.keytype+'/'+this+'/">'
							+self.getname(this)+
						'</a> \
					</li>');
				if (emen2.caches[self.options.mode][this] && self.options.expandable) {
					var expand = $(emen2.template.image('bg.open.'+self.options.mode+'.png', emen2.caches[self.options.mode][this].length, 'e2-tree-expand'))
					li.append(expand);
				}
				ul.append(li);
			});
			elem.find('ul').remove();

			// Don't forget to adjust top
			elem.append(ul);
			var h = ul.siblings('a').height();
			ul.css('margin-top', -h);
			ul.css('min-height', h);
			
			// Adjust the heights and bind the img events
			this.bind(ul);
		},		

		// rebuild a branch
		expand: function(elem, name) {
			// elem is the LI
			var self = this;
			var name = (name == null) ? elem.attr('data-name') : name; 

			// Show activity indicator
			var img = elem.children('img');
			img.attr('src', EMEN2WEBROOT+'/static-'+VERSION+'/images/spinner.gif'); 
			
			// Remove any current children
			elem.find('ul').remove();

			// We use rel.childrentree because we want to grab 2 levels of children/parents
			// 	to determine if each child is itself expandable...
			var method = "rel.tree";

			emen2.db(method, {names:name, rel:this.options.mode, recurse:2, keytype:this.options.keytype}, function(tree){
				// Cache the result. This should be filtered for permissions
				$.each(tree, function(k,v) {emen2.caches[self.options.mode][k] = v});				
				// Get the items and/or rendered names, then build the tree
				// ... don't forget to use a .slice()'d copy!
				var names = (tree[name] || []).slice();
				names.push(name);
				names.push(self.options.root);
				self.getviews(names, function(){self.build_tree(elem)});
			});				
		},
		
		// expand/contract a branch		
		toggle_expand: function(elem) {
			// elem is the expand image element
			var self = this;
			var elem = $(elem);			
			if (elem.hasClass('e2-tree-expanded')) {
				// Contract this branch
				elem.removeClass('e2-tree-expanded');
				elem.siblings('ul').remove();
				elem.attr('src', EMEN2WEBROOT+'/static-'+VERSION+'/images/bg.open.'+this.options.mode+'.png');
			} else {
				// Expand this branch
				this.expand(elem.parent());
			}			
		},
		
		bind: function(root) {
			this.bind_expand(root);
			this.bind_state(root);
			this.bind_select(root);
		},
		
		bind_expand: function(root) {
			var self = this;

			// height adjustment
			$('ul', root).each(function() {
				var elem = $(this);
				var h = elem.siblings('a').height();
				elem.css('margin-top', -h);
				elem.css('min-height', h);
			});

			// Click icon to toggle
			$('img.e2-tree-expand', root).click(function(e) {self.toggle_expand(this)});
		},
		
		bind_select: function(root) {
			var self = this;
			if (this.options.selected) {
				$('a', root).click(function(e) {
					e.preventDefault();
					var name = $(this).parent().attr('data-name');
					self.options.selected(self, this, name);
				});
			}
		},

		bind_state: function(root) {
		},
		
		// cache items that we need, then go to the callback
		getviews: function(names, cb) {
			var self = this;
			var names = emen2.cache.check(this.options.keytype, names);
			if (names.length == 0) {
				cb();
				return
			}
			emen2.db('get', {names: names, keytype: this.options.keytype}, function(items) {
				emen2.cache.update(items);
				if (self.options.keytype == 'record') {
					// For records, we also want to render the names..
					var found = $.map(items, function(k){return k.name});
					emen2.db('record.render', [found], function(recnames) {
						$.each(recnames, function(k,v) {emen2.caches['recnames'][k]=v});
						cb();
					});
				} else {
					cb();
				}
			});		
		},
		
		// more type-specific handling..
		getname: function(item) {
			if (this.options.keytype == 'record') {
				return emen2.caches['recnames'][item] || '('+String(item)+')'
			} else if (this.options.keytype == 'paramdef') {
				return emen2.caches['paramdef'][item].desc_short || item
			} else if (this.options.keytype == 'recorddef') {
				return emen2.caches['recorddef'][item].desc_short || item
			}			
		}
	});
	
	////////////////////////////
	// Select items in a tree
	$.widget('emen2.TreeSelectControl', $.emen2.TreeControl, {
		init: function() {
			var self = this;
			// this option name might change; I was already using 'selected'
			if (this.options.active.length) {
				this.add(this.options.active);
			}
			//$(this.options.submit).click(function(e){self.submit(e)});
			this.element.parent('form').submit(function(e){self.submit(e)});
		},
		
		submit: function(e) {
			var self = this;
			// console.log("Submitting -- building inputs");
			$('input[name=state]', this.element).remove();
			$.each(this.state, function(k,v) {
				if (v) {
					// console.log('adding', k);
					self.element.append('<input type="hidden" name="state" value="'+k+'" />');
				}
			});
		},
		
		bind_state: function(root) {
			var self = this;
			$('li', root).each(function() {
				var name = $(this).attr('data-name');
				if (self.state[name]) {
					$(this).children('a').addClass('e2-browse-selected');
				} else {
					$(this).children('a').removeClass('e2-browse-selected');					
				}
			});
		},

		bind_select: function(root) {
			var self = this;
			$('a', root).click(function(e) {
				e.preventDefault();
				var name = $(this).parent().attr('data-name');
				self.toggle_select(e, this, name);
			});
		},
			
		add: function(items) {
			for (var i=0;i<items.length;i++) {
				var name = items[i];
				this.state[name] = true;
				$('li[data-name='+name+'] > a').addClass('e2-browse-selected');
			}
			this.count_selected();		
		},
		
		remove: function(items) {
			for (var i=0;i<items.length;i++) {
				var name = items[i];
				this.state[name] = false;
				$('li[data-name='+name+'] > a').removeClass('e2-browse-selected');
			}
			this.count_selected();		
		},
		
		count_selected: function() {
			var count = 0;
			$.each(this.state, function(k,v) {
				if (v) {count++}
			});
			$(this.options.display_count).html(count);
			return count
		},
		
		toggle_select: function(e, elem, name) {
			var state = this.state[name];
			var self = this;
			if (e.shiftKey) {
				// This element and all children, recursively
				emen2.db('rel.children', {names: name, recurse:-1}, function(children) {
					children.push(name);
					if (state) {
						self.remove(children);
					} else {
						self.add(children);
					}
				});
			} else {
				// Just this element
				if (state) {
					this.remove([name]);
				} else {
					this.add([name]);
				}
			}
		},
	});
	
	
	
	
})(jQuery);



<%!
public = True
headers = {
	'Content-Type': 'application/javascript',
	'Cache-Control': 'max-age=86400'
}
%>