(function($) {
    $.widget("ui.SelectQuery", {
		options: {
			rectype: null,
			children: null,
			show: false,
			cb_select: function(name) {}
		},
		
		_create: function() {
			var self = this;
			this.options.rectype = this.element.attr('data-rectype') || this.options.rectype;			
			if (this.options.show) {
				this.build();				
			} else {
				this.element.click(function(){self.build()});
			}
		},

		build: function() {
			var self = this;
			this.dialog = $('<div><img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /></div>');
			this.element.append(this.dialog);
			this.dialog.attr("title", "Select Record");
			
			var c = [];
			if (this.options.rectype) {
				c.push(['rectype','==',this.options.rectype]);
			}
			if (this.options.children) {
				c.push(['children','==',this.options.children]);
			}
			var query = {
				'c':c,
			}

			$.jsonRPC("query", query, function(data) {
				var recs = data['names'];
				var rq = {
					'names':recs,
					'viewdef': '$@recname() $$creator $$creationtime',
					'table': true,
					'markup': false
				}
				
				$.jsonRPC('renderview', rq, function(rendered) {
					self.dialog.empty();
					var table = $('<table cellspacing="0" cellpadding="0"><thead></thead><tbody></tbody></table>');
					var trh = $('<tr/>');
					$.each(rendered['headers'][null], function() {
						trh.append('<th>'+this[0]+'</th>');
					});

					for (var i=0;i<recs.length;i++) {
						var row = rendered[recs[i]];
						var tr = $('<tr/>');
						if (i%2) {
							tr.addClass('s');
						}
						
						for (var j=0;j<row.length;j++) {
							var td = $('<td data-name="'+recs[i]+'" class="clickable">'+row[j]+'</td>');
							tr.append(td);
						}
						$('tbody', table).append(tr);
					}

					$('thead', table).append(trh)
					self.dialog.append(table);
					
					$('.clickable', table).click(function() {
						var name = $(this).attr('data-name');
						self.options.cb_select(name);
						self.dialog.dialog('close');
					});

				});
			});

			if (!this.options.embed) {
				this.dialog.dialog({
					width: 800,
					height: $(window).height()*0.8,
					modal: true,
					autoOpen: true
				});
			}
		},	
		
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);




(function($) {
    $.widget("ui.FindControl", {

		options: {
			show: 0,
			keytype: 'user',
			value: '',
			modal: true,
			vartype: null,
			minimum: 2,
			cb: function(self, value){self.element.val(value)}
		},
				
		_create: function() {
			this.built = 0;
			var self=this;
			this.element.click(function(e){self.event_click(e);})
			if (this.options.show) {
				this.show();
			}
		},
	
	
		build: function() {
			if (this.built) {
				return
			}
			var self = this;
			this.built = 1;

			this.dialog = $('<div/>');
			if (this.options.keytype == 'user'){
				this.dialog.attr('title', 'Find User');
				this.add = this.adduser;
			} else if (this.options.keytype == 'group') {
				this.dialog.attr('title', 'Find Group');			
				this.add = this.addgroup;
			} else if (this.options.keytype == 'paramdef') {
				this.dialog.attr('title', 'Find Parameter');
				this.add = this.addparamdef;
			} else if (this.options.keytype == 'recorddef') {
				this.dialog.attr('title', 'Find Protocol');
				this.add = this.addrecorddef;
			}
		
			this.searchinput = $('<input type="text" />');
			this.searchinput.val(this.options.value);

			this.searchinput.keyup(function(e) {
				var v = self.searchinput.val();
				if (e.keyCode == '13') { 
					e.preventDefault();
					self.select(v);
					}
				self.search(v);
			});

			this.statusmsg = $('<span class="floatright">No Results</span>');
			var searchbox = $('<div class="searchbox">Search: </div>');
			searchbox.append(this.searchinput, this.statusmsg); //,this.searchbutton
			this.resultsarea = $('<div>Results</div>');
		
			this.dialog.append(searchbox, this.resultsarea);
			this.dialog.dialog({
				modal: this.options.modal,
				autoOpen: false,
				width: 700,
				height: 400
			});
			
			$('.ui-dialog-titlebar', this.dialog.dialog('widget')).append('<span class="spinner hide"><img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /></span>');		
		},

		event_click: function(e) {
			this.show();
		},
	
		show: function() {
			this.build();		
			if (this.element.val() != "+") {
				this.searchinput.val(this.element.val());
				this.options.value = this.searchinput.val();
			}
			this.dialog.dialog('open');
			this.search(this.options.value);		
			this.searchinput.focus();
		},

		event_select: function(e) {
			this.select($(e.target).attr("data-name"));
		},
	
		select: function(name) {
			//this.elem.val(name);
			this.options.cb(this, name);
			this.dialog.dialog('close');		
		},
	
		add: function(item) {
			//console.log(item);
		},

		addparamdef: function(paramdef) {
			caches["paramdefs"][paramdef.name] = paramdef;
			var d = $('<div class="userbox" data-name="'+paramdef.name+'" />');
			var self=this;
			d.click(function(e){self.event_select(e)});
			d.append('<img data-name="'+paramdef.name+'" src="'+EMEN2WEBROOT+'/static/images/gears.png" alt="Parameter" />');	
			d.append('<div data-name="'+paramdef.name+'">'+paramdef.desc_short+' ('+paramdef.name+')<br />'+paramdef.vartype+'</div>');
			this.resultsarea.append(d);			
		},

		addrecorddef: function(recorddef) {
			caches["recorddefs"][recorddef.name] = recorddef;
			var d = $('<div class="userbox" data-name="'+recorddef.name+'" />');
			var self=this;
			d.click(function(e){self.event_select(e)});
			d.append('<img data-name="'+recorddef.name+'" src="'+EMEN2WEBROOT+'/static/images/gears.png" alt="Protocol" />');	
			d.append('<div data-name="'+recorddef.name+'">'+recorddef.desc_short+'<br />'+recorddef.name+'</div>');
			this.resultsarea.append(d);			
		},
		
		adduser: function(user) {
			caches["users"][user.name] = user;
			var d = $('<div class="userbox" data-name="'+user.name+'" />');
			var self=this;		
			d.click(function(e){self.event_select(e)});
			if (user.userrec["person_photo"]) {
				d.append('<img data-name="'+user.name+'" src="'+EMEN2WEBROOT+'/download/'+user.userrec["person_photo"]+'/'+user.name+'.jpg?size=thumb" alt="Photo" />');
			} else {
				d.append('<img data-name="'+user.name+'" src="'+EMEN2WEBROOT+'/static/images/nophoto.png" alt="Photo" />');			
			}
			d.append('<div data-name="'+user.name+'">'+user.displayname+'<br />'+user.email+'</div>');
			this.resultsarea.append(d);
		},
	
	
		addgroup: function(group) {
			caches["groups"][group.name] = group;
			var d = $('<div class="userbox" data-name="'+group.name+'" />');
			var self=this;		
			d.click(function(e){self.event_select(e)});
			d.append('<img  data-name="'+group.name+'" src="'+EMEN2WEBROOT+'/static/images/nophoto.png" alt="Photo" />');
			d.append('<div data-name="'+group.name+'">'+group.displayname+'<br />'+group.name+'</div>');
			this.resultsarea.append(d);
		},
	
		
		search: function(q) {
			var self=this;
			if (q.length < this.options.minimum) {
				self.resultsarea.empty();
				self.statusmsg.text('Minimum '+this.options.minimum+' characters');
				return
			}
			
			$('.spinner', this.dialog.dialog('widget')).show();
			
			var query = {}
			query['query'] = q;
			if (this.options.vartype) {
				query['vartype'] = this.options.vartype;
			}
				
			$.jsonRPC('find'+this.options.keytype, query, function(items) {
				$('.spinner', self.dialog.dialog('widget')).hide();				
				self.resultsarea.empty();
				var l = items.length;
				if (l==0) {
					self.statusmsg.text('No results');
					return
				}
				if (l>50) {
					self.statusmsg.text(items.length + ' results; showing 1-50');
				} else {
					self.statusmsg.text(items.length + ' results');				
				}
				items = items.slice(0,50);
				$.each(items, function() {
					self.add(this)			
				});
			})
		},
		
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
	
})(jQuery);