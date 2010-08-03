PermissionControl = (function($) { // Localise the $ function

function PermissionControl(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, PermissionControl.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
};


PermissionControl.DEFAULT_OPTS = {
	levels: ["Read-only","Comment","Write","Admin"],
	newrecord: 0,
	edit: 0,
	open: 0,
	modal: false
};

PermissionControl.prototype = {
	
	init: function() {
		var self=this;
		this.elem.click(function(e){self.event_click(e);})
		this.built = 0;
		this.copy_from_rec(caches["recs"][this.recid]);
		if (this.open) {
			this.show();
		}		
	},
	
	
	reinit: function() {
		this.copy_from_rec(caches["recs"][this.recid]);
		this.build_userarea();
		this.build_grouparea();
	},
	

	copy_from_rec: function(rec) {
		this.permissions = [[],[],[],[]];
		this.groups = [];
		var self=this;
		$.each(rec["permissions"], function(i) {
			self.permissions[i]=this;
		});
		$.each(rec["groups"], function(i) {
			self.groups.push(this);
		});
	},


	event_click: function(e) {
		this.show();
	},
	
	build: function() {

		if (this.built) {
			return
		}
		this.built = 1;
		var self=this;

		////////////////////////////////
		// Add user controls
		
		this.dialog = $('<div class="permissions"></div>');
		this.grouparea = $('<div/>');
		this.userarea = $("<div/>");
		this.dialog.append(this.grouparea);
		this.dialog.append(this.userarea);

		// Save controls
		if (!this.newrecord && this.edit) {
			this.savearea = $('<div/>');
			var savearea_apply = $('<input type="button" value="Apply Changes" />').click(function(){self.save()});
			var savearea_applyrec = $('<input type="checkbox" id="recurse" />').click(function(){self.recurse=$(this).attr("checked")});
			this.savearea.append(savearea_apply,savearea_applyrec,'<label for="recurse">Recursive</label>');
			this.dialog.append(this.savearea);
		}

		// this.elem.append(user_outer);
		this.dialog.attr("title","Permissions");
		
		var pos = this.elem.offset();

		this.dialog.dialog({
			autoOpen: false,
			width: 800,
			height: 600,
			position: [pos.left, pos.top+this.elem.outerHeight()],
			modal: this.modal
		});
		
	},
	
	
	show: function() {
		this.build();
		this.dialog.dialog('open');		
		this.getdisplaynames();
	},

	hide: function() {
		this.dialog.dialog('close');
	},
	
	getdisplaynames: function() {	
		var self=this;
		$.jsonRPC("getuser", [[this.recid]], function(users){ 
			$.each(users, function() {
				caches["users"][this.username] = this;
			});
			self.build_userarea();			
		});

		this.build_grouparea();
	},
	
	
	build_grouparea: function() {
		var self=this;
		this.grouparea.empty();

		// group area
		// if (this.groups.length == 0) {
		// 	
		// } else {

		var level = $('<div class="level clearfix" data-level="group"></div>');
		this.grouparea.append(level);

		var title = $('<h4 class="clearfix"> Groups</h4>');
		if (this.edit) {
			var button = $('<input class="addbutton" type="button" value="+" /> ');
			button.FindUserControl({
				mode: 'findgroup',
				cb:function(groupname){self.addgroup(groupname)}
			});
			title.prepend(button);
		}
		level.append(title);

		$.each(this.groups, function(i, groupname) {
			self.drawgroup(groupname);
		});

		
	},


	build_userarea: function() {
		var self=this;
		this.userarea.empty();		
		
		$.each(this.permissions, function(k,v) {			
			var level = $('<div class="level clearfix" data-level="'+k+'"></div>');
			var title = $('<h4 class="clearfix"> '+self.levels[k]+'</h4>');
			if (self.edit) {
				var button = $('<input class="addbutton" type="button" value="+" />');
				button.FindUserControl({
					cb:function(username){self.add(username, k)}
				});
				title.prepend(button);
			}
			level.append(title);
			
			self.userarea.append(level);

			if (v.length == 0) {
				//level.append('<div class="userbox"></div>');
			} else {
				// var level_removeall=$('<span class="small_label">[<span class="jslink">X</span>]</span>').click(function () {
				$.each(v, function(i,username) {
					self.drawuser(username, k);
				});
			}

		});	
	 },
	
	addgroup: function(groupname) {
		var self=this;
		$('.userbox[data-groupname='+groupname+']', this.dialog).each(function(){
			$(this).remove();
		});
		self.drawgroup(groupname, true);
	},
	
	
	add: function(username, level) {
		level = parseInt(level);
		var self=this;
		$('.userbox[data-username='+username+']', this.dialog).each(function(){
			$(this).remove();
		});
		self.drawuser(username, level, true);
	},
	
	
	drawuser: function(username, level, add) {
		level = parseInt(level);
		var self = this;				
		var user = caches["users"][username];

		if (!user) {
			user = {};
			user.username = username;
			user.displayname = username;
			user.userrec = {};
			user.email = '';
		}

		var userdiv = $('<div class="userbox user" data-username="'+user.username+'" data-level="'+level+'"/>');
		if (user.userrec["person_photo"]) {
			userdiv.append('<img  data-username="'+user.username+'" src="'+EMEN2WEBROOT+'/download/'+user.userrec["person_photo"]+'/photo.png?size=tiny" />');
		} else {
			userdiv.append('<img  data-username="'+user.username+'" src="'+EMEN2WEBROOT+'/images/nophoto.png" />');			
		}
		userdiv.append('<div data-level="'+level+'" data-username="'+user.username+'">'+user.displayname+'<br />'+user.email+'</div>');					

		if (this.edit) {
			userdiv.click(function() {self.toggleuser(userdiv.attr("data-username"), userdiv.attr("data-level"))});
		}
		if (add) {
			userdiv.addClass('add');
		}

		$('.level[data-level='+level+']', this.dialog).append(userdiv);
	},


	drawgroup: function(groupname, add) {
		var self = this;				
		var groupdiv = $('<div class="userbox group" data-groupname="'+groupname+'" />');
		groupdiv.append('<img  data-groupname="'+groupname+'" src="'+EMEN2WEBROOT+'/images/group.png" />');	
		groupdiv.append('<div data-groupname="'+groupname+'">'+groupname+'<br /></div>');
		
		if (this.edit) {
			groupdiv.click(function() {self.togglegroup(groupdiv.attr("data-groupname"));});
		}
		if (add) {
			groupdiv.addClass('add');
		}
		
		$('.level[data-level=group]', this.dialog).append(groupdiv);
	},


	toggleuser: function(username, level) {
		$('.userbox[data-username='+username+']', this.dialog).each(function(){
			$(this).toggleClass('removed');
		});
	},

	togglegroup: function(groupname) {
		$('.userbox[data-groupname='+groupname+']', this.dialog).each(function(){
			$(this).toggleClass('removed');
		});
	},	
	
	getaddgroups: function() {
		var r = $('.userbox.group.add:not(.removed)').map(function(){return $(this).attr('data-groupname')});	
		return $.makeArray(r);
	},
	
	getdelgroups: function() {
		var r = $('.userbox.group.removed').map(function(){return $(this).attr('data-groupname')});
		return $.makeArray(r);
	},
	
	getdelusers: function() {
		var r = $('.userbox.user.removed').map(function(){return $(this).attr('data-username')});	
		return $.makeArray(r);
	},
	
	getaddusers: function() {
		var ret = [];
		var self = this;
		for (var i=0;i<4;i++) {	
			var r = $('.userbox.user.add:not(.removed)[data-level='+i+']').map(function(){
				return $(this).attr('data-username')
			});
			ret.push($.makeArray(r));
		}
		return ret
	},
	

	save: function() {		
		var self=this;		
		var rlevels=0;
		if (this.recurse) {
			rlevels=-1;
		}

		var sec_commit = {};
		sec_commit["recid"] = this.recid;
		sec_commit["umask"] = this.getaddusers();
		sec_commit["delusers"] = this.getdelusers();
		sec_commit["addgroups"] = this.getaddgroups();
		sec_commit["delgroups"] = this.getdelgroups();
		sec_commit["reassign"] = 1;
		sec_commit["recurse"] = rlevels;
		
		$.jsonRPC("secrecordadduser_compat", sec_commit, 
			function() {
				
				$.jsonRPC("getrecord",[self.recid],
					function(record) {
						// ian: changing permissions shouldn't require a full rebuild...
						notify("Saved Permissions");
						caches["recs"][self.recid] = record;
						self.reinit();
						self.hide();
					});

			}
		);		

	},
		
	
}

$.fn.PermissionControl = function(opts) {
  return this.each(function() {
		new PermissionControl(this, opts);
	});
};

return PermissionControl;

})(jQuery); // End localisation of the $ function