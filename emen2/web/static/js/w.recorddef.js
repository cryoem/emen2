ParamDefEditor = (function($) { // Localise the $ function

function ParamDefEditor(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, ParamDefEditor.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
};

ParamDefEditor.DEFAULT_OPTS = {
	root:null,
	add:0,
	parents:null,
	commit:function(){this.default_commit_put()}
};

ParamDefEditor.prototype = {
	
	init: function() {
		this.pd={};
		if (this.add) {
			this.commit = this.default_commit_add;
		}		
		this.build();
	},
	
		
	build: function() {
		this.bindall();
	},
	
	connect_buttons: function() {
		var self=this;
		$("#ext_save",this.root).bind("click",function(e){
			self.event_save(e)
		});
	},
	
	bindall: function() {
		var self=this;
		this.connect_buttons();		
	},
			
	event_save: function(e) {
		this.save();
	},	
	
	save: function() {
		this.pd=this.getvalues();
		this.commit();
	},
	
	default_commit_put: function() {
		var self=this;
		$.jsonRPC("putparamdef",[this.pd],function(data){notify_post(EMEN2WEBROOT+'/paramdef/'+self.pd.name+'/', ["Changes Saved"])});
	},
	
	default_commit_add: function() {
		var self=this;
		// console.log(this.pd);
		// console.log(this.parents);
		$.jsonRPC("putparamdef",[this.pd,this.parents],function(data){notify_post(EMEN2WEBROOT+'/paramdef/'+self.pd.name+'/', ["Changes Saved"])});
	},	
		
	getvalues: function() {
		pd={}
		pd["name"] = $("input[name='name']",this.root).val();
		pd["desc_short"] = $("input[name='desc_short']",this.root).val();
		pd["desc_long"] = $("textarea[name='desc_long']",this.root).val();
		pd["vartype"] = $("select[name='vartype']",this.root).val();
		pd["property"] = $("select[name='property']",this.root).val();
		pd["defaultunits"] = $("select[name='defaultunits']",this.root).val();

		pd["choices"] = [];

		$("input[name^='choices']",this.root).each(function(){
			if ($(this).val()) {
				pd["choices"].push($(this).val());
			}
		});
		return pd
	}
	
	
}

$.fn.ParamDefEditor = function(opts) {
  return this.each(function() {
		new ParamDefEditor(this, opts);
	});
};

return ParamDefEditor;

})(jQuery); // End localisation of the $ function
