(function($) {

	$.widget('emen2.InfoBox', {
		options: {
			name: null,
			keytype: null,
			time: null,
			title: null,
			body: null,
			deleteable: false,
			autolink: false,
			selectable: false,
			// toggle: 'e2-infobox-selected',
			// hover: 'e2-infobox-hover',
			input: ['radio', 'test', false],
			addcb: function(elem){console.log('added', elem)},
			removecb: function(elem){console.log('removed', elem)}
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
				title = $.trim(this.options.title || item.displayname) || item.name;
				body = this.options.body || item.email;
			} else if (this.options.keytype == 'group') {
				title = $.trim(item.displayname) || item.name;
				var count = 0;
				for (var i=0;i<item['permissions'].length;i++) {
					count += item['permissions'][i].length;
				}
				body = count+' members'
			} else {
				title = $.trim(item.desc_short) || item.name;
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
			var p = $('<p class="e2l-small" />');
			p.append(body);
			
			var src = EMEN2WEBROOT+'/static/images/nophoto.png';
			if (this.options.keytype == 'user' && item.userrec['person_photo']) {
				src = EMEN2WEBROOT+'/download/'+item.userrec['person_photo']+'/?size=thumb';
			}
			var img = $('<img data-src="'+src+'" src="'+src+'" class="e2l-thumbnail" alt="Photo" />');
			if (link) {img = $('<a href="'+link+'" />').append(img)}

			// Widget!!
			var input = ''
			if (this.options.selectable && this.options.input) {
				var type = this.options.input[0];
				var name = this.options.input[1];
				var state = this.options.input[2];
				var input = $('<input class="e2-infobox-input" type="'+type+'" name="'+name+'" />');
				input.val(this.options.name);
				input.attr('checked', state);
			}

			// Put it all together..
			this.element.append(img, input, h4, p);
			
			this.element.click(function() {
				var input = $('input', self.element);
				var state = input.attr('checked')
				if (state) {
					input.attr('checked',null);
				} else {
					input.attr('checked','checked');					
				}
			});
			
			// // Hover classes
			// if (this.options.hover) {
			// 	this.element.hover(function(){
			// 		$(this).addClass(self.options.hover);
			// 	}, function() {
			// 		$(this).removeClass(self.options.hover);
			// 	});
			// }
			// 
			// // Selected classes
			// if (this.options.selectable && this.options.toggle) {
			// 	this.element.click(function() {self.toggle($(this))})
			// };

			// $('time.e2-timeago', this.element).timeago();
			this.built = 1;
		},
		
		toggle: function(elem) {
			var keytype = elem.attr('data-keytype');
			var name = elem.attr('data-name');
			var state = elem.hasClass(this.options.toggle);
			if (state) {
				this.options.removecb(elem);
			} else {
				this.options.addcb(elem);
			}
			elem.toggleClass(this.options.toggle);
		}
	});
	
	
	// Search for users, groups, parameters, etc..
	
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
			
			$('.ui-dialog-titlebar', this.dialog.dialog('widget')).append($.spinner());		
		},

		event_click: function(e) {
			this.show();
		},
	
		show: function() {
			this.build();		
			if (this.element.val() != "+") {
				// this.searchinput.val(this.element.val());
				// this.options.value = this.searchinput.val();
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

<%!
public = True
headers = {
	'Content-Type': 'application/javascript',
	'Cache-Control': 'max-age=86400'
}
%>
