// js is stupid at sorting.
function sortNumber(a, b) {
	return a - b;
}

var edit=0;
var paramdefs={};
var recs={};


function notify(msg) {
	$("#alert").empty();
	var msg=$('<li>'+msg+'</li>');
	$("#alert").append(msg).fadeIn();
	setTimeout(function(){msg.fadeOut()},3000)
}

function updatecomments() {
	elem=$("#page_comments_commentstext");
}


$.postJSON = function(uri,data,callback,errback) {
	if (!errback) {
		errback = function(xhr){
				$("#alert").append("<li>Error: "+xhr.responseText+"</li>");
			}
		}
	$.ajax({
    type: "POST",
    url: uri,
    data: {"args_json":$.toJSON(data)},
    success: callback,
    error: errback,
		dataType: "html"
    });
}

$.jsonRPC = function(method,data,callback,errback) {
	$.ajax({
    type: "POST",
    url: "/json/"+method,
    data: $.toJSON(data),
    success: callback,
    error: errback,
		dataType: "json"
    });
}

function getrecords_paramdefs(recids,finalcallback) {
	// get data.
	
	$.jsonRPC(
		"getrecord",
		[recids,ctxid],
 		function(json){
			//console.log("got records");
			$.each(json, function() {
				setrecord(this["recid"],this);
			});			

			//
			$.jsonRPC(
				"getparamdefs",
				[recids,ctxid],
				function (json) {
					//console.log("got paramdefs");
					$.each(json, function(i) {
						//console.log(i,this);
						paramdefs[i]=this;
					});
					// calling final callback
					finalcallback();
				}
			);
			//

 		}
	);
}


function record_page_edit(elem, key) {
	new multiwidget(
		elem, {
			'now':1,
			'ext_edit_button':1,
			'root': '#page_recordview_'+key
			});
}

function table_editcolumn(elem,key) {

	new multiwidget(
			elem, {
				'commitcallback':function(){table_reload()},
				'now':1,
				'ext_edit_button':1,
				'rootless':1,
				'restrictparams':[key]
				});	

}	



function table_reload() {
	var ns={};
	ns["sortkey"]=tablestate["sortkey"];
	ns["reverse"]=tablestate["reverse"];
	ns["pos"]=tablestate["pos"];
	ns["reset"]=1;
	
	$.postJSON(
		'/db/table/'+tablestate["mode"]+'/'+tablestate["args"].join('/')+'/',
		ns,
		function(data) {
			$(tablestate['id']).html(data);
			}
		);
}

function table_setpos(pos) {
	var ns={};
	//def table_children(recid,group,recids=None,pos=0,count=100,reccount=None,sortkey=None,reverse=0,ctxid=None,db=None,rctx=0,reset=1,host=None):
	//ns["pos"]=pos;
	//ns["count"]=tablestate["count"];

	ns["recids"]=tablestate["recids"].slice(pos,pos+tablestate["count"]);

	ns["sortkey"]=tablestate["sortkey"];
	ns["reverse"]=tablestate["reverse"];
	ns["reccount"]=tablestate["reccount"];
	ns["pos"]=pos;
	ns["reset"]=0;

	$.postJSON(
		'/db/table/'+tablestate["mode"]+'/'+tablestate["args"].join('/')+'/',
		ns,
		function(data) {
			$(tablestate['id_inner']).html(data);
		}
		);
}

function table_sort(key) {
	var ns={};
	ns["sortkey"]=key;

	// these events reset position to zero
	if (tablestate["sortkey"] == key) {
		ns["reverse"] = tablestate["reverse"] ? 0 : 1
	} 

	$.postJSON(
		'/db/table/'+tablestate["mode"]+'/'+tablestate["args"].join('/')+'/',
		ns,
		function(data) {
			$(tablestate['id']).html(data);
			}
		);
	
}



function reload_record_view(view) {
	if (!view) {view="defaultview"}
	$("#page_recordview_"+view).remove(".controls");
	$("#page_recordview_"+view+" .view").load("/db/recordview/"+recid+"/"+view,{},	function(data){editelem_makeeditable();});
}

function jsonrpccallback(json){}

function jsonrpcerror(xhr){
	//console.log("error, "+xhr.responseText);
	$("#alert").append("<li>Error: "+param+","+xhr.responseText+"</li>");
}


function editelem_revertview(page,view) {
	if (!view) {view="defaultview"}
	$(page).load("/db/recordview/"+recid+"/"+view,{},	function(){editelem_makeeditable()});
}


function editelem_makeeditable() {
	$('.editable').bind("click",function(){new widget(this)});
	//$('.page_recordview .view').multiwidget();
}


paramindex={};
rec={};
recs={};

function getvalue(recid,param) {
	if (paramindex[param]) {
		if (paramindex[param][recid]) {return paramindex[param][recid]}
		}
	if (recs[recid]) {
		if (recs[recid][param]) {return recs[recid][param]}
	}
	return null
}
function setvalue(recid,param,value) {
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
	if (recs[recid]) {
		return recs[recid];
	}
}



//////////////////////////////////////////
// not used; for testing
function tableinit() {

	var testtable=document.getElementById("testtable");

	var order=1;

	var tr=document.createElement("tr");
	for(var j=0;j<tablekeys.length;j++) {
		var th=document.createElement("th");
		th.innerHTML=tablekeys[j];
		new multiwidget(th,{restrictparams:[tablekeys[j]], rootless:1, controlsroot: $(th)});
		tr.appendChild(th);
	}
	testtable.appendChild(tr);

	for (var i=0;i<recids.length;i++) {
		var tr=document.createElement("tr");
		for (var j=0;j<tablekeys.length;j++) {
			var td=document.createElement("td");
			var sp=document.createElement("span");
			sp.innerHTML=getvalue(recids[i],tablekeys[j]);
			sp.className="editable paramdef___"+tablekeys[j]+" recid___"+recids[i];
			td.appendChild(sp);
			tr.appendChild(td);
		}
		new multiwidget(tr,{restrictparams:["name_first"],rootless:1});
		testtable.appendChild(tr);	
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
	commitcallback: function(){reload_record_view(switchedin["recordview"])}
};

multiwidget.prototype = {
	
	init: function() {
		console.log("multiwidget init");

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
		
		console.log("multiwidget building...");


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
		this.cancel=$('<input type="button" value="Cancel" />').click(this.bindToObj(function(e) {e.stopPropagation();this.revert()}));

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

	 		if (getvalue(this.recid,this.param)==null && value != "" && value != null) {
	 			console.log("new value "+this.param+"; orig is null");
				newval=value;
				count+=1;
	 		}
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
		
		console.log(changed);
		//console.log(changed.length);
		
		if (allcount==0) {console.log("no changes made..");}
		else {
			console.log("committing...");
			this.commit(changed);
		}


	},
	
	revert: function() {
		console.log("revert");
		$(this.ws).each(function(i){
			this.revert();
			this.remove();
		});
		this.now=0;
		this.init();
		this.elem.show();
	},
	
	commit: function(values) {
		var cb=this.commitcallback;
		var self=this;
		console.log("commit...");
	
		$.jsonRPC("putrecordsvalues",[values,ctxid],
	 		function(json){
				setrecords(json);
	 			cb();
				notify("Changes saved");
				self.revert();
	 		},
			function(xhr){
				//ole.log("error, "+xhr.responseText);
				//editelem_revert(elem,key);
				$("#alert").append("<li>Error: "+this.param+", "+xhr.responseText+"</li>");
			}
		)	
				
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
		console.log("widget init");
		//this.elem.click(this.bindToObj(function(e) {e.stopPropagation();this.build()}));
		//this.elem.one("click",this.bindToObj(function(e) {this.build();return false}));
		//this.build();
	},
	
  build: function() {
		console.log("widget building...");
				
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
	 			console.log(self.build());
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