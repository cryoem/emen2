/*****************************/

 

function combobox(elem,cache,force) { // inspiration drawn from a few places.. refined based on facebook typeahead
	this.keyed = 0;
	this.selectedindex=-1;
	this.force=force;
	this.elem = elem;
	this.cache = cache;
	this.results = new Array();
	this.list = document.createElement("div");
	this.list.className = "combobox_items";
	this.elem.parentNode.appendChild(this.list);
	
	this.elem.onfocus = this.onfocus.bind(this);
	this.elem.onblur = this.onblur.bind(this);
	this.elem.onkeyup = this.onkeyup.bind(this);
	this.elem.onkeydown = this.onkeydown.bind(this);
	this.elem.onkeypress = this.onkeypress.bind(this);
	
//  this.elem.addEventListener('focus', this.onfocus.bind(this), true);
//  this.elem.addEventListener('blur', this.onblur.bind(this), true);
//	this.elem.addEventListener('keyup', this.onkeyup.bind(this), true);
//	this.elem.addEventListener('keydown', this.onkeydown.bind(this), true);
//	this.elem.addEventListener('keypress', this.onkeypress.bind(this), true);

	this.show();

}
combobox.prototype.show = function() {
	this.refresh();
	this.list.style.display = "block";
}
combobox.prototype.hide = function() {
	if (this.force && !this.results[this.selectedindex]) {
		this.elem.value="";
	}
	this.list.style.display="none";
}
combobox.prototype.onblur = function(event) {
	this.hide();
}
combobox.prototype.onfocus = function(event) {
	this.keyed = 0;
	this.show();
}
combobox.prototype.onkeydown = function(event) {
	this.keyed = 1;

	var keycode;
	if (window.event) keycode = window.event.keyCode;
	else if (e) keycode = e.which;

  switch (keycode) {
    case 9: // tab
    case 13: // enter
      if (this.results[this.selectedindex]) {
        this.hide();
        event.preventDefault();
      }
      break;

    case 38: // up
      this.select(this.selectedindex - 1);
      event.preventDefault();
      break;

    case 40: // down
      this.select(this.selectedindex + 1);
      event.preventDefault();
      break;
  }	
}
combobox.prototype.onkeyup = function(event) {
	var keycode;
	if (window.event) keycode = window.event.keyCode;
	else if (e) keycode = e.which;

  switch (keycode) {    case 27: // escape
      this.hide();
      break;

    case 0:
    case 13: // enter
    case 37: // left
    case 38: // up
    case 39: // right
    case 40: // down
      break;

    default:
      this.refresh();
      break;
  }	
}

combobox.prototype.onkeypress = function(event) {
	var keycode;
	if (window.event) keycode = window.event.keyCode;
	else if (e) keycode = e.which;

  switch (keycode) {    case 13: // return
    case 38: // up
    case 40: // down
      event.preventDefault();
      break;
  }
}
combobox.prototype.refresh = function() {
  // Search the list of potential results and find ones that match what we have so far
  var results = new Array();
  var value = this.elem.value.toLowerCase();
	if (this.keyed == 0) {value = ""}

  for (var i = 0; i < this.cache.length; i++) {
    if (this.cache[i][0].toLowerCase().indexOf(value) > -1 || this.cache[i][1].toLowerCase().indexOf(value) > -1) {
      results.push(this.cache[i]);
    }
  }

	while (this.list.firstChild) {this.list.removeChild(this.list.firstChild)};	

  // Generate a list to display the elements to the user
  for (var i = 0; i < results.length; i++) {
		var d=document.createElement('div');
		d.innerHTML = results[i][1];
		
		//d.addEventListener('mousedown', function(event) {this[0].selectedindex=this[1];this[0].set(results[this[1]][0])}.bind([this,i]), true)
		d.onmousedown = function(event) {this[0].selectedindex=this[1];this[0].set(results[this[1]][0])}.bind([this,i])

		this.list.appendChild(d);
   }
  this.results = results;	
}
combobox.prototype.set = function(value) {
	this.elem.value=value;
}
combobox.prototype.select = function(index) {
}












/********************************************/

function getselectchoice(obj) {
	//replace into formelementgetvalue
	var r = new Array();
	for (var i=0;i<obj.length;i++) {
    if (obj.options[i].selected) {
			r.push(obj.options[i].text);
		}
  }
	return r;
}

function checkall(formobj) {
	for (var i=0;i<formobj.length;i++) {
		if (formobj[i].type == "checkbox") {
			formobj[i].checked = 1;
		}
	}
}
function uncheckall(formobj) {
	for (var i=0;i<formobj.length;i++) {
		if (formobj[i].type == "checkbox") {
			formobj[i].checked = 0;
		}
	}
}

function input_moreoptions_text(elem) {
	var target=elem.parentNode;
	var i=target.getElementsByTagName("input");
	var expanded = i[0].name.split("___");
	expanded[4] = i.length+1;
	var n=document.createElement("input");
	n.type = "text";
	n.name=expanded.join("___");
	var n2=document.createElement("br");
	target.appendChild(n2); 
	target.appendChild(n); 	
}	

function input_moreoptions_select(elem) {
	var target=elem.parentNode;
	var i=target.getElementsByTagName("select");
	var expanded = i[0].name.split("___");
	expanded[4] = i.length+1;	
	var n=i[0].cloneNode(1);
	n.name=expanded.join("___");
	var n2=document.createElement("br");
	target.appendChild(n2);
	target.appendChild(n);
}

function input_moreoptions_combobox(elem) {
	var target=elem.parentNode;
	var i=target.getElementsByTagName("input");
	var expanded = i[0].name.split("___");
	expanded[4] = i.length+1;
	var n=i[0].cloneNode(1);
	n.name=expanded.join("___");
	n.value="";
	var n2=document.createElement("br");
	var n3=document.createElement("span");
	n3.appendChild(n);
	target.appendChild(n2);
	target.appendChild(n3);
}


function formelementgetvalue(elem) {
	var value;
	if (elem.type == "select-multiple") {
		value = new Object();
		for (var i = 0; i < elem.options.length; i++) {
			if (elem.options[i].selected) { value[elem.options[i].value]=1 }
		}
	} else if (elem.type == "checkbox") {
		if (elem.checked) { value = 1 } else { value = 0 }
	} else {
		value = elem.value;
	}
	if (value==""){value=null}
	return value;
}


function validate_date(date) {
	var sp = date.split(" ");
	var sd = sp[0].split("/");
	var st=0;
	if (sp.length>1) {st=sp[1].split(":")}
	if (st.length<3) {throw RangeError}
	var year=parseInt(sd[0]);
	if (sd[0].length != 4) {throw RangeError}
	var month=parseInt(sd[1]);
	if (month > 12 || sd[1].length != 2) {throw RangeError}
	var day=parseInt(sd[2]);
	if (day > 31 || sd[1].length != 2) {throw RangeError}
	if (st) {
		if (st.length<3){throw RangeError};
		var hours=parseInt(st[0]);
		if (hours>23 || st[0].length != 2){throw RangeError}
		var minutes=parseInt(st[1]);
		if (minutes>59 || st[1].length != 2){throw RangeError}
		var seconds=parseInt(st[2]);
		if (seconds>59 || st[2].length != 2){throw RangeError}
	}
	return date
}
function validate_float(f) {
	var r=parseFloat(f);
	if (isNaN(r)) {throw TypeError}
	return f
}
function validate_int(i) {
	var r=parseInt(i);
	if (isNaN(r)) {throw TypeError}
	return r
}
function validate_bool(b) {
	var b = parseInt(b);
	if (b>1||b<0) {throw TypeError}
	return b
}

function collectpubvalues_new(formobj) {
	var r = new Object();
	r["r"] = new Object();
	r["p"] = new Object();
	var alerts=new Array();
	
	for (var i=0;i<formobj.elements.length;i++) {
		var expanded = formobj.elements[i].name.split("___");
		var e = formobj.elements[i];
		var ekind = expanded[0] || "r";
		var ename = expanded[1];
		var etype = expanded[2] || "string";
		var elist = parseInt(expanded[3]) || 0;
		var epos = expanded[4] || null;
		
		if (e.disabled||e.type=="button") {continue}
		
		if ( (elist) && (!r[ekind][ename])) {
			if (etype=="floatlist"||etype=="stringlist"||etype=="intlist"||etype=="userlist") {
					r[ekind][ename] = new Array();
			} else {
					r[ekind][ename] = new Object();
			}
		}

// # 	"int":("d",lambda x:int(x)),			# 32-bit integer
// # 	"longint":("d",lambda x:int(x)),		# not indexed properly this way
// # 	"float":("f",lambda x:float(x)),		# double precision
// # 	"longfloat":("f",lambda x:float(x)),	# arbitrary precision, limited index precision
// # 	"choice":("s",lambda x:str(x)),			# string from a fixed enumerated list, eg "yes","no","maybe"
// # 	"string":("s",lambda x:str(x)),			# a string indexed as a whole, may have an extensible enumerated list or be arbitrary
// # 	"text":("s",lambda x:str(x)),			# freeform text, fulltext (word) indexing
// # 	"time":("s",lambda x:str(x)),			# HH:MM:SS
// # 	"date":("s",lambda x:str(x)),			# yyyy/mm/dd
// # 	"datetime":("s",lambda x:str(x)),		# yyyy/mm/dd HH:MM:SS
// # 	"intlist":(None,lambda y:map(lambda x:int(x),y)),		# list of integers
// # 	"floatlist":(None,lambda y:map(lambda x:float(x),y)),	# list of floats
// # 	"stringlist":(None,lambda y:map(lambda x:str(x),y)),	# list of enumerated strings
// # 	"url":("s",lambda x:str(x)),			# link to a generic url
// # 	"hdf":("s",lambda x:str(x)),			# url points to an HDF file
// # 	"image":("s",lambda x:str(x)),			# url points to a browser-compatible image
// # 	"binary":("s",lambda y:map(lambda x:str(x),y)),				# url points to an arbitrary binary... ['bdo:....','bdo:....','bdo:....']
// # 	"binaryimage":("s",lambda x:str(x)),		# non browser-compatible image requiring extra 'help' to display... 'bdo:....'
// # 	"child":("child",lambda y:map(lambda x:int(x),y)),	# link to dbid/recid of a child record
// # 	"link":("link",lambda y:map(lambda x:int(x),y)),		# lateral link to related record dbid/recid
// # 	"boolean":("d",lambda x:int(x)),
// # 	"dict":(None, lambda x:x)
// # user
// # userlist


		var value=formelementgetvalue(e);
		if (value!=null) {
			if (etype=="int"||etype=="longint"||etype=="intlist") {
				try{value=validate_int(value)} catch(error) {alerts.push(ename+": invalid integer.")}

			}	else if (etype=="float"||etype=="longfloat"||etype=="floatlist") {
				try{value=validate_float(value)} catch(error) {alerts.push(ename+": invalid float.")}

			}	else if (etype == "choice") {

			} else if (etype=="string"||etype=="text") {

			} else if (etype=="boolean") {
				try{value=validate_bool(value)} catch(error) {alerts.push(ename+": invalid choice.")}
				
			} else if (etype == "dict") {

			} else if (etype == "datetime"||etype=="time"||etype=="date") {
				try{value=validate_date(value)} catch(error) {alerts.push(ename+": invalid date format.")}

			} else {
				// url, hdf, image, binary, binaryimage, child, link
			}
		
			if (elist&&epos!=null) {
				if (etype=="floatlist"||etype=="stringlist"||etype=="intlist"||etype=="userlist") {
					r[ekind][ename].push(value);
				} else {
					r[ekind][ename][epos] = value;
				}
			} else {
					r[ekind][ename] = value;
			}
		}
		
	}

	if (alerts.length > 0) {
		topalert(alerts);
		return 0
	} 
	return r
}