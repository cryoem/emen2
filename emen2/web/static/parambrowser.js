/*****************************/

function picker(param, type, elem, event) {
	if (type == "record") {
		param=parseInt(param);
	}

	this.names = new Object();
	this.stack = new Array();
	this.ttype = type || "record";
	this.param = param || 0;

	this.action = function() {}
	this.actiontext = "Select";

	this.callback = function() {}
	
	this.b2current = document.createElement("div");
	this.b2parents = document.createElement("div");
	this.b2children = document.createElement("div");
	this.b2buttons = document.createElement("div");
	this.b2current.className="b2current";
	this.b2parents.className="b2parents";
	this.b2children.className="b2children";
	this.b2buttons.className="b2buttons";
	
	this.owner = elem;
//	this.owner.onclick = null;
	
	
	var posx = 0;
	var posy = 0;
	if (!event) var event = window.event;
	if (event.pageX || event.pageY) 	{
		posx = event.pageX;
		posy = event.pageY;
	} else if (event.clientX || event.clientY) 	{
		posx = event.clientX + document.body.scrollLeft	+ document.documentElement.scrollLeft;
		posy = event.clientY + document.body.scrollTop + document.documentElement.scrollTop;
	}
		
	this.browser = document.createElement("div");
	this.browser.className = "newbrowser";
	this.browser.style.position = "absolute";
	this.browser.style.top = posy+"px";
	this.browser.style.left = posx+"px";
		
	document.body.appendChild(this.browser);
//	this.browser.clearChildren();
	
	this.browser.appendChild(this.b2parents);
	this.browser.appendChild(this.b2current);
	this.browser.appendChild(this.b2buttons);
	this.browser.appendChild(this.b2children);
	
	
	this.closebutton = document.createElement("img");
	this.closebutton.src = "/images/close.png";
	this.closebutton.className = "b2close";
	//this.closebutton.addEventListener('click', function(value,event) {this.close();}.bind(this), true)
	this.closebutton.onclick = function(value,event) {this.close();}.bind(this);
	
	this.browser.appendChild(this.closebutton);	
	
	this.set(this.param);
	return
}
picker.prototype.addchild = function(parent) {
	this.pclink(parent,this.param,ctxid);
}
picker.prototype.addparent = function(child) {
	this.pclink(this.param,child,ctxid);
}
picker.prototype.pclink = function(parent,child) {

	if (this.ttype == "record") {
		parent=parseInt(parent);
		child=parseInt(child);
	}

	var pclink = new CallbackManager();
	pclink.register(this.pclink_cb.bind(this));
	pclink.req("pclink",[parent,child,this.ttype,ctxid]);
}
picker.prototype.pclink_cb = function(r,cbargs) {
	// FIXME: move this callback into a more flexible system
	topalert("Added link");
	makeRequest("/db/parentmap/"+this.ttype+"/"+name,'zone_parentmap');
	makeRequest('/db/parentmap/record/'+name+'?edit=1&editboth=1','page_recordview_relationships');	
//	this.close();
}
picker.prototype.pcunlink = function(value) {
	
}
picker.prototype.set = function(value) {
	if (this.stack.indexOf(value) > -1) {
		this.stack = this.stack.slice(0,this.stack.indexOf(value)+1);
	} else {
		this.stack.push(value);
	}
	this.param = this.stack[this.stack.length-1];
	if (this.ttype == "record") { this.param = parseInt(this.param) }
	this.update();
}

picker.prototype.update = function() {

	// parents in stack
	for (var i=0;i<this.stack.length;i++) {
		// if there is no stored name..
		if (this.names[this.stack[i]] == null) {
			if (this.ttype == "record") {
				// if missing a recname, request it, and start again..
				var getrecnames = new CallbackManager();
				getrecnames.register(this.getrecnames.bind(this));
				getrecnames.register(function(r,cbargs) {this.update()}.bind(this));
				getrecnames.req("getrecnames", [ [parseInt(this.stack[i])], ctxid ]);
				return;
			} else {
				this.names[this.stack[i]]=this.stack[i];
			}
		}
	}
	

	clearChildren(this.b2parents);
//	this.b2parents.clearChildren();
	

	for (var i=0;i<this.stack.length;i++) {
		var d=document.createElement("div");
		var a=document.createElement("a");		
		a.innerHTML = this.names[this.stack[i]];

		// I hate IE
		//a.addEventListener('click', function(value,event) {this.set(value);}.bind(this,this.stack[i]), true)
		a.onclick = function(value,event) {this.set(value);}.bind(this,this.stack[i]);
		
		d.appendChild(a);
		this.b2parents.appendChild(d);
	}
	
//	param = this.stack[i-1];
	
	// show a parent if stack is just 1...
	if (this.stack.length==1) {
		var getparents = new CallbackManager();
		getparents.register(this.getparents.bind(this));
		getparents.req("getparents",[this.param,this.ttype,0,ctxid]);
	}

	var getparamdef = new CallbackManager();
 	getparamdef.register(this.getparamdef.bind(this));

	var getchildren = new CallbackManager();
	getchildren.register(this.getchildren.bind(this));
	
 	var getrecorddef = new CallbackManager();
 	getrecorddef.register(this.getrecorddef.bind(this));
	
	var getrecord = new CallbackManager();
	getrecord.register(this.getrecord.bind(this));
	
	if (this.ttype == "paramdef") {getparamdef.req("getparamdef",[this.param])}
	if (this.ttype == "recorddef") {getrecorddef.req("getrecorddef",[this.param,ctxid])}
	if (this.ttype == "record") {getrecord.req("getrecord",[this.param,ctxid])}

//	this.b2children.clearChildren();
	clearChildren(this.b2children);
	
	getchildren.req("getchildren",[this.param,this.ttype,0,ctxid]);
}

// map recnames into cache
picker.prototype.getrecnames = function (r,cbargs) {
	for (var i=0;i<r.length;i++) {
		this.names[r[i][0]] = r[i][1];
	}
}

picker.prototype.getrecord = function (r,cbargs) {
//	this.b2current.innerHTML = r;
//	console.log(r);
//	this.b2current.clearChildren();
	clearChildren(this.b2current);
	
	var created=document.createElement("div");
	var modified=document.createElement("div");
		
	created.innerHTML = "<h6>Created:</h6><p class='small'>" + r["creationtime"] + " -- " + r["creator"] + "</p>";
	modified.innerHTML = "<h6>Created:</h6><p class='small'>" + r["modifytime"] + " -- " + r["modifyuser"] + "</p>";

	this.b2current.appendChild(created);
	this.b2current.appendChild(modified);


	////////////////
	clearChildren(this.b2buttons);

	var ul=document.createElement("ul");
	ul.className = "b2action";
	
	var selectview=document.createElement("li");
	var select=document.createElement("button");
	selectview.className="b2action_select";
	select.innerHTML = this.actiontext;
	select.onclick = function() {this.select()}.bind(this);
	selectview.appendChild(select);
	ul.appendChild(selectview);
	
	var gotorecord=document.createElement("li");

//	var link2=document.createElement("button");
//	link2.innerHTML = "View: "+this.param;
//	link2.href = "/db/"+this.ttype+"/"+this.param;
//	gotorecord.appendChild(link2);

	var gotoroot=document.createElement("button");	
	gotoroot.onclick = function() {this.stack=new Array;this.set(0)}.bind(this);
	gotoroot.innerHTML = "&raquo; Go to root";
	gotorecord.appendChild(gotoroot);
	var gotospacer=document.createElement("span");
	gotospacer.innerHTML = " ";
	gotorecord.appendChild(gotospacer);

	var gotorecordbutton=document.createElement("button");
	this.gotorecordinput=document.createElement("input");
	this.gotorecordinput.size=6;
	this.gotorecordinput.value=this.param;
	gotorecordbutton.innerHTML="&raquo; Go to:";
	gotorecordbutton.onclick = function() {this.stack=new Array;this.set(this.gotorecordinput.value)}.bind(this);
	gotorecord.appendChild(gotorecordbutton);
	gotorecord.appendChild(this.gotorecordinput);

	ul.appendChild(gotorecord);



	this.b2buttons.appendChild(ul);
}

picker.prototype.select = function() {
	// return current value...
	this.action();
	this.close();
	this.callback();
}

picker.prototype.close = function() {
	document.body.removeChild(this.browser);
}

picker.prototype.getparamdef = function (r,cbargs) {
	this.b2current = r;
}

picker.prototype.getrecorddef = function (r,cbargs) {
	this.b2current = r;
}

picker.prototype.getparents = function (r,cbargs) { 
	clearChildren(this.b2parents);
	
	if (r.length==0) {return}

	// fetch recnames before continuing, if necessary
	if (this.ttype == "record") {
		var getnames=new Array();
		for (var i=0;i<r.length;i++) {
			if (this.names[r[i]] == null) { getnames.push(parseInt(r[i])); }
		}
		if (getnames.length > 0) {
			var getrecnames = new CallbackManager();
			getrecnames.register(this.getrecnames.bind(this));
			getrecnames.register(this.getparents.bind(this, r));
			getrecnames.req("getrecnames", [ getnames, ctxid ]);
			return
		}
	} else {
		for (var i=0;i<r.length;i++) {
			this.names[r[i]] = r[i];
		}
	}
	
	this.stack.unshift(r[0]);
	this.update();

}

picker.prototype.getchildren = function (r,cbargs) { 

	// fetch recnames before continuing, if necessary
	if (this.ttype == "record") {
		var getnames=new Array();
		for (var i=0;i<r.length;i++) {
			if (this.names[r[i]] == null) { getnames.push(parseInt(r[i])); }
		}
		if (getnames.length > 0) {
			var getrecnames = new CallbackManager();
			getrecnames.register(this.getrecnames.bind(this));
			getrecnames.register(this.getchildren.bind(this, r));
			getrecnames.req("getrecnames", [ getnames, ctxid ]);
			return
		}
	} else {
		for (var i=0;i<r.length;i++) {
			this.names[r[i]] = r[i];
		}
	}

//	this.b2children.clearChildren();
	clearChildren(this.b2children);

	var ul=document.createElement("ul");
	for (var i=0;i<r.length;i++) {
		var li=document.createElement("li");
		var a=document.createElement("span");
		a.innerHTML = this.names[r[i]];
		//a.addEventListener('click', function(value,event) {this.set(value);}.bind(this,r[i]), true)
		a.onclick = function(value,event) {this.set(value);}.bind(this,r[i]);

		li.appendChild(a);
		ul.appendChild(li);
	}
	this.b2children.appendChild(ul);
}

function picker_pcunlink(parent,child,type) {
	// not elegant but simplifies things elsewhere...
	if (type == "record") {
		parent=parseInt(parent);
		child=parseInt(child);
	}
	
	var answer = confirm("Remove link between "+parent+" and "+child+" ?")
	if (answer) {
		var pclink = new CallbackManager();
		pclink.register(picker_pcunlink_cb);
		pclink.setcbargs([type]);
		pclink.req("pcunlink",[parent,child,ctxid,type]);
	}
}
function picker_pcunlink_cb(r,cbargs) {
	topalert("Removed link.");
	makeRequest("/db/parentmap/"+cbargs[0]+"/"+name,'zone_parentmap');
	makeRequest('/db/parentmap/record/'+name+'?edit=1&editboth=1','page_recordview_relationships');		
}