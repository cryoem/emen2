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
			
			var t = $('<table> \
				<tr><td style="width:50px"><input name="ymax" type="text" size="4"></td><td style="width:650px" class="plot_title"></td><td></td></tr> \
				<tr><td class="vertical plot_ylabel"></td><td class="plot_image"></td><td class="plot_legend"><h4>Legend</h4><ul class="nonlist"></ul><input type="button" name="update" value="Update" /></td></tr> \
				<tr><td><input name="ymin" type="text" size="4"></td><td class="plot_xlabel"><input style="float:left" name="xmin" type="text" size="4" value=""/><span class="label"></span><input style="float:right" type="text" size="4" value="" name="xmax" /></td><td></td></tr> \
				</table> \
			');
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
		
			$.each(this.options.q['groupnames'], function(k,v) {
				var i = $('<li> \
					<input type="checkbox" checked="checked" name="groupshow" data-group="'+k+'" value="'+k+'" /> \
					<input class="colorpicker" name="groupcolor" data-group="'+k+'" type="text" size="4" value="'+self.options.q['groupcolors'][k]+'" /> '+v+'</li>');
					
				$('.plot_legend ul', this.element).append(i);
			});					

			$('.colorpicker', this.element).colorPicker();


			// Check the boxes for groups that are being displayed
			if (this.options.q['groupshow']) {
				$('input[name=groupshow]').each(function(){$(this).attr('checked',null)});
				$.each(this.options.q['groupshow'], function() {
					$('input[name=groupshow][data-group='+this+']', self.element).attr('checked', 'checked');
				});
			}

			$('input[name=update]', this.element).click(function(){
				self.query();
			});
			
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
			keywords: true,
			plot: true,
			ext_save: null,
			ext_q: null,
			//ext_reset: null,
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

			this.container = $('<div class="query clearfix" />');
			
			var keywords = $(' \
				<h4>Keywords</h4> \
				<input type="text" name="q" value="" /> \
			');
			
			var m = $(' \
				<h4>General</h4> \
				<table><tr> \
					<td>Protocol:</td><td><input type="text" name="rectype" /><input type="checkbox" name="rectype_recurse" /><img class="listicon" data-clear="rectype" src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" /></td> \
					<td>Creator:</td><td><input type="text" name="creator" /> <img  class="listicon" data-clear="creator" src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" /></td> \
				</tr><tr> \
					<td>Child of</td><td><input type="text" name="parent" /><input type="checkbox" name="parent_recurse" /><img class="listicon" data-clear="parent" src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" /></td> \
					<td>Parent of</td><td><input type="text" name="child" /> <img  class="listicon" data-clear="child" src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" /></td> \
				</tr></table> \
				<table class="constraints"> \
					<thead><tr><th>Parameter</th><th>Operator</th><th>Value</th><th>Child Params</th><th>Search Parents</th><th style="width:30px"/></tr></thead> \
					<tbody></tbody> \
				</table> \
				<h4>Options</h4> \
				<p>Match \
					<input type="radio" value="AND" name="boolmode" checked="checked"> all <input type="radio" value="OR" name="boolmode"> any \
					<input type="checkbox" checked="checked" name="ignorecase" /> Case Insensitive</p> \
				');

			
			var plot = $(' \
				<h4>Plot</h4> \
				<p>X <input type="text" name="xparam" value="" /> Y <input type="text" name="yparam" value="" /></p>');

			// var plot = $(' \
			// 	<h4>Plot</h4> \
			// 	<table cellpadding="0" cellspacing="0"> \
			// 		<thead><th /><th>Param</th><th>Min</th><th>Max</th></tr></thead> \
			// 		<tbody> \
			// 			<tr><td>X</td><td><input type="text" name="xparam" value="" /></td><td><input type="text" name="xmin" /></td><td><input type="text" name="xmax" /></td></tr> \
			// 			<tr><td>Y</td><td><input type="text" name="yparam" value="" /></td><td><input type="text" name="ymin" /></td><td><input type="text" name="ymax" /></td></tr> \
			// 		</tbody> \
			// 	</table> \
			// 	<p>Output: <input type="checkbox" name="png" checked="checked" /> PNG <input type="checkbox" name="pdf" /> PDF <input type="text" name="width" value="800" /> Pixels </p> \
			// ');


			// Append
			if (this.options.keywords) {
				this.container.append(keywords);
			}

			this.container.append(m);
			
			if (this.options.plot) {
				this.container.append(plot);
			}


			$('input[name=xparam]', this.container).FindControl({mode: 'findparamdef'});			
			$('input[name=yparam]', this.container).FindControl({mode: 'findparamdef'});			
			$('input[name=rectype]', this.container).FindControl({mode: 'findrecorddef'});			
			$('input[name=creator]', this.container).FindControl({mode: 'finduser'});
			$('input[name=parent]', this.container).Browser({});
			$('input[name=child]', this.container).Browser({});
			
			// var controls = $('<div class="controls"></div>');
			// if (this.options.ext_reset) {
			// 	this.options.ext_reset.click(function() {self.reset()});
			// } else {
			// 	controls.append('<input type="button" value="Reset" name="reset" />');
			// }

			if (!this.options.ext_save) {
				this.options.ext_save = $('<div class="controls bigbutton"><img class="spinner" style="display:none" src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /><input type="button" value="Query" name="save" /></div>');
			}
			$('input[name=save]', this.options.ext_save).bind("click",function(e){self.query()});
			

			// controls.append('<input type="button" value="Demo Plot" name="demo" />');
			// if (!this.options.ext_save || !this.options.ext_reset) {
			// 	this.container.append(controls);
			// }

			// $('input[name=query]', controls).click(function() {self.query()});
			// $('input[name=reset]', controls).click(function() {self.reset()});
			// $('input[name=demo]', controls).click(function() {self.demo()});


			$('.listicon', this.container).click(function() {
				var clearselector = $(this).attr('data-clear');
				$('input[name='+clearselector+']').val('');
			});
			
			this.element.append(this.container);						
			this.update();
		},
		
		demo: function() {
			$("input[name=xparam]", this.element).val('ctf_defocus_measured');
			$("input[name=yparam]", this.element).val('ctf_bfactor');
			
		},
		
		reset: function() {
			this.options.q = {};
			$.extend(this.options.q, this.oq);
			//this.query();
			this.update();
		},
		
		query_bookmark: function(self, q) {
			//cmp_order = ["==", "!=", ".!contains.", ".contains.", ">=", "<=", ">", "<", ".!None.", '.recid.']
			var lut = {
				'!contains': '.!contains.',
				'contains': '.contains.',
				'!None': '.!None.',
				'recid': '.recid.'
			}

			var output = [];
			$.each(q['c'], function() {
				if (lut[this[1]] != null) {this[1]=lut[this[1]]}
				output.push(this[0]+this[1]+this[2]);
			});
			delete q['c'];
			
			// remove some default arguments..
			if (q['ignorecase'] == 1){
				delete q['ignorecase'];
			}
			if (q['boolmode'] == 'AND') {
				delete q['boolmode'];
			}

			qs = '?' + $.param(q);
			window.location = EMEN2WEBROOT + '/query/' + output.join("/") + '/' + qs;
			
		},
		
		getquery: function() {
			var self = this;
			var newq = {};
			var c = [];

			var ignorecase = $('input[name=ignorecase]', this.container).attr('checked');
			var boolmode = $('input[name=boolmode]:checked', this.container).val();

			var xparam = $('input[name=xparam]', this.container).val();
			var yparam = $('input[name=yparam]', this.container).val();
			if (xparam || yparam) {
				newq['xparam'] = xparam;
				newq['yparam'] = yparam;
				newq['formats'] = ['png'];

				// var xmin = $('input[name=xmin]', this.container).val();
				// if (xmin) {newq["xmin"]=xmin}
				// var xmax = $('input[name=xmax]', this.container).val();
				// if (xmax) {newq["xmax"]=xmax}
				// var ymin = $('input[name=ymin]', this.container).val();
				// if (ymin) {newq["ymin"]=ymin}
				// var ymax = $('input[name=ymax]', this.container).val();
				// if (ymax) {newq["ymax"]=ymax}
				// var width = $('input[name=width]', this.container).val();
				// if (width) {newq["width"]=width}
			}

			var rectype = $('input[name=rectype]', this.container).val();			
			var rectype_recurse = $('input[name=rectype_recurse]', this.container).attr('checked');
			if (rectype_recurse && rectype) {
				rectype = rectype + '*';
			}
			
			if (rectype) {c.push(['rectype', '==', rectype])}

			var creator = $('input[name=creator]', this.container).val();
			if (creator) {c.push(['creator', '==', creator])}


			var parent = $('input[name=parent]', this.container).val();
			var parent_recurse = $('input[name=parent_recurse]', this.container).attr('checked');
			if (parent_recurse && parent) {
				parent = parent + '*';
			}
			if (parent) {c.push(['parent', 'recid', parent])}

			var child = $('input[name=child]', this.container).val();
			if (child) {c.push(['child', 'recid', child])}

			var q = $('input[name=q]').val();
			if (this.options.ext_q) {
				q = $('input[name=q]', this.options.ext_q).val();
			}
						
			$('.constraints .constraint', this.container).each(function() {
				var param = $('input[name=param]', this).val();
				var cmp = $('select[name=cmp]', this).val();
				var value = $('input[name=value]', this).val();
				var childparams = $('input[name=childparams]', this).attr('checked');
				var parents = $('input[name=parents]', this).attr('checked');
				if (param && childparams) {param = param+'*'}
				if (param && parents) {param = param+'^'}
				if (param && cmp) { c.push([param, cmp, value]) }
			});
			
			newq['c'] = c;
			
			if (ignorecase) {newq['ignorecase'] = 1}
			if (boolmode) {newq['boolmode'] = boolmode}
			if (q) {newq['q'] = q}		
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
			var childparams = false;
			var parents = false;
			var self = this;
			var cmpi = this.build_cmp(cmp);

			if (param.indexOf('*') != -1) {
				param = param.replace('*', '');
				childparams = true;
			}	
			
			if (param.indexOf('^') != -1) {
				param = param.replace('^', '');
				parents = true;
			}	

			var newconstraint = $('<tr class="constraint">')
				.append('<td><input type="text" name="param" value="'+param+'" size="15" /></td>')
				.append($('<td/>').append(cmpi))
				.append('<td><input type="text" name="value" value="'+value+'" size="10"  /></td>')
				.append('<td><input name="childparams" type="checkbox" />')
				.append('<td><input name="parents" type="checkbox" />');

			if (childparams) {$('input[name=childparams]', newconstraint).attr('checked', 'checked')}
			if (parents) {$('input[name=parents]', newconstraint).attr('checked', 'checked')}

			var controls = $('<td />');

			var addimg = $('<img class="listicon" src="'+EMEN2WEBROOT+'/static/images/add_small.png" alt="Add" />');
			addimg.click(function() {self.addconstraint()});

			var removeimg = $('<img  class="listicon" src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" />');
			removeimg.click(function() {
				if ($('.constraints .constraint', self.element).length > 1) {$(this).parent().parent().remove()}
			});

			controls.append(addimg, removeimg);
			newconstraint.append(controls);
			$('input[name=param]', newconstraint).FindControl({mode: 'findparamdef'});
			$('.constraints', this.container).append(newconstraint);
		},
		
		build_cmp: function(cmp) {
			var comparators = {
				"==":"is",
				"!=":"is not",
				"contains":"contains",
				"!contains":"does not contain",
				">":"is greater than",
				"<":"is less than",
				">=":"is greater or equal than",
				"<=":"is less or equal than",
				"!None":"is any value"
			}
			var i = $('<select name="cmp" />');
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
			$('.constraints tbody', this.container).empty();

			// if (this.options.q['q'] != null) { // ? wtf in IE
			// 	$('input[name=q]', this.container).val(this.options.q['q']);
			// }
			if (this.options.ext_q) {
				$('input[name=q]', this.options.ext_q).val(this.options.q['q']);				
			}

			$.each(this.options.q['c'], function() {

				if (this[0] == 'rectype' && this[1] == '==') {

					if (this[2].indexOf('*') > -1) {
						this[2] = this[2].replace('*', '');
						$('input[name=rectype_recurse]', this.container).attr('checked', 'checked')
					}
					$('input[name=rectype]', self.container).val(this[2])

				} else if (this[0] == 'creator' && this[1] == 'recid') {

					$('input[name=creator]', self.container).val(this[2])

				} else if (this[0] == 'parent' && this[1] == 'recid') {
					this[2] = String(this[2]);
					if (this[2].indexOf('*') > -1) {
						this[2] = this[2].replace('*', '');
						$('input[name=parent_recurse]', this.container).attr('checked', 'checked');
					}					
					$('input[name=parent]', self.container).val(this[2]);

				} else {

					self.addconstraint(this[0], this[1], this[2]);

				}
			});
			
			this.addconstraint();
			if (this.options.q['ignorecase']) {
				$('input[name=ignorecase]', this.container).attr('checked', 'checked')
			}

		},		
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);
