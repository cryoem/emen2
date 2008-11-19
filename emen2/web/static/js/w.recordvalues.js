/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////


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

		//console.log(this.now);
		
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

		//console.log("t");
		if (this.rootless==0) {
			$(cl,this.root).each( function(i) {
//				console.log(z);
				ws.push(new widget(this, {controls:0,popup:0,show:1}));
			});
		} else {
		
			$(cl).each( function(i) {
		//console.log("Z2");

				ws.push(new widget(this, {controls:0,popup:0,show:1}));
			});			
		}

		//console.log("Z");

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
		
		if (allcount==0) changed[NaN]={};
		if (allcount==0 && self.newrecord==0) {
			notify("No changes made");
			return
		} else {
			//console.log("commit callback");
			this.savebutton.val("Saving...");
			//console.log(this.commitcallback);
			this.commitcallback(this,changed);
		}


	},
	
	revert: function() {
		//console.log("revert");
		$(this.ws).each(function(i){
			this.revert();
			//this.remove();
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



/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////


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

		if (paramdefs[this.param] == null) {
			return
		}

		if (paramdefs[this.param]["vartype"]=="text") {

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
		
		} else {

			this.editw=$('<input class="value" size="30" type="text" value="'+this.value+'" />');

			// autocomplete only for string vartype
			if (paramdefs[this.param]["vartype"]=="string") {
				this.editw.autocomplete({ 
					ajax: "/db/findvalue/"+this.param+"/",
					match: function(typed) { return this[1].match(new RegExp(typed, "i")) },				
					insertText: function(value)  { return value[1] }
				}).bind("activate.autocomplete", function(e,d) {  }
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

		//if (this.popup) {this.popup.hide()}
				
		this.w.siblings(".editable").show();
		this.w.remove();		
	},
	
	////////////////////////	
	save: function() {
		
		//if (this.popup) {this.popup.hide()}
		
		var save=$(":submit",this.w);
		save.val("Saving...");

		var recid=this.recid;
		var param=this.param;
	
		$.jsonRPC("putrecordvalue",[recid,this.param,this.getval(),ctxid],
	 		function(json){
				setvalue(recid,param,json);
	 			//rec[this.param]=json;
	 			//record_view_reload(recid,switchedin["recordview"]);
				// ian: just reload the page instead of trying to update everything.. for now..
				notify_post(window.location.pathname, ["Changes Saved"]);
				//notify("Changes saved");
	 		},
			function(xhr){
				//ole.log("error, "+xhr.responseText);
				//editelem_revert(elem,key);
				//$("#alert").append("<li>Error: "+this.param+","+xhr.responseText+"</li>");
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
			var item=$('<li></li>');
			var edit=$('<input type="text" value="'+v+'" />');
			
			if (self.paramdef["vartype"]=="userlist") {

				edit.autocomplete({ 
					ajax: "/db/finduser/",
					match:      function(typed) { return this[1].match(new RegExp(typed, "i")); },				
					insertText: function(value)  { return value[0] },
					template:   function(value)  { return "<li>"+value[1]+" ("+value[0]+")</li>"}
				}).bind("activate.autocomplete", function(e,d) {  });

			} else if (self.paramdef["vartype"]=="stringlist") {

				edit.autocomplete({ 

					ajax: "/db/findvalue/"+this.param+"/",
					match:      function(typed) { return this[1].match(new RegExp(typed, "i")); },				
					insertText: function(value)  { return value[1] }
					
				}).bind("activate.autocomplete", function(e,d) {  })
				
			}
			
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