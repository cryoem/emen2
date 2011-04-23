(function($) {
    $.widget("ui.CommonQueries", {
		options: {
		},
				
		_create: function() {
		},
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);


var comparators = {
	"is": "is",
	"not": "is not",
	"contains": "contains",
	"contains_w_empty": "contains, or is empty",
	"gt": "is greater than",
	"lt": "is less than",
	"gte": "is greater or equal than",
	"lte": "is less or equal than",
	"any": "is any value",
	'none': "is empty",
	'noop': "no constraint"
}


var comparators_lookup = {
	">": "gt",
	"<": "lt",
	">=": "gte",
	"<=": "lte",
	"==": "is",
	"!=": "not"				
}



function query_build_path(q, postpend) {
	var output = [];
	$.each(q['c'], function() {
		output.push(encodeURIComponent(this[0])+'.'+encodeURIComponent(this[1])+'.'+encodeURIComponent(this[2]));
	});
	delete q['c'];
	
	if (postpend) {
		output.push(postpend);
	}
	
	// remove some default arguments..
	if (q['ignorecase'] == 1){
		delete q['ignorecase'];
	}
	if (q['boolmode'] == 'AND') {
		delete q['boolmode'];
	}
	qs = '?' + $.param(q);
	return EMEN2WEBROOT + '/query/' + output.join("/") + '/' + qs;
}




(function($) {
    $.widget("ui.QueryControl", {
		options: {
			q: null,
			show: true,
			cb: function(self, q){self.query_bookmark(self, q)}
		},
				
		_create: function() {
			this.oq = {}
			$.extend(this.oq, this.options.q);
			
			this.built = 0;
			if (this.options.show) {
				this.show();
			}
		},
		
		show: function() {
			this.build();
			this.container.show();
		},
		
		
		build: function() {
			var self = this;
			
			if (this.built) {
				return
			}
			
			this.built = 1;
			this.element.addClass("query");
			this.container = $('<div class="clearfix" />');
						
			var m = $(' \
				<table cellpadding="0" cellspacing="0" > \
					<thead> \
						<tr> \
							<th>Parameter</th> \
							<th></th> \
							<th>Value</th> \
							<th></th> \
							<th><img class="listicon" src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" /> Reset</th> \
						</tr> \
					</thead> \
					<tbody class="base constraints"> \
						<tr> \
							<td><input type="hidden" name="param" value="root" />Keywords</td> \
							<td><input type="hidden" name="cmp" value="contains" /></td> \
							<td><input type="text" size="12" name="value" /></td> \
							<td><input type="checkbox" name="recurse_p" checked="checked" style="display:none" /></td> \
							<td><img class="listicon" src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" /></td> \
						</tr><tr class="s"> \
							<td><input type="hidden" name="param" value="rectype" />Protocol</td> \
							<td><input type="hidden" name="cmp" value="is" /></td> \
							<td><input type="text" size="12" name="value" class="findrecorddef" /></td> \
							<td><input type="checkbox" name="recurse_v" /><label>Child Protocols</label></td> \
							<td><img class="listicon" src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" /></td> \
						</tr><tr> \
							<td><input type="hidden" name="param" value="creator" />Creator</td> \
							<td><input type="hidden" name="cmp" value="is" /></td> \
							<td><input type="text" size="12" name="value" class="finduser" /></td> \
							<td></td> \
							<td><img class="listicon" src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" /></td> \
						</tr><tr class="s"> \
							<td><input type="hidden" name="param" value="permissions" />Permissions</td> \
							<td><input type="hidden" name="cmp" value="contains" /></td> \
							<td><input type="text" size="12" name="value" class="finduser" /></td> \
							<td></td> \
							<td><img class="listicon" src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" /></td> \
						</tr><tr> \
							<td><input type="hidden" name="param" value="groups" />Groups</td> \
							<td><input type="hidden" name="cmp" value="contains" /></td> \
							<td><input type="text" size="12" name="value" class="findgroup" /></td> \
							<td></td> \
							<td><img class="listicon" src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" /></td> \
						</tr><tr class="s"> \
							<td><input type="hidden" name="param" value="children" />Child Of</td> \
							<td><input type="hidden" name="cmp" value="name" /></td> \
							<td><input type="text" size="12" name="value" class="findrecord" /></td> \
							<td><input type="checkbox" name="recurse_v" /><label>Recursive</label></td> \
							<td><img class="listicon" src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" /></td> \
						</tr> \
					</tbody> \
					<tbody class="param constraints"></tbody> \
				</table> \
				');

			this.container.append(m);
			
			// ian: todo
			//$('.findrecord', this.container).Browser({});
			$('.finduser', this.container).FindControl({keytype: 'user'});
			$('.findgroup', this.container).FindControl({keytype: 'group'});
			$('.findrecorddef', this.container).FindControl({keytype: 'recorddef'});
			$('.findparamdef', this.container).FindControl({keytype: 'paramdef'});

			var save = $('<div class="controls"> \
				<img class="spinner" src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /> \
				<input type="button" value="Query" name="save" /></div>');
			this.container.append(save);
			$('input[name=save]', this.container).bind("click",function(e){self.query()});			

			$('thead .listicon', this.container).click(function(e) {
				$('.constraints tr').each(function(){self.clear($(this))});
			});

			$('.constraints .listicon', this.container).click(function(e) {
				self.event_clear(e, true);
			});
			
			this.element.append(this.container);						
			this.update();
		},
		
		event_clear: function(e, base) {
			var t = $(e.target).parent().parent();
			this.clear(t);
		},
		
		clear: function(t) {
			var base = t.parent().hasClass('base');
			$('input[name=value]', t).val('')
			$('input[name=recurse_p]', t).attr('checked', null);
			$('input[name=recurse_v]', t).attr('checked', null);
			if (!base) {
				$('input[name=param]', t).val('');
				$('select[name=cmp]', t).val('any');
			}			
		},
				
		query_bookmark: function(self, q) {
			window.location = query_build_path(q);
		},
		
		_getconstraint: function(elem) {
			var param = $('input[name=param]', elem).val();
			var cmp = $('[name=cmp]', elem).val();
			var value = $('input[name=value]', elem).val();

			// These two recurse/parent checks are kindof ugly..
			var recurse_v = $('input[name=recurse_v]', elem).attr('checked');
			if (value && recurse_v) {value = value+'*'}

			var recurse_p = $('input[name=recurse_p]', elem).attr('checked');
			if (param && recurse_p) {param = param+'*'}
			return [param, cmp, value];
		},
		
		getquery: function() {
			var self = this;
			var newq = {};
			var c = [];

			var ignorecase = $('input[name=ignorecase]', this.container).attr('checked');
			var boolmode = $('input[name=boolmode]:checked', this.container).val();
									
			$('.base.constraints tr', this.container).each(function() {
				var p = self._getconstraint(this);
				if (p[0] && p[1] && p[2]) {c.push(p)}
			});
			$('.param.constraints tr', this.container).each(function() {
				var p = self._getconstraint(this);
				if (p[0]) {c.push(p)}
			});

			newq['c'] = c;
			//newq['stats'] = true;
			
			if (ignorecase) {newq['ignorecase'] = 1}
			if (boolmode) {newq['boolmode'] = boolmode}
			return newq
		},
		
		query: function() {
			var newq = this.getquery();
			this.options.cb(this, newq);
		},
		
		addconstraint: function(param, cmp, value) {
			param = param || '';
			cmp = cmp || 'any';
			value = value || '';
			var recurse = false;
			var self = this;
			var cmpi = this.build_cmp(cmp);

			if (param.search('\\*') > -1) {
				param = param.replace('*', '');
				recurse = true;
			}	
			
			var newconstraint = $('<tr>')
				.append('<td><input type="text" name="param" size="12" value="'+param+'" /></td>')
				.append($('<td/>').append(cmpi))
				.append('<td><input type="text" name="value" size="12" value="'+value+'" /></td>')
				.append('<td><input name="recurse_p" type="checkbox" /><label>Child Parameters</td>');

			if (recurse) {$('input[name=recurse_p]', newconstraint).attr('checked', 'checked')}

			var controls = $('<td />');

			var addimg = $('<img class="listicon" src="'+EMEN2WEBROOT+'/static/images/add_small.png" alt="Add" />');
			addimg.click(function() {self.addconstraint()});

			var removeimg = $('<img  class="listicon" src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" />');
			removeimg.click(function(e) {
				self.event_clear(e, false);
			});

			controls.append(addimg, removeimg);
			newconstraint.append(controls);
			$('input[name=param]', newconstraint).FindControl({keytype: 'paramdef'});
			$('.param.constraints', this.container).append(newconstraint);
		},
		
		build_cmp: function(cmp) {
			//"!contains":"does not contain",
			// Check the transforms..
			var cmp2 = comparators_lookup[cmp] || cmp;
			
			var i = $('<select name="cmp" style="width:150px" />');
			$.each(comparators, function(k,v) {
				var r = $('<option value="'+k+'">'+v+'</option>');
				if (cmp2==k) {r.attr("selected", "selected")}
				i.append(r);
			});
			return i		
		},
		
		_compare_constraint: function(elem, c, base) {
			// Another ugly block to deal with these items..

			var param = c[0] || '';
			var cmpi = c[1] || 'any';
			var value = c[2] || '';
			var recurse_p = false;
			var recurse_v = false;
			if (param.search('\\*') > -1) { 
				recurse_p = true;
				param = param.replace('*', '');
			}
			if (value.search('\\*') > -1) { 
				recurse_v = true;
				value = value.replace('*', '');
			}


			cmpi = comparators_lookup[cmpi] || cmpi;
			
			// Get the constraint elements.
			var _param = $('input[name=param]', elem);
			var _cmpi = $('input[name=cmp]', elem);
			var _value = $('input[name=value]', elem);
			var _recurse_p = $('input[name=recurse_p]', elem);
			var _recurse_v = $('input[name=recurse_v]', elem);
			
			// Get the values
			var _param2 = _param.val();
			var _cmpi2 = _cmpi.val();
			var _value2 = _value.val();
			var _recurse_p2 = _recurse_p.attr('checked');
			var _recurse_v2 = _recurse_v.attr('checked');

			base = true;
			if (base) {
				_value2 = value;
				_recurse_p2 = recurse_p;
				_recurse_v2 = recurse_v;
			}
			
			// If this constraint matches, update the element and return True
			if (
				param == _param2
				&& cmpi == _cmpi2
				&& value == _value2
				&& recurse_p == _recurse_p2
				&& recurse_v == _recurse_v2
			) {
				_value.val(value);
				_recurse_p.attr('checked', recurse_p);
				_recurse_v.attr('checked', recurse_v);
				return true
			}
			return false
		},
		
		_find_constraints: function(c, base) {
			var self = this;
			var selector = '.param.constraints tr';
			var param_constraints = [];
			if (base) {
				var selector = '.base.constraints tr';
			}
			$.each(c, function() {
				var constraint = this;
				var found = false;
				$.each($(selector), function() {
					if (found == false) {
						found = self._compare_constraint(this, constraint, base);
					}
				});
				if (found == false) {
					param_constraints.push(constraint);
				}
			});
			return param_constraints
		},
		
		update: function(q) {
			q = q || this.options.q;
			this.options.q = q;			
			var self = this;

			// Check all base constraints, w/o recurse
			// Check remaining param constraints..
			var param_constraints = this._find_constraints(this.options.q['c'], true);
			var new_constraints = this._find_constraints(param_constraints, false);
			$.each(new_constraints, function() {
				self.addconstraint(this[0], this[1], this[2]);
			});	
			if (new_constraints.length == 0) {
				self.addconstraint();
			}
		},		
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);
