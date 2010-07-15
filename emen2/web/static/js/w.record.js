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
			//console.log("build");
			this.f = $('<form name="login" action="'+EMEN2WEBROOT+'/auth/login/" method="POST">');
			this.username = $('<input name="username" type="text" />');
			this.pw = $('<input name="pw" type="password" />');
			this.submit = $('<input type="submit" value="Login" />');
			this.f.append(this.username, this.pw, this.submit);
			this.elem.append(this.f);
		} else {
			//console.log("no build");
			this.f = this.elem.children("form");
			this.username = this.elem.find("input:text");
			this.pw = this.elem.find("input:password");
			this.submit = this.elem.find("input:button");
			//console.log(this.f.attr("action"));
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
		//console.log("Success!");
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
	groups: [],
	levels: ["Read","Comment","Write","Admin"],
	inherit: [],
	parents: [],
	newrecord: 0,
	recurse: null
};

permissions.prototype = {
	
	init: function() {

		var self=this;

		this.reinit();
		this.ajaxqueue={};
		
		this.inheritcontrols=[];
		
		////////////////////////////////
		// Inherit / parent controls
		this.inheritarea=$('<table class="inherittable" cellspacing="0" cellpadding="0"><tr><th>Parent</th><th>Permissions</th><th>Record</th></tr></table>');

		if (this.inherit.length > 0) {


			var ihc = $('<div class="user_add clearfix">Parents:</div>');
			var ihcul = $('<ul />');
			ihc.append(ihcul);
			for (var i=0;i<this.inherit.length;i++) {
				this.addinherititem(this.inherit[i],1);
				ihcul.append('<li>'+recnames[this.inherit[i]]+' ('+this.inherit[i]+')</li>');
			}
			this.elem.append(ihc);

		}


		////////////////////////////////
		// Add user controls
		
		var user_outer=$('<div class="user_outer clearfix"></div>');
		var useradd=$('<div class="user_add clearfix"></div>');
		var useradd_user=$('<div/>');
		var useradd_group=$('<div/>');


		this.user_search=$('<input class="value" size="20" type="text" value="" />');

		this.user_search.autocomplete( EMEN2WEBROOT+"/db/find/user/", { 
			minChars: 0,
			max: 1000,
			matchSubset: false,
			scrollHeight: 360,
			highlight: false,
			formatResult: function(value, pos, count)  { return value }			
		});


		this.user_levelselect=$('<select><option value="0">Read</option><option value="1">Comment</option><option value="2">Write</option><option value="3">Admin</option></select>');
		this.user_addbutton=$('<input type="button" value="Add User">');

		this.user_addbutton.click(function(){
			self.add(self.user_search.val(),self.user_levelselect.val());
			self.build();
		});
		

		
		this.group_search=$('<input class="value" size="20" type="text" value="" />');

		this.group_search.autocomplete( EMEN2WEBROOT+"/db/find/group/", { 
			minChars: 0,
			max: 100,
			matchSubset: false,
			scrollHeight: 360,
			formatResult: function(value, pos, count)  { return value }			
		});

		
		//this.group_levelselect=$('<select><option value="0">Read</option><option value="1">Comment</option><option value="2">Write</option><option value="3">Admin</option></select>');
		this.group_addbutton=$('<input type="button" value="Add Group">');
		this.group_addbutton.click(function(){
			self.addgroup(self.group_search.val());
			self.build_grouparea();
		});


		useradd_user.append(this.user_search, this.user_levelselect, this.user_addbutton);
		useradd_group.append(this.group_search, this.group_levelselect, this.group_addbutton);	
		useradd.append(useradd_user, useradd_group);


		// Save controls
		if (!this.newrecord) {
			this.savearea = $('<div class="permissions_savearea" />');
			var savearea_apply = $('<input type="button" value="Apply Changes" />').click(function(){self.save_record()});
			var savearea_applyrec = $('<input type="checkbox" id="recurse" />').click(function(){self.recurse=$(this).attr("checked")});

			this.savearea.append(savearea_apply,savearea_applyrec,'<label for="recurse">Recursive</label>');
			//this.savearea.append('<br /><hr />Apply to children: ');
			//this.savearea_children=$('<select><option>ADD (orange) users</option><option>REMOVE (red) users</option><option>REASSIGN (yellow) users</option><option>UNION of this set</option><option>INTERSECTION of this set</option></select>')
			//this.savearea.append(this.savearea_children);
			//this.savearea.append('<input type="button" value="Apply" />');
			useradd.append(this.savearea);
		}

		user_outer.append(useradd);

		this.grouparea = $('<div clearfix user_level></div>');
		this.userarea = $("<div></div>");

		user_outer.append($('<h6>Groups:</h6>'))
		user_outer.append(this.grouparea);
		user_outer.append(this.userarea);

		this.elem.append(user_outer);

		// Build user lists
		// this.build();
		this.getdisplaynames();

	},
	
	getdisplaynames: function() {

		// build widgets on callback...
		var self=this;
		
		// def getuserdisplayname(self, username, lnf=1, perms=0, filt=True, ctx=None, txn=None):
		// get group names...
		// $.jsonRPC("getuserdisplayname",[recid, 1, 1, 1], function(names){
		// 	$.each(names, function(k,v) {
		// 		displaynames[k] = v;
		// 	});			
		self.build_userarea();
		// });

		// get group names...
		// $.jsonRPC("getgroupdisplayname", [recid], function(names) {
		// 	$.each(names, function(k,v) {
		// 		groupnames[k] = v;
		// 	});			
		self.build_grouparea();
		// });
		
	},
	
	
	build_grouparea: function() {
		var self=this;

		this.grouparea.empty();

		// group area
		var level_ul = $('<ul></ul>');
		$.each(this.groups, function(k,v) {
			var userdiv = $('<li class="user clearfix"></li>');
			var username=$('<span class="name">'+(groupnames[v] || v)+'</span>');
			var useraction=$('<span class="action">X</span>');
			var tag=self.groupstatetag(v);			
			userdiv.addClass(tag);
			if (tag=="removed") {	
				useraction.html("U");
				useraction.click(function(){
					self.addgroup(useraction.username);
					self.build_grouparea();
				});
			} else {
				useraction.click(function(){
				self.removegroup(useraction.username);
				self.build_grouparea();});	
			}

			useraction.username=v;
			userdiv.append(useraction,username);
			level_ul.append(userdiv);
					
		});
		
		this.grouparea.append(level_ul);
		
	},


	build_userarea: function() {

		var self=this;

		this.userarea.empty();
		$.each(this.getlist(1), function(k,v) {
			v=self.sortbydisplayname(v);
			
			var level=$('<div class="clearfix user_level"><h6>'+self.levels[k]+'</h6></div>');
			var level_ul = $("<ul></ul>");

			if (v.length == 0) {
				//level_ul.append("<li>Emtpy</li>");
			} else {

				var level_removeall=$('<span class="small">[<span class="jslink">X</span>]</span>').click(function () {
					var q = v.slice();
					for (var i=0;i<q.length;i++) {
						self.remove(q[i]);
					}
					self.build_userarea();
				});
				level.append(level_removeall);
				
				$.each(v, function(k2,v2) {
					var userdiv=$('<li class="user clearfix"></li>');
					var tag=self.userstatetag(v2);
					userdiv.addClass(tag);
		
					var username=$('<span class="name">'+(displaynames[v2] || v2)+'</span>');
					var useraction=$('<span class="action">X</span>');
					if (tag=="removed") {	
						useraction.html("U");
						useraction.click(function(){
							self.add(useraction.username,useraction.level);
							self.build_userarea();
						});
					} else {
						useraction.click(function(){
							self.remove(useraction.username);
							self.build_userarea();
						});	
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

	build: function() {
		this.build_grouparea();
		this.build_userarea();
	},

	getlistchanged: function() {
		var l=[[],[],[],[]];
		var self=this;
		$.each(this.userstate, function(k,v) {
			if (v > -1 && self.inituserstate[k] != v) {
				l[v].push(k);
			}
		});
		return l
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
	
	groupstatetag: function(group) {
		if (this.groupstate[group] == -1){
			return "removed"
		}
		return "newuser"
	},

	// sort usernames by their display names	
	sortbydisplayname: function(list) {
		var reversenames={};
		var sortnames=[];
		var retnames=[];
		for (var i=0;i<list.length;i++) {
		    reversenames[getdisplayname(list[i])] = list[i];
		    sortnames.push(getdisplayname(list[i]) || list[i]);
		}
		sortnames.sort();
		for (var i=0;i<sortnames.length;i++) {
			retnames.push(reversenames[sortnames[i]] || sortnames[i]);
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
				self.addgroups(getvalue(precid, 'groups'));
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
	
	addgroup: function(group) {
		if (this.groups.indexOf(group) == -1) {
			this.groups.push(group);
		}
		this.groupstate[group] = 1;
	},
	
	addgroups: function(groups) {
		for (var i=0;i<groups.length;i++) {
			this.addgroup(groups[i]);
		}
	},
	
	// add a user to permissions	
	add: function(username,level) {
		level=parseInt(level);
		//if (getdisplayname(username) == null) {return 0}
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
	
	removegroup: function(group) {
		if (this.initgroups.indexOf(group) == -1) {
			this.groups.splice(this.groups.indexOf(group), 1);			
			return
		}
		this.groupstate[group] = -1;

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
	
	getgroups: function() {
		ret=[];
		for (var i=0;i<this.groups.length;i++) {
			if (this.groupstate[this.groups[i]] != -1) {ret.push(this.groups[i])}
		}
		return ret
	},
		
	getparents: function() {
		return this.parents
	}, 
	
	save_record: function() {
		
		this.ajaxqueue["record_permissions_save"]=1;
		var self=this;
		
		var rlevels=0;
		if (this.recurse) {
			rlevels=50;
		}
		

		var sec_commit = {};
		sec_commit["recid"] = recid;
		sec_commit["umask"] = this.getlistchanged();
		sec_commit["delusers"] = this.getdelusers();
		sec_commit["addgroups"] = this.getaddgroups();
		sec_commit["delgroups"] = this.getdelgroups();
		sec_commit["reassign"] = 1;
		sec_commit["recurse"] = rlevels;

		// console.log(sec_commit);
		// return
		
		$.jsonRPC("secrecordadduser_compat", sec_commit, function() {
			$.jsonRPC("getrecord",[recid], function(record) {
				notify("Saved Permissions");
				recs[recid] = record;
				self.reinit();
				self.build();
			});
		});		


	},
	
	getaddgroups: function() {
		var self=this;
		var r=[];
		$.each(this.groups, function(k,v) {
			if (self.initgroups.indexOf(v) == -1) {
				r.push(v);
			}
		});
		return r
	},
	
	getdelgroups: function() {
		var self=this;
		var r=[];
		$.each(this.initgroups, function(k,v) {
			if (self.groupstate[v]==-1) {
				r.push(v);
			}
		});
		return r
	},
	
	getdelusers: function() {
		var self=this;
		var r=[];
		$.each(this.userstate, function(k,v) {
			if ( v == -1 && self.inituserstate[k] > -1) {r.push(k)}
		});
		return r		
	},
	
	reinit: function() {
		// ian: todo: reget record
		
		var r = recs[recid];
		
		// reinit inituserstate;
		this.list = r["permissions"]
		this.userstate={};
		this.inituserstate={};
		for (var i=0;i<4;i++) {
			for (var j=0;j<this.list[i].length;j++) {
				this.userstate[this.list[i][j]]=i;
				this.inituserstate[this.list[i][j]]=i;
			}
		}

		this.initgroups = [];
		this.groupstate = {};	
		this.groups = r["groups"];
		for (var i=0;i<this.groups.length;i++) {
			this.initgroups.push(this.groups[i]);
		}

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
		//var reccomments_text = getvalue(recid,"comments_text");

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

		var cr = this.comments.reverse();

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
		
		var comments_text = getvalue(recid,"comments_text");
		if (comments_text) {
			self.elem_body.append('<strong>Comment:</strong><p>'+comments_text+'</p>');
		}


	},
	
	revert: function() {
		this.edit.val("");
	},
	
	////////////////////////////
	save: function() {
		var self=this;
		//console.log([recid,this.edit.val()])
		$.jsonRPC("addcomment",[recid,this.edit.val()],
	 		function(json){
				//console.log(json);
				setvalue(recid,"comments",json);
				//rec["comments"]=json;
				//console.log("addcomments return");
				//console.log(json);
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
		this.rechistory = getvalue(recid,"history");
		
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
		for (var i=0;i<this.rechistory.length;i++) {
			this.log.push(this.rechistory[i]);
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
			
			//if (typeof(this[2])=="object") {
			if (this.length == 4) {
				self.elem_body.append('<strong>'+dname+' @ '+time+'</strong><p>LOG: ' + this[2] + ' updated: was '+this[3]+'</p>');
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


/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////


multiwidget = (function($) { // Localise the $ function

function multiwidget(elem, opts) {
	// init
	this.elem = $(elem);
  	if (typeof(opts) != "object") opts = {};
  	$.extend(this, multiwidget.DEFAULT_OPTS, opts);
	this.init();

};

multiwidget.DEFAULT_OPTS = {
	newrecord: 0,
	popup: 0,
	controls: 1,
	controlsroot: null,
	ext_save: null, // external save/cancel buttons
	ext_cancel: null,
	restrictparams: null, // show only these params...
	display: 0,
	root: null
};


multiwidget.prototype = {
		
	init: function() {
		// console.log("multiwidget init");

		var self=this;
		
		// built status
		this.built = 0;

		// attempted to get paramdefs
		this.trygetparamdefs = 0;
		this.trygetrecords = 0;
		
		// stored paramdefs and element references
		this.paramdefs = {};
		this.elems = [];

		// cache a list of all editable elements
		this.ext_elems = $(".editable",this.root);
			
		this.bind_edit();

		// build widgets if requested
		// if (this.display) {
		// 	this.build(1);
		// }
		
		// and build control widgets if required
		if (!this.controlsroot) {
			this.controlsroot = this.elem;
		}

		if (this.newrecord) {
			this.build(1);
		}

	},
	
	bind_editable: function() {
		// attach hidden widgets to all editable items

		var self=this;
		this.ext_elems.each(function(){
			self.elems.push(new widget($(this), self.widgetopts_hide));
		});
	},
	
	bind_edit: function() {
		// if controls exist, bind single click to show edit widgets

		var self=this;
		if (this.controls) {
			this.elem.bind("click",function(e){e.stopPropagation();self.event_click(e)});
		}
	},
	
	bind_save: function() {
		// if ext_save and ext_cancel are specified, bind save/cancel events
		
		if (this.ext_save) {
			var self=this;
			this.ext_save.one("click", function(e){
				e.stopPropagation();self.event_save(e)
				});
		}
		if (this.ext_cancel) {
			var self=this;
			this.ext_cancel.bind("click", function(e){
				e.stopPropagation();self.event_cancel(e)
				});
		}	
			
	},

	event_click: function(e) {
		// show widgets and controls
		this.show();
	},

	event_save: function(e) {
		// begin commit
		this.ext_save.val("Committing...");
		this.save();
	},
	
	event_cancel: function(e) {
		// hide widgets and controls
		this.hide();
	},
		
	build: function() {
		// build all the widgets and controls
		
		// console.log("begin build");
		
		var self = this;

		// get all the records and paramdefs if necessary
		var set_getpds = {};
		var getpds = [];

		var set_getrecs = {}
		var getrecs = [];

		var cb_wait = 0;

		this.ext_elems.each(function(){		
			set_getpds[$(this).attr("data-param")] = null;
			set_getrecs[$(this).attr("data-recid")] = null;
		});

		// if we need to fetch some paramdefs...
		$.each(set_getpds, function(index, value) { 
			if (!paramdefs[index]) {
				getpds.push(index);
			} 
		});
		if (getpds.length && this.trygetparamdefs == 0) {
			this.trygetparamdefs = 1;
			json_getparamdef(getpds,function(){self.build()});
		}
		
		// get all the records if necessary
		$.each(set_getrecs, function(index, value) {
			index = parseInt(index);
			if (!recs[index] && index >= 0) {
				getrecs.push(index);
			} 
		});
		if (getrecs.length && this.trygetrecords == 0) {
			this.trygetrecords = 1;
			json_getrecords(getrecs,function(){self.build()});
		}

		if (getpds.length || getrecs.length) {
			// console.log("Ok, waiting on a callback...");
			return
		}
		
		//console.log("got everything we need -- building");
				
		//
		// we have all the records and paramdefs we need -- proceed
		//
		
		// check if built; set built to true		
		if (this.built) {
			//console.log("already built!");
			return
		}		
		this.built = 1;
				
		// build the controls if requested, as child of controlsroot
		if (this.controls) {
			this.c_edit = $(".jslink",this.controlsroot);
			this.ext_save = $('<input type="submit" value="Save" />');
			this.ext_cancel = $('<input type="button" value="Cancel" />');
			this.c_box = $('<span />');
			this.c_box.append(this.ext_save,this.ext_cancel);
			this.controlsroot.append(this.c_box);
		}
	
		// bind control keys
		this.bind_save();		
	
	
		//console.log("creating widgets...");
		// attach hidden widgets to all editable items
		this.ext_elems.each(function(){
			self.elems.push(new widget($(this)));
		});
		//console.log("done creating widgets");
		
		
		// sometimes we'll get build(True) as a callback
		this.show()
		
	},
	
	show: function() {
		// show the widgets we have created

		//console.log("showing");

		if (!this.built) {
			this.build()
			return
		}

		var self = this;

		if (this.controls) {
			this.c_edit.hide();
			this.c_box.show();
			// this.bind_();
		}				

		//console.log("showing widgets");

		$.each(this.elems, function(){
			this.show();
		});
		
		//console.log("done");
		
	},
	
	hide: function() {
		// hide the widgets and controls
		
		var self=this;

 		if (this.controls) {
			this.c_box.hide();
 			this.c_edit.show();
 		}

		$.each(this.elems,function(){
			this.hide();
			// this.reset_opts(self.widgetopts_hide);
		});
		
	},
	
	remove: function() {
		//console.log("multiw remove");
		
		if (this.built) {this.hide()};
		this.ext_elems=null;
		this.init();
	},
	
	reset: function(root) {
		//console.log("multiw reset");
		
		this.root=root;
		this.remove();
	},
	

	
	save: function() {
		//console.log("multiw save");

		var changed={};
		$.each(this.elems, function(){
			if (!changed[this.recid]) {changed[this.recid]={}}
			changed[this.recid][this.param] = this.getval();
			// console.log(this.recid, this.param, this.getval())			
			// } else {
			//	// console.log(this.param+" is unchanged; value is "+this.getval());
			//}
		});
		
		if (this.newrecord) {
			this.save_newrecord_callback(this, changed);
		} else {
			this.save_default_callback(this, changed);			
		}		
	},
	
	compare: function(a,b) {
		if (a instanceof Array && b instanceof Array) {
  		// array comparator
			if (a.length != b.length) return false
			for (var i=0;i<a.length;i++) {
				if (a[i] != b[i]) return false
			}
			return true
		} else {
			return a==b
		}
	},
	
	save_start: function() {
		this.ext_save.val("Committing...");
	},
	
	save_end: function(text) {
		if (text==null){text="Retry"}
		this.ext_save.val(text);
	},
	
	save_default_callback: function(self, changed) {
		self.save_start();
		$.jsonRPC("putrecordsvalues",[changed],function(data){self.commit_default_callback(self,data)},function(data){self.commit_default_errback(self,data)});
	},
	
	save_newrecord_callback: function(self, changed) {
		if (!changed[null]) {
			changed[null]={}
		}
	
		changed[null]["permissions"] = permissionscontrol.getpermissions();
		changed[null]["parents"] = permissionscontrol.getparents();
		changed[null]["groups"] = permissionscontrol.getgroups();
	
		// console.log(changed[null]);
	
		// commit
		var rec_update = getrecord(null);
	
		$.each(changed[null], function(i,value) {
			if ((value!=null) || (getvalue(recid,i)!=null)) {
				rec_update[i]=value;
			}
		});
		
	
		$.jsonRPC("putrecord", [rec_update], //rec_update["parents"]
			function(rec){
				notify_post(EMEN2WEBROOT+'/db/record/'+rec["recid"]+'/',["Record Saved"]);
			},
			function(xhr){
				notify("Error: "+this.param+", "+xhr.responseText);
				self.ext_save.val("Retry");		
				self.bind_save();
			}
		);	
	},	
	
	commit_default_errback: function(self,r) {
		notify(r.responseText);
		self.save_end();
		self.bind_save();		
	},
	
	commit_default_callback: function(self,r) {
		self.save_end("Save Successful");
		notify_post(window.location.pathname, ["Changes Saved"]);
	}
}

$.fn.multiwidget = function(opts) {
  return this.each(function() {
		new multiwidget(this, opts);
	});
};

return multiwidget;

})(jQuery); // End localisation of the $ function



/////////////////////////////////////////////
/////////////////////////////////////////////


widget = (function($) { // Localise the $ function

function widget(elem, opts) {
	this.elem = $(elem);
	this.opts=opts;
	if (typeof(opts) != "object") opts = {};
	this.controls = opts["controls"];
	this.init();
};

widget.prototype = {

	init: function() {
		this.built = 0;
		this.param = this.elem.attr("data-param");
		this.recid = parseInt(this.elem.attr("data-recid"));
		if (isNaN(this.recid)) this.recid = null;
		this.rec_value = getvalue(this.recid, this.param);	
		this.bind_edit();
	},
	
	event_click: function(e) {
		this.show();
	},
	
	bind_edit: function() {
		var self = this;
		this.elem.click(function(e) {self.event_click(e)});
	},
		
	build: function() {

		var self = this;

		if (!paramdefs[this.param]) {
			json_getparamdef([this.param], function(){self.build()});
			return
		}


		if (this.built){
			return
		}
		
		this.built = 1;
		
		
		if (this.rec_value == null) {
			this.rec_value = "";
		}


		// container

		this.w = $('<span class="widget"></span>');
		
		if (this.controls) {
			this.w.addClass("widget_inplace");
		}
		var pd = paramdefs[this.param];

		// Delegate to different edit widgets
		
		if (pd["vartype"]=="html") {
			
			this.editw=$('<textarea class="value" cols="80" rows="20">'+this.rec_value+'</textarea>');
			this.w.append(this.editw);				
			

		} else if (pd["vartype"]=="text") {

			this.editw=$('<textarea class="value" cols="80" rows="20">'+this.rec_value+'</textarea>');
			this.w.append(this.editw);				
			

		} else if (pd["vartype"]=="choice") {
			
			this.editw=$('<select></select>');
			var pdc = paramdefs[this.param]["choices"];
			pdc.unshift("");
			
			for (var i=0;i<pdc.length;i++) {
				var selected="";
				if (this.rec_value == pdc[i]) { selected = 'selected="selected"'; }
				this.editw.append('<option val="'+pdc[i]+'" '+selected+'>'+pdc[i]+'</option>');
			}

			this.w.append(this.editw);				
							
		} else if (pd["vartype"]=="datetime") {
		
			// this.popup=new DateInput(this.editw);
			this.editw = $('<input class="value" size="18" type="text" value="'+this.rec_value+'" />');
			this.w.append(this.editw);				

		} else if (pd["vartype"]=="boolean") {
		
			this.editw = $("<select><option>True</option><option>False</option></select>");
			this.w.append(this.editw);				
		
		} else if (["intlist","floatlist","stringlist","userlist","urilist"].indexOf(pd["vartype"]) > -1) {
		
			this.editw = new listwidget(this.w,{values:this.rec_value, paramdef:pd});
		
		}  else if (pd["vartype"]=="user") {

				this.editw = $('<input class="value" size="30" type="text" value="'+this.rec_value+'" />');

				this.editw.autocomplete(
					EMEN2WEBROOT+"/db/find/user/",
					{ 
						minChars: 0,
						max: 1000,
						matchSubset: false,
						scrollHeight: 360,
						highlight: false,
						formatResult: function(value, pos, count)  { return value }			
					}
				);
				
				this.w.append(this.editw);			
		
		} else if (pd["vartype"]=="binary" || pd["vartype"]=="binaryimage") {
			
				this.editw = $('<div>File Browser</div>');
				new filewidget(this.editw, {recid:recid, param:this.param});
				this.w.append(this.editw);
				
		} else {

			this.editw = $('<input class="value" size="30" type="text" value="'+this.rec_value+'" />');
			
			if (pd["vartype"]=="string" || pd["choices"]) {
								
				this.editw.autocomplete(
					EMEN2WEBROOT+"/db/find/value/"+this.param+"/",
					{ 
						minChars: 0,
						max: 100,
						matchSubset: false,
						scrollHeight: 360,
						formatResult: function(value, pos, count)  { return value }			
					}
				);
				
			}

			this.w.append(this.editw);
			
			var property = pd["property"];
			var units = pd["defaultunits"];

			if (property != null) {

				this.editw_units=$('<select></select>');

				for (var i=0;i < valid_properties[property][1].length;i++) {
					var sel = "";
					if (units == valid_properties[property][1][i]) sel = "selected";
					this.editw_units.append('<option '+sel+'>'+valid_properties[property][1][i]+'</option>');
				}
				
				this.w.append(this.editw_units);

			}


		}

		if (this.controls) {
			this.c_controls=$('<div class="controls"></div>').append(
				$('<input type="submit" value="Save" />').one("click", function(e) {e.stopPropagation();self.save()}),
				$('<input type="button" value="Cancel" />').bind("click", function(e) {e.stopPropagation();self.hide()})
			);
			this.w.append(this.c_controls);
		}


		$(this.elem).after(this.w);

		this.show();
		
	},
	
	show: function() {
		// show the widget

		var self=this;
		
		if (!this.built) {
			this.build();
			return
		}
		
		this.elem.hide();
		this.w.show();

	},
	
	hide: function() {
		//console.log("w hide");

		this.w.hide();
		this.elem.show();
	},
	
	remove: function() {
		//console.log("w remove");		
		
		if (this.built==0){return}
		this.w.remove();
		this.built=0;
	},


	////////////////////////
	
	getval: function() {
		//console.log("w getval");		
		
		var ret = this.editw.val();		

		if (ret == "" || ret == []) {
			return null;
		}
		
		if (this.editw_units) {
			ret = ret + this.editw_units.val();
		}
		
		return ret
	},

	
	////////////////////////	
	save: function() {
		//console.log("w save");

		var save=$(":submit",this.w);
		save.val("Committing...");

		var recid=this.recid;
		var param=this.param;
	
		$.jsonRPC("putrecordvalue",[recid,this.param,this.getval()],
	 		function(json){
				setvalue(recid,param,json);
				// ian: just reload the page instead of trying to update everything.. for now..
				notify_post(window.location.pathname, ["Changes Saved"]);
	 		},
			function(json){
				notify("Error: "+this.param+","+json.responseText);
			}
		);		
	}	
	
}

$.fn.widget = function(opts) {
  return this.each(function() { new widget(this, opts); });
};

return widget;

})(jQuery); // End localisation of the $ function


/////////////////////////////////////////////
/////////////////////////////////////////////


listwidget = (function($) { // Localise the $ function

function listwidget(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, listwidget.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
};

listwidget.DEFAULT_OPTS = {
	values:[],
	paramdef:{}
};

listwidget.prototype = {
	
	init: function() {
		this.items=$('<ul></ul>');
		this.elem.append(this.items);
		this.build();
	},
	
	build: function() {

		if (this.values.length == 0) {
			this.values = [""];
		}
	
		this.items.empty();
		
		var self=this;

		$.each(this.values, function(k,v) {
			var item=$('<li class="widget_list"></li>');
			var edit=$('<input type="text" value="'+v+'" />');
						
			if (self.paramdef["vartype"]=="userlist") {

				edit.autocomplete( EMEN2WEBROOT+"/db/find/user/", { 
					minChars: 0,
					max: 1000,
					matchSubset: false,
					scrollHeight: 360,
					highlight: false,
					formatResult: function(value, pos, count)  { return value }			
				});


			} else if (self.paramdef["vartype"]=="stringlist") {

				edit.autocomplete( EMEN2WEBROOT+"/db/find/value/"+self.paramdef["name"]+"/", { 
					minChars: 0,
					max: 100,
					matchSubset: false,
					scrollHeight: 360,
					formatResult: function(value, pos, count)  { return value }			
				});

			}
			
			var add=$('<span><img src="'+EMEN2WEBROOT+'/images/add_small.png" class="listwidget_add" /></span>').click(function() {
				self.addoption(k+1);
				self.build();
			});
			
			var remove=$('<span><img src="'+EMEN2WEBROOT+'/images/remove_small.png" class="listwidget_remove" /></span>').click(function() {
				self.removeoption(k);
				self.build();
			});

			item.append(edit,add,remove);
			self.items.append(item);

		});

	},

	addoption: function(pos) {
		// add another option to list
		// save current state so rebuilding does not erase changes
		this.values = this.val_withblank();
		this.values.splice(pos,0,"");
	},
	
	removeoption: function(pos) {
		// remove an option from the list
		this.values = this.val_withblank();
		this.values.splice(pos,1);
	},
	
	val: function() {
		// return the values
		var ret=[];
		$("input:text",this.elem).each(function(){
			if (this.value != "") ret.push(this.value);
		});
		return ret
	},
	
	val_withblank: function() {
		var ret=[];
		$("input:text",this.elem).each(function(){
			ret.push(this.value);
		});
		return ret		
	}
	
}

$.fn.listwidget = function(opts) {
  return this.each(function() {
		return new listwidget(this, opts);
	});
};

return listwidget;

})(jQuery); // End localisation of the $ function



//////////////////////
//////////////////////
//////////////////////

filewidget = (function($) { // Localise the $ function


function filewidget(elem, opts) {
  this.elem = $(elem);
  if (typeof(opts) != "object") opts = {};
  $.extend(this, filewidget.DEFAULT_OPTS, opts);
  this.init();
};

filewidget.prototype = {
	
	init: function() {
		this.built = 0;
		this.bdos = {};
		this.recid = parseInt(this.elem.attr("data-recid"));
		this.param = this.elem.attr("data-param");
		this.vartype = this.elem.attr("data-vartype");
		this.bind_edit();
	},
	
	
	event_click: function(e) {
		this.build();
	},

	
	event_build_tablearea: function(e) {
		var self = this;
		this.tablearea.empty();
		this.tablearea.append('<div>Loading...</div>');
		$.jsonRPC("getrecord", [this.recid],
			function(rec) {				
				setrecord(rec.recid, rec);
				$.jsonRPC("getbinary", [rec[self.param]], 
					function(bdos) {
						if (bdos == null) {bdos=[]}
						if (bdos.length == null) {bdos=[bdos]}
						self.bdos = bdos || {};
						self.build_tablearea();
					}
				);
			}
		);
	},
	
	
	event_removebdos: function(e) {
		var self = this;
		var keep = [];
		$("input:checkbox:not(:checked)", this.tablearea).each(function(){return keep.push(this.value)});
		if (this.vartype == "binaryimage") {
			keep = keep[0];
		}
		$.jsonRPC("putrecordvalue",
			[this.recid, this.param, keep],
			function(data) {
				self.event_build_tablearea();
			}
		);
			
	},
	
	
	bind_edit: function() {
		var self = this;
		this.elem.click(function(e) {self.event_click(e)});
	},

		
	build: function() {
		var self=this;
		this.built = 1;

		this.container = $('<div class="modalbrowser_container clearfix" />');
		this.elem = $('<div class="modalbrowser_container_inner clearfix" />');
		
		this.elem.css("left", ($(window).width()-896)/2);
		var toph=($(window).height()-730)/2;
		if (toph<=10) toph=10;
		this.elem.css("top", toph);
		$(document.body).append(this.container.append(this.elem));
		
		this.elem.empty();		

		var title=$('<div class="modalbrowser_title clearfix"><span class="floatleft">Manage Attachments for '+this.param+'</span></div>').append(
			$('<span class="floatright"></span>').append(
				$('<input type="button" value="Close" />').click(function(){
					self.close();
				})
			)
		);
		this.elem.append(title);

		this.tablearea = $('<div class="modalbrowser_tablearea clearfix" />');
		this.browserarea = $('<div class="modalbrowser_browserarea clearfix" />');

		var mbody = $('<div class="modalbrowser_body" />');
		mbody.append(this.tablearea, this.browserarea);
		this.elem.append(mbody);

		this.build_browser();
		this.event_build_tablearea();

	},
	
	
	build_tablearea: function() {
		// build a column-style browser
		this.tablearea.empty();
		var self=this;
		
		var bdotable = $('<table id="modalbrowser_bdotable" class="files" />');
		bdotable.append('<tr><th style="width:20px"/><th>Filename</th><th>Size</th><th>Creator</th><th>Created</th><th>md5</th></tr>');
		//console.log(this.bdos);
		$.each(this.bdos, function(k,v) {
			var row = $('<tr/>');
			var remove = $('<td><input type="checkbox" name="remove" value="'+v.name+'" /></td>');
			row.append(remove);
			var link = $('<td><a target="_blank" href="'+EMEN2WEBROOT+'/download/'+v.name+'/'+v.filename+'">'+v.filename+'</a></td>');
			row.append(link);
			row.append('<td>'+v.filesize+'</td>');
			row.append('<td>'+v.creator+'</td>');
			row.append('<td>'+v.creationtime+'</td>');
			row.append('<td>'+v.md5+'</td>');
			bdotable.append(row);
		});	
		
		this.tablearea.append(bdotable);
		
		var reset = $('<input type="button" value="Remove Selected Items" />');
		reset.click(function(e){self.event_removebdos(e)});
		this.tablearea.append(reset);		

	},
	
	build_browser: function() {
		var self = this;
		var infoc = $('<div class="modalbrowser_info" style="margin-top:20px;"><h3>Upload</h3></div>');
		//var fform = $('<form action="'+EMEN2WEBROOT+'/upload/'+this.recid+'" enctype="multipart/form-data" method="POST">');
		var fform = $('<div />');

		this.button_browser = $('<input type="file" />');
		this.button_submit = $('<input type="submit" value="Upload" />');

		if (this.vartype == "binary") {
			this.button_browser.attr("multiple","multiple");
			fform.append("(multiple files allowed)");
		}
		
		this.button_browser.html5_upload({
			url: function() {
					return EMEN2WEBROOT+'/upload/'+recid+'?param='+self.param;
			},
			onStart: function(event, total) {
				if (total > 1) {
					return confirm("You are trying to upload " + total + " files. Are you sure?");
				} else {
					return true;
				}
			},
			setName: function(text) {
					$("#progress_report_name").text(text);
			},
			setStatus: function(text) {
					$("#progress_report_status").text(text);
			},
			setProgress: function(val) {
					$("#progress_report_bar").css('width', Math.ceil(val*100)+"%");
			},
			onFinishOne: function(event, response, name, number, total) {
				// self.event_build_tablearea();		
			},
			onFinish: function(event, total) { 
				self.event_build_tablearea();	
			},
			autostart: false
		});
		
		this.button_submit.bind('click', function(){self.button_browser.trigger("html5_upload.start");});
		
		var progress_status = $('<div id="progress_report_status">Progress:</div>');
		var progress_report = $('<div id="progress_report" />');
		var progress_report_name = $('<div id="progress_report"/>');
		var progress_report_status = $('<div id="progress_report"/>');
		var progress_report_bar_container = $('<div id="progress_report_bar_container">');
		var progress_report_bar = $('<div id="progress_report_bar" style="background-color: blue; width: 0; height: 100%;" />');

		fform.append(this.button_browser, this.button_submit)
		infoc.append(fform);
				
		progress_report_bar_container.append(progress_report_bar);
		progress_report.append(progress_status, progress_report_name, progress_report_status, progress_report_bar_container);
		
		this.browserarea.append(infoc, progress_report);

	},
	
	close: function() {
		this.container.remove();
	}
		
}

$.fn.filewidget = function(opts) {
  return this.each(function() {
		return new filewidget(this, opts);
	});
};

return filewidget;

})(jQuery); // End localisation of the $ function

