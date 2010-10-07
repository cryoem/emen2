(function($) {
    $.widget("ui.FindControl", {

		options: {
			show: 0,
			mode: 'finduser',
			value: '',
			modal: true,
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

			this.dialog = $('<div class="find" />');
			if (this.options.mode == 'finduser'){
				this.dialog.attr('title', 'Find User');
				this.add = this.adduser;
			} else if (this.options.mode == 'findgroup') {
				this.dialog.attr('title', 'Find Group');			
				this.add = this.addgroup;
			} else if (this.options.mode == 'findparamdef') {
				this.dialog.attr('title', 'Find Parameter');
				this.add = this.addparamdef;
			} else if (this.options.mode == 'findrecorddef') {
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

			this.statusmsg = $('<span class="status">No Results</span>');
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
			
			$('.ui-dialog-titlebar', this.dialog.dialog('widget')).append('<span class="spinner"><img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /></span>');		
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
	
		add: function() {
			alert("unbound");
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
			caches["users"][user.username] = user;
			var d = $('<div class="userbox" data-name="'+user.username+'" />');
			var self=this;		
			d.click(function(e){self.event_select(e)});
			if (user.userrec["person_photo"]) {
				d.append('<img data-name="'+user.username+'" src="'+EMEN2WEBROOT+'/download/'+user.userrec["person_photo"]+'/'+user.username+'.jpg?size=thumb" alt="Profile Photo" />');
			} else {
				d.append('<img data-name="'+user.username+'" src="'+EMEN2WEBROOT+'/static/images/nophoto.png" alt="No Photo" />');			
			}
			d.append('<div data-name="'+user.username+'">'+user.displayname+'<br />'+user.email+'</div>');
			this.resultsarea.append(d);
		},
	
	
		addgroup: function(group) {
			caches["groups"][group.name] = group;
			var d = $('<div class="userbox" data-name="'+group.name+'" />');
			var self=this;		
			d.click(function(e){self.event_select(e)});
			d.append('<img  data-name="'+group.name+'" src="'+EMEN2WEBROOT+'/static/images/nophoto.png" alt="Group" />');
			d.append('<div data-name="'+group.name+'">'+group.displayname+'<br />'+group.name+'</div>');
			this.resultsarea.append(d);
		},
	
		
		search: function(q) {
			var self=this;
			if (q.length < 3 && this.options.mode != "findgroup") {
				self.resultsarea.empty();
				self.statusmsg.text('Minimum 3 characters');
				return
			}
			
			$('.spinner', this.dialog.dialog('widget')).show();
				
			$.jsonRPC(this.options.mode, [q], function(items) {
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