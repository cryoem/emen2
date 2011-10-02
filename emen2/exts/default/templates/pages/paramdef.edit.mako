## -*- coding: utf-8 -*-
<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<%block name="js_inline">
	${parent.js_inline()}
	(function($) {
		///////////////// Parameter Editor /////////////////////
	
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
				$('.e2l-spinner', this.options.ext_save).show();
			
				if (this.options.newdef) {
					this.pd['parents'] = this.options.parents;
				}
				$.jsonRPC.call("putparamdef", [this.pd], function(data){
					$('.e2l-spinner', self.options.ext_save).hide();
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
	});
</%block>


<%block name="js_ready">
	${parent.js_ready}
	$('#paramdef_edit').ParamDefEditControl({
		newdef: ${jsonrpc.jsonutil.encode(new)},
		parents:['${paramdef.name}'],
		ext_save: "#ext_save",
	});
</%block>	

<h1>
	${title}

	<div class="e2l-controls" id="ext_save">
		${buttons.spinner(false)}
		<input type="button" value="Save" name="save">
	</div>	

</h1>

<form action="" method="get" id="paramdef_edit">


<table>

	<tr>
		<td>Name</td>
		<td>
		% if action=="new":
			<input type="text" name="name" value="" />
		% else:
			${paramdef.name}
			<input type="hidden" name="name" value="${paramdef.name}" />
		% endif
		</td>
	</tr>
	
	<tr>
		<td>Short Description</td>
		<td><input type="text" name="desc_short" value="${paramdef.desc_short or ""}"/></td>
	</tr>
	
	<tr>
		<td>Long Description</td>
		<td>
			<textarea name="desc_long" cols="80" rows="5" />${paramdef.desc_long or ""}</textarea>
		</td>
	</tr>	
	
	<tr>
		<td>Default Choices</td>
		<td>
			<ul>
				% for i,j in enumerate(list(paramdef.choices or [])+[""]*6):
					<li><input type="text" name="choices" value="${j}"></li>
				% endfor
			</ul>
		</td>
	</tr>
	
	<tr>
		<td>UI Control</td>
		<td><input type="text" name="controlhint" value="${paramdef.get('controlhint') or ""}"/></td>
	</tr>
	
	<tr>
		<td>Immutable</td>
		<td>
			% if new:
				% if paramdef.get('immutable'):
					<input type="checkbox" name="immutable" checked="checked">
				% else:
					<input type="checkbox" name="immutable">
				% endif
			% else:
				${paramdef.get('immutable', False)}
			% endif
		</td>
	</tr>	

	<tr>
		<td>Indexed</td>
		<td>
			% if new:			
				% if paramdef.get('indexed', False):
					<input type="checkbox" name="indexed" checked="checked" />
				% else:
					<input type="checkbox" name="indexed" />
				% endif
			% else:
				${paramdef.get('indexed', False)}
			% endif
		</td>
	</tr>	
	
	<tr>
		<td>Data Type</td>
		<td>
			% if new:
				<select name="vartype">
					% for i in sorted(vartypes):
						<option value="${i}" ${['','selected="selected"'][i==paramdef.vartype]}>${i}</option>
					% endfor
				</select>
			% else:
				${paramdef.vartype}
			% endif
		</td>
	</tr>
	
	<tr>
		<td>Property</td>
		<td>
			% if new:
				<select name="property">
					<option value=""></option>
					% for i in sorted(properties):
						<option value="${i}" ${['','selected="selected"'][i==paramdef.property]}>${i}</option>
					% endfor
				</select>
			% else:
				${paramdef.property}
			% endif
		</td>
	</tr>

	<tr>
		<td>Default Units</td>
		<td>
			% if new:
				<select name="defaultunits">
					% if paramdef.property:
						% for i in units:
							<option value="${i}"  ${['','selected="selected"'][i==paramdef.defaultunits]}>${unicode(i)}</option>
						% endfor
					% else:
						<option value="">(select property)</option>
					% endif
				</select>
			% else:
				${paramdef.defaultunits}
			% endif
		</td>
	</tr>
		
</table>							



</form>


## <h1>Relationships<h1>
## <div id="reledit">
## </div>


