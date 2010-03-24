/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////


multiwidget = (function($) { // Localise the $ function

function multiwidget(elem, opts) {
  this.elem = $(elem);
	var self = this.elem.data("ref");

	// init
	if (!self) {
		this.elem.data("ref",this);		

  	if (typeof(opts) != "object") opts = {};

  	$.extend(this, multiwidget.DEFAULT_OPTS, opts);
		this.init();
		self=this;
	}

};

multiwidget.DEFAULT_OPTS = {
	newrecord: 0,
	popup: 0,
	controls: 1,
	controlsroot: null,
	ext_save: null,
	ext_cancel: null,
	ext_elems: null,
	restrictparams: null,
	display: 0,
	recid: null,
	root: null,
	widgetopts_hide: {controls:1,popup:1,display:0,inplace:1},
	widgetopts_show: {controls:0,popup:1,display:0,inplace:0},
	save_callback: function(self,changed) {self.save_default_callback(self,changed)},
	commit_callback: function(self,r) {self.commit_default_callback(r)},
	commit_errback: function(self,r) {self.commit_default_errback(r)}
};

multiwidget.prototype = {
		
	init: function() {
		//console.log("multiwidget init");

		var self=this;
		this.built = 0;
		this.trygetparamdef = 0;
		this.paramdefs=[];
		this.elems = [];

		if (!this.ext_elems) {
			this.ext_elems = $(".editable",this.root);
		}
		
		this.bindeditable();
		this.bind();


		if (this.display) {
			this.build(1);
		}
		
		if (!this.controlsroot) {
			this.controlsroot=this.elem;
		}

	},
	
	bindeditable: function() {
		//console.log("multiw bindeditable");		
		
		var self=this;
		this.ext_elems.each(function(){
			self.elems.push(new widget($(this),self.widgetopts_hide));
			self.paramdefs.push($(this).attr("data-param"));
		});
	},
	
	bind: function() {
		//console.log("multiw bind");
		if (this.controls) {
			var self=this;
			this.elem.one("click",function(e){e.stopPropagation();self.event_click(e)});
		}
	},
	
	bind_save: function() {
		if (this.ext_save) {
			var self=this;
			this.ext_save.one("click", function(e){
				e.stopPropagation();self.event_save(e)
				});
		}
	},

	event_click: function(e) {
		this.show();
	},

	event_save: function(e) {
		this.ext_save.val("Committing...");
		this.save();
	},
	
	event_cancel: function(e) {
		this.hide();
	},
		
	build: function(show) {
		//console.log("multiw build");

		
		var self=this;
		if (this.trygetparamdef==0) {
			this.trygetparamdef = 1;
			var getpd = [];
			for (var i=0;i<this.paramdefs.length;i++) {
				if (!paramdefs[this.paramdefs[i]]) { getpd.push(this.paramdefs[i]) }
			}
			if (getpd.length) {
				getparamdefs(getpd,function(){self.build(show)});
				return
			}
		}
		
		if (this.built){return}
				
		this.built = 1;
		
		if (this.controls) {
			this.c_edit = $(".jslink",this.controlsroot);
			
			this.ext_save = $('<input type="submit" value="Save" />');

			this.ext_cancel = $('<input type="button" value="Cancel" />');

			this.c_box = $('<span />');
			this.c_box.append(this.ext_save,this.ext_cancel);
			this.controlsroot.append(this.c_box);
		}
		
	
		this.bind_save();
	
		if (this.ext_cancel) {
			var self=this;
			this.ext_cancel.bind("click", function(e){
				e.stopPropagation();self.event_cancel(e)
				});
		}

		
		if (show) {this.show()}
		
	},
	
	show: function() {
		//console.log("multiw show");
		
		if (!this.built) {
			this.build(1)
			return
		}
				
		var self=this;
				
		$.each(this.elems, function(){
			this.reset_opts(self.widgetopts_show);
			this.show();
		});

		if (this.controls) {
			this.c_edit.hide();
			this.c_box.show();
			this.bind();
		}
				
	},
	
	hide: function() {
		//console.log("multiw hide");
		
 		if (this.controls) {
			this.c_box.hide();
 			this.c_edit.show();
 		}
		var self=this;

		$.each(this.elems,function(){
			this.hide();
			this.reset_opts(self.widgetopts_hide);
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
			if (this.changed) {
				if (!changed[this.recid]) {changed[this.recid]={}}
				changed[this.recid][this.param]=this.getval();
			} else {
				// console.log(this.param+" is unchanged; value is "+this.getval());
			}
		});
		
		this.save_callback(this, changed);
		
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
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////


widget = (function($) { // Localise the $ function

function widget(elem, opts) {

	this.elem = $(elem);
	this.opts=opts;
	if (typeof(opts) != "object") opts = {};
	$.extend(this, widget.DEFAULT_OPTS, opts);
	this.init();

};

widget.DEFAULT_OPTS = {
	popup: 0,
	inplace: 0,
	controls: 0,
	display: 0
};

widget.prototype = {

	init: function() {
		//console.log("w init");
		
		this.changed=0;
		this.built=0;
		this.trygetparamdef=0;
		this.bind();
		
		var self=this;

		var props=this.getprops();
		this.param=props.param;
		this.recid=props.recid;
		this.value=getvalue(this.recid,this.param);
		
		
		if (this.display) {
			this.build(this.show);
		}
		
	},
	
	event_click: function(e) {
		this.show();
	},
	
	bind: function() {
		//console.log("w bind");

		var self=this;
		this.elem.click(function(e) {self.event_click(e)});
	},
	
  build: function(show) {
		//console.log("w build");

		if (this.built){return}

		this.built=1;
		

		// replace this big switch with something better
		if (paramdefs[this.param] == null) {
			return
		}

		if (this.value == null) {
			this.value = "";
		}

		var self=this;

		// container
		this.w = $('<span class="widget"></span>');
		if (this.inplace) {
			this.w.addClass("widget_inplace");
		}

		if (paramdefs[this.param]["vartype"]=="html") {
			this.editw=$('<textarea class="value" cols="80" rows="20">'+this.value+'</textarea>');
			this.editw.change(function(){self.changed=1;});
			this.w.append(this.editw);				
			

		} else if (paramdefs[this.param]["vartype"]=="text") {

			this.editw=$('<textarea class="value" cols="80" rows="20">'+this.value+'</textarea>');
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
			//this.popup=new DateInput(this.editw);
			this.editw.change(function(){self.changed=1;});
			this.w.append(this.editw);				

		} else if (paramdefs[this.param]["vartype"]=="boolean") {
		
			this.editw=$("<select><option>True</option><option>False</option></select>");
			this.editw.change(function(){self.changed=1;});
			this.w.append(this.editw);				
		
		} else if (["intlist","floatlist","stringlist","userlist"].indexOf(paramdefs[this.param]["vartype"]) > -1) {

			this.editw = new listwidget(this.w,{values:this.value,paramdef:paramdefs[this.param]});
			//needs comparison to see if changed
			this.changed=1;
			//this.editw.change(function(){self.changed=1;});
		
		}  else if (paramdefs[this.param]["vartype"]=="user") {

				this.editw=$('<input class="value" size="30" type="text" value="'+this.value+'" />');
				// this.editw.autocomplete({ 
				// 	ajax: EMEN2WEBROOT+"/db/find/user/",
				// 	match:      function(typed) { return true },				
				// 	insertText: function(value)  { return value[0] },
				// 	template:   function(value)  { return "<li>"+value[1]+" ("+value[0]+")</li>"}
				// }).bind("activate.autocomplete", function(e,d) {  });
				// this.editw.change(function(){self.changed=1;});

				this.editw.autocomplete( EMEN2WEBROOT+"/db/find/user/", { 
					minChars: 0,
					max: 1000,
					matchSubset: false,
					scrollHeight: 360,
					highlight: false,
					formatResult: function(value, pos, count)  { return value }			
				});
				this.editw.blur(function(e,d) {		//bind("onblur", function(e,d) {
					self.changed = 1;
				});
				
				this.w.append(this.editw);			

		} else {

			this.editw=$('<input class="value" size="30" type="text" value="'+this.value+'" />');
			
			if (paramdefs[this.param]["vartype"]=="string") {

				var l=null;
				if (paramdefs[this.param]["choices"] != null) {
					l=$(paramdefs[this.param]["choices"]).map(function(n){return [[n,this]]})
				} 
								
				this.editw.autocomplete( EMEN2WEBROOT+"/db/find/value/"+this.param+"/", { 
					minChars: 0,
					max: 100,
					matchSubset: false,
					scrollHeight: 360,
					formatResult: function(value, pos, count)  { return value }			
				});
				this.editw.blur(function(e,d) {		//bind("onblur", function(e,d) {
					self.changed = 1;
				}
				)

			}

			this.editw.change(function(){self.changed=1});			
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
			this.c_controls=$('<div class="controls"></div>').append(
				$('<input type="submit" value="Save" />').one("click", function(e) {e.stopPropagation();self.save()}),
				$('<input type="button" value="Cancel" />').bind("click", function(e) {e.stopPropagation();self.hide()})
				//$('<input type="submit" value="Save" />').click(function(e) {e.stopPropagation();self.save()}),
				//$('<input type="button" value="Cancel" />').click(function(e) {e.stopPropagation();self.hide()})
			);
			this.w.append(this.c_controls);
		}


		$(this.elem).after(this.w);
		//$(this.elem).css("color","white");
		//$(this.elem).hide();

		//if (this.popup) {
		//	this.edit.focus();
		//	this.edit.select();
		//}
		if (show){this.show()}
		
	},
	
	show: function() {
		//console.log("w show");

		var self=this;

		if (!paramdefs[this.param] && this.trygetparamdef==0) {
			this.trygetparamdef=1;
			getparamdefs([this.param],function(){self.show()});
			return
		}
		
		if (!this.built) {this.build()}
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
	
	reset_opts: function(opts) {
		//console.log("w reset_opts");
		this.remove();
		this.set_opts(widget.DEFAULT_OPTS);
		this.set_opts(this.opts);
		this.set_opts(opts);
	},
	
	set_opts: function(opts) {
		if (typeof(opts) != "object") opts = {};
		$.extend(this, opts);
	},

	////////////////////////
	getprops: function() {
		var prop=new Object();
		prop.recid=parseInt(this.elem.attr("data-recid"));
		prop.param=this.elem.attr("data-param");
		if (!prop.recid) {prop.recid=recid}
		return prop
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
			function(xhr){
				notify("Error: "+this.param+","+xhr.responseText);
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
/////////////////////////////////////////////
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
			var item=$('<li class="widget_list"></li>');
			var edit=$('<input type="text" value="'+v+'" />');
						
			if (self.paramdef["vartype"]=="userlist") {

				// edit.autocomplete({ 
				// 	ajax: EMEN2WEBROOT+"/db/find/user/",
				// 	match:      function(typed) { return true },				
				// 	insertText: function(value)  { return value[0] },
				// 	template:   function(value)  { return "<li>"+value[1]+" ("+value[0]+")</li>"}
				// }).bind("activate.autocomplete", function(e,d) {  });

				edit.autocomplete( EMEN2WEBROOT+"/db/find/user/", { 
					minChars: 0,
					max: 1000,
					matchSubset: false,
					scrollHeight: 360,
					highlight: false,
					formatResult: function(value, pos, count)  { return value }			
				});
				edit.blur(function(e,d) {		//bind("onblur", function(e,d) {
					//self.changed = 1;
				});

			} else if (self.paramdef["vartype"]=="stringlist") {

				// edit.autocomplete({ 
				// 
				// 	ajax: EMEN2WEBROOT+"/db/find/value/"+this.param+"/",
				// 	match:      function(typed) { return this[1].match(new RegExp(typed, "i")); },				
				// 	insertText: function(value)  { return value[1] }
				// 	
				// }).bind("activate.autocomplete", function(e,d) {  })

				edit.autocomplete( EMEN2WEBROOT+"/db/find/value/"+self.paramdef["name"]+"/", { 
					minChars: 0,
					max: 100,
					matchSubset: false,
					scrollHeight: 360,
					formatResult: function(value, pos, count)  { return value }			
				});
				edit.blur(function(e,d) {		//bind("onblur", function(e,d) {
					//self.changed = 1;
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
		return new listwidget(this, opts);
	});
};

return listwidget;

})(jQuery); // End localisation of the $ function
