<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />

<%block name="js_inline">
	${parent.js_inline()}
	(function($) {
	///////////////// Protocol Editor /////////////////////

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
		
			$('.e2l-tab-page[data-tabgroup="recdefviews"]', this.element).each(function() {
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
		
			var obutton=$('.e2l-tab-button[data-tabname="'+t+'"]');
			obutton.attr("data-t",t);

		},
	
		event_namechange: function(e) {
			var t=$(e.target).attr("data-t");
			var v=$(e.target).val();

			$('.e2l-tab-button-recdefviews[data-t="'+t+'"]').html("New View: "+v);
		
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

			$('.e2l-spinner').show();
			emen2.db("recorddef.put", [this.rd], function(data){
				$('.e2l-spinner').hide();
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
		
			var ol = $('<li id="button_recdefviews_'+t+'" data-t="'+t+'" class="e2l-button" data-tabgroup="recdefviews" data-tabname="'+t+'">New View: '+this.counter_new+'</li>');
			ol.bind("click",function(e){switchin('recdefviews',t)});

			var p = $('<div id="page_recdefviews_'+t+'" data-t="'+t+'" class="e2l-tab-page" data-tabgroup="recdefviews" data-tabname="'+t+'" />');

			var ul = $('<ul class="e2l-cf" />');
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
</%block>


<%block name="js_ready">
	$('#recdef_edit').RecordDefEditControl({
		newdef: ${jsonrpc.jsonutil.encode(new)},
		parents:['${recdef.name}'],
		ext_save: "#ext_save"
	});
</%block>


<h1>
	${title}

	<div class="e2l-controls" id="ext_save">
		${buttons.spinner(false)}
		<input type="button" value="Save" name="save">
	</div>
		
</h1>

<form action="" method="get" id="recdef_edit">


<%buttons:singlepage label='Protocol Details'>
	<table>
	

		% if new:
			<tr><td>Name:</td><td><input type="text" name="name" value="" /></td></tr>
		% else:
			<tr><td>Name:</td><td>${recdef.name}</td></tr>
			<tr><td>Created:</td><td><a href="${EMEN2WEBROOT}/users/${recdef.creator}/">${recdef.creator}</a> @ <time class="e2-localize" datetime="${recdef.creationtime}">${recdef.creationtime}</time></td></tr>
			<input type="hidden" name="name" value="${recdef.name}" />
		% endif
	

		<tr>
			<td>Private:</td>
			<td>
				<input type="checkbox" ${['','checked="checked"'][recdef.private]} name="private" />
			</td>
		</tr>

		<tr>
			<td>Suggested child protocols</td>
			<td>
				<ul id="typicalchld">
				% for k,i in enumerate(recdef.typicalchld):
					<li><input type="text" value="${i}" name="typicalchld"></li>
				% endfor

				<li><input type="text" name="typicalchld"></li>			
				<li><input type="text" name="typicalchld"></li>			
				<li><input type="text" name="typicalchld"></li>			
				<li><input type="text" name="typicalchld"></li>			
				<li><input type="text" name="typicalchld"></li>			

				</ul>
			</td>
	
		</tr>

		<tr>
			
			<td>Short Description</td>
			<td>
				<input type="text" name="desc_short" value="${recdef.get("desc_short","")}" />
			</td>
	
		</tr>

		<tr>
			<td colspan="2">
				<p>Detailed Description</p>
				<p>
					<textarea cols="80" rows="10" name="desc_long">${recdef.get("desc_long") or ""}</textarea>
				</p>
			</td>
		</tr>


	</table>
</%buttons:singlepage>




<%buttons:singlepage label='Protocol'>
		<input type="hidden" value="mainview" name="viewkey_mainview" data-t="mainview" />
		<textarea cols="80" rows="30" name="view_mainview" data-t"mainview">${recdef.mainview}</textarea>
</%buttons:singlepage>



	% for k,v in pages_recdefviews.content.items():

				<ul class="recdef_edit_actions e2l-cf">
					<li>Name: <input type="text" value="${k}" data-t="${k}" name="viewkey_${k}" /></li>
					<li>Copy: <select name="viewcopy_${k}" data-t="${k}" /></li>
					<li class="recdef_edit_action_remove" data-t="${k}"><img src="${EMEN2WEBROOT}/static/images/remove_small.png" alt="Remove" /> Remove</li>
				</ul>
					
				<textarea cols="80" rows="30" data-t="${k}" name="view_${k}">${v}</textarea>
		
		</%call>

	% endfor
	
	
		No additional views defined; why not add some?				


</form>


## <h1>Relationships<h1>
## <div id="reledit">
## </div>





