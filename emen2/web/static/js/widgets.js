//////////////////////////////////////////

// access values from correct sources

paramindex={};
rec={};
recs={};



function getvalue(recid,param) {
	if (rec["recid"]==recid || recid==null) {return rec[param]}
	if (paramindex[param]) {
		if (paramindex[param][recid]) {return paramindex[param][recid]}
		}
	if (recs[recid]) {
		if (recs[recid][param]) {return recs[recid][param]}
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
			this.edit=$('<input class="editbutton" type="button" value="Edit" />').click(this.bindToObj(function(e) {e.stopPropagation();this.build()}));
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
	
		this.savebutton=$('<input type="button" value="Save" />').click(this.bindToObj(function(e) {e.stopPropagation();this.save()}));

		if (!this.newrecord) {
			this.cancel=$('<input type="button" value="Cancel" />').click(this.bindToObj(function(e) {e.stopPropagation();this.revert()}));
		}
		
		$(this.controls).append(this.savebutton,this.cancel);		
	},
	
	////////////////////////////
	save: function() {
		var changed={};
		var allcount=0;

		$(this.ws).each(function(i){

			var value=this.getval();
			var newval;
			var count=0;

	 		//if (getvalue(this.recid,this.param)==null && value != "" && value != null) {
	 		//	console.log("new value "+this.param+"; orig is null");
			//	newval=value;
			//	count+=1;
	 		//}
			if (getvalue(this.recid,this.param)!=null && value == null) {
				console.log("unsetting "+this.param);
				newval=null;
				count+=1;
	 		}
	 		else if (getvalue(this.recid,this.param)!=value) {
	 			console.log("changed: "+this.param+" , "+getvalue(this.recid,this.param)+" , "+value);
				newval=value;
				count+=1;
	 		}

			if (!changed[this.recid] && count > 0) {changed[this.recid]={}}
			if (count > 0) {changed[this.recid][this.param]=newval}
			allcount+=count;

		});
		
		//console.log(changed);
		
		if (allcount==0) {
			console.log("no changes made..");
		} else {
			console.log("commit callback");
			this.commitcallback(changed);
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
	},

	
	
	///////////////////////
  bindToObj: function(fn) {
    var self = this;
    return function() { return fn.apply(self, arguments) };
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
		//console.log("widget init");
		//this.elem.click(this.bindToObj(function(e) {e.stopPropagation();this.build()}));
		//this.elem.one("click",this.bindToObj(function(e) {this.build();return false}));
		//this.build();
	},
	
  build: function() {
				
		var props=this.getprops();		
		this.param=props["paramdef"];
		this.recid=parseInt(props["recid"]);		
		//console.log(this.recid);

		this.value=getvalue(this.recid,this.param);

		if (this.value==null) {
			this.value="";
		}

		this.w = $('<span class="widget"></span>');
		this.edit = $('<input />');

		if (paramdefs[this.param]["vartype"]=="text") {

			this.edit=$('<textarea class="value" cols="40" rows="10"></textarea>');
			this.edit.val(this.value);

		} else if (paramdefs[this.param]["vartype"]=="choice") {

			this.edit=$('<select></select>');

			for (var i=0;i<paramdefs[this.param]["choices"].length;i++) {
				this.edit.append('<option val="'+paramdefs[this.param]["choices"][i]+'">'+paramdefs[this.param]["choices"][i]+'</option>');
			}
		
		} else if (paramdefs[this.param]["vartype"]=="datetime") {
		
			this.edit=$('<input class="value" size="18" type="text" value="'+this.value+'" />');
			//.date_input();

		} else if (paramdefs[this.param]["vartype"]=="boolean") {
		
			this.edit=$("<select><option>True</option><option>False</option></select>");
		
		} else {

			this.edit=$('<input class="value" size="20" type="text" value="'+this.value+'" />');
			//.autocomplete("/db/findvalue/"+this.param, {
			//	width: 260,
			//	selectFirst: true,
			//});

		}

	
		this.w.append(this.edit);				

		if (this.controls) {

			this.controls=$('<div class="controls"></div>').append(
				$('<input type="submit" value="Save" />').click(this.bindToObj(function(e) {e.stopPropagation();this.save()})),
				$('<input type="button" value="Cancel" />').click(this.bindToObj(function(e) {e.stopPropagation();this.revert()}))
			);

			this.w.append(this.controls);

		}

		$(this.elem).after(this.w);
		$(this.elem).hide();

		if (this.popup) {
			this.edit.focus();
			this.edit.select();
		}
		
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
		var ret=this.edit.val();
		if (ret == "") {
			ret = null;
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
	 			reload_record_view(switchedin["recordview"]);
				notify("Changes saved");
	 		},
			function(xhr){
				//ole.log("error, "+xhr.responseText);
				//editelem_revert(elem,key);
				$("#alert").append("<li>Error: "+this.param+","+xhr.responseText+"</li>");
			}
		);		
	},
	
	///////////////////////
  bindToObj: function(fn) {
    var self = this;
    return function() { return fn.apply(self, arguments) };
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
	levels: ["Read","Comment","Write","Admin"]
};

permissions.prototype = {
	
	init: function() {
		this.build();
	},
	
  build: function() {

		
		this.elem.empty();
		var userarea=$("<div></div>");
		var useradd=$("<div></div>");


		this.search=$('<input class="value" size="20" type="text" value="" />').autocomplete(
			"/db/finduser/", {
			parsecallback: autocomplete_parse_finduser,
			width: 260,
			minChars:3,
			dataType:"json",
			selectFirst: true,
		});
		this.levelselect=$('<select><option value="Read">Read</option><option value="Comment">Comment</option><option value="Write">Write</option><option value="Admin">Admin</option></select>');
		this.adduserbutton=$('<input type="submit" value="Add">');
		this.adduserbutton.click(function(){
			self.add(self.search.val(),self.levelselect.val())
		});
		
		useradd.append(this.search,this.levelselect,this.adduserbutton);
		this.elem.append(useradd);


		var self=this;
		$.each(this.list, function(k,v) {
			if (v.length>0) {

				var level=$('<div class="clearfix">'+self.levels[k]+'</div>');

				$.each(v, function(k2,v2) {

					var userdiv=$('<div class="user"></div>');
					var username=$('<span class="name">'+displaynames[v2]+'</span>');
					var useraction=$('<span class="action">X</span>').click(function(){self.remove(useraction.username)});

					useraction.username=v2;
					useraction.level=k;
					userdiv.append(useraction,username);
					//users.push(userdiv);
					level.append(userdiv);

				});
				userarea.append(level);
			}
		});

		this.elem.append(userarea);
		//$.each(users, function(k,v){console.log(v.level+": "+v.username)});

	},
	
	add: function(username,level) {
		level=this.levels.indexOf(level);
		console.log(username);
		this.list[level].push(username);
		this.build();
	},
	
	remove: function(username) {

		if (username==user) {return}
		
		var newlist=[];
		$.each(this.list, function(k,v) {
			var pos=v.indexOf(username);
			if (pos>-1) {
				v.splice(pos,1);
			}
			newlist.push(v);
		});
		this.list=newlist;
		console.log(this.list);
		this.build();	
	},
	
	///////////////////////
  bindToObj: function(fn) {
    var self = this;
    return function() { return fn.apply(self, arguments) };
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

	},
	
	save: function() {

	},
	
	revert: function() {

	},
	
	commit: function(values) {
				
	},
	
  bindToObj: function(fn) {
    var self = this;
    return function() { return fn.apply(self, arguments) };
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

addcomment = (function($) { // Localise the $ function

function addcomment(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, addcomment.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
};

addcomment.DEFAULT_OPTS = {
};

addcomment.prototype = {
	
	init: function() {
		this.build();
	},
	
  build: function() {

		this.elem.empty();

		var comments = $('<div style="clear:both;padding-top:20px;"></div>');

		this.widget = $('<div></div>');
		
		this.edit = $('<textarea style="float:left" cols="60" rows="2"></textarea>');
		
		this.controls=$('<div></div>');
		this.commit=$('<input class="editbutton" type="submit" value="Save" />').click(this.bindToObj(function(e) {e.stopPropagation();this.save()}));
		this.clear=$('<input class="editbutton" type="button" value="Revert" />').click(this.bindToObj(function(e) {e.stopPropagation();this.revert()}));
		this.controls.append(this.commit,"<br />",this.clear);

		this.widget.append(this.edit, this.controls);
		this.elem.append(this.widget);

		var cr=getvalue(recid,"comments").reverse();
		//rec["comments"].reverse();

		$.each(cr, function() {
			var dname=this[0];
			if (displaynames[this[0]]!=null) {
				var dname = displaynames[this[0]];
			}
			var time=this[1];
			
			if (typeof(this[2])=="object") {
				comments.append('<h3>'+dname+' @ '+time+'</h3><p>'+this[2][0]+'changed: '+this[2][2]+' -&gt; '+this[2][1]+'</p>');
			}
			else {
				comments.append('<h3>'+dname+' @ '+time+'</h3><p>'+this[2]+'</p>');
			}
		});
		this.elem.append(comments);
		

	},
	
	////////////////////////////
	save: function() {
		var self=this;
		
		$.jsonRPC("addcomment",[recid,this.edit.val(),ctxid],
	 		function(json){
				console.log(json);
				setvalue(recid,"comments",json);
				//rec["comments"]=json;
	 			self.build();
				notify("Changes saved");
	 		},
			function(xhr){
				//ole.log("error, "+xhr.responseText);
				//editelem_revert(elem,key);
				$("#alert").append("<li>Error: "+this.param+","+xhr.responseText+"</li>");
			}
		)			
		
		
	},
	
	revert: function() {
		console.log("revert");
	},
	
	commit: function(values) {
				
	},
	
	///////////////////////
  bindToObj: function(fn) {
    var self = this;
    return function() { return fn.apply(self, arguments) };
  }	
	
}

$.fn.addcomment = function(opts) {
  return this.each(function() {
		new addcomment(this, opts);
	});
};

return addcomment;

})(jQuery); // End localisation of the $ function