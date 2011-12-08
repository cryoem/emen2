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
					emen2.db('renderview', [found], function(recnames) {
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
				<div class="e2l-hide e2l-help" role="help"><p> \
					Each record can have an arbitrary number of parent and child relationships. \
					To add a new parent or child relationship, click the "+" button in that section. \
					This will show a record chooser; you can either navigate to the record you want to add, or type \
					the record ID directly into the input box. Saving this form will keep any relationships that are checked, \
					and remove any unchecked relationships. \
				</p><p> \
					Additional information is available at the <a href="http://blake.grid.bcm.edu/emanwiki/EMEN2/Help/Relationships">EMEN2 Wiki</a>. \
				</p></div>');
				this.element.append(help);
				var helper = $('<div class="e2l-label"><input type="button" value="Help" /></div>');
				$('input', helper).click(function(e){$('[role=help]', self.element).toggle()})
				$('h4', this.element).append(helper);
			}
			// Build a textual summary
			if (this.options.summary && this.options.keytype == 'record') {
				this.element.append(this.build_summary(parents, children));
			}
			
			// Add the items
			this.element.append(this.build_level('Parents', 'parents', parents));
			this.element.append(this.build_level('Children', 'children', children));
			
			if (this.options.controls) {
				this.build_controls();
			}

			// Show all the infoboxes...
			$('.e2-relationships-infobox', this.element).InfoBox('show');
		},
		
		build_summary: function(parents, children) {
			// Make a descriptive summary of the parent and child relationships
			var summary = $('<p class="e2-relationships-summary"></p>')
			var p = this.build_summary_label(parents);
			var c = this.build_summary_label(children);
			var label = 'parent';
			if (parents.length > 1) {label = 'parents'}		

			summary.append('This record has '+
				this.build_summary_label(parents, 'parents')+
				' and '+
				this.build_summary_label(children, 'children')+
				'. Select <span class="e2l-a e2-permissions-all">all</span> \
				or <span class="e2l-a e2-permissions-none">none</span>. \
				Click to <a href="'+EMEN2WEBROOT+'/sitemap/'+this.options.name+'/">view children in tree format</a>.');

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
			$('input:button', header).BrowseControl({
				root: this.options.name,
				keytype: this.options.keytype,
				tool: 'browse',
				selected: function(browse, name) {
					self.add(level, name);
				}
			}).click(function(){
				$(this).BrowseControl('show');
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
			this.element.submit();
		},
		
		cache: function() {
			return emen2.caches[this.options.keytype][this.options.name];
		}
	});
	
	
	////////////////////////////
	// Browse for an item
	$.widget('emen2.BrowseControl', {
		options: {
			root: null,
			keytype: null,
			action: 'view',
			controls: false,
			embed: false,
			tool: 'none',
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
			this.dialog.dialog('open');
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
					<div class="e2-browse-parents e2l-float-left" style="width:249px;"> Parents </div> \
					<div class="e2-browse-action e2l-float-left" style="width:249px;">&nbsp;</div> \
					<div class="e2-browse-children e2l-float-left" style="width:249px;"> Children </div> \
				</div> \
				<div class="e2l-cf e2-browse-map" style="position:relative" />');

			// build the switcher...
			if (this.options.controls) {
				this.build_controls();
			}

			// Set the tools..
			this.settool(this.options.tool);

			// Refresh the map area
			this.reroot(this.options.root);

			// Embed or show the dialog
			if (this.options.embed) {
				this.element.append(this.dialog);
			} else {
				// Show the dialog
				this.dialog.attr("title", "Relationship Browser");
				this.dialog.dialog({
					modal: true,
					width: 800,
					height: 600
				});			
			}
		},
		
		build_controls: function() {
			var self = this;
			var controls = $('.e2-browse-controls', this.dialog);
			// controls.append(' \
			// 	<p>Current tool:</p> \
			// 	<ul> \
			// 		<li> \
			// 			<input id="e2-browse-tool-none" type="radio" name="settool" value="none" checked /> \
			// 			<label for="e2-browse-tool-none">None (links open normally)</label> \
			// 		</li> \
			// 		<li> \
			// 			<input id="e2-browse-tool-browse" type="radio" name="settool" value="browse" /> \
			// 			<label for="e2-browse-tool-browse">Re-center map when clicked</label> \
			// 		</li> \
			// 		<li> \
			// 			<input id="e2-browse-tool-move" type="radio" name="settool" value="move" /> \
			// 			<label for="e2-browse-tool-move">Select items &amp; drag to move them</label> \
			// 		</li> \
			// 	</ul>');
			$('input[name=settool]', controls).change(function() {
				var tool = $(this).val();
				self.settool(tool);
			});
		},
		
		settool: function(tool) {
			$('input[name=tool]', this.dialog).val(tool);
			
			// Empty current tool areas
			$('.e2-browse-action', this.dialog).html('&nbsp;');

			// What happens when a map item is clicked..
			this.mapselect = function(w, e, elem, rel1, rel2){};
			
			if (tool == 'browse') {
				this.build_browse();
			} else if (tool == 'move') {
				this.build_move();
			}
		},
		
		reroot: function(name) {
			var self = this;
			this.options.root = name;
			$('input[name=value]', this.dialog).val(name);
			
			// Selected callback is an "outer callback" to pass off to this.mapselect
			var cb = function(w, e, elem, rel1, rel2) {self.mapselect(w, e, elem, rel1, rel2)}
			
			var parents = $('<div class="e2-map e2l-float-left" style="position:absolute;left:0px;width:250px;">&nbsp;</span>');
			parents.MapControl({
				root: name, 
				keytype: this.options.keytype, 
				mode: 'parents',
				skiproot: true,
				show: true,
				selected: cb
			});			
			
			// The parents needs a spinner -- the MapControl one doesn't work right
			parents.append(emen2.template.spinner(true));

			var children = $('<div class="e2-map e2l-float-left" style="position:absolute;left:250px;" />');
			children.MapControl({
				root: name, 
				keytype: this.options.keytype, 
				mode: 'children',
				show: true,
				selected: cb
			});
			
			// var input = $('input[name=value]', this.dialog);
			// var val = input.val();
			// input.focus();
			// if (val.toString() == this.options.root.toString()) {
			// 	$('input[name=submit]', this.dialog).val('Select');
			// }
			
			$('.e2-browse-map', this.dialog).empty();
			$('.e2-browse-map', this.dialog).append(parents, children);
		},
		
		build_move: function() {
			var self = this;
			// When an element is clicked, make it draggable
			this.mapselect = function(w, e, elem, rel1, rel2){
				e.preventDefault();
				var a = elem.children('a');
				a.toggleClass('e2-browse-selected');
				a.draggable({
					addClasses: false,
					helper: function(e, ui){return self.helper_move(self, e, ui)}
				});
			};
		},

		helper_move: function(self, e, ui) {
			// Set droppables when I start dragging..
			// this could be made simpler...
			// be careful with binding of 'self'
			$('li[data-name] > a:not(.e2-browse-selected)', self.dialog).droppable({
				tolerance: 'pointer',
				addClasses: false,
				hoverClass: "e2-browse-hover",
				activeClass: "e2-browse-active",
				drop: function(e, ui) {
					self.helper_drop(self, this, e, ui);
				}
			});
			var selected = $('.e2-browse-selected', self.dialog);
			return '<div class="e2-browse-helper">Moving '+selected.length+' '+self.options.keytype+'s</div>'
		},
		
		helper_drop: function(self, dropped, e, ui) {
			var removerels = [];
			var addrels = [];
			
			var newparent = $(dropped).parent().attr('data-name');
			$('.e2-browse-selected', self.dialog).each(function() {
				var li = $(this).parent();
				var child = li.attr('data-name')
				var parent = li.parent().attr('data-name');
				removerels.push([parent, child]);
				addrels.push([newparent, child]);
			});

			var txt = 'Please be careful moving items. There is no "undo." \nKeep multiple-item moves as simple as possible, \
				\n\te.g. moving siblings together to a new parent.\n\nRemoving these relationships ('+removerels.length+'):\n\n';			
			for (var i=0;i<removerels.length;i++) {
				var p = emen2.caches['recnames'][removerels[i][0]];
				var c = emen2.caches['recnames'][removerels[i][1]];
				txt += p+' -> '+c+'\n';
			}
			txt += '\nAnd adding these relationships ('+addrels.length+'):\n\n';
			for (var i=0;i<addrels.length;i++) {
				var p = emen2.caches['recnames'][addrels[i][0]];
				var c = emen2.caches['recnames'][addrels[i][1]];
				txt += p+' -> '+c+'\n';
			}

			if (!confirm(txt)) {return}

			emen2.db('rel.relink', {removerels: removerels, addrels: addrels, keytype: self.options.keytype}, function (){
				alert("Move was successful. Please reload the page to see the changes.");
			});
		},
		
		helper_confirm: function() {

		},
		
		helper_success: function() {
			
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
				if (val.toString()==self.options.root.toString()) {
					self.options.selected(self, val);
					self.dialog.dialog('close');
				} else {
					self.reroot(val);
				}
			});

			var action = $('.e2-browse-action', this.dialog);
			action.append(controls);
			
			this.mapselect = function(w, e, elem, rel1, rel2){
				e.preventDefault();
				self.reroot(rel2);
			};			
		},		
	});
	
	
	////////////////////////////	
	// Display a map
    $.widget("emen2.MapControl", {		
		options: {
			root: null,
			keytype: null,
			mode: null,
			expandable: true,
			show: false,
			attach: false,
			skiproot: false,
			// events
			// collapsed: null,
			// expanded: null,
			selected: null
		},

		_create: function() {
			var self = this;
			this.built = 0;

			this.options.mode = emen2.util.checkopt(this, 'mode', 'children');
			this.options.root = emen2.util.checkopt(this, 'root');
			this.options.keytype = emen2.util.checkopt(this, 'keytype', 'record');

			this.element.addClass('e2-map-'+this.options.mode);			
			if (this.options.attach) {
				this.attach(this.element);
			} else if (this.options.show) {
				this.build();
			}
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
					emen2.template.image('bg-open.'+this.options.mode+'.png', '+', 'e2-map-expand')+
				'</li>');
			this.element.append(root);
			this.attach(root);
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
			var img = elem.find('img.e2-map-expand');
			img.addClass('e2-map-expanded');
			img.attr('src', EMEN2WEBROOT+'/static-'+VERSION+'/images/bg-close.'+this.options.mode+'.png');
			
			// The new ul
			var ul = $('<ul data-name="'+name+'"></ul>');

			// lower-case alpha sort...
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
					var expand = $(emen2.template.image('bg-open.'+self.options.mode+'.png', emen2.caches[self.options.mode][this].length, 'e2-map-expand'))
					li.append(expand);
				}
				ul.append(li);
			});
			elem.find('ul').remove();

			// don't forget to adjust top
			elem.append(ul);
			var h = ul.siblings('a').height();
			ul.css('margin-top', -h);
			ul.css('min-height', h);
			// Adjust the heights and bind the img events
			this.attach(ul);
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

			// We use rel.children.tree because we want to grab 2 levels of children/parents
			// 	to determine if each child is itself expandable...
			var method = "rel.children.tree";
			if (this.options.mode == "parents") {method = "rel.parents.tree"}
			emen2.db(method, {names:name, recurse:2, keytype:this.options.keytype}, function(tree){
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
		toggle: function(elem) {
			// elem is the expand image element
			var self = this;
			var elem = $(elem);
			
			if (elem.hasClass('e2-map-expanded')) {
				// Contract this branch
				elem.removeClass('e2-map-expanded');
				elem.siblings('ul').remove();
				elem.attr('src', EMEN2WEBROOT+'/static-'+VERSION+'/images/bg-open.'+this.options.mode+'.png');
			} else {
				// Expand this branch
				this.expand(elem.parent());
			}			
		},
		
		attach: function(root) {
			var self = this;
			// height adjustment
			$('ul', root).each(function() {
				var elem = $(this);
				var h = elem.siblings('a').height();
				elem.css('margin-top', -h);
				elem.css('min-height', h);
			});	
					
			$('img.e2-map-expand', root).click(function() {self.toggle(this)});
			
			if (this.options.selected) {
				$('a', root).click(function(e) {
					var elem = $(e.target).parent();
					var rel1 = elem.parent().attr('data-name');
					var rel2 = elem.attr('data-name');
					self.options.selected(self, e, elem, rel1, rel2);
				});
			}
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
				return emen2.caches['recnames'][item] || String(item)
			} else if (this.options.keytype == 'paramdef') {
				return emen2.caches['paramdef'][item].desc_short || item
			} else if (this.options.keytype == 'recorddef') {
				return emen2.caches['recorddef'][item].desc_short || item
			}			
		},
		
		// rebuild all branches for key
		refresh: function(name) {
			var self = this;
			$('a[data-name='+name+']', this.dialog).each(function() {
				self.expand($(this).parent());
			});
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