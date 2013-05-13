(function($) {

    $.widget('emen2.InfoBox', {
        options: {
            name: null,
            keytype: null,
            time: null,
            title: '',
            body: '',
            selectable: false,
            retry: true,
            input: ['checkbox', '', true],
            show: true,
            // events
            built: function(self) {},
            selected: function(self, e) {}
        },
        
        _create: function() {
            var self = this;
            this.retry = 0;
            this.built = 0;
            if (this.options.show) {
                this.show();
            }
        },
        
        show: function(e) {
            this.build();
        },
        
        build: function() {
            var self = this;
            if (this.built) {return}
            this.built = 1;

            // Check if we have the item.
            var item = emen2.caches[this.options.keytype][this.options.name];
            if (item) {
                return this._build();
            }

            // Get and cache the item.
            emen2.db('get', {
            		keytype: this.options.keytype,
					names: this.options.name
          	  	}, 
				function(item) {
					emen2.caches[item.keytype][item.name] = item;
					self._build();
				}
			);
        }, 
		
        _build: function() {
            var self = this;
			var item = emen2.caches[this.options.keytype][this.options.name];
            if (!item) {
                return
            }

			// Run the builder.
			this['_build_'+this.options.keytype](item);
            
            // Set the box properties.
            this.element.addClass('e2-infobox');
            this.element.attr('data-name', this.options.name);
            this.element.attr('data-keytype', this.options.keytype);

            // Widget!! Refactor this.
            if (this.options.selectable && this.options.input) {
                var type = this.options.input[0];
                var name = this.options.input[1];
                var state = this.options.input[2];
                // Todo: Only checkbox is supported right now...
                $('<input type="checkbox" class="e2-infobox-input" />')
                    .attr('name', name)
                    .attr('checked', state)
                    .val(this.options.name)
                    .appendTo(this.element);
            }

			// Default thumbnail.
            var img = emen2.template.image(this.options.keytype+'.png', '', 'e2l-thumbnail');
			img.appendTo(this.element);
            if (this.options.thumbnail) {
				img.attr('src', this.options.thumbnail);
			}

            // Box title.
            var title = $('<h4 />');
            title.text(this.options.title);
			title.appendTo(this.element);
            
			// Time
            if (this.options.time) {
                $('<time class="e2-localize e2l-float-right" />')
                    .attr('datetime', this.options.time)
                    .text(this.options.time)
                    .localize()
                    .appendTo(title);
            }

			// Are we linking?
            if (this.options.link) {
                img.wrap($('<a />').attr('href', this.options.link));
                title.wrapInner($('<a />').attr('href', this.options.link));
			}

            // The body
            // Todo: Build the body as an element in _build...
            $('<p />').text(this.options.body).appendTo(this.element);

            // Put it all together..
            this.options.built();
        },        
        
		_build_user: function(item) {
            this.options.title = this.options.title || item.displayname || item.name;
            this.options.body = this.options.body || item.email;
            if (item['person_photo']) {
				this.options.thumbnail = ROOT+'/download/'+$.escape(item.userrec['person_photo'])+'/user.jpg?size=thumb';
			}
		},
		
		_build_recorddef: function(item) {
			this.options.title = this.options.title || item.desc_short;
		},
        
		_build_group: function(item) {
            this.options.title = this.options.title || item.displayname || item.name;
            var count = 0;
            for (var i=0;i<item['permissions'].length;i++) {
                count += item['permissions'][i].length;
            }
            var body = count+' members';
            if (item.name == 'authenticated') {
                body = 'All logged in users';
            } else if (item.name == 'anon') {
                body = 'Public access';
            }
			this.options.body = this.options.title || body;
		},
		
		_build_record: function(item) {
            var recname = emen2.caches['recnames'][item.name];
            this.options.title = $.trim(recname || item.rectype);
            this.options.body = 'Created: '+$.localize(new Date(item.creationtime));
            this.element.attr('data-rectype', item.rectype);		
		},
		
		_build_binary: function(item) {
            var title = item.filename;
            if (item.filesize) {
                title = title+' ('+emen2.template.prettybytes(item.filesize)+')';
            }
			this.options.title = title;
			this.options.body = 'Uploaded on '+$.localize(new Date(item.creationtime));
            this.options.thumbnail = ROOT+'/download/'+$.escape(item.name)+'/user.jpg?size=thumb';
			this.options.link = ROOT+'/download/'+$.escape(item.name)+'/'+$.escape(item.filename);
		},
        
        toggle: function(e) {
            var input = $('input', this.element);
            if ($(e.target).is('input, a')) {return}
            if (input.attr('checked')) {
                input.attr('checked',null);
            } else {
                input.attr('checked','checked');        
            }
        }
    });
    
    // Search for users, groups, parameters, etc..
    $.widget("emen2.FindControl", {
        options: {
            show: false,
            keytype: 'user',
            value: '',
            modal: true,
            vartype: null,
            minimum: 2,
            target: null,
            selected: function(self, value){self.selected(self, value)}
        },
        
        _create: function() {
            this.built = 0;
            var self=this;
			emen2.util.checkopts(this, ['keytype', 'vartype', 'modal', 'minimum', 'value', 'target']);
            this.element.click(function(e){self.show(e)});
            if (this.options.show) {
                this.show();
            }
        },
    
        build: function() {
            if (this.built) {return}
            this.built = 1;

            var self = this;
            this.dialog = $('<div class="e2-find" />');
            // Todo: Find a smarter way of doing this.
            var titles = {
                'user':'Find User',
                'group':'Find Group',
                'paramdef':'Find Parameter',
                'recorddef':'Find Protocol',
                'record':'Find Record',
                'binary':'Find Binary'
            }
            this.dialog.attr('title', titles[this.options.keytype]);

            // Top part of dialog.
            var searchbox = $('<div class="e2-find-searchbox">Search: </div>')
                .appendTo(this.dialog);
            
            // Run a search for every key press
            // Todo: cancel searches properly on add'l input
            this.searchinput = $('<input class="e2-find-input" type="text" />')
                .val(this.options.value)
                .keyup(function(e) {
                    var v = self.searchinput.val();
                    // // Enter should check for an exact match and return
                    // if (e.keyCode == '13') { 
                    //     e.preventDefault();
                    //     var check = $('[data-name="'+$.escape(v)+'"]');
                    //     if (check.length) {
                    //         self.select(v);
                    //     }
                    // }
                    self.search(v);
                })
                .appendTo(searchbox);

            this.statusmsg = $('<span class="e2-find-count e2l-float-right">No Results</span>')
                .appendTo(searchbox);

            // Bottom part of dialog
            this.resultsarea = $('<div class="e2-find-result">Results</div>').appendTo(this.dialog);

            // Show the dialog.
            this.dialog.dialog({
                modal: this.options.modal,
                autoOpen: false,
                width: 750,
                height: 600,
                draggable: false,
                resizable: false,                
            });
            
            // Show activity wheel.
            // $('.ui-dialog-titlebar', this.dialog.dialog('widget')).append(emen2.template.spinner());        
        },
    
        show: function(e) {
            this.build();        
            if (this.element.val() != "+") {
                this.searchinput.val(this.element.val());
                this.options.value = this.element.val();
            }
            this.dialog.dialog('open');
            this.search(this.options.value);        
            this.searchinput.focus();
        },

        select: function(name) {
            if  (this.options.selected) {
                this.options.selected(this, name);
                this.dialog.dialog('close');                
            }
        },
        
        selected: function(self, value) {
            // Hacked together. Clean this up later.
            if (this.options.target) {
                $('#'+$.escape(this.options.target)).val(value);
            }            
            this.element.val(value);
        },
                
        add: function(item) {
            var self = this;
            $('<div />')
                .InfoBox({
                    keytype: this.options.keytype,
                    name: item.name
                })
                .click(function(e){
                    self.select(item.name);
                })
                .appendTo(this.resultsarea);    
        },
        
        cb: function(items) {
            var self = this;
            // $('.e2l-spinner', this.dialog.dialog('widget')).hide();
            this.resultsarea.empty();
            var l = items.length;
            if (l==0) {
                self.statusmsg.text('No results');
                return
            }
            if (l>=100) {
                self.statusmsg.text('More than 100 results; showing 1-100');
            } else {
                self.statusmsg.text(items.length+' results');                
            }
            items = items.slice(0,100);
            $.each(items, function() {
                emen2.caches[this.keytype][this.name] = this;
                self.add(this)            
            });            
        },
    
        search: function(q) {
            var self = this;
            if (q.length < this.options.minimum) {
                self.resultsarea.empty();
                self.statusmsg.text('Minimum '+escape(this.options.minimum)+' characters');
                return
            }
            
            var query = {}
            query['query'] = q;
            if (this.options.vartype) {
                query['vartype'] = this.options.vartype;
            }
            
            // Abort any open requests
            if (this.request) {
                if (this.request.readyState != 4) {
                    this.request.abort();
                    this.request = null;
                }
            }
            // $('.e2l-spinner', this.dialog.dialog('widget')).show();
            this.request = emen2.db(this.options.keytype+'.find', query, function(items) {self.cb(items)});
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
