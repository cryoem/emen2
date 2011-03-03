(function($) {
    $.widget("ui.RelationshipControl", {
		options: {
			recid: null,
			cb: function(recid){},
			keytype: "record",
			modal: false,
			embed: false,
			show: false,
			edit: false
		},
				
		_create: function() {
			var self = this;
			this.element.click(function() {
				self.event_click();
			});	
			this.event_click();
		},
	
		event_click: function() {
			var self = this;
			this.build();
		},
			
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
					autoOpen: false,
					modal: this.options.modal
				});			
			}
			
			// build the table area to reflect the current ID
			this.rebuild(this.options.recid);
		},
		
		build_browser: function(r) {
			console.log(this);
			var self = this;
			this.currentid = r;
			this.tablearea.empty();
			var parents = $('<ul></ul>');
			var children = $('<ul></ul>');

			//<li><a class="view draggable" data-key="451350" data-parent="473000" href="http://localhost:8080/record/451350/">Parent 1</a></li>						
			$.each(caches['parents'][this.currentid], function() {
				var li = $('<a class="view draggable" data-key="'+this+'">'+caches['recnames'][this]+'</a>');
				li.click(function(){self.event_select(this)});
				parents.append(li);
				li.wrap('<li></li>');
			});

			$.each(caches['children'][this.currentid], function() {
				var li = $('<a class="view draggable" data-key="'+this+'">'+caches['recnames'][this]+'</a>');
				li.click(function(){self.event_select(this)});
				children.append(li);
				li.wrap('<li></li>');
			});

			var i = $('<div style="float:left;width:200px;">'+caches['recnames'][this.currentid]+'</div>');

			var p = $('<div class="clearfix" style="padding-bottom:4px;border-bottom:solid 1px #ccc;"> \
						<div class="floatleft" style="width:262px;"><input class="floatleft save" name="addparent" type="button" value="+"> Parents</div> \
						<div class="floatleft" style="width:200px;">This Record</div> \
						<div class="floatleft" style="width:262px;"><input class="floatleft save" name="addchild" type="button" value="+"> Children</div> \
					</div>');

			this.tablearea.append(p, parents, i, children);
			// it seems it needs to be in the DOM before .wrap will work..
			parents.wrap('<div class="ulm parents" style="float:left"></div>');
			children.wrap('<div class="ulm children"style="float:left"></div>');
		},
		
		event_select: function(elem) {
			var self = this;
			var key = $(elem).attr('data-key');
			self.rebuild(key);
		},
	
		rebuild: function(key) {
			// Check the parents and children, get the recnames, run the build method...
			var self = this;		
			$.jsonRPC("getparents", [key, 1, null, self.options.keytype], function(parents) {
				caches["parents"][key] = parents;

				$.jsonRPC("getchildren", [key, 1, null, self.options.keytype], function(children) {
					caches["children"][key] = children;					
					var getnames = Array.concat(caches["parents"][key], caches["children"][key]);

					$.jsonRPC("renderview", [getnames], function(recnames) {
						$.each(recnames, function(k,v){ 
							caches['recnames'][k]=v;
						});
						self.build_browser(key);
					});					
					
				});

			});
		},
		
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
	
})(jQuery);








