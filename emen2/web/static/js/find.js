(function($) {

	$.widget('emen2.InfoBox', {
		options: {
			name: null,
			keytype: null,
			time: null,
			title: null,
			body: null,
			deleteable: false,
			autolink: false
		},
		
		_create: function() {
			var self = this;
			this.tryget = false;
			this.built = 0;
			this.build();
		},
		
		build: function() {
			var self = this;
			if (this.built) {return}
			var item = caches[this.options.keytype][this.options.name];
			if (!item) {
				$.jsonRPC.call('get', {
					keytype: this.options.keytype,
					names: this.options.name
				}, function(item) {
					caches[item.keytype][item.name] = item;
					self.build();
				});
				return
			}

			var title = '';
			var body = '';
			if (this.options.keytype == 'user') {
				title = this.options.title || item.displayname || item.name;
				body = this.options.body || item.email;
			} else if (this.options.keytype == 'group') {
				title = item.displayname || item.name;
				var count = 0;
				for (var i=0;i<item['permissions'].length;i++) {
					count += item['permissions'][i].length;
				}
				body = count+' members'
			} else {
				title = item.desc_short;
				body = ''
			}
			
			var link = '';
			if (this.options.autolink) {
				var link = EMEN2WEBROOT+'/'+this.options.keytype+'/'+this.options.name+'/';
			}

			this.element.addClass('e2-infobox');
			this.element.attr('data-name', this.options.name);
			this.element.attr('data-keytype', this.options.keytype);

			var h4 = $('<h4 />');
			if (link) {
				title = '<a href="'+link+'">'+title+'</a>';
			}
			h4.append(title);
			if (this.options.time) {
				// h4.append(' @ '+this.options.time);
				// <abbr class="timeago" title="2008-07-17T09:24:17Z">July 17, 2008</abbr>
				h4.append('<time class="e2-timeago e2l-float-right" datetime="'+this.options.time+'">'+this.options.time+'</time>');
			}
			var p = $('<p class="small" />');
			p.append(body);
			
			var src = EMEN2WEBROOT+'/static/images/nophoto.png';
			if (this.options.keytype == 'user' && item.userrec['person_photo']) {
				src = EMEN2WEBROOT+'/download/'+item.userrec['person_photo']+'/?size=thumb';
			}
			var img = $('<img data-src="'+src+'" src="'+src+'" class="e2l-thumbnail" alt="Photo" />');
			if (link) {img = $('<a href="'+link+'" />').append(img)}
			this.element.append(img, h4, p);

			if (this.options.deleteable) {
				//this.element.append('<img class="delete" src="'+EMEN2WEBROOT+'/static/images/delete.png" alt="Remove" />');
				$(this.element).hover(function(){
					$('img.e2l-thumbnail', this).attr('src', EMEN2WEBROOT+'/static/images/delete.png');
				}, function() {
					$('img.e2l-thumbnail', this).attr('src', $('img.e2l-thumbnail', this).attr('data-src'));
				})
				
			}
			// console.log('time.e2-timeago');
			// $('time.e2-timeago', this.element).timeago();
			this.built = 1;
		}
	});
	
	

    $.widget("emen2.QuerySelectControl", {
		options: {
			rectype: null,
			children: null,
			show: false,
			cb_select: function(name) {}
		},
		
		_create: function() {
			var self = this;
			this.options.rectype = this.element.attr('data-rectype') || this.options.rectype;			
			if (this.options.show) {
				this.build();				
			} else {
				this.element.click(function(){self.build()});
			}
		},

		build: function() {
			var self = this;
			this.dialog = $('<div><img class="e2l-spinner" src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /></div>');
			this.element.append(this.dialog);
			this.dialog.attr("title", "Select Record");
			
			var c = [];
			if (this.options.rectype) {
				c.push(['rectype','==',this.options.rectype]);
			}
			if (this.options.children) {
				c.push(['children','==',this.options.children]);
			}
			var query = {
				'c':c,
			}

			$.jsonRPC.call("query", query, function(data) {
				var recs = data['names'];
				var rq = {
					'names':recs,
					'viewdef': '$@recname() $$creator $$creationtime',
					'table': true,
					'markup': false
				}
				
				$.jsonRPC.call('renderview', rq, function(rendered) {
					self.dialog.empty();
					var table = $('<table cellspacing="0" cellpadding="0"><thead></thead><tbody></tbody></table>');
					var trh = $('<tr/>');
					$.each(rendered['headers'][null], function() {
						trh.append('<th>'+this[0]+'</th>');
					});

					for (var i=0;i<recs.length;i++) {
						var row = rendered[recs[i]];
						var tr = $('<tr/>');
						if (i%2) {
							tr.addClass('s');
						}
						
						for (var j=0;j<row.length;j++) {
							var td = $('<td data-name="'+recs[i]+'" class="clickable">'+row[j]+'</td>');
							tr.append(td);
						}
						$('tbody', table).append(tr);
					}

					$('thead', table).append(trh)
					self.dialog.append(table);
					
					$('.clickable', table).click(function() {
						var name = $(this).attr('data-name');
						self.options.cb_select(name);
						self.dialog.dialog('close');
					});

				});
			});

			if (!this.options.embed) {
				this.dialog.dialog({
					width: 800,
					height: $(window).height()*0.8,
					modal: true,
					autoOpen: true
				});
			}
		}
	});
})(jQuery);




(function($) {
    $.widget("emen2.FindControl", {

		options: {
			show: 0,
			keytype: 'user',
			value: '',
			modal: true,
			vartype: null,
			minimum: 2,
			cb: function(self, value){self.element.val(value)}
		},
				
		_create: function() {
			this.built = 0;
			var self=this;
			this.element.click(function(e){self.event_click(e);})
			if (this.options.show) {
				this.show();
			}
		},
	
	
		build: function() {
			if (this.built) {
				return
			}
			var self = this;
			this.built = 1;

			this.dialog = $('<div/>');
			if (this.options.keytype == 'user'){
				this.dialog.attr('title', 'Find User');
			} else if (this.options.keytype == 'group') {
				this.dialog.attr('title', 'Find Group');			
			} else if (this.options.keytype == 'paramdef') {
				this.dialog.attr('title', 'Find Parameter');
			} else if (this.options.keytype == 'recorddef') {
				this.dialog.attr('title', 'Find Protocol');
			}
		
			this.searchinput = $('<input type="text" />');
			this.searchinput.val(this.options.value);

			this.searchinput.keyup(function(e) {
				var v = self.searchinput.val();
				// ian: this should only work for exact matches..
				if (e.keyCode == '13') { 
					e.preventDefault();
					var check = $('[data-name='+v+']');
					if (check.length) {
						self.select(v);
					}
				}
				self.search(v);
			});

			this.statusmsg = $('<span class="e2l-float-right">No Results</span>');
			var searchbox = $('<div class="e2l-searchbox">Search: </div>');
			searchbox.append(this.searchinput, this.statusmsg); //,this.searchbutton
			this.resultsarea = $('<div>Results</div>');
		
			this.dialog.append(searchbox, this.resultsarea);
			this.dialog.dialog({
				modal: this.options.modal,
				autoOpen: false,
				width: 700,
				height: 400
			});
			
			$('.ui-dialog-titlebar', this.dialog.dialog('widget')).append('<span class="e2l-spinner hide"><img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /></span>');		
		},

		event_click: function(e) {
			this.show();
		},
	
		show: function() {
			this.build();		
			if (this.element.val() != "+") {
				this.searchinput.val(this.element.val());
				this.options.value = this.searchinput.val();
			}
			this.dialog.dialog('open');
			this.search(this.options.value);		
			this.searchinput.focus();
		},

		select: function(name) {
			//this.elem.val(name);
			this.options.cb(this, name);
			this.dialog.dialog('close');		
		},
	
		add: function(item) {
			var self = this;
			caches[item.keytype][item.name] = item;
			var d = $('<div />');
			d.InfoBox({
				keytype: this.options.keytype,
				name: item.name
			});
			d.click(function(e){
				self.select(item.name);
				});
			this.resultsarea.append(d);
		},
	
		search: function(q) {
			var self=this;
			if (q.length < this.options.minimum) {
				self.resultsarea.empty();
				self.statusmsg.text('Minimum '+this.options.minimum+' characters');
				return
			}
			
			$('.e2l-spinner', this.dialog.dialog('widget')).show();
			
			var query = {}
			query['query'] = q;
			if (this.options.vartype) {
				query['vartype'] = this.options.vartype;
			}
				
			$.jsonRPC.call('find'+this.options.keytype, query, function(items) {
				$('.e2l-spinner', self.dialog.dialog('widget')).hide();				
				self.resultsarea.empty();
				var l = items.length;
				if (l==0) {
					self.statusmsg.text('No results');
					return
				}
				if (l>50) {
					self.statusmsg.text(items.length + ' results; showing 1-50');
				} else {
					self.statusmsg.text(items.length + ' results');				
				}
				items = items.slice(0,50);
				$.each(items, function() {
					self.add(this)			
				});
			})
		}
	});
	
})(jQuery);
