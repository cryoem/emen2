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


function query_build_path(q, postpend) {
	//cmp_order = ["==", "!=", ".contains.", ">=", "<=", ">", "<", ".any.", '.recid.']
	// '!contains': '.!contains.',
	var lut = {
		'contains': '.contains.',
		'any': '.any.',
	'none': '.none.',
		'recid': '.recid.',
		'rectype': '.rectype.',
	}

	var output = [];
	$.each(q['c'], function() {
		if (lut[this[1]] != null) {this[1]=lut[this[1]]}
		output.push(this[0]+this[1]+this[2]);
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
    $.widget("ui.PlotControl", {
		options: {
			q: null,
			cb: function(self, newq) {}
		},
				
		_create: function() {
			if (this.options.q['plots']) {
				this.update(this.options.q);				
			}
		},

		update: function(q) {
			var q = q || this.options.q;
			this.options.q = q;			
			this.element.empty();
			var self = this;

			if (!this.options.q['plots']) {
				return
			}
			
			// Trust me -- I hate tables, especially table-embedded-tables, but this is the easiest way..
			var t = $(' \
				<table> \
					<tr> \
						<td style="width:50px"><input name="ymax" type="text" size="4"></td> \
						<td style="width:650px" class="plot_title"></td> \
						<td></td> \
					</tr><tr> \
						<td class="vertical plot_ylabel"></td><td class="plot_image"></td> \
						<td> \
							<table>\
								<thead> \
									<tr> \
										<th>Show<button data-sort="show" class="buttonicon sort" style="float:right"><img src="'+EMEN2WEBROOT+'/static/images/sort_able.png" alt="Sort" /></button></th> \
										<th>Color</th> \
										<th>Group<button data-sort="group" class="buttonicon sort" style="float:right"><img src="'+EMEN2WEBROOT+'/static/images/sort_able.png" alt="Sort" /></button></th> \
										<th>Count<button data-sort="count" class="buttonicon sort" style="float:right"><img src="'+EMEN2WEBROOT+'/static/images/sort_able.png" alt="Sort" /></button></th> \
									</tr> \
								</thead> \
								<tbody class="plot_legend"></tbody> \
								<thead> \
									<tr> \
										<td colspan="3"> \
											<input name="checkall" type="button" value="All" /> \
											<input name="checknone" type="button" value="None" /> \
											<input name="checkinvert" type="button" value="Invert" /> \
											<input name="partcolors" type="button" value="Group Colors" /> \
										</td> \
										<td><input type="button" name="update" value="Update" /></td> \
									</tr> \
								</thead> \
							</table> \
						</td> \
						<td></td> \
					</tr><tr> \
						<td><input name="ymin" type="text" size="4"></td> \
						<td class="plot_xlabel"> \
							<input style="float:left" name="xmin" type="text" size="4" value=""/> \
							<span class="label"></span><input style="float:right" type="text" size="4" value="" name="xmax" /> \
						</td> \
						<td></td> \
					</tr> \
				</table>');
			this.element.append(t);	

			$('input[name=xmin]', this.element).val(this.options.q['xmin']);
			$('input[name=xmax]', this.element).val(this.options.q['xmax']);
			$('input[name=ymin]', this.element).val(this.options.q['ymin']);
			$('input[name=ymax]', this.element).val(this.options.q['ymax']);
			$('.plot_title', this.element).html(this.options.q['title']);
			$('.plot_xlabel .label', this.element).html(this.options.q['xlabel']);
			$('.plot_ylabel', this.element).html(this.options.q['ylabel']);

			// $('.plot_image').empty();
			var png = this.options.q['plots']['png'];
			var i = $('<img src="'+EMEN2WEBROOT+'/download/tmp/'+png+'" alt="Plot" />');
			$('.plot_image', this.element).append(i);
			
			// init group order
			this.setgrouporder();

			// bind checkall / uncheckall
			$('input[name=checkall]').click(function() {
				$('input[name=groupshow]').each(function() {
					$(this).attr('checked', true);
				});
			});
			$('input[name=checknone]').click(function() {
				$('input[name=groupshow]').each(function() {
					$(this).attr('checked', false);
				});
			});
			$('input[name=checkinvert]').click(function() {
				$('input[name=groupshow]').each(function() {
					var state = $(this).attr('checked');
					$(this).attr('checked', !state);
				});
			});
			$('input[name=partcolors]').click(function() {
				$('input[name=groupshow]', this.element).each(function(){
					var group = $(this).attr('data-group');
					var state = $(this).attr('checked');
					var color = '#000000';
					if (!state) {
						color = '#FFFFFF';
					}
					$('input[name=groupcolor][data-group='+group+']').val(color).change();
				});
			});

			$('input[name=update]', this.element).click(function(){
				self.query();
			});
			
			
			$('button[data-sort=show]', this.element).click(function() {
				var s1=[];
				var s2=[];
				$('input[name=groupshow]').each(function() {
					var group = $(this).attr('data-group');
					var state = $(this).attr('checked');
					if (state) {s1.push(group)} else {s2.push(group)}
				});
				self.setgrouporder(s1.concat(s2));
			});
			$('button[data-sort=group]', this.element).click(function() {
				var neworder = self.options.q['grouporder'].slice();
				neworder.sort();
				self.setgrouporder(neworder);
			});
			$('button[data-sort=count]', this.element).click(function() {
				var sortable = [];
				for (var group in self.options.q['groupcount']) sortable.push([group, self.options.q['groupcount'][group]])
				sortable.sort(function(a, b) {return a[1] - b[1]});
				var neworder = [];
				$.each(sortable, function(i,k){neworder.push(k[0])});
				self.setgrouporder(neworder);
			});
			
		},
		
		
		setgrouporder: function(neworder) {
			var self = this;
			neworder = neworder || this.options.q['grouporder'];
			// console.log("Setting order", neworder);
			// console.log(this.options.q['grouporder']);

			$('.plot_legend', this.element).empty();
			$.each(this.options.q['grouporder'], function(i,k) {
				var row = $('\
					<tr> \
						<td><input type="checkbox" checked="checked" name="groupshow" data-group="'+k+'" value="'+k+'" /></td> \
						<td><input class="colorpicker" name="groupcolor" data-group="'+k+'" type="text" size="4" value="'+self.options.q['groupcolors'][k]+'" /></td> \
						<td>'+k+'</td> \
						<td>'+self.options.q['groupcount'][k]+'</td> \
					</tr>');					
				$('.plot_legend', this.element).append(row);
			});					
			$('.colorpicker', this.element).colorPicker();
			
			// Check the boxes for groups that are being displayed
			if (this.options.q['groupshow']) {
				$('input[name=groupshow]').each(function(){$(this).attr('checked',null)});
				$.each(this.options.q['groupshow'], function() {
					$('input[name=groupshow][data-group='+this+']', self.element).attr('checked', 'checked');
				});
			}			
			this.options.q['grouporder'] = neworder;
		},
		
		query: function() {
			var newq = this.options.q;
			newq['xmin'] = $('input[name=xmin]', this.element).val();
			newq['xmax'] = $('input[name=xmax]', this.element).val();
			newq['ymin'] = $('input[name=ymin]', this.element).val();
			newq['ymax'] = $('input[name=ymax]', this.element).val();
			
			// groupshow
			var el = $('input[name=groupshow]:checked', this.element);
			var groupshow = el.map(function(){return $(this).attr('data-group')});
			//if (groupshow.length < el.length) {
			newq['groupshow'] = $.makeArray(groupshow);
			//} else {
			//	newq['groupshow'] = null;
			//}
			
			// groupcolor
			var groupcolors = {};
			$('input[name=groupcolor]', this.element).each(function() {
				groupcolors[$(this).attr('data-group')] = $(this).val();
			});
			newq['groupcolors'] = groupcolors;
			this.options.cb(this, newq);			
		},
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);




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
							<td><input type="hidden" name="param" value="root_parameter" />Keywords</td> \
							<td><input type="hidden" name="cmp" value="contains" /></td> \
							<td><input type="text" size="12" name="value" /></td> \
							<td><input type="checkbox" name="recurse_p" checked="checked" style="display:none" /></td> \
							<td><img class="listicon" src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" /></td> \
						</tr><tr class="s"> \
							<td><input type="hidden" name="param" value="rectype" />Protocol</td> \
							<td><input type="hidden" name="cmp" value="==" /></td> \
							<td><input type="text" size="12" name="value" class="findrecorddef" /></td> \
							<td><input type="checkbox" name="recurse_v" /><label>Child Protocols</label></td> \
							<td><img class="listicon" src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" /></td> \
						</tr><tr> \
							<td><input type="hidden" name="param" value="creator" />Creator</td> \
							<td><input type="hidden" name="cmp" value="==" /></td> \
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
							<td><input type="hidden" name="cmp" value="recid" /></td> \
							<td><input type="text" size="12" name="value" class="findrecord" /></td> \
							<td><input type="checkbox" name="recurse_v" /><label>Recursive</label></td> \
							<td><img class="listicon" src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" /></td> \
						</tr> \
					</tbody> \
					<tbody class="param constraints"></tbody> \
				</table> \
				<table> \
					<thead> \
						<tr> \
							<th colspan="4">Plot</th> \
						</tr> \
					</thead> \
					<tbody> \
						<tr> \
							<td>X <input type="text" name="xparam" size="12" value="" class="findparamdef" /></td> \
							<td>Y <input type="text" name="yparam" size="12" value="" class="findparamdef"/></td> \
							<td>Group By <input type="text" name="groupby" size="12" value="" class="findparamdef" /></td> \
							<td> \
								<select name="plotmode"><option value="scatter">X-Y Scatter</option><option value="hist">Histogram</option><option value="bin">Bins</option></select> \
								<input type="text" name="binw" value="" size="4" /> Bin Width \
							</td> \
						</tr> \
					</tbody> \
				</table> \
				');

			this.container.append(m);
			$('.findrecord', this.container).Browser({});
			$('.finduser', this.container).FindControl({mode: 'finduser'});
			$('.findgroup', this.container).FindControl({mode: 'findgroup'});
			$('.findrecorddef', this.container).FindControl({mode: 'findrecorddef'});
			$('.findparamdef', this.container).FindControl({mode: 'findparamdef'});

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
				$('select[name=cmp]', t).val('==');
			}			
		},
		
		demo: function() {
			$("input[name=xparam]", this.element).val('ctf_defocus_measured');
			$("input[name=yparam]", this.element).val('ctf_bfactor');			
		},
				
		query_bookmark: function(self, q) {
			window.location = query_build_path(q);
		},
		
		getquery: function() {
			var self = this;
			var newq = {};
			var c = [];

			var ignorecase = $('input[name=ignorecase]', this.container).attr('checked');
			var boolmode = $('input[name=boolmode]:checked', this.container).val();
			var xparam = $('input[name=xparam]', this.container).val();
			var yparam = $('input[name=yparam]', this.container).val();
			var plotmode = $('select[name=plotmode]', this.container).val();
			var binw = $('input[name=binw]', this.container).val();
			var groupby = $('input[name=groupby]', this.container).val();
			if (xparam) {
				newq['xparam'] = xparam;
				newq['yparam'] = yparam;
				newq['groupby'] = groupby;
				newq['plotmode'] = plotmode;
				newq['binw'] = binw;
			}
						
			$('.constraints tr', this.container).each(function() {
				var param = $('input[name=param]', this).val();
				var cmp = $('[name=cmp]', this).val();
				var value = $('input[name=value]', this).val();

				// These two recurse/parent checks are kindof ugly..
				var recurse_v = $('input[name=recurse_v]', this).attr('checked');
				if (value && recurse_v) {value = value+'*'}

				var recurse_p = $('input[name=recurse_p]', this).attr('checked');
				if (param && recurse_p) {param = param+'*'}

				if (param && cmp && value) { c.push([param, cmp, value]) }
			});
			newq['c'] = c;

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
			cmp = cmp || '';
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
			$('input[name=param]', newconstraint).FindControl({mode: 'findparamdef'});
			$('.param.constraints', this.container).append(newconstraint);
		},
		
		build_cmp: function(cmp) {
			//"!contains":"does not contain",
			var comparators = {
				"==":"is",
				"!=":"is not",
				"contains":"contains",
				">":"is greater than",
				"<":"is less than",
				">=":"is greater or equal than",
				"<=":"is less or equal than",
				"any":"is any value",
				'none':"is empty",
				'recid': 'recod id',
				'rectype': 'protocol'
			}
			var i = $('<select name="cmp" style="width:150px" />');
			$.each(comparators, function(k,v) {
				var r = $('<option value="'+k+'">'+v+'</option>');
				if (cmp==k) {r.attr("selected", "selected")}
				i.append(r);
			});
			return i		
		},
		
		test: function() {
		},
		
		update: function(q) {
			q = q || this.options.q;
			this.options.q = q;			
			var self = this;
			$('.constraints tbody.base input[name=value]', this.container).val('');
			$('.constraints tbody.param', this.container).empty();

			if (this.options.q['xparam']!=null) {$('input[name=xparam]', this.container).val(this.options.q['xparam'])}
			if (this.options.q['yparam']!=null) {$('input[name=yparam]', this.container).val(this.options.q['yparam'])}
			if (this.options.q['groupby']!=null) {$('input[name=groupby]', this.container).val(this.options.q['groupby'])}
			if (this.options.q['plotmode']!=null) {$('select[name=plotmode]', this.container).val(this.options.q['plotmode'])}
			if (this.options.q['binw']!=null) {$('input[name=binw]', this.container).val(this.options.q['binw'])}
			if (this.options.q['binc']!=null) {$('input[name=binc]', this.container).val(this.options.q['binw'])}

			$.each(this.options.q['c'], function() {
				// Another ugly block to deal with these items..
				var param = this[0];
				var cmpi = this[1];
				var value = this[2];
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
				var finditem = $('.base.constraints input[name=param][value='+param+']', this.element);
				if (finditem.length > 0) {
					var tr = finditem.parent().parent();
					$('input[name=cmp]', tr).val(cmpi);
					$('input[name=value]', tr).val(value);
					if (recurse_p) {$('input[name=recurse_p]', tr).attr('checked', 'checked')} else {$('input[name=recurse_p]', tr).attr('checked', null)}
					if (recurse_v) {$('input[name=recurse_v]', tr).attr('checked', 'checked')} else {$('input[name=recurse_v]', tr).attr('checked', null)}

				} else {
					self.addconstraint(this[0], this[1], this[2]);					
				}

			});

			this.addconstraint();

		},		
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);
