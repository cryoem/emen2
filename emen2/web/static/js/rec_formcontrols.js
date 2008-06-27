// js is stupid at sorting.
function sortNumber(a, b) {
	return a - b;
}

var edit=0;



function notify(msg) {
	$("#alert").empty();
	var msg=$('<li>'+msg+'</li>');
	$("#alert").append(msg).fadeIn();
	setTimeout(function(){msg.fadeOut()},3000)
}

function updatecomments() {
	elem=$("#page_comments_commentstext");
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

function reload_record_view(view) {
	if (!view) {view="defaultview"}

	$("#page_recordview_"+view+" .view").load("/db/recordview/"+recid+"/"+view,{},	function(data){editelem_makeeditable();});
	
	//$.get("/db/recordview/"+recid+"/"+view,{},	function(data){
	//	$("#page_recordview_"+view+" .view").html(data);	
	//	editelem_makeeditable();
	//});

}

function jsonrpccallback(json){}

function jsonrpcerror(xhr){
	//console.log("error, "+xhr.responseText);
	$("#alert").append("<li>Error: "+param+","+xhr.responseText+"</li>");
}





$(document).ready(function() {
		editelem_makeeditable();
		$("#page_comments_commentstext").addcomment()
});


function editelem_revertview(page,view) {
	if (!view) {view="defaultview"}
	$(page).load("/db/recordview/"+recid+"/"+view,{},	function(){editelem_makeeditable()});
}


function editelem_makeeditable() {
	$('.editable').widget();
	$('.page_recordview').widget_page();
	//$(".page_recordview").each( function(i) {
		//
	//});

}



//////////////////////////////////////////


addcomment = (function($) { // Localise the $ function

function addcomment(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, widget_page.DEFAULT_OPTS, opts);
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

		var cr=rec["comments"].reverse();

		$.each(cr, function() {
			var dname=this[0];
			if (displaynames[user]!=null) {
				var dname = displaynames[user];
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
		console.log("saving comment");
		console.log(this.edit.val());
		var self=this;
		
		
		$.jsonRPC("addcomment",[recid,this.edit.val(),ctxid],
	 		function(json){
				console.log(json);
				rec["comments"]=json;
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


//////////////////////////////////////////


widget_page = (function($) { // Localise the $ function

function widget_page(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, widget_page.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
console.log(elem);
};

widget_page.DEFAULT_OPTS = {
	popup: 0,
	controls: 0,
	now: 0
};

widget_page.prototype = {
	
	init: function() {
		console.log("init");
		this.elem.children("input").remove();
		this.editcontrol=$('<input class="editbutton" type="button" value="Edit" />').click(this.bindToObj(function(e) {e.stopPropagation();this.build()}));
		console.log(this);
		this.elem.append(this.editcontrol);	
		if (this.now) {
			this.build();
			}	
	},
	
  build: function() {
		//console.log(this.elem);
		var ws=[];
		
		this.editcontrol.remove();
	
		$(".editable",this.elem).each( function(i) {
			ws.push(new widget(this, {controls:0,popup:0,show:1}));
		});

		console.log(ws);
		this.ws = ws;
	
		this.savebutton=$('<input type="button" value="Save" />').click(this.bindToObj(function(e) {e.stopPropagation();this.save()}));
		this.cancel=$('<input type="button" value="Cancel" />').click(this.bindToObj(function(e) {e.stopPropagation();this.revert()}));

		$(this.elem).append(this.savebutton,this.cancel);		
	},
	
	////////////////////////////
	save: function() {
		var changed={}
		var count=0;
		$(this.ws).each(function(i){

			var param=this.param;
			var value=this.getval();

	 		if (rec[param]==null && value != "" && value != null) {
	 			console.log("new value "+param+"; orig is null");
				changed[param]=value;
				count+=1;
	 		}
			if (rec[param]!=null && value == null) {
				console.log("unsetting "+param);
				changed[param]=null;
				count+=1;
	 		}
	 		else if (rec[param]!=value) {
	 			console.log("changed: "+param+" , "+rec[param]+" , "+value);
				changed[param]=value;
				count+=1;
	 		}

		});
		console.log(changed);
		console.log(changed.length);
		
		if (count==0) {console.log("no changes made..");}
		else {
			this.commit(changed);
		}
	},
	
	revert: function() {
		console.log("revert");
		$(this.ws).each(function(i){
			this.revert();
		});
		this.init();
	},
	
	commit: function(values) {

		console.log("committing..");
		console.log(values);
	
		$.jsonRPC("putrecordvalues",[recid,values,ctxid],
	 		function(json){
				console.log(json);
				rec=json;
	 			//rec[this.param]=json;
	 			reload_record_view(switchedin["recordview"]);
				notify("Changes saved");
	 		},
			function(xhr){
				//ole.log("error, "+xhr.responseText);
				//editelem_revert(elem,key);
				$("#alert").append("<li>Error: "+this.param+","+xhr.responseText+"</li>");
			}
		)	
				
	},
	
	///////////////////////
  bindToObj: function(fn) {
    var self = this;
    return function() { return fn.apply(self, arguments) };
  }	
	
}

$.fn.widget_page = function(opts) {
  return this.each(function() {
		new widget_page(this, opts);
	});
};

return widget_page;

})(jQuery); // End localisation of the $ function



//////////////////////////////////////////


widget = (function($) { // Localise the $ function

function widget(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, widget.DEFAULT_OPTS, opts);
  
  this.elem = $(elem);
  //this.bindMethodsToObj("show", "hide", "hideIfClickOutside", "selectDate", "prevMonth", "nextMonth", "prevYear", "nextYear");
  
  this.init();
	if (this.show) {
		this.build();
	}
};

widget.DEFAULT_OPTS = {
	popup: 1,
	controls: 1,
	show: 0
};

widget.prototype = {
	init: function() {
		this.elem.click(this.bindToObj(function(e) {e.stopPropagation();this.build()}));
	},
	
  build: function() {
		//console.log("building...");
				
		this.param=this.getparamname();
		
		// accessing global var of paramdefs cache
		this.pd=paramdefs[this.param];
		this.vt=this.pd["vartype"];				

		this.value=rec[this.param];
		if (this.value==null) {
			this.value="";
		}

		this.w = $('<span class="widget"></span>');
		this.edit = $('<input />');

		if (this.vt=="text") {

			this.edit=$('<textarea class="value" cols="40" rows="10"></textarea>');
			this.edit.val(this.value);

		} else if (this.vt=="choice") {

			this.edit=$('<select></select>');

			for (var i=0;i<this.pd["choices"].length;i++) {
				this.edit.append('<option val="'+this.pd["choices"][i]+'">'+this.pd["choices"][i]+'</option>');
			}
		
		} else if (this.vt=="datetime") {
		
			this.edit=$('<input class="value" size="18" type="text" value="'+this.value+'" />').date_input();

		} else if (this.vt=="boolean") {
		
			this.edit=$("<select><option>True</option><option>False</option></select>");
		
		} else {

			this.edit=$('<input class="value" size="20" type="text" value="'+this.value+'" />').autocomplete("/db/findvalue/"+this.param, {
				width: 260,
				selectFirst: true,
			});

		}

	
		this.w.append(this.edit);				

		if (this.controls) {

			this.controls=$('<div class="controls"></div>').append(
				$('<input type="submit" value="Save" />').click(this.bindToObj(function(e) {e.stopPropagation();this.save()})),
				$('<input type="button" value="Cancel" />').click(this.bindToObj(function(e) {e.stopPropagation();this.revert()}))
			);

			this.w.append(this.controls);

		}

		//console.log(this.w);

		$(this.elem).after(this.w);
		$(this.elem).hide();

		if (this.popup) {
			this.edit.focus();
			this.edit.select();
		}
		
	},

	////////////////////////
	getparamname: function() {
		var classes = this.elem.attr("class").split(" ");
		var prop = new Object();
		for (var i in classes) {
			var j = classes[i].split("___");
			if (j.length > 1) {
				prop[j[0]] = j[1];
			}
		}
		return prop["paramdef"]		
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
	
		$.jsonRPC("putrecordvalue",[recid,this.param,this.getval(),ctxid],
	 		function(json){
	 			rec[this.param]=json;
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