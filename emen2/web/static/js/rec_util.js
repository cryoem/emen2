// globals

paramindex={};
paramdefs={};

recid=null;
rec={};
recs={};
parents=[];
children=[];

recnames={};
displaynames={};
groupnames={};

// groupnames={};
// groupnames["-4"]="Anonymous Access";
// groupnames["-3"]="Authenticated Users";
// groupnames["-1"]="Administrators";



// js is stupid at sorting.
function sortNumber(a, b) {
	return a - b;
}



/// switch.js
function switchbutton(type,id) {
	$(".button_"+type).each(function() {
		var elem=$(this);
		if (this.id != "button_"+type+"_"+id) {
			elem.removeClass("button_active");
			elem.removeClass("button_"+type+"_active");
		} else {
			elem.addClass("button_active");
			elem.addClass("button_"+type+"_active");
		}
	});
}


switchedin=new Array();
switchedin["recordview"]="defaultview";
// hide class members, show one, switch the button
function switchin(classname, id) {
	//console.log("Switching in "+classname+" "+id);
	switchedin[classname]=id;
	switchbutton(classname,id);
	$(".page_"+classname).removeClass("page_active");
	$(".page_"+classname).removeClass("page_"+classname+"_active");	
	$("#page_"+classname+"_"+id).addClass("page_active");
	$("#page_"+classname+"_"+id).addClass("page_"+classname+"_active");
	//$(".page_"+classname).css("display","none");
	//document.getElementById("page_" + classname + "_" + id).style.display = 'block';	
}



//////////////////////////////////////////
// access values from cached sources

function getdisplayname(name) {
	if (displaynames[name]!=null) return displaynames[name];
	if (groupnames[name]!=null) return "Group: "+groupnames[name]; 
}

function setdisplayname(name,value) {
	if (isNaN(parseInt(name))) {
		displaynames[name]=value;
	} else {
		groupnames[name]=value;
	}
}

function getrecname(name) {
	return recnames[name]
}
function setrecname(name,value) {
	recnames[name]=value;
}


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


function notify(msg, fade, error) {
	var msg=$('<li>'+msg+'</li>');

	if (error) {
		msg.addClass("error");
	}

	//var killbutton = $('<img src="'+EMEN2WEBROOT+'/images/delete.png" />');
	var killbutton = $('<span>X</span>');
	killbutton.click(function() {
		$(this).parent().fadeOut(function(){
			//fadeoutcallback; in this context, 'this' is li
			$(this).remove();
			});		
	});
	killbutton.addClass("kill");
	msg.append(killbutton);

	// auto fade if given time value
	//if (!fade) {
	//	setTimeout(function(){msg.fadeOut()},3000)
	//}
	//if (fade > 0) {
	//	setTimeout(function(){msg.fadeOut()},fade*1000)
	//}

	$("#alert").append(msg); //.fadeIn();
	
}


function notify_post(uri,msgs) {
  var postform = document.createElement("form");
  postform.method="post" ;
  postform.action = uri;
	for (var i=0;i<msgs.length;i++) {
		var note = document.createElement("input") ;
		note.setAttribute("name", "notify___"+i) ;
		note.setAttribute("value", msgs[i]);
		postform.appendChild(note) ;
	}
	document.body.appendChild(postform);
  postform.submit();	
}



/////////////////////////////////////////


function record_action_delete(drecid) {
	var test=confirm("Are you sure you want to delete this record?");
	if (test) {
		$.jsonRPC("deleterecord",[drecid], function() {
			//$.post("/db/record/"+recid,{"notify___0":"This record has been marked for deletion and removed from hierarchy"});
			notify_post(window.location,["This record has been marked for deletion and removed from the hierarchy"]);
			//window.location.reload();
		}, function() {
			notify("Error deleting record!");
		});
	}
}




function toggle_record_menu(elem) {
	
	var elem=$(elem);
	var state=elem.data("active");
	if (state == null || state == 0) {state=1} else {state=0}

	// reset state
	$(".record_editbar_hidden").hide();
	$(".record_editbar_item").removeClass("record_editbar_no_border_bottom");	
	$(".record_editbar_item").addClass("record_editbar_border_bottom");	
	$(".record_editbar_item").children("span").data("active",0);
	elem.data("active",state);
	
	//elem.data("active",elem.data("active") ? 0 : 1);

	if (state) {
		//console.log("show");
		elem.parent().addClass("record_editbar_no_border_bottom");	
		elem.parent().removeClass("record_editbar_border_bottom");	
		elem.siblings(".record_editbar_hidden").show();
	}

}

function record_permissions_toggle(elem) {
	toggle_record_menu(elem);
	//var target=$("#record_editbar_menu_permissions");	
	var target=$(elem).siblings(".record_editbar_hidden");				

	if (permissionscontrol==null) {
	
		target.empty();
	
		$.jsonRPC("getuserdisplayname",[recid,1,1], function(result) {
			$.each(result, function(k,v) {
				setdisplayname(k,v);
			});
			permissionscontrol = new permissions(target, {
				'list':getvalue(recid,"permissions"),
				'groups':getvalue(recid,"groups")
				}
			)
					
		});
	}

	return false

}

function record_form_newrecord_toggle(elem) {
	toggle_record_menu(elem);
}


function record_upload_toggle(elem) {
	toggle_record_menu(elem);
}

function record_tools_toggle(elem) {
	toggle_record_menu(elem);
}

function record_relationships_toggle(elem) {
	toggle_record_menu(elem);
	var target=$(elem).siblings(".record_editbar_hidden");
	
	if (relationships==null) {
		
		target.empty();
		
		$.jsonRPC("getrecordrecname",[parents.concat(children).concat([recid])], function(result) {
			$.each(result, function(k,v) {
					setrecname(k,v);
					//recnames[v[0]]=v[1];
			});
			relationships = new relationshipcontrol(target, {
				'parents':parents,
				'children':children,
				'recid':recid
			});
			
		});

	} 
}



function newrecord_getoptionsandcommit(self, values) {
		
	if (!values["None"]){values["None"]={}}
	
	values["None"]["permissions"] = permissionscontrol.getpermissions();
	values["None"]["parents"] = permissionscontrol.getparents();
	values["None"]["groups"] = permissionscontrol.getgroups();
	//var parents=permissionscontrol.getparents();
	// console.log(values);
	// return
	
	// commit
	commit_newrecord(
		self,
		values,
		parents,
		function(recid){
			notify_post(EMEN2WEBROOT+'/db/record/'+recid.recid+'/',["Record Saved"]);
		}
	);
	
}
	
function commit_newrecord(self, values, parents, cb, self) {
	if (cb==null) {cb=function(){}}
	var rec_update=getrecord(null);

	$.each(values["None"], function(i,value) {
		if ((value!=null) || (getvalue(recid,i)!=null)) {
			rec_update[i]=value;
		}
	});
	
	$.jsonRPC("putrecord", [rec_update, parents],
		function(json){
			cb(json);
		},
		function(xhr){
			//$("#alert").append("<li>Error: "+this.param+", "+xhr.responseText+"</li>");
			notify("Error: "+this.param+", "+xhr.responseText);
			self.ext_save.val("Retry");		
		}
	);
}









