(function($) {
    // Create a new record in a dialog box
    $.widget('emen2.RecordControl', {
        options: {
            parent: null,
            rectype: null,
            show: false,
            action: null,
            modal: true,
            redirect: null,
            name: null,
            mode: 'new'
        },
        
        _create: function() {
            var self = this;
            this.built = 0;
			emen2.util.checkopts(this, ['rectype', 'parent', 'name', 'redirect']);
            if (this.options.name != null) {
                this.options.mode = 'edit';
            }
            if (this.options.show) {
                this.show();
            } else {
                this.element.click(function(e){self.show(e)})
            }
        },
        
        show: function(e) {
            if (e) {e.preventDefault()}
            this.build();
            if (this.options.modal) {
                this.dialog.dialog('open');
            }
        },
        
        build: function() {
            if (this.built) {return}
            this.built = 1;
            
            var self = this;
            this.dialog = $('<div />');
            this.dialog.attr('title', 'Loading...');
            this.dialog.text('Loading...');
            
            if (this.options.modal) {
                // grumble... get the viewport dimensions..
                // 'auto' won't work because the content
                // is added by the callbacks
                var w = $(window).width() * 0.8;
                var h = $(window).height() * 0.8;
                this.dialog.dialog({
                    modal: this.options.modal,
                    autoOpen: false,
                    width: w,
                    height: h,
                    draggable: false,
                    resizable: false,
                    buttons: {
                        "Cancel": function() {
                            $(this).dialog('close');
                        },
                        "Save": function() {
                            $('form', this).submit();
                        }
                    }
                });
                
            } else {
                this.element.append(this.dialog);
            }            
            
            if (this.options.mode=='new') {
                this._record_new();
            } else {
                this._record_edit();
            }

        },
        
        _record_new: function() {
            var self = this;
            emen2.db('recorddef.get', [[self.options.rectype]], function(rds) {
                emen2.cache.update(rds);
                emen2.db('record.new', {'rectype':self.options.rectype, 'inherit':[self.options.parent]}, function(rec) {
                    emen2.caches['record']['None'] = rec;
                    emen2.db('view', {'names':rec, 'viewname':'mainview', 'options':{'output':'form', 'markdown':true}}, function(rendered) {
                        self._build(rendered);
                    });                
                });
            });            
        },
        
        _record_edit: function() {
            var self = this;
            emen2.db('record.get', [self.options.name], function(rec) {
                emen2.cache.update([rec]);
                self.options.rectype = rec['rectype']
                emen2.db('recorddef.get', [rec['rectype']], function(rds) {
                    emen2.cache.update([rds]);
                    emen2.db('view', {'names':self.options.name, 'viewname':'mainview', 'options':{'output':'form', 'markdown':true}}, function(rendered) {
                        self._build(rendered);
                    });                
                });            
            });
        },
                
        _build: function(rendered) {
            // Clear the dialog.
            this.dialog.empty();

            // Create the form.
            var form = $('<form enctype="multipart/form-data" action="" method="post" />');
            form.attr('data-name', this.options.name);
            
            // Set the form action.
            var action_alt = emen2.template.uri(['record', this.options.parent, 'new', this.options.rectype]);
            if (this.options.mode == 'edit') {
                var action_alt = emen2.template.uri(['record', this.options.name, 'edit']);
            }
            var action = this.options.action || this.element.attr('data-action') || action_alt;
            form.attr('action', action);
            
            // ...redirect after submission.
            if (this.options.redirect) {
                $('<input type="hidden" name="_redirect" />').val(this.options.redirect).appendTo(form);
            }

            var rd = emen2.caches['recorddef'][this.options.rectype];
            if (this.options.mode == 'new') {
                // RecordDef description
                $('<p class="e2l-shadow-drop" />').text(rd.desc_long).appendTo(this.dialog);
                // Add the parent for a new record
                form.attr('data-name', 'None');
                $('<input type="hidden" name="parents" />').val(this.options.parent).appendTo(form);
                // Add the rectype
                $('<input type="hidden" name="rectype" />').val(this.options.rectype).appendTo(form);
            }
            
            // Todo: this should done as a mustache-style template and dictionary to render it safely client side.
            form.append(rendered);

            // Set the dialog title to show the record type and parent recname
            if (this.options.modal) {
                this.dialog.dialog('option', 'title', this.options.mode+' '+rd.desc_short);
            }

            // Show a submit button.
            if (!this.options.modal) {
                form.append('<ul class="e2l-controls"><li><input type="submit" value="Save" /></li></ul>');
            }

            // Add the editing control after it's in the DOM
            this.dialog.append(form);
            form.EditControl({});
        }
    });
    
    
    // Select a Protocol for a new record
    $.widget('emen2.NewRecordChooserControl', {
        options: {
            parent: null,
            rectype: null,
            private: null,
            copy: null,
            show: true,
            help: false,
            summary: false
        },
        
        _create: function() {
            this.built = 0;
			emen2.util.checkopts(this, ['rectype', 'parent', 'private', 'copy']);
            if (this.options.show) {
                this.show();
            }
        },
        
        show: function() {
            var self = this;
            this.build();
        },
        
        build: function() {
            var self = this;
            // Provide some loading feedback
            this.element.empty();
            this.element.append(emen2.template.spinner(true));
            
            // Get the RecordDef for typicalchildren and prettier display
            emen2.db("recorddef.find", {'record':[this.options.parent]}, function(rd) {
                var typicalchld = [];
                $.each(rd, function() {
                    self.options.rectype = this.name;
                    emen2.caches['recorddef'][this.name] = this;
                    typicalchld = this.typicalchld;                    
                });
                emen2.db("recorddef.get", [typicalchld], function(rd2) {
                    $.each(rd2, function() {
                        emen2.caches['recorddef'][this.name] = this;
                    })
                    self._build();
                })
            });            
        },
        
        _build: function() {
            if (this.built) {return}
            this.built = 1;
            var self = this;
            var rd = emen2.caches['recorddef'][this.options.rectype];
            this.element.empty();

            if (this.options.help || this.options.summary) {
                $('<h2 class="e2l-cf">New record</h2>').appendTo(this.element);
            }
            
            if (this.options.help) {
                $('<div class="e2l-help" role="help"><p> \
                        Records can have an arbitrary number of child records. \
                    </p><p>To <strong>create a new child record</strong>, select a <strong>protocol</strong> from the list below, or search for a different protocol. \
                        When you select a protocol, a form will be displayed where you can fill in the details for the new record. Click <strong>save</strong> to save the new record. \
                    </p><p> \
                        Additional information is available at the <a href="http://blake.grid.bcm.edu/emanwiki/EMEN2/Help/NewRecord">EMEN2 wiki</a>. \
                    </p></div>').appendTo(this.element);
            }            

            if (this.options.summary) {
                $('<p>To create a new record select one of the protocols below, or <span class="e2l-a e2-newrecord-other">search for a different protocol</span>.</p>').appendTo(this.element);
            }
            
            // Children suggested by RecordDef.typicalchld
            if (rd.typicalchld.length) {
                this.element.append(this.build_level('Suggested protocols', 'typicalchld', rd.typicalchld))
            }
            
            $('.e2-newrecord-other', this.element).FindControl({
                keytype: 'recorddef',
                value: rd.name,
                selected: function(widget, value) {
                    self.build_dialog(value);
                }
            });
            
        },
        
        build_dialog: function(rectype) {
            var self = this;
            // Action button
            if (!rectype) {
                return
            }            
            $('<input type="hidden" />').appendTo(this.element).RecordControl({
                parent: self.options.parent,
                rectype: rectype,
                show: true
            });
        },
        
        build_level: function(label, level, items) {
            var self = this;
            var level = $('<div class="e2l-cf" />').attr('data-level', level);
            $('<h4 />').text(label).appendTo(level);
            $.each(items, function() {
                $('<div/>').click(function(){self.build_dialog($(this).attr('data-name'))}).InfoBox({
                    keytype: 'recorddef',
                    name: this,
                    selected: function(self, e) {}
                }).appendTo(level);
            });
            return level
        }
    });
	
    
	//////
    $.widget("emen2.EditControl", {        
        options: {
            name: null,
            selector: null,
            controls: null,
            prefix: false
        },
                
        _create: function() {
			this.built = 0;
			this.build();
        },
                
        build: function() {
			if (this.built) {return}
			this.built = 1;
			this.bind(this.element);
		},
		
		bind: function(elem) {
			var self = this;
            
            // Add new items.
			$('.e2-edit-add', elem).click(function() {
				var parent = $(this).parent()
				var clone = parent.siblings('.e2-edit-template');
				var b = clone.clone();
				b.removeClass('e2-edit-template');
				b.removeClass('e2l-hide')
				parent.before(b);
				self.bind(b);
			});

            // Date picker
            $('.e2-edit[data-vartype="datetime"] input', elem).datetimepicker({
                showButtonPanel: true,
                changeMonth: true,
                changeYear: true,
                showSecond: true,
                showAnim: '',
                yearRange: 'c-100:c+100',
                dateFormat: 'yy-mm-dd',
                timeFormat: 'hh:mm:ssz',
                separator: 'T',
                timezone: '+0500',
                showTimezone: true
            });
            
            // Find items.
			$('.e2-edit-add-find', elem).FindControl({
			    minimum: 0,
			    selected: function(self, name){
					var parent = self.element.parent();
					var param = self.element.attr('data-param');
					var iter = self.element.attr('data-iter');
			        var d = $('<div/>').InfoBox({
			            keytype: 'user',
			            name: name,
						selectable: true,
						input: ['checkbox', param, true]
			        });
					if (iter) {
						parent.before(d);
					} else {
						parent.children('.e2-infobox').remove();
						parent.prepend(d);
					}
				}
			});
        }    
    });
	
    
	
    // Comments Widget
    $.widget("emen2.CommentsControl", {
        options: {
            name: null,
            edit: false,
            title: null,
            controls: null,
            historycount: false,
            commentcount: false
        },
                
        _create: function() {
            this.built = 0;
            this.element.addClass('e2-comments');
            this.build();
        },
        
        rebuild: function() {
            this.built = 0;
            this.build();
        },
    
        build: function() {    
            var self = this;    
            if (this.built) {return}
            this.built = 1;

            // Make a copy of the cached comments and history
            var rec = emen2.caches['record'][this.options.name];
            this.comments = rec['comments'].slice() || [];
            this.history = rec['history'].slice() || [];
            
            // Add a "comment" for the record creation time        
            this.comments.push([
                rec['creator'], 
                rec['creationtime'], 
                'Record created']);

            // Check for cached users
            var users = [];
            $.each(this.comments, function(){users.push(this[0])})
            $.each(this.history, function(){users.push(this[0])})
            users = emen2.cache.check('user', users);

            // Check cached parameters
            var params = $.map(this.history, function(item){return item[2]});
            params = emen2.cache.check('paramdef', params);

            // If we need users or params, fetch them.
            // Todo: find a nicer way to chain these together
            if (users && params) {
                emen2.db('user.get', [users], function(users) {
                    emen2.cache.update(users)
                    emen2.db('paramdef.get', [params], function(params) {
                        emen2.cache.update(params)
                        self._build();
                    });
                });
            } else if (params) {
                emen2.db("paramdef.get", [params], function(params) {
                    emen2.cache.update(params)
                    self._build();
                });
            } else if (users) {
                emen2.db("user.get", [users], function(users) {
                    emen2.cache.update(users)
                    self._build();
                });
            } else {
                self._build();
            }
        },
    
        _build: function() {
            // Build after all data is cached
            var self = this;            
            this.element.empty();            
            var total = this.comments.length + this.history.length
            var all = [];
            $.each(this.comments, function(){all.push(this)})
            $.each(this.history, function(){all.push(this)})
            $('<h2>Comments and history</h2>').appendTo(this.element);
            
            // Break each log event out by date
            var bydate = {};
            $.each(all, function() {
                var user = this[0];
                var date = this[1];
                // Emulate Python collections.defaultdict
                if (!bydate[date]) {bydate[date] = {}}
                if (!bydate[date][user]) {bydate[date][user] = []}
                bydate[date][user].push(this);
            });

            // Sort the keys. JS doesn't support sorted(dict, key=..)
            var keys = [];
            $.each(bydate, function(k,v){keys.push(k)})
            keys.sort();

            $.each(keys, function(i, date) {
                $.each(bydate[date], function(user, events) {
                    $('<div />').InfoBox({
                        'keytype':'user',
                        'name': user,
                        'time': date,
                        'body': self.makebody(events)
                    }).appendTo(self.element);
                });
            });

            if (this.options.edit && this.options.controls) {
                var controls = $(' \
                    <ul class="e2l-controls e2l-fw"> \
                        <li><textarea name="comment" rows="2" placeholder="Add a comment"></textarea></li> \
                        <li><input type="submit" class="e2l-float-right" value="Add Comment" /></li> \
                    </ul>');
                $('input:submit', controls).click(function(e) {self.save(e)});
                this.options.controls.append(controls)
            }
        },
        
        makebody: function(events) {
            var comments = $('<div />');
            $.each(events, function(i, e) {
                var row = $('<div />').appendTo(comments);
                if (e.length == 3) {
                    row.prepend(emen2.template.image('comment.closed.png'));
                    row.text(e[2]);
                    row.appendTo(comments);
                } else if (e.length == 4) {
                    var pdname = e[2];
                    if (emen2.caches['paramdef'][pdname]){
                        pdname=emen2.caches['paramdef'][pdname].desc_short
                    }
                    emen2.template.image('edit.png').appendTo(row);
                    row.append('Edited ' );
                    $('<a />')
                        .attr('href', emen2.template.uri(['paramdef', e[2]]))
                        .text(pdname)
                        .appendTo(row);
                    row.append('. Previous value was: ');
                    $('<span />')
                        .text(e[3] || "None")
                        .appendTo(row);
                }
            });
            return comments
        },
        
        save: function(e) {
            // Should probably just make this a POST form.
            var self = this;
            emen2.db('record.addcomment', [this.options.name, $('textarea[name=comment]', this.options.controls).val()], function(rec) {
                emen2.caches['record'][rec.name] = rec;
                self.rebuild();
            });
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
