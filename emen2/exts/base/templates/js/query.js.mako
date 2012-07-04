(function($) {
	
	$.query_build_path = function(q, postpend) {
		var comparators_lookup = {
			">": "gt",
			"<": "lt",
			">=": "gte",
			"<=": "lte",
			"==": "is",
			"!=": "not"				
		}
		var output = [];
		
		$.each(q['c'], function() {
			output.push(encodeURIComponent(this[0])+'.'+(comparators_lookup[this[1]] || this[1])+'.'+encodeURIComponent(this[2]));
		});
		delete q['c'];

		if (postpend) {
			output.push(postpend);
		}

		// remove some default arguments..
		// if (q['ignorecase'] == 1){
		delete q['ignorecase'];
		// }
		// if (q['boolmode'] == 'AND') {
		delete q['boolmode'];
		// }
		qs = '?' + $.param(q);
		return EMEN2WEBROOT + '/query/' + output.join("/") + '/' + qs;
	}


	$.widget('emen2.QueryStatsControl', {
		options: {
			q: null
		},
		
		_create: function() {
			var self = this;
			this.built = 0;
			// Check cache
			var rds = [];
			var stats = this.options.q['stats'];
			$.each(stats['rectypes'], function(k,v){
				if (emen2.caches['recorddef'][k]==null){rds.push(k)}
			});
			// Fetch any RecordDefs we need
			if (rds) {
				emen2.db('recorddef.get',[rds], function(items) {
					$.each(items, function(k,v){
						emen2.caches['recorddef'][v.name] = v;
					});
					self.build();
				})
			} else {
				this.build();
			}
		},
		
		build: function() {
			if (this.built) {return}
			this.element.empty();
			
			var stats = this.options.q['stats'];
			var d = $('<div></div>');			
			d.append('<h4>Protocols</h4>')
			var table = $('<table class="e2l-kv"></table>');
			$.each(stats['rectypes'] || {}, function(k,v){
				var name = k;
				if (emen2.caches['recorddef'][k]) {
					name = emen2.caches['recorddef'][k].desc_short
				}
				var row = $('<tr><td>'+name+'</td><td>'+v+'</td></tr>');
				table.append(row);
			});
			d.append(table);
			
			this.element.append(d);
			//this.built = 1;
		},
	
	});


    $.widget("emen2.QueryControl", {
		options: {
			q: null,
			show: true,
			query: function(self, q){self.query_bookmark(self, q)}
		},
				
		_create: function() {

			this.comparators = {
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

			this.comparators_lookup = {
				">": "gt",
				"<": "lt",
				">=": "gte",
				"<=": "lte",
				"==": "is",
				"!=": "not"				
			}

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
			this.container = $('<div class="e2l-cf" />');
						
			var m = $(' \
				<table cellpadding="0" cellspacing="0" class="e2l-shaded" > \
					<thead> \
						<tr> \
							<th>Parameter</th> \
							<th></th> \
							<th>Value</th> \
							<th></th> \
							<th>'+emen2.template.image('remove_small.png', 'Remove', 'e2-query-clear-all')+' Reset</th> \
						</tr> \
					</thead> \
					<tbody class="e2-query-base e2-query-constraints"> \
						<tr> \
							<td><input type="hidden" name="param" value="*" />Keywords</td> \
							<td><input type="hidden" name="cmp" value="contains" /></td> \
							<td><input type="text" size="12" name="value" /></td> \
							<td><input type="checkbox" name="recurse_p" checked="checked" class="e2l-hide" /></td> \
							<td>'+emen2.template.image('remove_small.png', 'Remove', 'e2-query-clear')+'</td> \
						</tr><tr> \
							<td><input type="hidden" name="param" value="rectype" />Protocol</td> \
							<td><input type="hidden" name="cmp" value="is" /></td> \
							<td><input type="text" size="12" name="value" class="e2-find-recorddef" /></td> \
							<td><input type="checkbox" name="recurse_v" /><label>Child Protocols</label></td> \
							<td>'+emen2.template.image('remove_small.png', 'Remove', 'e2-query-clear')+'</td> \
						</tr><tr> \
							<td><input type="hidden" name="param" value="creator" />Creator</td> \
							<td><input type="hidden" name="cmp" value="is" /></td> \
							<td><input type="text" size="12" name="value" class="e2-find-user" /></td> \
							<td></td> \
							<td>'+emen2.template.image('remove_small.png', 'Remove', 'e2-query-clear')+'</td> \
						</tr><tr> \
							<td><input type="hidden" name="param" value="permissions" />Permissions</td> \
							<td><input type="hidden" name="cmp" value="contains" /></td> \
							<td><input type="text" size="12" name="value" class="e2-find-user" /></td> \
							<td></td> \
							<td>'+emen2.template.image('remove_small.png', 'Remove', 'e2-query-clear')+'</td> \
						</tr><tr> \
							<td><input type="hidden" name="param" value="groups" />Groups</td> \
							<td><input type="hidden" name="cmp" value="contains" /></td> \
							<td><input type="text" size="12" name="value" class="e2-find-group" /></td> \
							<td></td> \
							<td>'+emen2.template.image('remove_small.png', 'Remove', 'e2-query-clear')+'</td> \
						</tr><tr> \
							<td><input type="hidden" name="param" value="children" />Child Of</td> \
							<td><input type="hidden" name="cmp" value="name" /></td> \
							<td><input type="text" size="12" name="value" class="e2-find-record" /></td> \
							<td><input type="checkbox" name="recurse_v" /><label>Recursive</label></td> \
							<td>'+emen2.template.image('remove_small.png', 'Remove', 'e2-query-clear')+'</td> \
						</tr> \
					</tbody> \
					<tbody class="e2-query-param e2-query-constraints"></tbody> \
				</table> \
				');

			this.container.append(m);
			
			// ian: todo
			$('.e2-find-user', this.container).FindControl({keytype: 'user'});
			$('.e2-find-group', this.container).FindControl({keytype: 'group'});
			$('.e2-find-recorddef', this.container).FindControl({keytype: 'recorddef'});
			$('.e2-find-paramdef', this.container).FindControl({keytype: 'paramdef'});

			var save = $('<div class="e2l-controls"> \
				'+emen2.template.spinner()+' \
				<input type="button" value="Query" name="save" /></div>');				
			this.container.append(save);
			$('input[name=save]', this.container).bind("click", function(e){self.query()});			

			$('.e2-query-clear-all', this.container).click(function(e) {
				$('.e2-query-constraints tr').each(function(){self.clear($(this))});
			});

			$('.e2-query-clear', this.container).click(function(e) {
				self.event_clear(e);
			});
			
			this.element.append(this.container);						
			this.update();
		},
		
		event_clear: function(e) {
			var t = $(e.target).parent().parent();
			this.clear(t);
		},
		
		clear: function(t) {
			var base = t.parent().hasClass('e2-query-base');
			$('input[name=value]', t).val('')
			$('input[name=recurse_p]', t).attr('checked', null);
			$('input[name=recurse_v]', t).attr('checked', null);
			if (!base) {
				$('input[name=param]', t).val('');
				$('select[name=cmp]', t).val('any');
			}			
		},
				
		query_bookmark: function(self, q) {
			window.location = $.query_build_path(q);
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
									
			$('.e2-query-base tr', this.container).each(function() {
				var p = self._getconstraint(this);
				if (p[0] && p[1] && p[2]) {c.push(p)}
			});
			$('.e2-query-param tr', this.container).each(function() {
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
			this.options.query(this, newq);
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

			var addimg = $(emen2.template.image('add_small.png', 'Add'))
			addimg.click(function() {self.addconstraint()});

			var removeimg = $(emen2.template.image('remove_small.png', 'Remove', 'e2-query-clear'))
			removeimg.click(function(e) {
				self.event_clear(e);
			});

			controls.append(addimg, removeimg);
			newconstraint.append(controls);
			$('input[name=param]', newconstraint).FindControl({keytype: 'paramdef'});
			$('.e2-query-param', this.container).append(newconstraint);
		},
		
		build_cmp: function(cmp) {
			//"!contains":"does not contain",
			// Check the transforms..
			var cmp2 = this.comparators_lookup[cmp] || cmp;
			
			var i = $('<select name="cmp" />');
			$.each(this.comparators, function(k,v) {
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


			cmpi = this.comparators_lookup[cmpi] || cmpi;
			
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
			var selector = '.e2-query-param tr';
			var param_constraints = [];
			if (base) {
				var selector = '.e2-query-base tr';
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
		}
	});
	
	/***** Table Control *****/
	
    $.widget("emen2.TableControl", {
		options: {
			q: null,
			create: null,
			parent: null,
			header: true,
			controls: true
		},
				
		_create: function() {
			this.build();
		},
		
		build: function() {
			if (this.options.controls) {
				// Rebuild the controls
				this.build_controls();
				// Set the control values from the current query state
				this.update_controls();
				// Rebind to table header controls
				this.rebuild_thead();
			}
		
			if (this.options.header) {				
			}
		},
		
		build_controls: function() {
			var self = this;

			// Tab control
			var tab = $('.e2-tab', this.element)
			var ul = $('.e2-tab ul', this.element);
			
			// Statistics
			ul.append('<li><span class="e2-query-length">Records</span></li>'); //'+emen2.template.caret()+'
			ul.append('<li data-tab="controls"><span class="e2l-a">Query '+emen2.template.caret()+'</span></li>')

			// Edit
			ul.append('<li data-tab="edit"><span class="e2l-a">Edit '+emen2.template.caret()+'</span></li>')

			// Plotting
			// ul.append('<li data-tab="plot"><span class="e2l-a">Plot '+emen2.template.caret()+'</span></li>')

			// Pages
			ul.append('<li class="e2l-float-right e2-query-pages"></li>');

			// Row count
			var count = $('<select name="count" class="e2l-small"></select>');
			count.append('<option value="100">Rows</option>');
			$.each([1, 10,100,1000], function() {
				count.append('<option value="'+this+'">'+this+'</option>');
			});
			count.change(function() {
				self.options.q['pos'] = 0;
				self.query();
			})			
			count = $('<li class="e2l-float-right" />').append($('<span class="e2l-a"></span>').append(count));
			ul.append(count);

			// Create new record
			// if (this.options.rectype && this.options.parent != null) {
			if (this.options.rectype != null && this.options.parent != null) {
				var create = $(' \
					<li class="e2l-float-right"> \
						<span> \
						<form action="'+EMEN2WEBROOT+'/record/'+this.options.parent+'/new/'+this.options.rectype+'/" method="get"> \
							<input type="button" data-rectype="'+this.options.rectype+'" data-parent="'+this.options.parent+'" value="New '+this.options.rectype+'" /> \
						</form> \
						</span> \
					</li>');
				ul.append(create);
				// <input type="button" data-rectype="'+this.options.rectype+'" data-parent="'+this.options.parent+'" value="New '+this.options.rectype+'" />
				$('input[type=button]', create).RecordControl();
			}			


			// Download all attachments
			ul.append('<li class="e2l-float-right"><span><input type="button"  class="e2-query-download" value="Download attachments" /></span></li>')
			$('.e2-query-download', ul).click(function() {self.query_download()});

			// Activity spinner
			ul.append('<li class="e2l-float-right e2-query-activity" style="display:none"><span>'+emen2.template.spinner(true)+'</span></li>');

			// Init tab control
			tab.TabControl({});

			// Add callbacks
			tab.TabControl('setcb', 'stats', function(page) {
				page.QueryStatsControl({
					q: self.options.q,
					show: true
				})
			});
			
			tab.TabControl('setcb', 'controls', function(page) {
				page.QueryControl({
					q: self.options.q,
					keywords: false
					// query: function(test, newq) {self.query(newq)} 
				});	
			});
			
			tab.TabControl('setcb', 'plot', function(page) {
				page.PlotControl({
					q: self.options.q
				});	
			});			
			
			tab.TabControl('setcb', 'edit', function(page) {
				var form = $('form.e2-query-tableform');
				form.MultiEditControl({
					selector: '.e2-edit',
					controls: page,
					prefix: true
				});
				form.MultiEditControl('show');
			});
			tab.TabControl('sethidecb', 'edit', function(page) {
				var form = $('form.e2-query-tableform');				
				form.MultiEditControl('hide');	
			});	
			
			if (this.options.qc) {
				tab.TabControl('show', 'controls');
			}
					
		},
		
		query_download: function() {
			// Get all the binaries in this table, and prepare a download link.
			var newq = {};
			newq['c'] = this.options.q['c'];
			newq['boolmode'] = this.options.q['boolmode'];
			newq['ignorecase'] = this.options.q['ignorecase'];
			window.location = $.query_build_path(newq, 'attachments');
		},
				
		query: function(newq) {
			$('.e2-query-activity', this.element).show();
			// Update the query from the current settings
			newq = newq || this.options.q;
			$('.e2-query-header .e2l-spinner', this.element).show();
			var self = this;
			var count = $('.e2-query-header select[name=count]', this.element).val();
			if (count) {newq["count"] = parseInt(count)}
			newq['names'] = [];
			newq['recs'] = true;
			newq['table'] = true;
			emen2.db("table", newq, function(q){self.update(q)});			
		},
		
		query_bookmark: function(newq) {
		},
		
		setpos: function(pos) {
			// Change the page
			if (pos == this.options.q['pos']) {return}
			var self = this;
			this.options.q['pos'] = pos;
			this.query();
		},
		
		resort: function(sortkey, args) {
			// Sort by a column key
			if (args) {
				sortkey = '$@' + sortkey + "(" + args + ")"
			}
			if (this.options.q['sortkey'] == sortkey) {
				this.options.q['reverse'] = (this.options.q['reverse']) ? false : true;
			} else {
				this.options.q['reverse'] = false;
			}
			this.options.q['sortkey'] = sortkey;
			this.query();
			// this.query_bookmark();
		},
		
		update: function(q) {
			// Callback from a query; Update the table and all controls
			this.options.q = q;
			$('.e2-query-control', this.element).QueryControl('update', this.options.q)					

			this.update_controls();
			this.rebuild_table();
			this.options.q['stats'] = true;
			$('.e2-query-activity', this.element).hide();					
		},	
		
		update_controls: function() {
			// Update the table controls
			var self = this;

			// Update the title bar information
			var title = '';
			var rtkeys = [];
			for (i in this.options.q['stats']['rectypes']) {
				rtkeys.push(i);
			}
			rtkeys.sort();
			
			
			// Build a nice string for the title
			// This gives basic query statistics
			title = this.options.q['stats']['length'] + ' records, ' + rtkeys.length + ' protocols';
			if (rtkeys.length == 0) {
				title = this.options.q['stats']['length'] + ' records';				
			} else if (rtkeys.length == 1) {
				title = this.options.q['stats']['length'] + ' ' + rtkeys[0] + ' records';
			} else if (rtkeys.length <= 5) {
				title = title + ": ";
				for (var i=0;i<rtkeys.length;i++) {
					title = title + self.options.q['stats']['rectypes'][rtkeys[i]] + ' ' + rtkeys[i];
					if (i+1<rtkeys.length) {
						title = title + ', ';
					}
				}
			}
			if (this.options.q['stats']['time']) {
				title = title + ' ('+this.options.q['stats']['time'].toFixed(2)+'s)';
			}
			$('.e2-query-header .e2-query-length').html(title);

			// Update the page count
			var pages = $('li.e2-query-pages', this.element);
			pages.empty();
			var pc = $('<span class="e2-query-extraspacing"></span>');
			
			// ... build the pagination controls
			var count = this.options.q['count'];
			var l = this.options.q['stats']['length'];
			if (count == 0 || count > l || l == 0) {
				//pages.append("All Records");
			} else {			
				var current = (this.options.q['pos'] / this.options.q['count']);
				var pagecount = Math.ceil(this.options.q['stats']['length'] / this.options.q['count'])-1;
				var setpos = function() {self.setpos(parseInt($(this).attr('data-pos')))}			

				var p1 = $('<span class="e2l-a" data-pos="0">&laquo;</span>').click(setpos);
				var p2 = $('<span class="e2l-a" data-pos="'+(this.options.q['pos'] - this.options.q['count'])+'">&lsaquo;</span>').click(setpos);
				var p  = $('<span> '+(current+1)+' / '+(pagecount+1)+' </span>');
				var p3 = $('<span class="e2l-a" data-pos="'+(this.options.q['pos'] + this.options.q['count'])+'">&rsaquo;</span>').click(setpos);
				var p4 = $('<span class="e2l-a" data-pos="'+(pagecount*this.options.q['count'])+'">&raquo;</span>').click(setpos);

				if (current > 0) {pc.prepend(p2)}
				if (current > 1) {pc.prepend(p1, '')}
				pc.append(p);
				if (current < pagecount) {pc.append(p3)}
				if (current < pagecount - 1) {pc.append('', p4)}
				pages.append(pc);
			}
		},
				
		
		rebuild_table: function() {
			// Rebuild everything
			this.rebuild_thead();
			this.rebuild_tbody();
		},
				
		rebuild_thead: function() {
			// Rebuild the table header after each update			
			var self = this;
			var t = $('.e2-query-table', this.element);

			// The query result includes details about columns
			var headers = this.options.q['table']['headers']['null'];
			
			// Clear out the current header
			$('thead', t).empty();
			
			// ian: todo: Check 'immutable' attr
			var immutable = ["creator","creationtime","modifyuser","modifytime","history","name","rectype","keytype","parents","children"];
			
			var tr = $('<tr />');
			var tr2 = $('<tr class="e2-query-sort"/>');
			// Build the check boxes for selecting records
			// tr.append('<th><input type="checkbox" /></th>');

			// Build the rest of the column headers
			$.each(headers, function() {
				if (this[3] == null) {
					this[3]=''
				}
				tr.append('<th>'+this[0]+'</th>');


				// Build the sort button
				var direction = 'able';
				if (self.options.q['sortkey'] == this[2] || self.options.q['sortkey'] == '$@'+this[2]+'('+this[3]+')') {
					var direction = 1;
					if (self.options.q['reverse']) {direction = 0}
				}				
				var sortable = $('<button name="sort" class="e2l-float-right">'+emen2.template.image('sort.'+direction+'.png', 'Sort')+'</button>');
				var iw = $('<th data-name="'+this[2]+'" data-args="'+this[3]+'" ></th>');				
				iw.append(sortable);
				tr2.append(iw)
			});

			// Connect the sort and edit buttons
			$('button[name=sort]', tr2).click(function(e){
				e.preventDefault();
				self.resort($(this).parent().attr('data-name'), $(this).parent().attr('data-args'))
			});
			
			// Append the title row and control row
			$('thead', t).append(tr, tr2);
		},
		
		rebuild_tbody: function() {
			// Rebuild the table body
			var self = this;
			var t = $('.e2-query-table', this.element);			
			var headers = this.options.q['table']['headers']['null'];
			var names = this.options.q['names'];
			var rows = []			

			// Empty results
			if (names.length == 0) {
				var row = '<tr><td>No Records found for this query.</td</tr>';
				rows.push(row);
			}

			// Build each row
			for (var i=0;i<names.length;i++) {
				var row = [];
				for (var j=0;j<headers.length;j++) {
					row.push('<td>'+self.options.q['table'][names[i]][j]+'</td>');
				}
				row = '<tr>' + row.join('') + '</tr>';					
				rows.push(row);
			}
			
			// This was a easonably fast way to do this
			$('tbody', t).empty();
			$('tbody', t).append(rows.join(''));
			$('tbody time').localize();
		}
	});	
	
	
	
})(jQuery);

<%!
public = True
headers = {
	'Content-Type': 'application/javascript',
	'Cache-Control': 'max-age=86400'
}
%>