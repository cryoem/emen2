///////////////// Parameter Editor /////////////////////

(function($) {
    $.widget("emen2.ParamDefEditControl", {
		options: {
			newdef: null,
			parents: null,
			ext_save: null,
		},
				
		_create: function() {
			this.pd = {};
			this.build();
		},

		build: function() {
			this.bindall();
		},

		bindall: function() {
			var self=this;
			$('input[name=save]', this.options.ext_save).bind("click",function(e){self.event_save(e)});
			
			$('select[name=property]', this.element).change(function() {
				var val = $(this).val();
				var sel = $('select[name=defaultunits]', this.element);
				sel.empty();
				if (!val) {
					return
				}

				var defaultunits = valid_properties[val][0];
				var units = valid_properties[val][1];
				$.each(units, function() {
					var opt = $('<option value="'+this+'">'+this+'</option>');
					sel.append(opt);
				});
				sel.val(defaultunits);				
			});
			
		},

		event_save: function(e) {
			this.save();
		},	

		save: function() {
			var self = this;
			this.pd = this.getvalues();
			$('.spinner', this.options.ext_save).show();
			
			if (this.options.newdef) {
				this.pd['parents'] = this.options.parents;
			}
			$.jsonRPC2("putparamdef", [this.pd], function(data){
				$('.spinner', self.options.ext_save).hide();
				//notify_post(EMEN2WEBROOT+'/paramdef/'+self.pd.name+'/', ["Changes Saved"])
				window.location = EMEN2WEBROOT+'/paramdef/'+self.pd.name+'/';
			});
		},

		getvalues: function() {
			pd={}
			pd["name"] = $("input[name='name']", this.element).val();
			pd["desc_short"] = $("input[name='desc_short']",this.element).val();
			pd["desc_long"] = $("textarea[name='desc_long']",this.element).val();
			pd["controlhint"] = $("input[name='controlhint']",this.element).val();

			pd["choices"] = [];
			$("input[name=choices]",this.element).each(function(){
				if ($(this).val()) {
					pd["choices"].push($(this).val());
				}
			});

			var vartype = $("select[name='vartype']",this.element);
			if (vartype) {pd["vartype"] = vartype.val()} 

			var property = $("select[name='property']",this.element);
			if (property) {pd["property"] = property.val()}
			
			var defaultunits = $("select[name='defaultunits']",this.element);
			if (defaultunits) {pd["defaultunits"] = defaultunits.val()}
			
			var indexed = $("input[name='indexed']",this.element);
			if (indexed) {pd["indexed"] = indexed.attr('checked')}
			
			var immutable = $("input[name='immutable']",this.element);
			if (immutable) {pd['immutable'] = immutable.attr('checked')}
			
			return pd
		}
	});
})(jQuery);



 
///////////////// Protocol Editor /////////////////////



(function($) {
    $.widget("emen2.RecordDefEditControl", {
		options: {
			newdef: null,
			parents: null,
			ext_save: null
		},
				
		_create: function() {
			this.build();
			this.rd = {};
			this.counter_new = 0;
		},
	
		
		build: function() {
			this.bindall();
			this.refreshall();
			this.getvalues();
		},
	
		bindall: function() {
			var self=this;
	
			$('input[name=save]', this.options.ext_save).bind("click",function(e){self.event_save(e)});
		
			$("#button_recdefviews_new", this.element).bind("click",function(e){self.event_addview(e)});
		
			$('.page[data-tabgroup="recdefviews"]', this.element).each(function() {
				var t=$(this).attr("data-tabname");
				self.bindview(t,$(this));
			});
			
			$('input[name=typicalchld]', this.element).FindControl({keytype: 'recorddef'});			
		
		},
	
		bindview: function(t,r) {
			var self=this;

			var oname = $('input[data-t="'+t+'"]',r);
			oname.bind("change",function(e){self.event_namechange(e)});

			var ocopy = $('select[data-t="'+t+'"]',r);
			ocopy.bind("refreshlist",self.event_copy_refresh);
			ocopy.bind("change",function(e){self.event_copy_copy(e,oname.val())});
		
			var oremove = $('.e2-editdefs-remove[data-t="'+t+'"]',r);
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
			$("input[name^='viewkey']", this.element).each(function(){
				t.append('<option>'+$(this).val()+'</option>');
			});
		},

		event_copy_copy: function(e,d) {
			var t=$(e.target);
			this.copyview(t.val(),d);
		},	
	
		save: function() {
			this.rd=this.getvalues();
			if (this.options.newdef) {
				this.rd['parents'] = this.options.parents;
			}

			var self=this;

			$('.spinner').show();
			$.jsonRPC2("putrecorddef", [this.rd], function(data){
				$('.spinner').hide();
				// notify_post(EMEN2WEBROOT+'/recorddef/'+self.rd.name+'/', ["Changes Saved"])
				window.location = EMEN2WEBROOT+'/recorddef/'+self.rd.name+'/';
			});

		},	
	
		refreshall: function(e) {
			$("select[name^='viewcopy']", this.element).each(function(){$(this).trigger("refreshlist");});
		},
	
		addview: function() {
			this.counter_new += 1;
			var t = 'new' + this.counter_new;
			var self = this;
		
			var ol = $('<li id="button_recdefviews_'+t+'" data-t="'+t+'" class="button button_recdefviews" data-tabgroup="recdefviews" data-tabname="'+t+'">New View: '+this.counter_new+'</li>');
			ol.bind("click",function(e){switchin('recdefviews',t)});

			var p = $('<div id="page_recdefviews_'+t+'" data-t="'+t+'" class="page page_recdefviews" data-tabgroup="recdefviews" data-tabname="'+t+'" />');

			var ul = $('<ul class="clearfix" />');
			var oname = $('<li>Name: <input type="text" name="viewkey_'+t+'" data-t="'+t+'" value="'+t+'" /></li>');
			var ocopy = $('<li>Copy: <select name="viewcopy_'+t+'" data-t="'+t+'" "/></li>');
			var oremove = $('<li class="e2-editdefs-remove" data-t="'+t+'"><img src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" /> Remove</li>');
			ul.append(oname, ocopy, oremove);
		
			var ovalue = $('<textarea name="view_'+t+'" data-t="'+t+'" rows="30" cols="80">');

			p.append(ul,ovalue);

			$("#buttons_recdefviews ul").prepend(ol);
			$("#pages_recdefviews", this.element).append(p);

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
			rd["name"]=$("input[name='name']", this.element).val();

			var prv=$("input[name='private']", this.element).attr("checked");
			if (prv) {rd["private"]=1} else {rd["private"]=0}

			rd["typicalchld"]=[];

			$("input[name^='typicalchld']", this.element).each(function(){
				if ($(this).val()) {
					rd["typicalchld"].push($(this).val());
				}
			});

			rd["desc_short"]=$("input[name='desc_short']", this.element).val();
			rd["desc_long"]=$("textarea[name='desc_long']", this.element).val();

			rd["mainview"]=$("textarea[name='view_mainview']", this.element).val();

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
	});
	
})(jQuery);

