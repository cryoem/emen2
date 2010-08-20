(function($) {
    $.widget("ui.TableControl", {
		options: {
			q: null
		},
				
		_create: function() {
			this.build();
		},
		
		query: function(newq) {
			newq = newq || this.options.q;
			
			var self = this;
			var count = $('.header select[name=count]').val();
			newq["count"] = parseInt(count);
			newq["rendered"] = {};
			
			$.ajax({
				type: 'POST',
				url: EMEN2WEBROOT+'/db/table/',
				dataType: 'json',
			    data: {"args___json":$.toJSON(newq)},
				success: function(q) {self.update(q)}
			});
		},
		
		unique: function(li) {
			var o = {}, i, l = li.length, r = [];
			for(i=0; i<l;i++) o[li[i]] = li[i];
			for(i in o) r.push(o[i]);
			return r;
		},
		
		setpos: function(pos) {
			if (pos == this.options.q['pos']) {return}
			var self = this;
			this.options.q['pos'] = pos;
			this.query();
		},
		
		resort: function(sortkey, args) {
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
			$('.header .query').QueryControl('update', this.options.q)					
			this.update_controls();
			this.rebuild_table();			
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
		
		build: function() {
			var self = this;
			
			this.cachewidth = {};
			
			var length = $('<div class="length" style="float:left">Records</div>');

			var q = $('<div class="control" style="float:right"><input type="text" name="q" size="8" /><input type="button" name="search" value="Search" /><img src="'+EMEN2WEBROOT+'/images/caret_small.png" alt="^" /></div>');
			$('img', q).click(function(){$('.query').toggle()});
			
			
			var count = $('<select name="count" style="float:right"></select>');
			count.append('<option value="100">Rows</option>');
			$.each([10,50,100,500,1000], function() {
				count.append('<option value="'+this+'">'+this+'</option>');
			});
			count.change(function() {
				self.query();
			})
			count = $('<div class="control"  style="float:right"/>').append(count);
						
			var pages = $('<div class="control pages" style="float:right">Pages</div>');

			$('.header', this.element).append(length, pages, count, q);

			$('.header', this.element).QueryControl({
				show: false,
				q: this.options.q,
				cb: function(test, newq) {self.query(newq)} 
			});

			this.update_controls();
			this.rebuild_thead();
			
			$(".inner thead th").each(function() {
				self.cachewidth[$(this).attr('data-name')] = $(this).width();
			});			

		},
		
		rebuild_table: function() {
			this.rebuild_thead();
			this.rebuild_tbody();
		},
		
		rebuild_thead: function() {
			//<th data-name="${v[1]}" data-args="${v[2]}">${v[0]}</th>
			
			var self = this;
			var t = $('.inner', this.element);
			$('thead', t).empty();
			var headers = this.options.q['rendered']['headers']['null'];
			
			var tr = $('<tr />');
			$.each(headers, function() {
				var i = $('<th data-name="'+this[2]+'" data-args="'+this[3]+'" >'+this[0]+'</th>');

				if (this[1] != "@") {
					i.click(function(){self.resort($(this).attr('data-name'), $(this).attr('data-args'))});
				}
				
				if (self.options.q['sortkey'] == this[2]) {
					if (self.options.q['reverse']) {
						i.append('<img src="'+EMEN2WEBROOT+'/images/sort_0.png" />');
					} else {
						i.append('<img src="'+EMEN2WEBROOT+'/images/sort_1.png" />');						
					}
				}				
				i.width(self.cachewidth[this[2]]);
				tr.append(i);
			});
						
			$('thead', t).append(tr);
		},
		
		
		rebuild_tbody: function() {
			var self = this;
			var t = $('.inner', this.element);
			$('tbody', t).empty();
			
			var headers = this.options.q['rendered']['headers']['null'];
			
			$.each(this.options.q['recids'], function(i) {
				var recid = this;
				var r = $('<tr/>');
				$.each(headers, function(j) {
					r.append('<td><a href="'+EMEN2WEBROOT+'/db/record/'+recid+'/">'+self.options.q['rendered'][recid][j]+'</a></td>');
				});
				if (i%2) {
					r.addClass('s');
				}
				
				$('tbody', t).append(r);
			});

		},
		
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);







// var r = [0, current-1, current, current+1, pagecount-1];
// var r = [0, current, pagecount-1];
// r = this.unique(r);
// r = r.sort(function(a,b){return a-b});
// $.each(r, function(i,j) {
// 	if (j >= 0 && j < pagecount) {
// 		if (j > 0 && r[i-1]!=j-1) {pages.append('<span>...</span>')}
// 		var page = $('<span data-pos="'+(j*self.options.q['count'])+'" class="clickable clickable_box">'+(j+1)+'</span>');
// 		page.click(function() {self.setpos(parseInt($(this).attr('data-pos')))});
// 		pages.append(page);
// 	}
// });