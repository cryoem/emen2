function record_permissions_show() {
	switchin('comments','permissions');
	$("#page_comments_permissions").append('<img src="/images/spinner.gif" />');
	$("#page_comments_permissions").load("/main.css");
}

function record_relationships_show() {
	switchin('comments','relationships');
	$("#page_comments_relationships").append('<img src="/images/spinner.gif" />');
	$("#page_comments_relationships").load("/main.css");
}






/***********************************************/

function form_makeedits(formobj) {
	formobj.commit.style.display = "block";
	formobj.cancel.style.display = "block";
	formobj.edit.style.display = "none";

	showclass('input_elem');
	hideclass('param_display');
	return false
}

function form_makeedits_cancel(formobj) {
	formobj.commit.style.display = "none";
	formobj.cancel.style.display = "none";
	formobj.edit.style.display = "block";

	showclass('param_display');
	hideclass('input_elem');
	return false
}

function form_makeedits_putrecord(formobj) {
	var newvalues = collectpubvalues_new(formobj)["r"];
	if (!newvalues) {return}
	
	newvalues["rectype"]=rectype;
	newvalues["recid"]=name;

	var cb = new CallbackManager();
	cb.register(function(r,cbargs) {window.location=window.location});
	cb.req("putrecord",[newvalues,ctxid]);
}

function form_makeedits_putnewrecord(formobj) {
	var alerts = new Array();
	var newvalues = collectpubvalues_new(formobj)["r"];
	if (!newvalues) {return}
	
	newvalues["rectype"]=rectype;

	var inheritperms = null;
	if (document.forms['form_newrecord_generaloptions'].inheritpermissions.checked) {
		inheritperms = pclink;
	}

	///////////////////////
	if (document.forms['form_newrecord_multiple'].enable.checked) {
		var nvm=new Array();
		var param=document.forms['form_newrecord_multiple'].param.value;
		var prefix=document.forms['form_newrecord_multiple'].prefix.value;
		var start=document.forms['form_newrecord_multiple'].value_start.value;
		var end=document.forms['form_newrecord_multiple'].value_end.value;
		try{start=validate_int(start)}catch(error){alerts.push("Ranges must be integers")}
		try{end=validate_int(end)}catch(error){alerts.push("Ranges must be integers")}

		if (alerts.length > 0) {
			topalert(alerts);
			return
		}

		for (var j=start;j<=end;j++) {
			// javascript has no deep copy. this is ugly but required.
			var newvalues = collectpubvalues_new(formobj)["r"];
			newvalues["rectype"]=rectype;
			newvalues[param]=prefix+String(j);
			//console.log(newvalues[param]);
			nvm.push(newvalues);
			//console.log(nvm);
		}

		var cb = new CallbackManager();
		cb.register(function(r){window.location = window.location.protocol + "//" + window.location.host + "/db/record/" + pclink + "?notify=" + 5});
		cb.req("putrecords",[nvm,ctxid,pclink,[],inheritperms]);

	////////////////////////
	} else {
		
		if (alerts.length > 0) {
			topalert(alerts);
			return
		} 
		var cb = new CallbackManager();
		cb.register(function(r){window.location = window.location.protocol + "//" + window.location.host + "/db/record/" + r + "?notify=2"});
		cb.req("putrecord",[newvalues,ctxid,pclink,[],inheritperms]);

	}
}


/*******************************************/

function form_permissions() {
}


function form_permissions_add(formobj) {
	var nv=collectpubvalues_new(formobj)["p"];
	if (!nv) {return}
	
	var user=nv["add"];
	var level=nv["addlevel"];
	var recurse = 0;
	if (nv["recursive"]) {
		recurse = 20;
	}
	var usertuple = [[],[],[],[]];
	usertuple[level] = user;
	
	var cb = new CallbackManager();
	cb.register(function(r,cbargs) {makeRequest('/db/permissions/'+name+'?edit=1','sidebar_permissions')})
	cb.req("secrecordadduser",[usertuple,name,ctxid,recurse]);
}

function form_permissions_remove(formobj) {
	var nv=collectpubvalues_new(formobj)["p"];
	if (!nv) {return}
	
	var recurse = 0;
	if (nv["recursive"]) {
		recurse = 20;
	}

	var users = new Array();
	for (i in nv["remove"]) {
		users.push(i);
	}
	
//	alert(typeof(name));
	form_permissions_remove_cb(null,[users,name,recurse]);

}	
// call secrecorddeluser for each user...
function form_permissions_remove_cb(r,cbargs) { // r=null .. cbargs = [users,recid,recurse]
	var users=cbargs[0];
	var recid=cbargs[1];
	var recurse=cbargs[2];
	
	//console.log(users);
	
	if (users.length > 0) {
		var user=users.shift();
		var cb = new CallbackManager();
		cb.setcbargs([users,recid,recurse]);
		cb.register(form_permissions_remove_cb);
		cb.req("secrecorddeluser",[user,recid,ctxid,recurse]);
		return
	}
	
	makeRequest('/db/permissions/'+name+'?edit=1','sidebar_permissions');
	
}
/******************************************/

function form_relationships_new() {
	//qhide("parentmap");
	var page_recordview = document.getElementById("page_recordview");
	var page_recordview_relationships = document.createElement("div");
	page_recordview_relationships.className="page page_recordview";
	page_recordview_relationships.id="page_recordview_relationships";
	page_recordview.appendChild(page_recordview_relationships);
	makeRequest('/db/parentmap/record/'+name+'?edit=1&editboth=1','page_recordview_relationships');	

//	var cancelbutton = document.createElement("button");
//	cancelbutton.innerHTML = "Cancel";
//	cancelbutton.onclick = switchin('recordview','defaultview');
//	page_recordview_relationships.appendChild(cancelbutton);

	switchin('recordview','relationships');
}
function form_relationships_new_cb() {
	
}

function form_relationships() {
}

function form_relationships_add(formobj,type) {
	var value=collectpubvalues_new(formobj)["p"][type];
	if (!value) {return}

	var cb = new CallbackManager();
	// change to refresh just parent tree and relationship editor
	cb.register(function(r,cbargs) {window.location = window.location.protocol + "//" + window.location.host + "/db/record/" + name + "?notify=" + "Added relationships"});

	if (type == "parent") {
		cb.req("pclink",[value,parseInt(name),"record",ctxid]);
	} else if (type == "child") {
		cb.req("pclink",[parseInt(name),value,"record",ctxid]);
	}
}


function form_relationships_remove(formobj,type) {
	var nv=collectpubvalues_new(formobj)["p"];
	if (!nv) {return}
	var links = new Array();
	for (i in nv["parents"]) {
		links.push(parseInt(i));
	}
	form_relationships_remove_cb(null,[links, name, type]);
}

function form_relationships_remove_cb(r,cbargs) { // r=null .. cbargs = [parents, recid, type]
	var parents=cbargs[0];
	var recid=cbargs[1];
	var type=cbargs[2];

	//console.log(parents);
	
	if (parents.length > 0) {
		var parent=parents.shift();
		var cb = new CallbackManager();
		cb.setcbargs([parents,recid,type]);
		cb.register(form_relationships_remove_cb);

		if (type=="parents") {
			cb.req("pcunlink",[parent,recid,ctxid]);
		} else {
			cb.req("pcunlink",[recid,parent,ctxid]);
		}
		return
	}

	// change to refresh just parent tree and relationship editor	
	window.location = window.location.protocol + "//" + window.location.host + "/db/record/" + name + "?notify=" + "Removed relationships"
}


/***********************************************/


function form_addfile(formobj) {
	formobj.fname.value = formobj.filedata.value;
}


function form_addcomment(formobj) {
	comment = formobj.comment.value;
	if (!comment) {return}
	
	var cb = new CallbackManager();
	cb.register(function(r,cbargs) {window.location.reload()});
	cb.req("addcomment",[name,comment,ctxid]);
}


function form_checkrecorddef(formobj) {
	//collects values, validates, and adds recorddef
	var rv=collectpubvalues_new(formobj);
	if (!rv) {return}
	
	var r=rv["r"];
	var alerts = new Array();

	if (r["views"]["defaultview"]==undefined) {
		r["views"]["defaultview"] = r["mainview"];
	}
	
	if (r["name"]==undefined||r["name"]=="") {
		alerts.push("You must specify a name");
	}
	if (r["mainview"]==undefined||r["mainview"]=="") {
		alerts.push("You must describe the experimental protocol.");
	}
	if (r["views"]["tabularview"]==undefined||r["views"]["tabularview"]=="") {
		alerts.push("You must specify a table view.");
	}
	if (r["views"]["recname"]==undefined||r["views"]["recname"]=="") {
		alerts.push("You must specify a format for the record name.");
	}
	if (r["views"]["defaultview"]!=undefined&&r["views"]["defaultview"]=="") {
		alerts.push("A default view is required.");
	}
			
	if (alerts.length > 0) {
		topalert(alerts);
		return false
	} 

	return r
}	

function form_putrecorddef(formobj) {
	r=form_checkrecorddef(formobj);
	if (!r) {return}
	
	var cb = new CallbackManager();
	cb.setcbargs(r["name"]);
	cb.register(form_putrecorddef_cb)
	cb.req("putrecorddef",[r,ctxid]);	
}
function form_putrecorddef_cb(r,cbargs) {
	window.location = window.location.protocol + "//" + window.location.host + "/db/recorddef/" + cbargs + "?notify=Updated%20Protocol%20Definintion";
}

function form_addrecorddef(formobj) {
	r=form_checkrecorddef(formobj);
	if (!r) {return}

	var cb = new CallbackManager();
	cb.setcbargs([ r["parents"] , r["children"] ] );
	cb.register(form_addrecorddef_cb)
	cb.req("addrecorddef",[r,ctxid]);	
}
function form_addrecorddef_cb(r,cbargs) { // add links to new recorddef. r = recdef.name .. cbargs = [parents,children]
	var parents=cbargs[0];
	var children=cbargs[1];
	var recdefname = r;
	
	var cb = new CallbackManager();
	cb.register(form_addrecorddef_cb);
	
	if (parents.length > 0) {
		var parent=parents.shift();
		cb.setcbargs([parents,children]);
		cb.req("pclink",[parent,recdefname,"recorddef",ctxid]);
		return
	}
	if (children.length > 0) {
		var child=children.shift();
		cb.setcbargs([parents,children]);
		cb.req("pclink",[recdefname,child,"recorddef",ctxid]);	
		return
	}
	
	window.location = window.location.protocol + "//" + window.location.host + "/db/recorddef/" + r + "?notify=" + 7;

}