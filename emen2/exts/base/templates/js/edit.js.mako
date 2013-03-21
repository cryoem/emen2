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
            // Todo: If self.options.rectype is null, 
            //        show the NewRecordChooserControl
            //        based on the parent
            var self = this;
            this.built = 0;
            this.options.rectype = emen2.util.checkopt(this, 'rectype');
            this.options.parent = emen2.util.checkopt(this, 'parent');
            this.options.name = emen2.util.checkopt(this, 'name');
            this.options.redirect = emen2.util.checkopt(this, 'redirect');
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
            this.dialog = $('<div>Loading...</div>');
            this.dialog.attr('title','Loading...');
            
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
                    // console.log("New record:", rec);
                    emen2.caches['record']['None'] = rec;
                    emen2.db('record.render', {'names':rec, 'viewname':'mainview', 'edit':true}, function(rendered) {
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
                    emen2.db('view', {'names':self.options.name, 'viewname':'mainview'}, function(rendered) {
                        self._build(rendered);
                    });                
                });            
            });
        },
                
        _build: function(rendered) {
            this.dialog.empty();

            // Create the form
            var form = $('<form enctype="multipart/form-data"  action="" method="post" data-name="'+this.options.name+'" />');

            // Set the form action
            var action_alt = ROOT+'/record/'+this.options.parent+'/new/'+this.options.rectype+'/';
            if (this.options.mode == 'edit') {
                var action_alt = ROOT+'/record/'+this.options.name+'/edit/';
            }
            var action = this.options.action || this.element.attr('data-action') || action_alt;
            form.attr('action',action);

            // ...redirect after submission
            if (this.options.redirect) {
                form.append('<input type="hidden" name="_redirect" value="'+this.options.redirect+'"/>');
            }

            // Show the recorddef long description
            var rd = emen2.caches['recorddef'][this.options.rectype];
            if (this.options.mode == 'new') {
                var desc = $.trim(rd.desc_long).replace('\n','<br /><br />'); // hacked in line breaks
                var desc = $('<p class="e2l-shadow-drop">'+desc+'</p>');
                this.dialog.append(desc);
                // Add the parent for a new record
                form.attr('data-name', 'None');
                // Add the rectype
                form.append('<input type="hidden" name="parents" value="'+this.options.parent+'" /><input type="hidden" name="rectype" value="'+this.options.rectype+'" />')                
            }
            
            // ...content
            form.append(rendered);

            // Set the dialog title to show the record type and parent recname
            if (this.options.modal) {
                this.dialog.dialog('option', 'title', this.options.mode+' '+rd.desc_short);
            }

            // Show a submit button. In dialogs, this is drawn by the dialog itself.
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
            this.options.rectype = emen2.util.checkopt(this, 'rectype');
            this.options.parent = emen2.util.checkopt(this, 'parent');
            this.options.private = emen2.util.checkopt(this, 'private');
            this.options.copy = emen2.util.checkopt(this, 'copy');
            
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
                var header = $('<h2 class="e2l-cf">New record</h2>');                
                this.element.append(header);
            }
            if (this.options.help) {
                var help = $(' \
                    <div class="e2l-help" role="help"><p> \
                        Records can have an arbitrary number of child records. \
                    </p><p>To <strong>create a new child record</strong>, select a <strong>protocol</strong> from the list below, or search for a different protocol. \
                        When you select a protocol, a form will be displayed where you can fill in the details for the new record. Click <strong>save</strong> to save the new record. \
                    </p><p> \
                        Additional information is available at the <a href="http://blake.grid.bcm.edu/emanwiki/EMEN2/Help/NewRecord">EMEN2 wiki</a>. \
                    </p></div>');
                this.element.append(help);
            }            
            if (this.options.summary) {
                var summary = $('<p></p>');
                summary.append('To create a new record select one of the protocols below, or <span class="e2l-a e2-newrecord-other">search for a different protocol</span>.');
                this.element.append(summary);
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
            var asd = $('<input type="hidden" />');
            self.element.append(asd);
            asd.RecordControl({
                parent: self.options.parent,
                rectype: rectype,
                show: true
            });
        },
        
        build_level: function(label, level, items) {
            var self = this;
            var header = $('<h4>'+label+'</h4>')
            var boxes = $('<div class="e2l-cf"></div>');
            boxes.attr('data-level', level);
            $.each(items, function() {
                var box = $('<div/>').InfoBox({
                    keytype: 'recorddef',
                    name: this,
                    selected: function(self, e) {
                        // console.log(e);
                    }
                });
                box.click(function(){self.build_dialog($(this).attr('data-name'))});
                boxes.append(box);
            });
            return $('<div/>').append(header, boxes);
        },
        
        add: function(level, name) {
            var selector = 'div[data-level='+level+']';
            var boxes = $(selector, this.element);
            if (!boxes.length) {
                this.element.prepend(this.build_level('Other protocols', level, []));
                var boxes = $(selector, this.element);
            }
            var box = $('<div/>').InfoBox({
                keytype: 'recorddef',
                selectable: true,                        
                name: name,
                input: ['radio', 'rectype']
            });
            box.InfoBox('check');
            boxes.append(box);
        }
    });
	
	
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
			$(".e2-edit-add", elem).click(function() {
				var parent = $(this).parent()
				var clone = parent.siblings('.e2-edit-template');
				var b = clone.clone();
				b.removeClass('e2-edit-template');
				b.removeClass('e2l-hide')
				parent.before(b);
				self.bind(b);
			});

			$(".e2-edit-add-find", elem).FindControl({
			    minimum: 0,
			    selected: function(self, name){
					var parent = self.element.parent();
					var param = self.element.attr('data-param');
					var iter = self.element.attr('data-iter');
			        var d = $('<div/>');
			        d.InfoBox({
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

            this.element.append("<h2>Comments and history</h2>");

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
            // keys.reverse();
            
            $.each(keys, function(i, date) {
                $.each(bydate[date], function(user, events) {
                    var d = $('<div />');
                    // put the text as 'body' so it is rendered after the callback to get the user info
                    d.InfoBox({
                        'keytype':'user',
                        'name': user,
                        'time': date,
                        'body': self.makebody(events) || ' '
                    });
                    self.element.append(d);
                });
            })

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
            var comments = [];
            var rows = [];
            $.each(events, function(i, e) {
                if (e.length == 3) {
                    comments.push('<div>'+emen2.template.image('comment.closed.png')+' '+e[2]+'</div>');
                } else if (e.length == 4) {
                    var pdname = e[2];
                    if (emen2.caches['paramdef'][pdname]){pdname=emen2.caches['paramdef'][pdname].desc_short}
                    var row = '<div>'+emen2.template.image('edit.png')+' edited <a href="'+ROOT+'/paramdef/'+e[2]+'/">'+pdname+'</a>. Previous value was:</div><div style="margin-left:50px">'+e[3]+'</div>';
                    comments.push(row);
                }
            });
            comments = comments.join('');
            return comments
        },
        
        save: function(e) {    
            var self = this;
            emen2.db('record.addcomment', [this.options.name, $('textarea[name=comment]', this.options.controls).val()], function(rec) {
                $.record_update(rec)
                $.notify('Comment Added');
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
