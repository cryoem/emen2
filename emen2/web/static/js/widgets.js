//////////////////////////////////////////

// access values from correct sources

paramindex={};
rec={};
recs={};



function getvalue(recid,param) {
	//if (rec["recid"]==recid || recid==null) {return rec[param]}
	if (paramindex[param]) {
		if (paramindex[param][recid]) {return paramindex[param][recid]}
		}
	if (recs[recid]) {
		return recs[recid][param]
	}
	return null
}
function setvalue(recid,param,value) {
	if (rec["recid"]==recid || recid==null) {rec[param]=value}
	if (paramindex[param]) {
		if (paramindex[param][recid]) {
			paramindex[param][recid]=value
			}
	}
	if (recs[recid]) {
		if (recs[recid][param]) {
			recs[recid][param]=value
			}
	}
}
function setrecord(recid,record) {
	recs[recid]=record;
}
function setrecords(records) {
	$.each(records,function(i){
		recs[i]=this;
	});
}
function getrecord(recid) {
	if (recid==null) { return rec }
	if (recs[recid]) {
		return recs[recid];
	}
}







//////////////////////////////////////////


multiwidget = (function($) { // Localise the $ function

function multiwidget(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, multiwidget.DEFAULT_OPTS, opts);
  this.elem = $(elem);
  this.init();
};

multiwidget.DEFAULT_OPTS = {
	popup: 0,
	now: 0,	
	controls: 0,
	root: null,
	controlsroot: null,	
	ext_edit_button: 0,
	restrictparams: null,
	rootless: 0,
	newrecord: 0,
	commitcallback: function(){}
};

multiwidget.prototype = {
	
	init: function() {

		if (this.controls) {
			this.controls.empty()
		} else {
			this.controls=$('<div class="controls"></div>');
		}

		if (!this.controlsroot) {
			this.controlsroot=this.elem;
		}

		if (this.root) {
			this.root=$(this.root);
		} else {
			this.root=this.elem;
		}

		if (this.ext_edit_button) {
			this.elem.hide();
		}

		this.controlsroot.after(this.controls);	

		if (this.now) {
			this.build()
		} else if (!this.ext_edit_button) {
			var self=this;
			this.edit=$('<input class="editbutton" type="button" value="Edit" />').click(function(e) {e.stopPropagation();self.build()});
			this.controls.append(this.edit);
		}
		
	},
	
  build: function() {

		var ws=[];

		var cl=".editable";
		if (this.restrictparams) {
			cl="";
			for (var i=0;i<this.restrictparams.length;i++) {cl += ".editable.paramdef___"+this.restrictparams[i]+","}
		}

		if (this.rootless==0) {
			$(cl,this.root).each( function(i) {
				ws.push(new widget(this, {controls:0,popup:0,show:1}));
			});
		} else {
			$(cl).each( function(i) {
				ws.push(new widget(this, {controls:0,popup:0,show:1}));
			});			
		}

		this.ws = ws;
		var self=this;
		this.savebutton=$('<input type="submit" value="Save" />').click(function(e) {e.stopPropagation();self.save()});

		if (!this.newrecord) {
			this.cancel=$('<input type="button" value="Cancel" />').click(function(e) {e.stopPropagation();self.revert()});
		}
		
		$(this.controls).append(this.savebutton,this.cancel);		
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
	
	////////////////////////////
	save: function() {
		var changed={};
		var allcount=0;
		var self=this;
		$(this.ws).each(function(i){

			var oldval=getvalue(this.recid,this.param);
			if (this.changed) {
				var newval=this.getval();
			} else {
				var newval=oldval;
			}
			var count=0;

			if ( oldval != null && newval == null) {
				count+=1;
	 		}
	 		else if ( !self.compare(oldval,newval) ) {
				count+=1;
	 		}

			if (!changed[this.recid] && count > 0) {changed[this.recid]={}}
			if (count > 0) {changed[this.recid][this.param]=newval}
			allcount+=count;

		});
				
		if (allcount==0) {
			//console.log("no changes made..");
			notify("No changes made");
		} else {
			//console.log("commit callback");
			this.savebutton.val("Saving...");
			this.commitcallback(this,changed);
		}


	},
	
	revert: function() {
		//console.log("revert");
		$(this.ws).each(function(i){
			this.revert();
			this.remove();
		});
		this.now=0;
		this.init();
		this.elem.show();
	}
	
}

$.fn.multiwidget = function(opts) {
  return this.each(function() {
		new multiwidget(this, opts);
	});
};

return multiwidget;

})(jQuery); // End localisation of the $ function



//////////////////////////////////////////
//////////////////////////////////////////
//////////////////////////////////////////
//////////////////////////////////////////


widget = (function($) { // Localise the $ function

function widget(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, widget.DEFAULT_OPTS, opts);
  
  this.elem = $(elem);
	if (this.show) {
		this.build();
	}
};

widget.DEFAULT_OPTS = {
	popup: 1,
	controls: 1,
	show: 1
};

widget.prototype = {
	init: function() {
		this.changed=0;
	},
	
  build: function() {
				
		var props=this.getprops();		
		this.param=props["paramdef"];
		this.recid=parseInt(props["recid"]);		
		this.value=getvalue(this.recid,this.param);
		var self=this;

		//console.log(this.value);
		if (this.value == null) {
			this.value = "";
		}


		// container
		this.w = $('<span class="widget"></span>');


		// replace this big switch with something better
		if (paramdefs[this.param]["vartype"]=="text") {

			this.editw=$('<textarea class="value" cols="40" rows="10">'+this.value+'</textarea>');
			this.editw.change(function(){self.changed=1;});
			this.w.append(this.editw);				
			

		} else if (paramdefs[this.param]["vartype"]=="choice") {
			
			this.editw=$('<select></select>');
			var pdc=paramdefs[this.param]["choices"];
			pdc.unshift("");
			
			for (var i=0;i<pdc.length;i++) {
				var selected="";
				if (this.value == pdc[i]) selected = "selected";
				this.editw.append('<option val="'+pdc[i]+'" '+selected+'>'+pdc[i]+'</option>');
			}

			this.editw.change(function(){self.changed=1;});			
			this.w.append(this.editw);				
							
		} else if (paramdefs[this.param]["vartype"]=="datetime") {
		
			this.editw=$('<input class="value" size="18" type="text" value="'+this.value+'" />');
			this.editw.change(function(){self.changed=1;});
			this.w.append(this.editw);				

		} else if (paramdefs[this.param]["vartype"]=="boolean") {
		
			this.editw=$("<select><option>True</option><option>False</option></select>");
			this.editw.change(function(){self.changed=1;});
			this.w.append(this.editw);				
		
		} else if (["intlist","floatlist","stringlist","userlist"].indexOf(paramdefs[this.param]["vartype"]) > -1) {

			this.editw = new listwidget(this.w,{values:this.value,paramdef:paramdefs[this.param]});
			this.editw.change(function(){self.changed=1;});
		
		} else {

			this.editw=$('<input class="value" size="20" type="text" value="'+this.value+'" />');
			console.log("=="+this.value);
			//.autocomplete("/db/findvalue/"+this.param, {
			//	width: 260,
			//	selectFirst: true,
			//});
			this.editw.change(function(){self.changed=1;});
			this.w.append(this.editw);
			
			var property=paramdefs[this.param]["property"];
			var units=paramdefs[this.param]["defaultunits"];

			if (property != null) {

				this.editw_units=$('<select></select>');

				for (var i=0;i<valid_properties[property][1].length;i++) {
					var sel="";
					if (units == valid_properties[property][1][i]) sel = "selected";
					this.editw_units.append('<option '+sel+'>'+valid_properties[property][1][i]+'</option>');
				}
				
				this.editw_units.change(function(){self.changed=1;});
				this.w.append(this.editw_units);

			}


		}

	

		if (this.controls) {
			this.controls=$('<div class="controls"></div>').append(
				$('<input type="submit" value="Save" />').click(function(e) {e.stopPropagation();self.save()}),
				$('<input type="button" value="Cancel" />').click(function(e) {e.stopPropagation();self.revert()})
			);

			this.w.append(this.controls);

		}


		$(this.elem).after(this.w);
		$(this.elem).hide();

		//if (this.popup) {
		//	this.edit.focus();
		//	this.edit.select();
		//}
		
	},
	
	remove: function() {
		//this.w=None;
		this.elem.unbind("click");
	},

	////////////////////////
	getprops: function() {
		var classes = this.elem.attr("class").split(" ");
		var prop = new Object();
		for (var i in classes) {
			var j = classes[i].split("___");
			if (j.length > 1) {
				prop[j[0]] = j[1];
			}
		}
		
		if (!prop["recid"]) {prop["recid"]=recid}
		
		return prop;	
		
	},

	////////////////////////
	getval: function() {
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
	revert: function() {
		this.w.siblings(".editable").show();
		this.w.remove();		
	},
	
	////////////////////////	
	save: function() {
				
		var save=$(":submit",this.w);
		save.val("Saving...");

		var recid=this.recid;
		var param=this.param;
	
		$.jsonRPC("putrecordvalue",[recid,this.param,this.getval(),ctxid],
	 		function(json){
				setvalue(recid,param,json);
	 			//rec[this.param]=json;
	 			record_view_reload(recid,switchedin["recordview"]);
				notify("Changes saved");
	 		},
			function(xhr){
				//ole.log("error, "+xhr.responseText);
				//editelem_revert(elem,key);
				$("#alert").append("<li>Error: "+this.param+","+xhr.responseText+"</li>");
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

		this.inheritcontrols=[];
		this.changed=[];
		this.removed=[];
		this.removedlevel={};


		////////////////////////////////
		// Inherit / parent controls
		this.inheritarea=$('<table class="inherittable" cellspacing="0" cellpadding="0"><tr><th>Parent</th><th>Permissions</th><th>Record</th></tr></table>');

		if (this.inherit.length > 0) {
			for (var i=0;i<this.inherit.length;i++) {
				this.addinherititem(this.inherit[i],1);
			}
		}

		this.inheritarea_addcontrols = $('<tr></tr>');
		this.inheritarea_addfield = $('<input type="text" value="" />');
		
		// add new inherit/parent item
		this.inheritarea_addbutton = $('<input type="button" value="Add Record" />').click(function(){
			var getrecid=parseInt(self.inheritarea_addfield.val());

			$.getJSON("/db/getrecordwithdisplay/"+getrecid+"/",null,function(result){

				setrecord(getrecid,result["recs"][getrecid]);

				$.each(result["displaynames"], function(k,v) {
					displaynames[k]=v;
				});
				
				$.each(result["recnames"], function(k,v) {
					recnames[k]=v;
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



		////////////////////////////////
		// Add user controls
		
		var user_outer=$('<div class="user_outer"></div>');
		
		var useradd=$('<div class="user_add">Assign Permissions: </div>');

		// Search using autocomplete plugin
		this.search=$('<input class="value" size="20" type="text" value="" />').autocomplete(
			"/db/finduser/", {
			parsecallback: autocomplete_parse_finduser,
			width: 260,
			minChars:3,
			dataType:"json",
			selectFirst: true,
		});
		
		this.levelselect=$('<select><option value="0">Read</option><option value="1">Comment</option><option value="2">Write</option><option value="3">Admin</option></select>');

		this.adduserbutton=$('<input type="submit" value="Add User">');

		this.adduserbutton.click(function(){
			self.add(self.search.val(),self.levelselect.val());
			self.build();
		});
		
		useradd.append(this.search,this.levelselect,this.adduserbutton);

		user_outer.append(useradd);


		// Save controls
		if (!this.newrecord) {
			this.savearea = $('<div></div>');
			this.savearea.append('<input type="button" value="Save for this Record" />');
			this.savearea.append('<input type="button" value="Apply ADDED users to children" />');
			this.savearea.append('<input type="button" value="Apply REMOVED users to children" />');
			user_outer.append(this.savearea);
		}


		this.userarea_removed = $("<div></div>");
		this.userarea = $("<div></div>");
		
		user_outer.append(this.userarea,this.userarea_removed);

		this.elem.append(user_outer);

		// Build user lists
		this.build();
		
	},
	
	build_removed: function() {
		// build list of removed users
		this.userarea_removed.empty()

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
					var username=$('<span class="name">'+displaynames[v]+'</span>');
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
	
  build: function() {

		this.build_removed();
		
		// build list of user permissions
		this.userarea.empty();

		var self=this;

		$.each(this.list, function(k,v) {
			v=self.sortbydisplayname(v);
			if (v.length>0) {

				var level=$('<div class="clearfix user_level">'+self.levels[k]+' </div>');
				var level_removeall=$('<span>[<span class="jslink">X</span>]</span>').click(function () {
					var q=v.slice();
					for (var i=0;i<q.length;i++) {
						self.remove(q[i]);
					}
					self.build();
				});
				level.append(level_removeall);
				
				level_ul = $("<ul></ul>");
				
				$.each(v, function(k2,v2) {

					var userdiv=$('<li class="user clearfix"></li>');

					if (self.changed.indexOf(v2) > -1) {userdiv.addClass("changed")}
					
					var username=$('<span class="name">'+displaynames[v2]+'</span>');
					var useraction=$('<span class="action">X</span>').click(function(){
						if(self.remove(useraction.username)){
							self.build();
						}
					});

					useraction.username=v2;
					useraction.level=k;
					userdiv.append(useraction,username);
					level_ul.append(userdiv);

				});
				level.append(level_ul)
				self.userarea.append(level);
			}
		});

	},

	// sort usernames by their display names	
	sortbydisplayname: function(list) {
		var reversenames={};
		var sortnames=[];
		var retnames=[];
		for (var i=0;i<list.length;i++) {
		    reversenames[displaynames[list[i]]]=list[i];
		    sortnames.push(displaynames[list[i]]);
		}
		sortnames.sort();
		for (var i=0;i<sortnames.length;i++) {
			retnames.push(reversenames[sortnames[i]]);
		}
		return retnames
	},
	
	// add a new item to list of parents/inherits; builds UI elements
	addinherititem: function(recid,check) {
		
		if (this.inheritcontrols.indexOf(recid) > -1) {return}
		this.inheritcontrols.push(recid);

		if (this.parents.indexOf(recid) == -1) {this.parents.push(recid);}
		

		var control=$("<tr></tr>");

		var p=getvalue(recid,"permissions");

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
				if (this.checked) {self.addparent(recid)}	else {self.removeparent(recid)}
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
		control.append('<td>'+recnames[recid]+' (recid: '+recid+', '+count+' users)</td>');
		this.inheritarea.append(control);
		
		if (this.inherit.indexOf(recid) > -1) {return}
		this.inherit.push(recid);

	},	
	
	// add a user to permissions	
	add: function(username,level) {
		ret = 0;
		level=parseInt(level);
		if (displaynames[username] == null) {return}
		if (this.list[level].indexOf(username) == -1) {
			this.remove(username);
			this.list[level].push(username);
			if (this.changed.indexOf(username)==-1) {this.changed.push(username)}
			if (this.removed.indexOf(username) > -1) {this.removed.splice(this.removed.indexOf(username),1)}
			ret=1;
		}
		return ret
		
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
		if (username==user) {
			return 0
			}
		
		var newlist=[];
		var self=this;
		$.each(this.list, function(k,v) {
			var pos=v.indexOf(username);
			if (pos>-1) {
				v.splice(pos,1);
				self.removedlevel[username]=k;
			}
			newlist.push(v);
		});
		this.list=newlist;

		if (this.removed.indexOf(username) == -1) {this.removed.push(username)}
		if (this.changed.indexOf(username) > -1) {this.changed.splice(this.changed.indexOf(username),1)}


		return 1
	},
	
	// unmerge a list of users	
	removelist: function(list) {
		var newlist=[];

		if (list==null){return}
		for (var i=0;i<this.list.length;i++) {
			var l=[];
			for (var j=0;j<this.list[i].length;j++) {
				if ((list[i].indexOf(this.list[i][j]) == -1)||(this.list[i][j]==user)) {
					l.push(this.list[i][j]);
				}
			}
			newlist.push(l);
		}
		this.list=newlist;
	},
	
	// add a parent
	addparent: function(recid) {
		if (this.parents.indexOf(recid) == -1) {this.parents.push(recid)}
	},
	
	// remove a parent
	removeparent: function(recid) {
		if (this.parents.indexOf(recid) > -1) {
			this.parents.splice(this.parents.indexOf(recid),1);
		}
	},
	
	getpermissions: function() {
		return this.list
	}, 
		
	getparents: function() {
		return this.parents
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


parentcontrol = (function($) { // Localise the $ function

function parentcontrol(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, parentcontrol.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
};

parentcontrol.DEFAULT_OPTS = {
	inherit: []
};

parentcontrol.prototype = {
	
	init: function() {
		this.inheritcontrols=[];
		this.build();
	},
	
  build: function() {
		this.inheritarea=$("<div>Parent Records: </div>");

		if (this.inherit.length > 0) {
			for (var i=0;i<this.inherit.length;i++) {
				this.addinherititem(this.inherit[i],1);
			}
		}

		this.elem.append(this.inheritarea);
		
		var self=this;
		this.inheritarea_addcontrols = $('<div></div>');
		this.inheritarea_addfield = $('<input type="text" value="" />');
		this.inheritarea_addbutton = $('<input type="button" value="Add Parent Record" />').click(function(){
			var getrecid=parseInt(self.inheritarea_addfield.val());
			$.jsonRPC("getrecordrecname",[getrecid,ctxid],function(recname){
				recnames[getrecid]=recname;
				self.addinherititem(getrecid);
			});
		});
		this.inheritarea_addcontrols.append(this.inheritarea_addfield,this.inheritarea_addbutton);

		this.elem.append(this.inheritarea_addcontrols);
	},

	addinherititem: function(recid,check) {
		//console.log(recid);
		
		if (this.inheritcontrols.indexOf(recid) > -1) {return}
		this.inheritcontrols.push(recid);

		var control=$("<div></div>");
		
		if (check) {
			check="checked";
		} else { 
			check="";
		}

		var self=this;
		var input=$('<input type="checkbox" '+check+' />').change(function(){
			//console.log(p);
			this.checked=(this.checked) ? 1:0;
			if (this.checked) {
				console.log("remove");
				//self.build()
			}	else {
				console.log("add");
				//self.build()
			}
		});

		control.append(input);

		control.append('<span>'+recnames[recid]+' (recid: '+recid+')</span>');
		this.inheritarea.append(control);
		
		if (this.inherit.indexOf(recid) > -1) {return}
		this.inherit.push(recid);

	},
	
}

$.fn.parentcontrol = function(opts) {
  return this.each(function() {
		new parentcontrol(this, opts);
	});
};

return parentcontrol;

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
		//this.w=$("<div></div>");
		//this.elem.append(this.w);
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
		//for (var i=0;i<this.values.length;i++) {
		$.each(this.values, function(k,v) {
			var item=$('<li></li>');
			var edit=$('<input type="text" value="'+v+'" />');
			var add=$('<span><img src="/images/add_small.png" class="listwidget_add" /></span>').click(function() {
				self.addoption(k+1);
				self.build();
			});
			var remove=$('<span><img src="/images/remove_small.png" class="listwidget_remove" /></span>').click(function() {
				self.removeoption(k);
				self.build();
			});
			item.append(edit,add,remove);
			self.items.append(item);
		});
		//this.elem.append(items);
	},

	// add another option to list
	addoption: function(pos) {
		// save current state so rebuilding does not erase changes
		this.values = this.val_withblank();
		this.values.splice(pos,0,"");
	},
	
	// remove an option from the list
	removeoption: function(pos) {
		this.values = this.val_withblank();
		this.values.splice(pos,1);
	},
	
	// return the values
	val: function() {
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
		new listwidget(this, opts);
	});
};

return listwidget;

})(jQuery); // End localisation of the $ function



/////////////////////////////////////////////


skeleton = (function($) { // Localise the $ function

function skeleton(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, skeleton.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
};

skeleton.DEFAULT_OPTS = {
};

skeleton.prototype = {
	
	init: function() {
		this.build();
	},
	
  build: function() {

	}
	
}

$.fn.skeleton = function(opts) {
    return this.each(function() {
		new skeleton(this, opts);
	});
};

return skeleton;

})(jQuery); // End localisation of the $ function



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

		this.widget = $('<div class="commentswidget_controls clearfix"></div>');
		
		this.edit = $('<textarea cols="60" rows="2"></textarea>');
		
		var self=this;
		this.controls=$('<div></div>');
		this.commit=$('<input class="editbutton" type="submit" value="Add Comment" />').click(function(e) {e.stopPropagation();self.save()});
		this.clear=$('<input class="editbutton" type="button" value="Clear" />').click(function(e) {e.stopPropagation();self.revert()});
		this.controls.append(this.commit,this.clear);

		this.widget.append(this.edit, this.controls);
		this.elem_body.append(this.widget);

		var cr=this.comments.reverse();

		if (cr.length == 0) {
			this.elem_body.append('<p>No Comments</p>');
		}
		
		if (this.elem_title) {
			this.elem_title.html("Comments ("+cr.length+")");
		}

		$.each(cr, function() {
			var dname=this[0];
			if (displaynames[this[0]]!=null) {
				var dname = displaynames[this[0]];
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
				notify("Changes saved");
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
			if (displaynames[this[0]]!=null) {
				var dname = displaynames[this[0]];
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
