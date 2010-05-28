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


////////////////////////////////////////////////
////////////////////////////////////////////////
////////////////////////////////////////////////

RecordDefEditor = (function($) { // Localise the $ function

function RecordDefEditor(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, RecordDefEditor.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
};

RecordDefEditor.DEFAULT_OPTS = {
	root:null,
	add:0,
	parents:null,
	commit:function(){this.default_commit_put()}
};

RecordDefEditor.prototype = {
	
	init: function() {
		this.build();
		this.rd={};
		this.counter_new=0;
		if (this.add) {
			this.commit = this.default_commit_add;
		}		
	},
	
		
	build: function() {
		this.bindall();
		this.refreshall();
		this.getvalues();
	},
	
	connect_buttons: function() {
		var self=this;
		$("#ext_save",this.root).bind("click",function(e){
			self.event_save(e)
			});
	},
	
	bindall: function() {
		var self=this;
	
		this.connect_buttons();
		
		$("#button_recdefviews_new",this.root).bind("click",function(e){self.event_addview(e)});
		
		
		$('.page[data-tabgroup="recdefviews"]',this.root).each(function() {
			var t=$(this).attr("data-tabname");
			self.bindview(t,$(this));
		});
		
	},
	
	bindview: function(t,r) {

		var self=this;

		var oname=$('input[data-t="'+t+'"]',r);
		oname.bind("change",function(e){self.event_namechange(e)});

		var ocopy=$('select[data-t="'+t+'"]',r);
		ocopy.bind("refreshlist",self.event_copy_refresh);
		ocopy.bind("change",function(e){self.event_copy_copy(e,oname.val())});
		
		var oremove=$('.recdef_edit_action_remove[data-t="'+t+'"]',r);
		oremove.bind("click",function(e){self.event_removeview(e)});
		
		r.attr("data-t",t);
		
		var obutton=$('.button[data-tabname="'+t+'"]');
		obutton.attr("data-t",t);

	},
	
	event_namechange: function(e) {
		var t=$(e.target).attr("data-t");
		var v=$(e.target).val();

		$('.button_recdefviews[data-t="'+t+'"]').html("New View: "+v);
		
		$('[data-t="'+t+'"]').each(function(){
			$(this).attr("data-t",v);
		});
		this.refreshall();
		
	},	
	
	event_addview: function(e) {
		this.addview();
	},
	
	event_removeview: function(e) {
		var t=$(e.target).attr("data-t");
		this.removeview(t);
	},
	
	event_save: function(e) {
		this.save();
	},
	
	event_copy_refresh: function(e) {
		var t=$(e.target);
		t.empty();
		t.append('<option />');
		$("input[name^='viewkey']",this.root).each(function(){
			t.append('<option>'+$(this).val()+'</option>');
		});
	},

	event_copy_copy: function(e,d) {
		var t=$(e.target);
		this.copyview(t.val(),d);
	},	
	
	
	save: function() {
		this.rd=this.getvalues();
		this.commit();
	},
	
	default_commit_put: function() {
		var self=this;
		$.jsonRPC("putrecorddef",[this.rd],function(data){notify_post(EMEN2WEBROOT+'/db/recorddef/'+self.rd.name+'/', ["Changes Saved"])});
	},
	
	default_commit_add: function() {
		var self=this;
		$.jsonRPC("putrecorddef",[this.rd,this.parents],function(data){notify_post(EMEN2WEBROOT+'/db/recorddef/'+self.rd.name+'/', ["Changes Saved"])});
	},	
	
	refreshall: function(e) {
		$("select[name^='viewcopy']",this.root).each(function(){$(this).trigger("refreshlist");});
	},
	
	addview: function() {

		this.counter_new+=1;
		var t='new'+this.counter_new;
		var self=this;
		
		var ol=$('<li id="button_recdefviews_'+t+'" data-t="'+t+'" class="button button_recdefviews" data-tabgroup="recdefviews" data-tabname="'+t+'">New View: '+this.counter_new+'</li>');
		ol.bind("click",function(e){switchin('recdefviews',t)});

		var p=$('<div id="page_recdefviews_'+t+'" data-t="'+t+'" class="page page_recdefviews" data-tabgroup="recdefviews" data-tabname="'+t+'" />');

		var ul=$('<ul class="recdef_edit_actions clearfix" />');
		
		var oname=$('<li>Name: <input type="text" name="viewkey_'+t+'" data-t="'+t+'" value="'+t+'" /></li>');
		var ocopy=$('<li>Copy: <select name="viewcopy_'+t+'" data-t="'+t+'" "/></li>');
		var oremove=$('<li class="recdef_edit_action_remove" data-t="'+t+'"><img src="'+EMEN2WEBROOT+'/images/remove_small.png" /> Remove</li>');
		ul.append(oname, ocopy, oremove);
		
		var ovalue=$('<textarea name="view_'+t+'" data-t="'+t+'" rows="30" cols="80">');

		p.append(ul,ovalue);

		$("#buttons_recdefviews ul").prepend(ol);
		$("#pages_recdefviews",this.root).append(p);

		switchin('recdefviews',t);
		this.bindview(t,p);
		this.refreshall();

	},
	
	
	removeview: function(t) {
		$('.button_recdefviews[data-t="'+t+'"]').remove();
		$('.page_recdefviews[data-t="'+t+'"]').remove();
		
		var tabname=$($('.button_recdefviews')[0]).attr("data-tabname");
		switchin('recdefviews',tabname);
		
		this.refreshall();
	},
	
	
	copyview: function(src,dest) {
		var v=$('textarea[data-t="'+src+'"]').val();
		$('textarea[data-t="'+dest+'"]').val(v);		
	},
	
	
	getvalues: function() {
		rd={}
		rd["name"]=$("input[name='name']",this.root).val();

		var prv=$("input[name='private']",this.root).attr("checked");
		if (prv) {rd["private"]=1} else {rd["private"]=0}


		rd["typicalchld"]=[];

		$("input[name^='typicalchld']",this.root).each(function(){
			if ($(this).val()) {
				rd["typicalchld"].push($(this).val());
			}
		});

		rd["desc_short"]=$("input[name='desc_short']",this.root).val();
		rd["desc_long"]=$("textarea[name='desc_long']",this.root).val();

		rd["mainview"]=$("textarea[name='view_mainview']",this.root).val();

		rd["views"]={};
		var viewroot=$('#pages_recdefviews');
		$('.page[data-tabgroup="recdefviews"]',viewroot).each(function() {
			var n=$('input[name^="viewkey_"]',this).val();
			var v=$('textarea[name^="view_"]',this).val();			
			if (n && v) {
				rd["views"][n]=v;
			}
		});

		return rd		
	}
	
	
}

$.fn.RecordDefEditor = function(opts) {
  return this.each(function() {
		new RecordDefEditor(this, opts);
	});
};

return RecordDefEditor;

})(jQuery); // End localisation of the $ function


////////////////////////////////////////////////
////////////////////////////////////////////////
////////////////////////////////////////////////

ParamDefEditor = (function($) { // Localise the $ function

function ParamDefEditor(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, ParamDefEditor.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
};

ParamDefEditor.DEFAULT_OPTS = {
	root:null,
	add:0,
	parents:null,
	commit:function(){this.default_commit_put()}
};

ParamDefEditor.prototype = {
	
	init: function() {
		this.pd={};
		if (this.add) {
			this.commit = this.default_commit_add;
		}		
		this.build();
	},
	
		
	build: function() {
		this.bindall();
	},
	
	connect_buttons: function() {
		var self=this;
		$("#ext_save",this.root).bind("click",function(e){
			self.event_save(e)
		});
	},
	
	bindall: function() {
		var self=this;
		this.connect_buttons();		
	},
			
	event_save: function(e) {
		this.save();
	},	
	
	save: function() {
		this.pd=this.getvalues();
		this.commit();
	},
	
	default_commit_put: function() {
		var self=this;
		$.jsonRPC("putparamdef",[this.pd],function(data){notify_post(EMEN2WEBROOT+'/db/paramdef/'+self.pd.name+'/', ["Changes Saved"])});
	},
	
	default_commit_add: function() {
		var self=this;
		// console.log(this.pd);
		// console.log(this.parents);
		$.jsonRPC("putparamdef",[this.pd,this.parents],function(data){notify_post(EMEN2WEBROOT+'/db/paramdef/'+self.pd.name+'/', ["Changes Saved"])});
	},	
		
	getvalues: function() {
		pd={}
		pd["name"] = $("input[name='name']",this.root).val();
		pd["desc_short"] = $("input[name='desc_short']",this.root).val();
		pd["desc_long"] = $("textarea[name='desc_long']",this.root).val();
		pd["vartype"] = $("select[name='vartype']",this.root).val();
		pd["property"] = $("select[name='property']",this.root).val();
		pd["defaultunits"] = $("select[name='defaultunits']",this.root).val();

		pd["choices"] = [];

		$("input[name^='choices']",this.root).each(function(){
			if ($(this).val()) {
				pd["choices"].push($(this).val());
			}
		});
		return pd
	}
	
	
}

$.fn.ParamDefEditor = function(opts) {
  return this.each(function() {
		new ParamDefEditor(this, opts);
	});
};

return ParamDefEditor;

})(jQuery); // End localisation of the $ function
