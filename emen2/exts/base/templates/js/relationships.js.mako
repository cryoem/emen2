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
			// This has to be a copy; the original gets emptied somewhere in the callback
			var names2 = names.slice()

			// Always empty the element before a rebuild, and place a spinner
			this.element.empty();
			this.element.append($.spinner(true));
			
			// Cache rendered views for all the items
			// ian: todo: replace this with a InfoBox pre-cache method
			// Filter for what we need
			names = $.checkcache(this.options.keytype, names);
			$.jsonRPC.call('get', {names:names, keytype:this.options.keytype}, function(items) {
				$.updatecache(items)
				// Records need a second callback for pretty rendered text
				if (self.options.keytype == 'record') {
					// var names2 = $.checkcache('recnames', names2); ???
					$.jsonRPC.call('renderview', [names2], function(recnames) {
						$.each(recnames, function(k,v) {caches['recnames'][k] = v})
						self._build();
					})
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
				this.element.append('<p>This record has '+this.build_summary(parents, 'parents')+' and '+this.build_summary(children, 'children')+'. Select <span class="e2l-a e2-permissions-all">all</span> or <span class="e2l-a e2-permissions-none">none</span></p>');
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
				var adds = '';
				if (v.length > 1) {adds='s'}
				ce.push(v.length+' '+rd.desc_short+' <span data-checked="checked" data-reltype="'+label+'" data-rectype="'+k+'" class="e2l-small e2l-a e2-relationships-rectype">(toggle)</span>');
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
		
		build_level: function(label, level, items) {
			var self = this;
			var header = $('<h4 class="e2l-cf">'+label+'</h4>');
			if (this.options.edit) {
				header.prepend('<input data-level="'+level+'" type="button" value="+" /> ');
			}
			$('input:button', header).BrowseControl({
				name: this.options.name,
				keytype: this.options.keytype
			}).click(function(){
				$(this).BrowseControl('show');
			})
			
			//click(function() {
			//	var level = $(this).attr('data-level');
			//	console.log("Add...", level);
			//});

			var d = $('<div data-level="'+level+'"></div>');
			for (var i=0;i<items.length;i++) {
				d.append(this.build_item(level, items[i]))
			}
			return $('<div></div>').append(header, d);
		},
		
		build_item: function(level, name) {
			return $('<div></div>').InfoBox({
				keytype: this.options.keytype,
				name: name,
				selectable: this.options.edit,
				input: ['checkbox', level, true]				
			});
		},
		
		build_controls: function() {
			var self = this;
			// ian: todo: move "Select all or none" to a template utility function
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
		
		save: function(e) {
			e.preventDefault();
			this.element.submit();
		},
		
		cache: function() {
			return caches[this.options.keytype][this.options.name];
		}
	})
	
	
	$.widget('emen2.BrowseControl', {
		options: {
			root: null,
			keytype: null,
			action: 'view',
			controls: true,
			cb: function() {}
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

			var p = $(' \
					<div class="e2l-cf" style="border-bottom:solid 1px #ccc;margin-bottom:6px;"> \
						<div class="e2-browser-parents e2l-float-left" style="width:249px;"> Parents </div> \
						<div class="e2-browser-action e2l-float-left" style="width:249px;">&nbsp;</div> \
						<div class="e2-browser-children e2l-float-left" style="width:249px;"> Children </div> \
					</div>');


			var parents = $('<div class="e2-map e2l-float-left" style="width:250px"/>');
			parents.MapControl({
				root: this.options.name, 
				keytype: this.options.keytype, 
				mode: 'parents',
				show: true
			});			
			
			var children = $('<div class="e2-map e2l-float-left" />');
			children.MapControl({
				root: this.options.name, 
				keytype: this.options.keytype, 
				mode: 'children',
				show: true
			});			
						
			this.dialog.append(p, parents, children);

			// Show the dialog
			this.dialog.attr("title", "Relationship Browser");
			this.dialog.dialog({
				width: 1200,
				height: 400
			});			
		},
	});
	
	
	// Relationship BROWSER
    $.widget("emen2.MapControl", {		
		options: {
			root: null,
			keytype: null,
			mode: 'children',
			expandable: true,
			show: false,
			attach: false,
			cb: function(key){console.log('Clicked:', key)}
		},

		_create: function() {
			var self = this;
			this.built = 0;

			this.options.mode = $.checkopt(this, 'mode');
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
			this.element.empty();
			var root = $('<ul></ul>');
			root.append('<li><a data-key='+this.options.root+'>'+this.getname(this.options.root)+'</a>'+$.e2image('bg-open.'+this.options.mode+'.png', '+', 'e2-map-expand')+'</li>')
			this.element.append(root);
			this.attach(root);
			this.expand(root.find('li'));
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
		},

		// cache items that we need, then go to the callback
		getviews: function(keys, cb) {
			var self = this;
			if (self.options.keytype == "record") {
				$.jsonRPC.call("record.render", [keys, null, "recname"], function(recnames){
					$.each(recnames, function(k,v) {caches['recnames'][k]=v});
					cb();
				});					
			} else if (self.options.keytype == "recorddef") {
				$.jsonRPC.call("recorddef.get", [keys], function(rds){
					$.updatecache(rds)
					cb();
				});											
			} else if (self.options.keytype == "paramdef") {
				$.jsonRPC.call("paramdef.get", [keys], function(pds){
					$.updatecache(pds)
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

		// The following methods use 'elem' as the first argument
		// This should be a 'ul' with a data-parent
		
		// expand/contract a branch		
		toggle: function(elem) {
			// elem is the expand image element			
			var self = this;
			var elem = $(elem);
			// pass the img's parent LI to this.expand
			if (elem.hasClass('e2-map-expanded')) {
				elem.removeClass('e2-map-expanded');
				elem.siblings('ul').remove();
				elem.attr('src', EMEN2WEBROOT+'/static-'+VERSION+'/images/bg-open.'+this.options.mode+'.png');
			} else {
				this.expand(elem.parent());
			}			
		},
		
		// rebuild a branch
		// todo: use items.parents, items.children
		expand: function(elem) {
			// elem is the LI
			var self = this;
			var key = elem.children('a').attr('data-key');
			var img = elem.children('img');
			img.attr('src', EMEN2WEBROOT+'/static-'+VERSION+'/images/spinner.gif'); 

			// remove current ul..
			elem.find('ul').remove();

			var method = "rel.child.tree";
			if (this.options.mode == "parents") {
				method = "rel.parent.tree";
			}
			
			$.jsonRPC.call(method, [key, 2, null, this.options.keytype], function(tree){
				// put these in the cache..
				$.each(tree, function(k,v) {caches[self.options.mode][k]=v});				
				self.getviews(tree[key], function(){self.buildtree(elem)});
			});				
		},

		// draw a branch.. elem is the LI
		buildtree: function(elem) {
			var self = this;
			var newl = $('<ul></ul>');
			var key = elem.find('a').attr('data-key');
			var img = elem.find('img');
			img.addClass('e2-map-expanded');
			img.attr('src', EMEN2WEBROOT+'/static-'+VERSION+'/images/bg-close.'+this.options.mode+'.png');
			
			// lower-case alpha sort...
			var sortby = {};
			$.each(caches[this.options.mode][key], function() {
				sortby[this] = self.getname(this);
			});
			var sortkeys = $.sortstrdict(sortby);
			sortkeys.reverse();			

			if (sortkeys.length == 0) {
				//img.attr('src', EMEN2WEBROOT+'/static-'+VERSION+'/images/bg-close.'+this.options.mode+'.png');
				img.remove();
			}
						
			$.each(sortkeys, function() {
				var line = $('<li> \
					<a data-key="'+this+'" data-parent="'+key+'" href="'+EMEN2WEBROOT+'/'+self.options.keytype+'/'+this+'/">'+self.getname(this)+'</a> \
					</li>');

				if (caches[self.options.mode][this] && self.options.expandable) {
					var expand = $($.e2image('bg-open.'+self.options.mode+'.png', caches[self.options.mode][this].length, 'e2-map-expand'))
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
			// this.bind_ul(newl);
			this.attach(newl);
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