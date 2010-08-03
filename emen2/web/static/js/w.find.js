FindUserControl = (function($) { // Localise the $ function

function FindUserControl(elem, opts) {
	this.elem = $(elem);
	if (typeof(opts) != "object") opts = {};
	$.extend(this, FindUserControl.DEFAULT_OPTS, opts);
	this.init();
};

FindUserControl.DEFAULT_OPTS = {
	open: 0,
	mode: 'finduser',
	value: '',
	modal: true,
	cb: function(){}
};

FindUserControl.prototype = {
	
	init: function() {
		this.built = 0;
		var self=this;
		this.elem.click(function(e){self.event_click(e);})
		if (this.open) {
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
		if (this.mode=='finduser'){
			this.dialog.attr("title","Find User");
		} else {
			this.dialog.attr("title","Find Group");			
		}
		

		this.searchinput = $('<input type="text" />');
		this.searchinput.val(this.value);
		this.searchinput.keyup(function() {
			self.search(self.searchinput.val());
		});

		this.statusmsg = $('<span class="status">No Results</span>');
		var searchbox = $('<div class="searchbox">Search: </div>');
		searchbox.append(this.searchinput, this.statusmsg); //,this.searchbutton
		this.userarea = $('<div>Results</div>');
		
		this.dialog.append(searchbox, this.userarea);
		$(this.dialog).dialog({
			modal: this.modal,
			autoOpen: false,
			width: 700,
			height: 400
		});
		
		// this.elem.click(function(){self.event_show()});
	},

	event_click: function(e) {
		this.show();
	},
	
	show: function() {
		this.build();
		this.searchinput.val(this.elem.val());
		this.dialog.dialog('open');
		this.search(this.value);		
		this.searchinput.focus();
	},

	event_select: function(e) {
		this.select($(e.target).attr("data-name"));
	},
	
	select: function(name) {
		this.elem.val(name);
		this.cb(name);
		this.dialog.dialog('close');		
	},
	
	add: function(user) {
		if (this.mode=='finduser') {
			this.adduser(user);
		} else {
			this.addgroup(user);
		}
	},
	
	adduser: function(user) {
		caches["users"][user.username]=user;
		var d = $('<div class="userbox" data-name="'+user.username+'" />');
		var self=this;		
		d.click(function(e){self.event_select(e)});
		if (user.userrec["person_photo"]) {
			d.append('<img  data-name="'+user.username+'" src="'+EMEN2WEBROOT+'/download/'+user.userrec["person_photo"]+'/photo.png?size=tiny" />');
		} else {
			d.append('<img  data-name="'+user.username+'" src="'+EMEN2WEBROOT+'/images/nophoto.png" />');			
		}
		d.append('<div data-name="'+user.username+'">'+user.displayname+'<br />'+user.email+'</div>');
		this.userarea.append(d);
	},
	
	
	addgroup: function(group) {
		caches["groups"][group.name]=group;
		var d = $('<div class="userbox" data-name="'+group.name+'" />');
		var self=this;		
		d.click(function(e){self.event_select(e)});
		d.append('<img  data-name="'+group.name+'" src="'+EMEN2WEBROOT+'/images/nophoto.png" />');			
		d.append('<div data-name="'+group.name+'">'+group.name+'<br /></div>');
		this.userarea.append(d);
	},
	
		
	search: function(q) {
		var self=this;
		$.jsonRPC(this.mode, [q], function(users) {
			self.userarea.empty();
			var l = users.length;
			if (l==0) {
				self.statusmsg.text('No results');
				return
			}
			if (l>12) {
				self.statusmsg.text(users.length + ' results; showing 1-12');
			} else {
				self.statusmsg.text(users.length + ' results');				
			}
			users = users.slice(0,12);
			$.each(users, function() {
				self.add(this)			
			})
		})
	}

}

$.fn.FindUserControl = function(opts) {
  return this.each(function() {
		return new FindUserControl(this, opts);
	});
};

return FindUserControl;

})(jQuery); // End localisation of the $ function




