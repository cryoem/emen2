(function($) {
    $.widget("ui.TableControl", {
		options: {
			q: null,
			qc: true
		},
				
		_create: function() {
			this.build();
		},
		
		build: function() {
			var self = this;
			
			this.cachewidth = {};
			
			// Build control elements

			// record count
			var length = $('<div class="length" style="float:left">Records</div>');
						
			// row count
			var count = $('<select name="count" style="float:right"></select>');
			count.append('<option value="">Rows</option>');
			
			$.each([10,50,100,500,1000], function() {
				count.append('<option value="'+this+'">'+this+'</option>');
			});
			count.change(function() {
				self.options.q['pos'] = 0;
				self.query();
			})			
			count = $('<div class="control" style="float:right"/>').append(count);

			// page controls			
			var pages = $('<div class="control pages" style="float:right">Pages</div>');

			// Bind to control elements
			$('.header', this.element).append(length, pages, count);


			// Kindof hacky..
			// query bar
			this.attach_querycontrol();

			this.attach_tools();

			var spinner = $('<div style="float:right"><img class="spinner" src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /></div>');
			$('.header', this.element).append(spinner);
						
			$('.plot', this.element).PlotControl({
				q:this.options.q,
				cb: function(test, newq) {self.query(newq)} 
			});						

			// Set the control values from the current query state
			this.update_controls();

			// Rebind to table header controls
			this.rebuild_thead();
			
			// Cache the column widths so they don't go crazy with every refresh
			$(".inner thead th").each(function() {
				self.cachewidth[$(this).attr('data-name')] = $(this).width();
			});			

		},
		
		attach_tools: function() {
			var self = this;
			var q = $('<div class="tools control" style="float:right"><span class="clickable label">\
				Tools <img src="'+EMEN2WEBROOT+'/static/images/caret_small.png" alt="^" /></span></div>');

			var hidden = $('<div class="hidden"><input type="button" name="download" value="Download all files in this table" /></div>');
			$('input[name=download]', hidden).click(function() {self.query_download()});

			q.append(hidden);

			q.EditbarHelper({
				width: 200,
				align: 'right', 
				init: function(self2) {
				}
			});				

			$('.header', this.element).append(q);			

		},
		
		attach_querycontrol: function() {
			if (!this.options.qc) {return}
			
			var self = this;
			
			var q = $('<div class="querycontrol control" style="float:right"><span class="clickable label"> \
				Query <img src="'+EMEN2WEBROOT+'/static/images/caret_small.png" alt="^" /></span></div>');

			q.EditbarHelper({
				align: 'right', 
				width: 700,
				init: function(self2) {
					self2.popup.QueryControl({
						q: self.options.q,
						keywords: false,
						cb: function(test, newq) {self.query(newq)} 
					});
				}
			});				

			// $('input[name=q]', q).focus(function(){
			// 	q.EditbarHelper('show');
			// });
			// 		
			// $('img', q).click(function(){
			// 	q.EditbarHelper('toggle');
			// });
			
			$('.header', this.element).append(q);
			
		},
		
		query_download: function() {
			// Get all the binaries in this table, and prepare a download link.
			var newq = {};
			newq['c'] = this.options.q['c'];
			newq['q'] = this.options.q['q'];
			newq['boolmode'] = this.options.q['boolmode'];
			newq['ignorecase'] = this.options.q['ignorecase'];
			// this doesn't work, because it won't trigger a Save-As
			// $.postJSON(EMEN2WEBROOT+'/download/archive.tar', {'q':newq});
			var f = $('<form action="'+EMEN2WEBROOT+'/query/files/" method="post"></form>')
			var i = $('<input type="text" name="q___json" />');
			i.val($.toJSON(newq));
			f.append(i);
			f.appendTo('body').submit().remove();

		},
		
		query: function(newq) {
			newq = newq || this.options.q;
			$('.header .spinner', this.element).show();
			var self = this;
			var count = $('.header select[name=count]').val();
			if (count) {newq["count"] = parseInt(count)}
			newq['plots'] = null;
			newq["rendered"] = {};
			newq['recids'] = [];
			$.jsonRPC("querytable", newq, function(q){self.update(q)});			
		},
		
		setpos: function(pos) {
			if (pos == this.options.q['pos']) {return}
			var self = this;
			this.options.q['pos'] = pos;
			this.query();
		},
		
		resort: function(sortkey, args) {
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
		},
		
		update: function(q) {
			this.options.q = q;
			$('.plot', this.element).PlotControl('update', this.options.q);
			$('.header .query').QueryControl('update', this.options.q)					
			$('.header .querycontrol').EditbarHelper('hide');
			this.update_controls();
			this.rebuild_table();	
			$('.header .spinner', this.element).hide();					
		},	
		
		update_controls: function() {
			var self = this;
			
			$('.header .length').html(this.options.q['length'] + ' Records');			
			// $('.header select[name=count]').val(this.options.q['count']);
			
			var current = (this.options.q['pos'] / this.options.q['count']);
			var pagecount = Math.ceil(this.options.q['length'] / this.options.q['count'])-1;
			var pages = $('.header .pages');
			pages.empty();
			
			var setpos = function() {self.setpos(parseInt($(this).attr('data-pos')))}			
			
			var p1 = $('<span data-pos="0" class="clickable clickable_box">&laquo;</span>').click(setpos);
			var p2 = $('<span data-pos="'+(this.options.q['pos'] - this.options.q['count'])+'" class="clickable clickable_box">&lsaquo;</span>').click(setpos);
			var pc = $('<span> '+(current+1)+' / '+(pagecount+1)+' </span>');
			var p3 = $('<span data-pos="'+(this.options.q['pos'] + this.options.q['count'])+'" class="clickable clickable_box">&rsaquo;</span>').click(setpos);
			var p4 = $('<span data-pos="'+(pagecount*this.options.q['count'])+'" class="clickable clickable_box">&raquo;</span>').click(setpos);
			if (current > 0) {pages.prepend(p2)}
			if (current > 1) {pages.prepend(p1, '')}
			pages.append(pc);
			if (current < pagecount) {pages.append(p3)}
			if (current < pagecount - 1) {pages.append('', p4)}
		},
				
		
		rebuild_table: function() {
			this.rebuild_plot();
			this.rebuild_thead();
			this.rebuild_tbody();
		},
		
		
		rebuild_plot: function() {
			//
			//"plots": {"png": "/data/tmp/2bf6df53a73d5160ceb9b202e0977c28aa7143a8-plot-2010.09.01-15.41.19.png"}
			// $('.plot', this.element).empty();
			// if (this.options.q['plots']) {
			// 	var pngfile = this.options.q['plots']['png'];
			// 	var i = $('<img src="'+EMEN2WEBROOT+'/download/tmp/'+pngfile+'" alt="Plot" />');
			// 	$('.plot', this.element).append(i);				
			// }
		},
		
		rebuild_thead: function() {
			//<th data-name="${v[1]}" data-args="${v[2]}">${v[0]}</th>
			
			var self = this;
			var t = $('.inner', this.element);
			$('thead', t).empty();
			var headers = this.options.q['rendered']['headers']['null'];			
			
			var tr = $('<tr />');
			$.each(headers, function() {
				
				if (this[3] == null) {
					this[3]=''
				}
				var i = $('<th style="position:relative" data-name="'+this[2]+'" data-args="'+this[3]+'" >'+this[0]+'</th>');

				// An editable, sortable field..
				if (this[1] == "$") {
					var editable = $('<img style="float:right" src="'+EMEN2WEBROOT+'/static/images/edit.png" alt="Edit" />');
					editable.click(function(e){self.event_edit(e)});
					i.append(editable);
				}

				var direction = 'able';
				if (self.options.q['sortkey'] == this[2] || self.options.q['sortkey'] == '$@'+this[2]+'('+this[3]+')') {
					var direction = 1;
					if (self.options.q['reverse']) {direction = 0}
				}
				
				var sortable = $('<img style="float:right" src="'+EMEN2WEBROOT+'/static/images/sort_'+direction+'.png" alt="Sort: '+direction+'" />');
				sortable.click(function(){self.resort($(this).parent().attr('data-name'), $(this).parent().attr('data-args'))});
				i.append(sortable);
				
				i.width(self.cachewidth[this[2]]);
				tr.append(i);
			});
						
			$('thead', t).append(tr);
		},
		
		
		rebuild_tbody: function() {
			var self = this;
			var t = $('.inner', this.element);			
			var headers = this.options.q['rendered']['headers']['null'];
			var recids = this.options.q['recids'];
			
			var rows = []
			for (var i=0;i<recids.length;i++) {
				var row = [];
				for (var j=0;j<headers.length;j++) {
					//row.push('<td>'+self.options.q['rendered'][recids[i]][j]+'</td>'); //
					//row.push('<td><a href="'+EMEN2WEBROOT+'/record/'+recids[i]+'/">'+self.options.q['rendered'][recids[i]][j]+'</a></td>');
					row.push('<td>'+self.options.q['rendered'][recids[i]][j]+'</td>');
				}
				if (i%2) {
					row = '<tr class="s">' + row.join('') + '</tr>';
				} else {
					row = '<tr>' + row.join('') + '</tr>';					
				}
				rows.push(row);
			}
			
			$('tbody', t).empty();
			$('tbody', t).append(rows.join(''));		
		},
		
		event_edit: function(e) {
			if (this.options.q['count'] > 500) {
				var check = confirm('Editing tables with more than 100 rows may use excessive resources. Continue?');
				if (check==false) {return}
			}
			var self = this;
			e.stopPropagation();
			var t = $(e.target);
			var key = t.parent().attr('data-name');
			t.MultiEditControl({
				show: true,
				selector: '.editable[data-param='+key+']',
				cb_save: function(caller){self.query()}
			});
		},
		
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);

