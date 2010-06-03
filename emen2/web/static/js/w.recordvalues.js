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
		this.recid = parseInt(this.elem.attr("data-recid")) || null;
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
		
		} else if (["intlist","floatlist","stringlist","userlist"].indexOf(pd["vartype"]) > -1) {
		
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
