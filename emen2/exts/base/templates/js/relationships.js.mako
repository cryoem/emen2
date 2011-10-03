(function($) {
	
	$.widget('emen2.RelationshipControl', {
		options: {
			name: null,
			keytype: null,
			edit: null,
			summary: null,
			show: true
		},

		_create: function() {
			this.built = 0;
			var self = this;
			this.options.name = $.checkopt(this, 'name');
			this.options.keytype = $.checkopt(this, 'keytype', 'record');
			this.options.edit = $.checkopt(this, 'edit')
			this.options.summary = $.checkopt(this, 'summary')
			if (this.options.show) {this.show()}			
		},
		
		rebuild: function() {
			this.built = 0;
			this.build();
		},
		
		show: function() {
			this.build();
		},
		
		build: function() {
			if (this.built) {return}
			var self = this;
			// Load all the parents and children
			var item = caches[this.options.keytype][this.options.name];
			var names = item.children.concat(item.parents);
			names = $.checkcache(this.options.keytype, names);

			// Always empty the element before a rebuild, and place a spinner
			this.element.empty();
			this.element.append($.spinner(true));
			
			// Cache rendered views for all the items
			// ian: todo: replace this with a InfoBox pre-cache method
			// Filter for what we need
			$.jsonRPC.call('get', {names:names, keytype:this.options.keytype}, function(items) {
				$.updatecache(items)
				var found = $.map(items, function(k){return k.name});
				
				// Records need a second callback for pretty rendered text
				if (self.options.keytype == 'record') {
					// var names2 = $.checkcache('recnames', names2); ???
					$.jsonRPC.call('renderview', [found], function(recnames) {
						$.each(recnames, function(k,v) {caches['recnames'][k] = v})
						self._build();
					});
				} else {
					self._build();
				}
			});
		}, 
		
		_build: function() {
			this.built = 1;
			var self = this;

			// Remove the spinner
			this.element.empty();
			
			// Get the parents and children from cache
			var rec = caches[this.options.keytype][this.options.name];
			var parents = rec.parents;
			var children = rec.children;
			
			// Build a textual summary
			if (this.options.summary && this.options.keytype == 'record') {
				var p = this.build_summary(parents)
				var c = this.build_summary(children)
				this.element.append('<h4>Relationships</h4>');
				var label = 'parent';
				if (parents.length > 1) {label = 'parents'}		
				this.element.append(' \
					<p>This record has '+
					this.build_summary(parents, 'parents')+
					' and '+
					this.build_summary(children, 'children')+
					'. Select <span class="e2l-a e2-permissions-all">all</span> \
					or <span class="e2l-a e2-permissions-none">none</span></p>');
			}
			
			// Select by rectype
			$('.e2-relationships-rectype', this.element).click(function() {
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
			
			// Add the items
			this.element.append(this.build_level('Parents', 'parents', parents));
			this.element.append(this.build_level('Children', 'children', children));
			
			if (this.options.controls) {
				this.build_controls();
			}

			// Do this here to find items in both the summary and options
			$('.e2-permissions-all').click(function(){$('input:checkbox', self.element).attr('checked', 'checked')});
			$('.e2-permissions-none').click(function() {$('input:checkbox', self.element).attr('checked', null)});			
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
				var rddesc = rd['desc_short'] || k;
				var adds = '';
				if (v.length > 1) {adds='s'}
				ce.push(v.length+' '+rddesc+' <span data-checked="checked" data-reltype="'+label+'" data-rectype="'+k+'" class="e2l-small e2l-a e2-relationships-rectype">(toggle)</span>');
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
				cb: function(browse, name) {
					self.add(level, name);
				}
			}).click(function(){
				$(this).BrowseControl('show');
			})

			var d = $('<div data-level="'+level+'"></div>');
			for (var i=0;i<items.length;i++) {
				d.append(this.build_item(level, items[i], false))
			}
			return $('<div></div>').append(header, d);
		},
		
		build_item: function(level, name, retry) {
			// retry parameter indiciates try again to find item if not in cache.
			return $('<div></div>').InfoBox({
				keytype: this.options.keytype,
				name: name,
				selectable: this.options.edit,
				retry: retry,
				input: ['checkbox', level, true]				
			});
		},
		
		build_controls: function() {
			var self = this;
			// ian: todo: move "Select all or none" to a template function (utils.js)
			var controls = $(' \
				<ul class="e2l-options"> \
					<li> \
						Select \
						<span class="e2-permissions-all e2l-a">all</span> \
						or <span class="e2-permissions-none e2l-a">none</span> \
					</li> \
				</ul> \
				<ul class="e2l-controls"> \
					<li><input type="submit" value="Save relationships" /></li> \
				</ul>');

			// <li><span class="e2-relationships-advanced e2l-a">'+$.caret('up')+'Advanced</span></li> \
			// <ul class="e2l-advanced e2l-hide"> \
			// 	<li><input type="button" value="Remove a parent from selected records" /></li> \
			// 	<li><input type="button" value="Remove a child from selected records" /></li> \
			// 	<li><input type="button" value="Add a parent to selected records" /></li> \
			// 	<li><input type="button" value="Add a child to selected records" /></li> \
			// 	<li><input type="button" value="Delete selected records" /></li> \
			// </ul> \

			$('input:submit', controls).click(function(e){self.save(e)});

			$('.e2-relationships-advanced', controls).click(function(){
				$.caret('toggle', self.options.controls);
				$('.e2l-controls', self.options.controls).toggle();
				$('.e2l-advanced', self.options.controls).toggle();
			});
			
			// The select all / none callbacks are added at the end of build
			this.options.controls.append(controls);
		},
		
		add: function(level, name) {
			var boxes = $('div[data-level='+level+']', this.element);
			if ($('.e2-infobox[data-name='+name+']', boxes).length) {
				return
			}
			var box = this.build_item(level, name, true);
			boxes.prepend(box);
		},
		
		save: function(e) {
			e.preventDefault();
			this.element.submit();
		},
		
		cache: function() {
			return caches[this.options.keytype][this.options.name];
		}
	})
	
	
	// Browse for an item
	$.widget('emen2.BrowseControl', {
		options: {
			root: null,
			keytype: null,
			action: 'view',
			controls: true,
			cb: function(self, name) {}
		},
		
		_create: function() {
			var self = this;
			this.built = 0;

			this.options.mode = $.checkopt(this, 'mode');
			this.options.root = $.checkopt(this, 'root');
			this.options.keytype = $.checkopt(this, 'keytype', 'record');

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
				<div class="e2l-cf e2-browse-header" style="border-bottom:solid 1px #ccc;margin-bottom:6px;"> \
					<div class="e2-browse-parents e2l-float-left" style="width:249px;"> Parents </div> \
					<div class="e2-browse-action e2l-float-left" style="width:249px;">Current Item</div> \
					<div class="e2-browse-children e2l-float-left" style="width:249px;"> Children </div> \
				</div> \
				<div class="e2l-cf e2-browse-map" style="position:relative" />');

			this.build_select();

			this.reroot(this.options.root);

			// Show the dialog
			this.dialog.attr("title", "Relationship Browser");
			this.dialog.dialog({
				modal: true,
				width: 800,
				height: 600
			});			
		},
		
		reroot: function(name) {
			var self = this;
			this.options.root = name;
			$('input[name=value]', this.dialog).val(name);
			
			var cb = function(w, elem, rel1, rel2) {
				self.reroot(rel2);
			}
			
			var parents = $('<div class="e2-map e2l-float-left" style="position:absolute;left:0px;width:250px;">&nbsp;</span>');
			parents.MapControl({
				root: name, 
				keytype: this.options.keytype, 
				mode: 'parents',
				skiproot: true,
				show: true,
				cb: cb
			});			
			
			// The parents needs a spinner -- the MapControl one doesn't work right
			parents.append($.spinner(true));

			var children = $('<div class="e2-map e2l-float-left" style="position:absolute;left:250px;" />');
			children.MapControl({
				root: name, 
				keytype: this.options.keytype, 
				mode: 'children',
				show: true,
				cb: cb
			});
			
			var input = $('input[name=value]', this.dialog);
			var val = input.val();
			input.focus();
			if (val.toString() == this.options.root.toString()) {
				$('input[name=submit]', this.dialog).val('Select');
			}
			
			$('.e2-browse-map', this.dialog).empty();
			$('.e2-browse-map', this.dialog).append(parents, children);
		},
		
		build_select: function() {
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
					self.select(val);
				} else {
					self.reroot(val);
				}
			});
				
			var action = $('.e2-browse-action', this.dialog);
			action.empty();
			action.append(controls);
		},
		
		select: function(name) {
			var self = this;
			this.options.cb(self, name)
			this.dialog.dialog('close');
		}
		
	});
	
	
	// Relationship BROWSER
    $.widget("emen2.MapControl", {		
		options: {
			root: null,
			keytype: null,
			mode: null,
			expandable: true,
			show: false,
			attach: false,
			skiproot: false,
			cb: null,
		},

		_create: function() {
			var self = this;
			this.built = 0;

			this.options.mode = $.checkopt(this, 'mode', 'children');
			this.options.root = $.checkopt(this, 'root');
			this.options.keytype = $.checkopt(this, 'keytype', 'record');

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
			if (!caches[this.options.keytype][name]) {
				// make a pass through this.getnames if we don't have this cached already
				this.getviews([name], function(){self.build_root(elem, name)});
				return
			}

			var root = $('<ul></ul>');
			root.append(' \
				<li data-name="'+name+'"> \
					<a href="#">'+this.getname(this.options.root)+'</a>'+
					$.e2image('bg-open.'+this.options.mode+'.png', '+', 'e2-map-expand')+
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
			$.each(caches[this.options.mode][name], function() {
				sortby[this] = self.getname(this);
			});
			var sortkeys = $.sortstrdict(sortby);
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
				if (caches[self.options.mode][this] && self.options.expandable) {
					var expand = $($.e2image('bg-open.'+self.options.mode+'.png', caches[self.options.mode][this].length, 'e2-map-expand'))
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

			// We use rel.child.tree because we want to grab 2 levels of children/parents
			// 	to determine if each child is itself expandable...
			var method = "rel.child.tree";
			if (this.options.mode == "parents") {method = "rel.parent.tree"}
			$.jsonRPC.call(method, {names:name, recurse:2, keytype:this.options.keytype}, function(tree){
				// Cache the result. This should be filtered for permissions
				$.each(tree, function(k,v) {caches[self.options.mode][k] = v});				
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
			
			if (this.options.cb) {
				$('a', root).click(function(e) {
					e.preventDefault();
					var elem = $(e.target).parent();
					var rel1 = elem.parent().attr('data-name');
					var rel2 = elem.attr('data-name');
					self.options.cb(self, elem, rel1, rel2);
				});
			}
		},

		// cache items that we need, then go to the callback
		getviews: function(names, cb) {
			var self = this;
			var names = $.checkcache(this.options.keytype, names);
			if (names.length == 0) {
				cb();
				return
			}
			$.jsonRPC.call('get', {names: names, keytype: this.options.keytype}, function(items) {
				$.updatecache(items);
				if (self.options.keytype == 'record') {
					// For records, we also want to render the names..
					var found = $.map(items, function(k){return k.name});
					$.jsonRPC.call('record.render', [found], function(recnames) {
						$.each(recnames, function(k,v) {caches['recnames'][k]=v});
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
				return caches['recnames'][item] || String(item)
			} else if (this.options.keytype == 'paramdef') {
				return caches['paramdef'][item].desc_short || item
			} else if (this.options.keytype == 'recorddef') {
				return caches['recorddef'][item].desc_short || item
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