
////////////////////////////////////////////////
////////////////////////////////////////////////
////////////////////////////////////////////////

RecordDefEditor = (function($) { // Localise the $ function

function RecordDefEditor(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, RecordDefEditor.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
};

RecordDefEditor.DEFAULT_OPTS = {
	root:null,
	add:0,
	parents:null,
	commit:function(){this.default_commit_put()}
};

RecordDefEditor.prototype = {
	
	init: function() {
		this.build();
		this.rd={};
		this.counter_new=0;
		if (this.add) {
			this.commit = this.default_commit_add;
		}		
	},
	
		
	build: function() {
		this.bindall();
		this.refreshall();
		this.getvalues();
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
		
		$("#button_recdefviews_new",this.root).bind("click",function(e){self.event_addview(e)});
		
		
		$('.page[data-tabgroup="recdefviews"]',this.root).each(function() {
			var t=$(this).attr("data-tabname");
			self.bindview(t,$(this));
		});
		
	},
	
	bindview: function(t,r) {

		var self=this;

		var oname=$('input[data-t="'+t+'"]',r);
		oname.bind("change",function(e){self.event_namechange(e)});

		var ocopy=$('select[data-t="'+t+'"]',r);
		ocopy.bind("refreshlist",self.event_copy_refresh);
		ocopy.bind("change",function(e){self.event_copy_copy(e,oname.val())});
		
		var oremove=$('.recdef_edit_action_remove[data-t="'+t+'"]',r);
		oremove.bind("click",function(e){self.event_removeview(e)});
		
		r.attr("data-t",t);
		
		var obutton=$('.button[data-tabname="'+t+'"]');
		obutton.attr("data-t",t);

	},
	
	event_namechange: function(e) {
		var t=$(e.target).attr("data-t");
		var v=$(e.target).val();

		$('.button_recdefviews[data-t="'+t+'"]').html("New View: "+v);
		
		$('[data-t="'+t+'"]').each(function(){
			$(this).attr("data-t",v);
		});
		this.refreshall();
		
	},	
	
	event_addview: function(e) {
		this.addview();
	},
	
	event_removeview: function(e) {
		var t=$(e.target).attr("data-t");
		this.removeview(t);
	},
	
	event_save: function(e) {
		this.save();
	},
	
	event_copy_refresh: function(e) {
		var t=$(e.target);
		t.empty();
		t.append('<option />');
		$("input[name^='viewkey']",this.root).each(function(){
			t.append('<option>'+$(this).val()+'</option>');
		});
	},

	event_copy_copy: function(e,d) {
		var t=$(e.target);
		this.copyview(t.val(),d);
	},	
	
	
	save: function() {
		this.rd=this.getvalues();
		this.commit();
	},
	
	default_commit_put: function() {
		var self=this;
		$.jsonRPC("putrecorddef",[this.rd],function(data){notify_post(EMEN2WEBROOT+'/db/recorddef/'+self.rd.name+'/', ["Changes Saved"])});
	},
	
	default_commit_add: function() {
		var self=this;
		$.jsonRPC("putrecorddef",[this.rd,this.parents],function(data){notify_post(EMEN2WEBROOT+'/db/recorddef/'+self.rd.name+'/', ["Changes Saved"])});
	},	
	
	refreshall: function(e) {
		$("select[name^='viewcopy']",this.root).each(function(){$(this).trigger("refreshlist");});
	},
	
	addview: function() {

		this.counter_new+=1;
		var t='new'+this.counter_new;
		var self=this;
		
		var ol=$('<li id="button_recdefviews_'+t+'" data-t="'+t+'" class="button button_recdefviews" data-tabgroup="recdefviews" data-tabname="'+t+'">New View: '+this.counter_new+'</li>');
		ol.bind("click",function(e){switchin('recdefviews',t)});

		var p=$('<div id="page_recdefviews_'+t+'" data-t="'+t+'" class="page page_recdefviews" data-tabgroup="recdefviews" data-tabname="'+t+'" />');

		var ul=$('<ul class="recdef_edit_actions clearfix" />');
		
		var oname=$('<li>Name: <input type="text" name="viewkey_'+t+'" data-t="'+t+'" value="'+t+'" /></li>');
		var ocopy=$('<li>Copy: <select name="viewcopy_'+t+'" data-t="'+t+'" "/></li>');
		var oremove=$('<li class="recdef_edit_action_remove" data-t="'+t+'"><img src="'+EMEN2WEBROOT+'/images/remove_small.png" /> Remove</li>');
		ul.append(oname, ocopy, oremove);
		
		var ovalue=$('<textarea name="view_'+t+'" data-t="'+t+'" rows="30" cols="80">');

		p.append(ul,ovalue);

		$("#buttons_recdefviews ul").prepend(ol);
		$("#pages_recdefviews",this.root).append(p);

		switchin('recdefviews',t);
		this.bindview(t,p);
		this.refreshall();

	},
	
	
	removeview: function(t) {
		$('.button_recdefviews[data-t="'+t+'"]').remove();
		$('.page_recdefviews[data-t="'+t+'"]').remove();
		
		var tabname=$($('.button_recdefviews')[0]).attr("data-tabname");
		switchin('recdefviews',tabname);
		
		this.refreshall();
	},
	
	
	copyview: function(src,dest) {
		var v=$('textarea[data-t="'+src+'"]').val();
		$('textarea[data-t="'+dest+'"]').val(v);		
	},
	
	
	getvalues: function() {
		rd={}
		rd["name"]=$("input[name='name']",this.root).val();

		var prv=$("input[name='private']",this.root).attr("checked");
		if (prv) {rd["private"]=1} else {rd["private"]=0}


		rd["typicalchld"]=[];

		$("input[name^='typicalchld']",this.root).each(function(){
			if ($(this).val()) {
				rd["typicalchld"].push($(this).val());
			}
		});

		rd["desc_short"]=$("input[name='desc_short']",this.root).val();
		rd["desc_long"]=$("textarea[name='desc_long']",this.root).val();

		rd["mainview"]=$("textarea[name='view_mainview']",this.root).val();

		rd["views"]={};
		var viewroot=$('#pages_recdefviews');
		$('.page[data-tabgroup="recdefviews"]',viewroot).each(function() {
			var n=$('input[name^="viewkey_"]',this).val();
			var v=$('textarea[name^="view_"]',this).val();			
			if (n && v) {
				rd["views"][n]=v;
			}
		});

		return rd		
	}
	
	
}

$.fn.RecordDefEditor = function(opts) {
  return this.each(function() {
		new RecordDefEditor(this, opts);
	});
};

return RecordDefEditor;

})(jQuery); // End localisation of the $ function


////////////////////////////////////////////////
////////////////////////////////////////////////
////////////////////////////////////////////////

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
		$.jsonRPC("putparamdef",[this.pd],function(data){notify_post(EMEN2WEBROOT+'/db/paramdef/'+self.pd.name+'/', ["Changes Saved"])});
	},
	
	default_commit_add: function() {
		var self=this;
		// console.log(this.pd);
		// console.log(this.parents);
		$.jsonRPC("putparamdef",[this.pd,this.parents],function(data){notify_post(EMEN2WEBROOT+'/db/paramdef/'+self.pd.name+'/', ["Changes Saved"])});
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
