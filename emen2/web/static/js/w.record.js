/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////

loginwidget = (function($) { // Localise the $ function

function loginwidget(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, loginwidget.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
};

loginwidget.DEFAULT_OPTS = {
	buildform:0,
	callback:null
};

loginwidget.prototype = {
	
	init: function() {
		this.build();
	},
	
  build: function() {
		var self=this;

		if (this.buildform) {
			console.log("build");
			this.f = $('<form name="login" action="/db/login" method="POST">');
			this.username = $('<input name="username" type="text" />');
			this.pw = $('<input name="pw" type="password" />');
			this.submit = $('<input type="submit" value="Login" />');
			this.f.append(this.username, this.pw, this.submit);
			this.elem.append(this.f);
		} else {
			console.log("no build");
			this.f = this.elem.children("form");
			this.username = this.elem.find("input:text");
			this.pw = this.elem.find("input:password");
			this.submit = this.elem.find("input:button");
			console.log(this.f.attr("action"));
		}
		
		this.msg = $("<div />");
		this.elem.prepend(this.msg);
		
		this.submit.click(function(){self.login();return false});
		
	},
	
	login: function() {
		var self=this;
		var username=this.username.val();
		var pw=this.pw.val();
		if (username==""|| pw==""){self.fail("Username or password empty"); return false}
		
		$.jsonRPC("login",[username,pw],
			function(){self.success()},
			function(e){self.fail(e.responseText)}
		);

	},
		
	success: function() {
		console.log("Success!");
		//return false
		this.f.submit();
	},
	
	fail: function(msg) {
		this.msg.html(msg);
	}
		
	
}

$.fn.loginwidget = function(opts) {
    return this.each(function() {
		new loginwidget(this, opts);
	});
};

return loginwidget;

})(jQuery); // End localisation of the $ function


// record metadata edit/view controls

/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////


permissions = (function($) { // Localise the $ function

function permissions(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, permissions.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
};

permissions.DEFAULT_OPTS = {
	list: [ [],[],[],[] ],
	levels: ["Read","Comment","Write","Admin"],
	inherit: [],
	parents: [],
	newrecord: 0
};

permissions.prototype = {
	
	init: function() {

		var self=this;

		this.userstate={};
		this.inituserstate={};
		for (var i=0;i<4;i++) {
			for (var j=0;j<this.list[i].length;j++) {
				this.userstate[this.list[i][j]]=i;
				this.inituserstate[this.list[i][j]]=i;
			}
		}
		
		this.inheritcontrols=[];


		////////////////////////////////
		// Inherit / parent controls
		this.inheritarea=$('<table class="inherittable" cellspacing="0" cellpadding="0"><tr><th>Parent</th><th>Permissions</th><th>Record</th></tr></table>');

		if (this.inherit.length > 0) {
			for (var i=0;i<this.inherit.length;i++) {
				this.addinherititem(this.inherit[i],1);
			}

			this.inheritarea_addcontrols = $('<tr></tr>');
			this.inheritarea_addfield = $('<input type="text" value="" />');
		
			// add new inherit/parent item
			this.inheritarea_addbutton = $('<input type="button" value="Add Record" />').click(function(){
				var getrecid=parseInt(self.inheritarea_addfield.val());
				$.getJSON("/db/getrecordwithdisplay/"+getrecid+"/",null,function(result){
					setrecord(getrecid,result["recs"][getrecid]);
					$.each(result["displaynames"], function(k,v) {
						setdisplayname(k,v);
					});
					$.each(result["recnames"], function(k,v) {
						setrecname(k,v);
					});
					self.addinherititem(getrecid,1);
					self.build();
				});
			});
		
			this.inheritarea_addcontrols.append(
				$("<td></td><td></td>"),
				$("<td></td>").append(this.inheritarea_addfield,this.inheritarea_addbutton)
				);
			this.inheritarea.append(this.inheritarea_addcontrols);
		
			this.elem.append(this.inheritarea);

		}


		////////////////////////////////
		// Add user controls
		
		var user_outer=$('<div class="user_outer clearfix"></div>');
		var useradd=$('<div class="user_add clearfix">Assign Permissions:</div>');
		var useradd_user=$('<div/>');
		var useradd_group=$('<div/>');


		this.user_search=$('<input class="value" size="20" type="text" value="" />');
		this.user_search.autocomplete({ 
					ajax: "/db/finduser/",
					match:      function(typed) { return this[1].match(new RegExp(typed, "i")); },				
					insertText: function(value)  { 
						setdisplayname(value[0],value[1]);
						return value[0] 
						},
					template:   function(value)  { return "<li>"+value[1]+" ("+value[0]+")</li>"}
				}).bind("activate.autocomplete", function(e,d) {  });


		this.user_levelselect=$('<select><option value="0">Read</option><option value="1">Comment</option><option value="2">Write</option><option value="3">Admin</option></select>');
		this.user_addbutton=$('<input type="button" value="Add User">');

		this.user_addbutton.click(function(){
			self.add(self.user_search.val(),self.user_levelselect.val());
			self.build();
		});
		

		this.group_search=$('<select><option></option></select>');
		$.each(groupnames,function(k,v){
			self.group_search.append('<option value="'+k+'">'+v+'</option>');
		});
		this.group_levelselect=$('<select><option value="0">Read</option><option value="1">Comment</option><option value="2">Write</option><option value="3">Admin</option></select>');
		this.group_addbutton=$('<input type="button" value="Add Group">');
		this.group_addbutton.click(function(){
			self.add(parseInt(self.group_search.val()),self.group_levelselect.val());
			self.build();
		});


		useradd_user.append(this.user_search, this.user_levelselect, this.user_addbutton);
		useradd_group.append(this.group_search, this.group_levelselect, this.group_addbutton);	
		useradd.append(useradd_user, useradd_group);

		// Save controls
		if (!this.newrecord) {
			this.savearea = $('<div class="permissions_savearea" />');
			var savearea_apply = $('<input type="button" value="Apply Permissions" />').click(function(){self.save_record()});
			this.savearea.append(savearea_apply);
			//this.savearea.append('<br /><hr />Apply to children: ');
			//this.savearea_children=$('<select><option>ADD (orange) users</option><option>REMOVE (red) users</option><option>REASSIGN (yellow) users</option><option>UNION of this set</option><option>INTERSECTION of this set</option></select>')
			//this.savearea.append(this.savearea_children);
			//this.savearea.append('<input type="button" value="Apply" />');
			useradd.append(this.savearea);
		}

		user_outer.append(useradd);

		//this.userarea_removed = $("<div></div>");
		this.userarea = $("<div></div>");
		user_outer.append(this.userarea);

		this.elem.append(user_outer);

		// Build user lists
		this.build();
		
	},
	
	/*
	build_removed: function() {
		// build list of removed users
		// this.userarea_removed.empty()

		var self=this;

		if (this.removed.length > 0) {
			var self=this;

			var level_remove=$('<div class="clearfix user_removed"> Removed ('+this.removed.length+' users) </div>');
			var level_remove_undoall=$('<span class="jslink">(undo all)</span>').click(function() {
				while (self.removed.length > 0) {
					self.add(self.removed[0],self.removedlevel[self.removed[0]]);
				}
				self.build();
			});
			level_remove.append(level_remove_undoall);

			this.removed = this.sortbydisplayname(this.removed);
			$.each(this.removed, function(k,v) {
					var userdiv=$('<div class="user removed"></div>');
					var username=$('<span class="name">'+getdisplayname(v)+'</span>');
					var useraction=$('<span class="action">+</span>').click(function(){
						self.add(useraction.username,self.removedlevel[useraction.username]);
						self.build();
					});
					useraction.username=v;
										
					userdiv.append(useraction,username);					
					level_remove.append(userdiv);
					
			});
			this.userarea_removed.append(level_remove);
		}
		
	},
	*/
	
  build: function() {

		//this.build_removed();
		
		// build list of user permissions
		this.userarea.empty();

		var self=this;
		$.each(this.getlist(1), function(k,v) {
			
			v=self.sortbydisplayname(v);
			
			var level=$('<div class="clearfix user_level"><h6>'+self.levels[k]+'</h6></div>');
			
			level_ul = $("<ul></ul>");


			if (v.length == 0) {
				//level_ul.append("<li>Emtpy</li>");
			} else {
				
				var level_removeall=$('<span class="small">[<span class="jslink">X</span>]</span>').click(function () {
					var q=v.slice();
					for (var i=0;i<q.length;i++) {
						self.remove(q[i]);
					}
					self.build();
				});
				level.append(level_removeall);

				$.each(v, function(k2,v2) {

					var userdiv=$('<li class="user clearfix"></li>');
					var tag=self.userstatetag(v2)
					userdiv.addClass(tag);
				
					var username=$('<span class="name">'+getdisplayname(v2)+'</span>');
					var useraction=$('<span class="action">X</span>')
					if (tag=="removed") {	
						useraction.html("U");
						useraction.click(function(){
						self.add(useraction.username,useraction.level);
						self.build();});
					} else {
						useraction.click(function(){
						self.remove(useraction.username);
						self.build();});	
					}

					useraction.username=v2;
					useraction.level=k;
					userdiv.append(useraction,username);
					level_ul.append(userdiv);

				});
			}
			
			level.append(level_ul)
			self.userarea.append(level);


		});

	},

	getlist: function(showrem) {
		var l=[[],[],[],[]];
		var self=this;
		$.each(this.userstate, function(k,v) {
			if (v > -1) {l[v].push(k)}
			else if (showrem && self.inituserstate[k] != null) {l[self.inituserstate[k]].push(k);}
		});
		return l
	},
	
	userstatetag: function(username) {
		var ol=this.inituserstate[username];
		var cl=this.userstate[username];
		if (ol==null && cl==null) {return "unknown"}
		if (ol==null && cl>-1) {return "newuser"}
		if (ol > -1 && cl==-1) {return "removed"}
		if (ol!=cl) {return "reassigned"}
	},

	// sort usernames by their display names	
	sortbydisplayname: function(list) {
		var reversenames={};
		var sortnames=[];
		var retnames=[];
		for (var i=0;i<list.length;i++) {
		    reversenames[getdisplayname(list[i])]=list[i];
		    sortnames.push(getdisplayname(list[i]));
		}
		sortnames.sort();
		for (var i=0;i<sortnames.length;i++) {
			retnames.push(reversenames[sortnames[i]]);
		}
		return retnames
	},
	
	// add a new item to list of parents/inherits; builds UI elements
	addinherititem: function(precid,check) {
		
		if (this.inheritcontrols.indexOf(precid) > -1) {return}
		this.inheritcontrols.push(precid);

		if (this.parents.indexOf(precid) == -1) {this.parents.push(precid);}
		

		var control=$("<tr></tr>");

		var p=getvalue(precid,"permissions");

		if (check) {
			this.addlist(p);
			check="checked";
		} else { 
			check="";
		}

		var self=this;

		// add parent selector
		if (this.newrecord) {
			var input_parent=$('<input type="checkbox" '+check+' />').change(function(){
				this.checked=(this.checked) ? 1:0;
				if (this.checked) {self.addparent(precid)}	else {self.removeparent(precid)}
			});
			control.append($("<td></td>").append(input_parent));
		}
		
		var input_perm=$('<input type="checkbox" '+check+' />').change(function(){
			this.checked=(this.checked) ? 1:0;
			if (this.checked) {
				self.addlist(p);
				self.build()
			}	else {
				self.removelist(p);
				self.build()
				}
		});
		control.append($("<td></td>").append(input_perm));

		var count=0;
		for (var j=0;j<p.length;j++) {count+=p[j].length;}
		control.append('<td>'+getrecname(precid)+' (recid: '+precid+', '+count+' users)</td>');
		this.inheritarea.append(control);
		
		if (this.inherit.indexOf(precid) > -1) {return}
		this.inherit.push(precid);

	},	
	
	// add a user to permissions	
	add: function(username,level) {
		level=parseInt(level);
		if (getdisplayname(username) == null) {return 0}
		if (username==user) {return 0}
		this.userstate[username]=level;
		return 1		
	},
	
	// merge permissions list
	addlist: function(list) {
		if (list==null){return}
		for (var i=0;i<list.length;i++) {
			for (var j=0;j<list[i].length;j++) {
				this.add(list[i][j],i);
			}
		}
	},
	
	// remove a user
	remove: function(username) {
		return this.add(username,-1); 
	},
	
	// unmerge a list of users	
	removelist: function(list) {
		if (list==null){return}
		for (var i=0;i<list.length;i++) {
			for (var j=0;j<list[i].length;j++) {
				this.remove(list[i][j],i);
			}
		}
	},
	
	// add a parent
	addparent: function(precid) {
		if (this.parents.indexOf(precid) == -1) {this.parents.push(precid)}
	},
	
	// remove a parent
	removeparent: function(precid) {
		if (this.parents.indexOf(precid) > -1) {this.parents.splice(this.parents.indexOf(precid),1)}
	},
	
	getpermissions: function() {
		return this.getlist()
	}, 
		
	getparents: function() {
		return this.parents
	}, 
	
	save_record: function() {
		
		ajaxqueue["record_permissions_save"]=1;
		var self=this;
		
		var r=[];
		$.each(this.userstate, function(k,v) {
			if ( v == -1 && self.inituserstate[k] > -1) {r.push(k)}
		});
		
		if (r.length > 0) {

			ajaxqueue["record_permissions_save"]++;
			$.jsonRPC("secrecorddeluser",[r,recid,ctxid], function() {
				ajaxqueue["record_permissions_save"]--;
				if (ajaxqueue["record_permissions_save"]==0) {
					//console.log("ajax queue done");
					self.reinit();
				}
			}
			
			);

		}

		// run with recurse = 0, reassign = 1
		$.jsonRPC("secrecordadduser",[this.getlist(), recid, ctxid,0,1], function(permissions) {
				setvalue(recid,"permissions");
				ajaxqueue["record_permissions_save"]--;
				if (ajaxqueue["record_permissions_save"]==0) {
					self.reinit(permissions);
				}
			}
			);		


	},
	
	reinit: function(list) {
		// ian todo: reget record
		notify("Saved Permissions");
		// reinit inituserstate;
		this.list=this.getlist();
		this.userstate={};
		this.inituserstate={};
		for (var i=0;i<4;i++) {
			for (var j=0;j<this.list[i].length;j++) {
				this.userstate[this.list[i][j]]=i;
				this.inituserstate[this.list[i][j]]=i;
			}
		}
		this.build();
	}
	
}

$.fn.permissions = function(opts) {
  return this.each(function() {
		new permissions(this, opts);
	});
};

return permissions;

})(jQuery); // End localisation of the $ function



/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////



commentswidget = (function($) { // Localise the $ function

function commentswidget(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, commentswidget.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
};

commentswidget.DEFAULT_OPTS = {
	elem_title: 0,
	elem_body: 0
};

commentswidget.prototype = {
	
	init: function() {
		this.comments = [];
		
		if (!this.elem_body) {
			this.elem_body = $("<div></div>");
			this.elem.append(this.elem_body);
		}
		this.build();
	},
	
	partition: function() {
		var reccomments = getvalue(recid,"comments");
		this.comments = [];
		this.log = [];
		for (var i=0;i<reccomments.length;i++) {
			if (reccomments[i][2].indexOf("LOG") != 0) {
				this.comments.push(reccomments[i]);
			}
		}
	},
	
  build: function() {

		this.partition();

		this.elem_body.empty();

		this.widget = $('<div class="commentswidget_controls"></div>');
		
		this.edit = $('<textarea cols="60" rows="2"></textarea>');
		
		var self=this;
		this.controls=$('<div></div>');
		this.commit=$('<input class="editbutton" type="submit" value="Add Comment" />').click(function(e) {e.stopPropagation();self.save()});
		//this.clear=$('<input class="editbutton" type="button" value="Clear" />').click(function(e) {e.stopPropagation();self.revert()});
		this.controls.append(this.commit);

		this.widget.append(this.edit, this.controls);
		this.elem_body.append(this.widget);

		var cr=this.comments.reverse();

		if (cr.length == 0) {
			//this.elem_body.append('<p>No Comments</p>');
		}
		
		if (this.elem_title) {
			this.elem_title.html("Comments ("+cr.length+")");
		}

		$.each(cr, function() {
			var dname=this[0];
			if (getdisplayname(this[0])!=null) {
				var dname = getdisplayname(this[0]);
			}
			var time=this[1];
			
			self.elem_body.append('<strong>'+dname+' @ '+time+'</strong><p>'+this[2]+'</p>');

		});
		

	},
	
	revert: function() {
		this.edit.val("");
	},
	
	////////////////////////////
	save: function() {
		var self=this;

		$.jsonRPC("addcomment",[recid,this.edit.val(),ctxid],
	 		function(json){
				//console.log(json);
				setvalue(recid,"comments",json);
				//rec["comments"]=json;
	 			self.build();
				notify("Comment Added");
	 		},
			function(xhr){
				notify("Error Adding Comment");
			}
		)		
	}	
}

$.fn.commentswidget = function(opts) {
  return this.each(function() {
		new commentswidget(this, opts);
	});
};

return commentswidget;

})(jQuery); // End localisation of the $ function


/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////



logwidget = (function($) { // Localise the $ function

function logwidget(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, logwidget.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
};

logwidget.DEFAULT_OPTS = {
	elem_title: 0,
	elem_body: 0
};

logwidget.prototype = {
	
	init: function() {
		this.reccomments = getvalue(recid,"comments");
		this.log = [];
		
		if (!this.elem_body) {
			this.elem_body = $("<div></div>");
			this.elem.append(this.elem_body);
		}
		
		this.build();
	},
	
	partition: function() {
		this.log = [];
		for (var i=0;i<this.reccomments.length;i++) {
			if (this.reccomments[i][2].indexOf("LOG") > -1) {
				this.log.push(this.reccomments[i]);
			}
		}
	},
		
	build: function() {

		this.partition();
		
		this.elem_body.empty();

		var cr=this.log.reverse();

		if (cr.length == 0) {
			this.elem_body.append('<p>No Recorded Changes</p>');
		}

		if (this.elem_title) {
			this.elem_title.html("History ("+cr.length+")");
		}
		
		var self=this;

		$.each(cr, function() {
			var dname=this[0];
			if (getdisplayname(this[0])!=null) {
				var dname = getdisplayname(this[0]);
			}
			var time=this[1];
			
			if (typeof(this[2])=="object") {
				this.elem_body.append('<strong>'+dname+' @ '+time+'</strong><p>'+this[2][0]+'changed: '+this[2][2]+' -&gt; '+this[2][1]+'</p>');
			}
			else {
				self.elem_body.append('<strong>'+dname+' @ '+time+'</strong><p>'+this[2]+'</p>');
			}
		});		
		
	}
}

$.fn.logwidget = function(opts) {
  return this.each(function() {
		new logwidget(this, opts);
	});
};

return logwidget;

})(jQuery); // End localisation of the $ function