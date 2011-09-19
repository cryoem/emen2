(function($) {
    $.widget("emen2.PermissionControl", {
		options: {
			keytype: 'record',
			name: null,
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
			if (this.options.keytype=='record') {
				var plist = caches['record'][this.options.name]['permissions'];
				var glist = caches['record'][this.options.name]['groups'];
			} else if (this.options.keytype=='group') {
				var plist = caches['group'][this.options.name]['permissions'];				
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
		
			this.dialog = $('<div/>');
			this.grouparea = $('<div/>');
			this.userarea = $("<div/>");
			this.dialog.append(this.grouparea);
			this.dialog.append(this.userarea);

			// Save controls
			if (this.options.edit) {
				this.savearea = $('<div class="controls save"><ul class="options nonlist"></ul><img class="spinner hide" src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /></div>');
				if (this.options.keytype == 'record' && this.options.name != "None") {
					
					var opt_recurse = $(' \
						<li><input type="checkbox" id="recurse" name="recurse"> <label for="recurse">Recursive</label></li> \
						<li> \
							<input type="checkbox" disabled="disabled" name="overwrite_users" id="e2-permissions-overwrite-users"> \
							<label for="e2-permissions-overwrite-users">Overwrite Users</label> \
						</li> \
						<li> \
							<input type="checkbox" disabled="disabled" name="overwrite_groups" id="e2-permissions-overwrite-groups"> \
							<label for="e2-permissions-overwrite-groups">Overwrite Groups</label> \
						</li>');


					$('input[name=recurse]', opt_recurse).click(function(){
						var state = $(this).attr('checked');
							if (state) {
								$('input[name=overwrite_users]', self.element).removeAttr("disabled");
								$('input[name=overwrite_groups]', self.element).removeAttr("disabled");							
							} else {
								$('input[name=overwrite_users]', self.element).attr("disabled", 1);
								$('input[name=overwrite_groups]', self.element).attr("disabled", 1);
							}
						});

					var apply = $('<input type="button" value="Apply Changes" />').click(function(){self.save_record()});
					
					$('.options', this.savearea).append(opt_recurse);
					this.savearea.append(apply);
					this.dialog.append(this.savearea);
					

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

			$.jsonRPC.call("getuser", [f2], function(users){ 
				$.each(users, function() {
					caches['user'][this.name] = this;
				});
				self.build_userarea();			
			});
			this.build_grouparea();
		},
	
	
		build_grouparea: function() {

			if (this.options.keytype=='group') {return}

			var self=this;
			this.grouparea.empty();

			var level = $('<div class="e2-permissions-level clearfix" data-level="group"></div>');
			this.grouparea.append(level);

			var title = $('<h4 class="clearfix"> Groups</h4>');
			if (this.options.edit) {
				var button = $('<input type="button" value="+" /> ');
				button.FindControl({
					keytype: 'group',
					minimum: 0,
					cb:function(test, groupname){self.add(groupname, 'group')}
				});
				title.prepend(button);
			}
			level.append(title);

			$.each(this.groups, function(i, groupname) {
				self.draw(groupname, 'group');
			});
		},


		build_userarea: function() {
			var self=this;
			this.userarea.empty();		
		
			$.each(this.permissions, function(k,v) {			
				var level = $('<div class="e2-permissions-level clearfix" data-level="'+k+'"></div>');
				var title = $('<h4 class="clearfix"> '+self.options.levels[k]+'</h4>');
				if (self.options.edit) {
					var button = $('<input type="button" value="+" />');
					button.FindControl({
						cb:function(test, name){self.add(name, k)}
					});
					title.prepend(button);
				}
				level.append(title);
			
				self.userarea.append(level);

				if (v.length == 0) {

				} else {
					// var level_removeall=$('<span class="small_label">[<span class="clickable">X</span>]</span>').click(function () {
					$.each(v, function(i,name) {
						self.draw(name, k);
					});
				}

			});	
		 },
	
		add: function(name, level) {
			var self = this;
			var keytype = 'user';
			if (level == 'group') {
				keytype = 'group';
			}
			$('.e2-infobox[data-keytype='+keytype+'][data-name='+name+']', this.dialog).each(function(){
				$(this).remove();
			});
			self.draw(name, level, true);
		},
	
	
		draw: function(name, level, add) {
			var self = this;				
			var keytype = 'user';
			if (level=='group') {
				keytype = 'group';
			}

			var d = $('<div />');
			d.InfoBox({
				'keytype':keytype,
				'name':name
			});
			d.attr('data-level', level);

			if (this.options.edit) {
				d.click(function(e) {
					e.stopPropagation();
					self.toggle(name, level);
				});
			}
			if (add) {
				d.addClass('add');
			}
			$('.e2-permissions-level[data-level='+level+']', this.dialog).append(d);			
		},
	
		toggle: function(name, level) {
			$('.e2-infobox[data-name='+name+'][data-level='+level+']', this.dialog).each(function(){
				$(this).toggleClass('removed');
			});
		},

		getaddgroups: function(all) {
			if (all) {
				var baseselector = '.e2-infobox[data-keytype=group]:not(.removed)'				
			} else {
				var baseselector = '.e2-infobox[data-keytype=group].add:not(.removed)'
			}						
			var r = $(baseselector, this.grouparea).map(function(){return $(this).attr('data-name')});	
			return $.makeArray(r);
		},
	
		getdelgroups: function() {
			var r = $('.e2-infobox[data-keytype=group].removed', this.grouparea).map(function(){return $(this).attr('data-name')});
			return $.makeArray(r);
		},
	
		getdelusers: function() {
			var r = $('.e2-infobox[data-keytype=user].removed', this.userarea).map(function(){return $(this).attr('data-name')});	
			return $.makeArray(r);
		},
	
		getaddusers: function(all) {
			if (all) {
				var baseselector = '.e2-infobox[data-keytype=user]:not(.removed)'				
			} else {
				var baseselector = '.e2-infobox[data-keytype=user].add:not(.removed)'
			}
			var ret = [];
			var self = this;
			for (var i=0;i<4;i++) {
				var r = $(baseselector+'[data-level='+i+']', this.userarea).map(function(){
					return $(this).attr('data-name')
				});
				ret.push($.makeArray(r));
			}
			return ret
		},
		
		getgroups: function() {
			var r = $('.e2-infobox[data-keytype=group]:not(.removed)', this.grouparea).map(function(){return $(this).attr('data-name')});
			return $.makeArray(r);
		},
	
		getusers: function() {
			return this.getaddusers(true);
		},

		save_group: function() {
			var group = caches['group'][this.options.name];
			group["permissions"] = this.getusers();
			$.jsonRPC.call("putgroup", [group], function(){
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
			sec_commit["names"] = this.options.name;
			sec_commit["recurse"] = rlevels;

			// sec_commit["reassign"] = 1;
			// sec_commit["delusers"] = this.getdelusers();
			// sec_commit["delgroups"] = this.getdelgroups();
			var overwrite_users = $('input[name=overwrite_users]', this.dialog).attr('checked');
			var overwrite_groups = $('input[name=overwrite_groups]', this.dialog).attr('checked');			
			if (overwrite_users) {
				sec_commit['overwrite_users'] = overwrite_users;
			}
			if (overwrite_groups) {
				sec_commit['overwrite_groups'] = overwrite_groups;
			}
			if (overwrite_users || overwrite_groups) {
				var c = confirm("This action will overwrite the permissions of all child records to be the same as this record. Are you sure you want to continue?")
				if (!c) {return}
			}			
			
			sec_commit["permissions"] = this.getaddusers(1);
			sec_commit["groups"] = this.getaddgroups(1);

			$('.spinner', this.savearea).show();			
			$.jsonRPC.call("setpermissions", sec_commit, 
				function() {				
					$.jsonRPC.call("getrecord",[self.options.name],
						function(record) {
							$('.spinner', self.savearea).hide();
							// ian: changing permissions shouldn't require a full rebuild...
							$.notify("Saved Permissions");
							caches['record'][self.options.name] = record;
							self.reinit();
							//self.hide();
						});

				}
			);		

		}
	});
	
})(jQuery);		
