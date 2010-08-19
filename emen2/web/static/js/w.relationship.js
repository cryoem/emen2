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
			this.saved = [];
			this.built = 0;
			
			if (this.options.show) {
				this.event_click();
			}
			
		},
	
		event_click: function() {
			this.build();
			if (!this.options.embed) {this.dialog.dialog('open')}
		},
			
		build: function() {
			if (this.built) {
				return
			}
			this.built = 1;
			
			this.update_rels();			
			
			var self=this;
			this.dialog = $('<div class="browser" title="Relationships" />');
			this.tablearea = $('<div class="clearfix"/>');
			this.dialog.append(this.tablearea);

			if (this.options.embed) {
				this.element.append(this.dialog);
			} else {
				var pos = this.element.offset();
				this.dialog.dialog({
					position:[pos.left, pos.top+this.element.outerHeight()],				
					autoOpen: false,
					modal: this.options.modal
				});			
			}
			this.build_browser(this.options.recid);
		},
		
		build_browser: function(r) {
			var self = this;
			
			if (r == null) {
				r = this.options.recid;
			}
			
			this.saved = $(".removed", this.tablearea).map(function(){
				return parseInt($(this).attr("data-recid"));
			});
			
			this.currentid = r;
			this.tablearea.empty();
			this.tablearea.html("Loading...");
			this.tablearea.load(EMEN2WEBROOT+'/db/map/record/'+this.currentid+'/both/', {maxrecurse: 1}, 
				function(response, status, xhr){
					if (status=='error') {
						self.tablearea.append('<p>Error!</p><p>'+xhr.statusText+'</p>');
						return
					}
					self.bind_table()
				}
			);
		},
		
		bind_table: function() {
			var self = this;
			
			this.header = $('<tr><th><input name="addparent" type="button" value="+" /> Parents</th><th/><th>This Record</th><th/><th><input name="addchild" type="button" value="+" /> Children</th></tr>');			

			$('input[name=addchild]', this.header).click(function() {
				self.event_addchild();
			})
			$('input[name=addparent]', this.header).click(function() {
				self.event_addparent();
			})

			$("thead", this.tablearea).prepend(this.header);

			if (this.options.edit) {
				$('a.map[data-recid!='+this.options.recid+']', this.tablearea).click(function(e){
					e.preventDefault();
					self.reltoggle(e);
					//self.build_browser(parseInt($(this).attr("data-recid")));
				});
				$('a.map[data-recid='+this.options.recid+']', this.tablearea).click(function(e){
					e.preventDefault();
				});



			}
			
			this.controlsarea = $('<div class="controls" />');
			var i = $('<input type="button" value="Removed Selected" />');
			i.click(function() {
				self.event_removeselected();
			});
			this.controlsarea.append(i);

			var j = $('<input type="button" value="Copy Selected" />');
			j.click(function() {
				self.event_showselected();
			});
			this.controlsarea.append(j);

			this.tablearea.append(this.controlsarea);
			
			this.saved.each(function(i,v) {
				self.tablearea.find('a.map[data-recid='+v+']').addClass("removed");
			})
			
					
		},
		
		update_rels: function(cb) {
			cb = cb || function() {};
			var self = this;
			$.jsonRPC("getparents", [self.options.recid], function(parents) {
				caches["parents"][self.options.recid] = parents;

				$.jsonRPC("getchildren", [self.options.recid], function(children) {
					caches["children"][self.options.recid] = children;
					cb();
				});

			});
		},
		
		record_update: function(cb) {
			cb = cb || function() {};
			var self = this;

			var t = $('.precontent table.map');
			var root = t.attr("data-root");
			var mode = t.attr("data-mode");
			var keytype = t.attr("data-keytype");			
			t.parent().load(EMEN2WEBROOT+'/db/map/'+keytype+'/'+root+'/'+mode+'/');

			this.update_rels(function(){self.build_browser()});
			
		},
		
		event_showselected: function() {
			var rp = $(".removed", this.tablearea).map(function(){
				return parseInt($(this).attr("data-recid"));
			});
			rp = $.makeArray(rp);
			var d = $('<div title="Copy & Paste"><textarea style="width:100%;height:100%;"/></div>');
			$("textarea", d).val(rp.join(", "));
			d.dialog({
				width:500,
				height:200,
				autoOpen: true
			});
		},
		
		event_removeselected: function() {
			var self = this;
			var p = caches["parents"][this.options.recid];
			var c = caches["children"][this.options.recid];

			//if (p == null || c == null) {
			//	update_rels(function(){self.event_removeselected()})
			//}
			
			var rp = $(".removed", this.tablearea).map(function(){
				return parseInt($(this).attr("data-recid"));
			});
			
			// sort out parents/children...
			var rlinks = [];
			var premoved = 0;
			$.each(rp, function(i,v) {
				if ($.inArray(v, p) > -1) { //p.indexOf(v)>-1
					rlinks.push([v, self.options.recid]);
					premoved += 1;
				} else if ($.inArray(v, c) > -1) { //c.indexOf(v)>-1
					rlinks.push([self.options.recid, v]);					
				}
			});
			
			if (premoved > 0 && premoved >= p.length) {
				var y = confirm("This action will orphan the record; continue?");
				if (!y) {
					return
				}
			}
			
			if (rlinks.length == 0) {
				return
			}
			
			//console.log(rlinks);
			$.jsonRPC("pcunlinks", [rlinks], function() {
				notify("Removed relationships");
				self.saved = [];
				//self.build_browser();
				self.record_update();
				//self.record_update();				
			});
			
		},
		
		event_addparent: function() {
			var i = $('<div>');
			var self = this;
			var cb = function(test, r) {self.addparent(r)}
			i.Browser({recid:this.options.recid, cb:cb, show:1});
		},
		
		event_addchild: function() {
			var i = $('<div>');
			var self = this;
			var cb = function(test, r) {self.addchild(r)}
			i.Browser({recid:this.options.recid, cb:cb, show:1});			
		},
		
		addparent: function(r) {
			var self = this;
			r = parseInt(r);
			$.jsonRPC("pclink", [r, this.options.recid], function() {
				notify("Added parent");
				self.record_update();
			});
		},
		
		addchild: function(r) {
			var self = this;
			r = parseInt(r);
			$.jsonRPC("pclink", [this.options.recid, r], function() {
				notify("Added child");
				self.record_update();
			});			
		},
		
		reltoggle: function(e) {
			var t = $(e.target);
			t.toggleClass('removed');
		},
		
		select: function(val) {
			this.options.cb();
			if (!this.options.embed) {this.dialog.dialog('close')}
		},
		
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
	
})(jQuery);
