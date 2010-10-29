(function($) {
    $.widget("ui.PermissionControl", {
		options: {
			recid: null,
			groupname: null,
			levels: ["Read-only","Comment","Write","Admin"],
			edit: 0,
			show: 0,
			modal: false,
			embed: false
		},
				
		_create: function() {
			var self=this;
			this.built = 0;
			this.reset_from_cache();

			if (!this.options.embed) {
				this.element.click(function(e){e.stopPropagation();self.event_click(e);})
			}

			if (this.options.show || this.options.embed) {
				this.show();
			}
		},
	
	
		reinit: function() {
			this.reset_from_cache();
			this.build_userarea();
			this.build_grouparea();
		},
	

		copy_from_cache: function(rec) {
			if (this.options.recid != null) {
				var plist = caches['recs'][this.options.recid]['permissions'];
				var glist = caches['recs'][this.options.recid]['groups'];
			} else if (this.options.groupname) {
				var plist = caches['groups'][this.options.groupname]['permissions'];				
				var glist = [];
			}
			return [plist, glist]
		},
		
		reset_from_cache: function() {
			var f = this.copy_from_cache();
			
			this.permissions = [[],[],[],[]];
			this.groups = [];

			var self=this;
			$.each(f[0], function(i) {
				self.permissions[i]=this;
			});			
			$.each(f[1], function(i) {
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
			if (this.options.edit) {
				// this.savearea = $('<div class="controls"/>');
				this.savearea = $('<div class="controls save"><ul class="options nonlist"></ul><img class="spinner" src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /></div>');
				if (this.options.recid != "None" && this.options.recid != null) {
					
					var opt_recurse = $(' \
						<li><input type="checkbox" id="recurse" name="recurse"> <label for="recurse">Recursive</label></li> \
						<li> \
							<input type="checkbox" disabled="disabled" name="overwrite_users" id="overwrite_users" class="overwrite disabled"> \
							<label class="overwrite disabled" for="overwrite_users">Overwrite Users</label> \
						</li><li> \
							<input type="checkbox" disabled="disabled" name="overwrite_groups" id="overwrite_groups" class="overwrite disabled"> \
							<label class="overwrite disabled" for="overwrite_groups">Overwrite Groups</label> \
						</li>');


					$('input[name=recurse]', opt_recurse).click(function(){
						var state = $(this).attr('checked');
						if (state) {
							$('.overwrite', self.dialog).removeAttr("disabled");
							$('.overwrite', self.dialog).removeClass("disabled");
						} else {
							$('.overwrite', self.dialog).attr('disabled', 1);
							$('.overwrite', self.dialog).addClass("disabled");
						}
						});

					var apply = $('<input type="button" value="Apply Changes" />').click(function(){self.save_record()});
					
					$('.options', this.savearea).append(opt_recurse);
					this.savearea.append(apply);
					this.dialog.append(this.savearea);
					

				} else if (this.options.groupname != "None" && this.options.groupname != null) {
				}
			}

			// this.elem.append(user_outer);
			this.dialog.attr("title","Permissions");
		
			if (this.options.embed) {
				this.element.append(this.dialog);
				return
			}

			var pos = this.element.offset();
			this.dialog.dialog({
				autoOpen: false,
				width: 800,
				height: 600,
				position: [pos.left, pos.top+this.element.outerHeight()],
				modal: this.options.modal
			});
		
		},
	
	
		show: function() {
			this.build();
			if (!this.options.embed) {this.dialog.dialog('open')}
			this.getdisplaynames();
		},

		hide: function() {
			this.dialog.dialog('close');
		},
	
		getdisplaynames: function() {	
			var self = this;
			var f = this.copy_from_cache();

			var f2 = [];
			for (var i=0;i<f[0].length;i++) {
				for (var j=0;j<f[0][i].length;j++) {
					f2.push(f[0][i][j]);
				}
			}

			$.jsonRPC("getuser", [f2], function(users){ 
				$.each(users, function() {
					caches["users"][this.username] = this;
				});
				self.build_userarea();			
			});
			this.build_grouparea();
		},
	
	
		build_grouparea: function() {

			if (this.options.groupname) {return}

			var self=this;
			this.grouparea.empty();

			// group area
			// if (this.groups.length == 0) {
			// 	
			// } else {

			var level = $('<div class="level clearfix" data-level="group"></div>');
			this.grouparea.append(level);

			var title = $('<h4 class="clearfix"> Groups</h4>');
			if (this.options.edit) {
				var button = $('<input class="addbutton" type="button" value="+" /> ');
				button.FindControl({
					mode: 'findgroup',
					cb:function(test, groupname){self.addgroup(groupname)}
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
				var title = $('<h4 class="clearfix"> '+self.options.levels[k]+'</h4>');
				if (self.options.edit) {
					var button = $('<input class="addbutton" type="button" value="+" />');
					button.FindControl({
						cb:function(test, username){self.add(username, k)}
					});
					title.prepend(button);
				}
				level.append(title);
			
				self.userarea.append(level);

				if (v.length == 0) {
					//level.append('<div class="userbox"></div>');
				} else {
					// var level_removeall=$('<span class="small_label">[<span class="clickable">X</span>]</span>').click(function () {
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
				userdiv.append('<img data-username="'+user.username+'" src="'+EMEN2WEBROOT+'/download/'+user.userrec["person_photo"]+'/'+user.username+'.jpg?size=thumb" alt="Profile" />');
			} else {
				userdiv.append('<img  data-username="'+user.username+'" src="'+EMEN2WEBROOT+'/static/images/nophoto.png" />');			
			}
			userdiv.append('<div data-level="'+level+'" data-username="'+user.username+'">'+user.displayname+'<br />'+user.email+'</div>');					

			if (this.options.edit) {
				userdiv.click(function(e) {e.stopPropagation();self.toggleuser(userdiv.attr("data-username"), userdiv.attr("data-level"))});
			}
			if (add) {
				userdiv.addClass('add');
			}

			$('.level[data-level='+level+']', this.dialog).append(userdiv);
		},


		drawgroup: function(groupname, add) {
			var self = this;				
			var groupdiv = $('<div class="userbox group" data-groupname="'+groupname+'" />');
			groupdiv.append('<img  data-groupname="'+groupname+'" src="'+EMEN2WEBROOT+'/static/images/group.png" />');	
			groupdiv.append('<div data-groupname="'+groupname+'">'+groupname+'<br /></div>');
		
			if (this.options.edit) {
				groupdiv.click(function(e) {e.stopPropagation();self.togglegroup(groupdiv.attr("data-groupname"));});
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
	
		getaddgroups: function(all) {
			if (all) {
				var baseselector = '.userbox.group:not(.removed)'				
			} else {
				var baseselector = '.userbox.group.add:not(.removed)'
			}						
			var r = $(baseselector).map(function(){return $(this).attr('data-groupname')});	
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
	
		getaddusers: function(all) {
			if (all) {
				var baseselector = '.userbox.user:not(.removed)'				
			} else {
				var baseselector = '.userbox.user.add:not(.removed)'
			}

			var ret = [];
			var self = this;
			for (var i=0;i<4;i++) {
				var r = $(baseselector+'[data-level='+i+']').map(function(){
					return $(this).attr('data-username')
				});
				ret.push($.makeArray(r));
			}
			return ret
		},
		
		getgroups: function() {
			var r = $('.userbox.group:not(.removed)').map(function(){return $(this).attr('data-groupname')});	
			return $.makeArray(r);
		},
	
		getusers: function() {
			return this.getaddusers(false);
		},


		save_group: function() {
			var group = caches['groups'][this.options.groupname];
			group["permissions"] = this.getusers();
			$.jsonRPC("putgroup", [group], function(){
				alert("Saved Group");
				window.location = window.location;
			});
		},

		save_record: function() {		
			var self = this;
			var rlevels=0;
			if ($('input[name=recurse]', this.dialog).attr('checked')) {
				rlevels = -1;
			}
						
			var sec_commit = {};
			sec_commit["recid"] = this.options.recid;
			sec_commit["delusers"] = this.getdelusers();
			sec_commit["delgroups"] = this.getdelgroups();
			sec_commit["reassign"] = 1;
			sec_commit["recurse"] = rlevels;
			
			var overwrite_users = $('input[name=overwrite_users]', this.dialog).attr('checked');
			var overwrite_groups = $('input[name=overwrite_groups]', this.dialog).attr('checked');
			
			if (overwrite_users) {
				sec_commit['overwrite_users'] = overwrite_users;
				sec_commit['delusers'] = null;
			}
			if (overwrite_groups) {
				sec_commit['overwrite_groups'] = overwrite_groups;
				sec_commit['delgroups'] = null;
			}
			
			sec_commit["umask"] = this.getaddusers(overwrite_users);
			sec_commit["addgroups"] = this.getaddgroups(overwrite_groups);

			if (overwrite_users || overwrite_groups) {
				var c = confirm("This action will overwrite the permissions of all child records to be the same as this record. Are you sure you want to continue?")
				if (!c) {return}
			}			


			$('.spinner', this.savearea).show();			
			$.jsonRPC("secrecordadduser_compat", sec_commit, 
				function() {
				
					$.jsonRPC("getrecord",[self.options.recid],
						function(record) {
							$('.spinner', self.savearea).hide();
							// ian: changing permissions shouldn't require a full rebuild...
							notify("Saved Permissions");
							caches["recs"][self.options.recid] = record;
							self.reinit();
							//self.hide();
						});

				}
			);		

		},
		
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
	
})(jQuery);		