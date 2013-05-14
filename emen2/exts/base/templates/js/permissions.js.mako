(function($) {
    $.widget('emen2.PermissionsControl', {
        options: {
            keytype: 'record',
            name: null,
            edit: false,
            show: true,
            controls: null,
            groups: true,
            summary: false,
            help: false,
        },
        
        _create: function() {
            var self = this;
            this.built = 0;
            if (this.options.show) {
                this.show();
            }
        },
        
        show: function() {
            this.build();
        },
        
        build: function() {
            // Cache items before real build..
            if (this.built) {return}
            this.built = 1;            
            var self = this;

            // Add the e2-permissions class
            this.element.empty();
            this.element.addClass('e2-permissions');
            this.element.append(emen2.template.spinner());

            // 1. Get the item...
            var item = emen2.caches[this.options.keytype][this.options.name];
            if (!item) {
                emen2.db('get', {'keytype':this.options.keytype, 'names':this.options.name}, function(item) {
                    emen2.cache.update([item]);
                    // 2. Get all the users before we draw the infoboxes
                    var users = [];
                    $.each(item['permissions'] || [], function(k, v) {users = users.concat(v)});
                    users = emen2.cache.check('user', users);
                    emen2.db('user.get', [users], function(users) {
                        emen2.cache.update(users);
                        // 3. ... also get groups ...
                        var groups = item['groups'] || [];
                        groups = emen2.cache.check('group', groups);
                        emen2.db('group.get', [groups], function(groups) {                    
                            emen2.cache.update(groups)
                            // 4. Finally call real build method
                            self._build();
                        });    
                    });
                });
            } else {
                // This should be broken down into a separate callback method
                // for each step of the chain
                var users = [];
                $.each(item['permissions'] || [], function(k, v) {users = users.concat(v)});
                users = emen2.cache.check('user', users);
                emen2.db('user.get', [users], function(users) {
                    emen2.cache.update(users);
                    // 3. ... also get groups ...
                    var groups = item['groups'] || [];
                    groups = emen2.cache.check('group', groups);
                    emen2.db('group.get', [groups], function(groups) {                    
                        emen2.cache.update(groups)
                        // 4. Finally call real build method
                        self._build();
                    });    
                });
                
            }
        },
        
        _build: function() {
            var self = this;
            var permissions = emen2.caches[this.options.keytype][this.options.name]['permissions'] || [];
            var groups = emen2.caches[this.options.keytype][this.options.name]['groups'] || [];

            // Remove anything that is bound
            this.element.empty();

            // Add help, controls, summary, etc.
            if (this.options.summary || this.options.help) {
                $('<h2 />').text('Permissions').appendTo(this.element);
            }
            if (this.options.help) {
                $('<div class="e2l-help" role="help"><p> \
                    There are four types of permissions: \
                </p><ul><li><strong>Read-only</strong>: access record</li> \
                    <li><strong>Comment</strong>: access record and add comments</li> \
                    <li><strong>Write</strong>: access record, add comments, and change values</li> \
                    <li><strong>Owner</strong>: access record, add comments, change values, and change permissions</li> \
                </ul><p>You can also assign <strong>group</strong> permissions, including a few special groups. \
                    <em>Authenticated</em> group will permit <em>all</em> logged-in users to access the record. \
                    <em>Anonymous</em> will make the record publicly accessible to anyone who can access the server. \
                    See the wiki for more details on how to manage groups. \
                </p><p>To <strong>add a user or group</strong>, click one of the <strong>+</strong> buttons below. \
                    Search for the user or group you wish to add, and click their name to add to the list. \
                    To <strong>remove users or groups</strong>, uncheck their name. Click <strong>save permissions</strong> to save the permissions for this record, \
                    or click <strong>save permissions recursively</strong> to save to this record and all child records. \
                </p><p> \
                    Additional information is available at the <a href="http://blake.grid.bcm.edu/emanwiki/EMEN2/Help/Permissions">EMEN2 Wiki</a>. \
                </p></div>')
                .appendTo(this.element);
            }
            if (this.options.summary) {
                this.build_summary().appendTo(this.element);
            }
            if (this.options.controls && this.options.edit) {
                this.build_controls().appendTo(this.options.controls);
            }

            // Build the permissions levels
            if (this.options.groups) {
                this.build_level('Groups', 'groups', groups, 'group').appendTo(this.element);
            }
            this.build_level('Read-only', 'read', permissions[0]).appendTo(this.element);
            this.build_level('Comment', 'comment', permissions[1]).appendTo(this.element);
            this.build_level('Write', 'write', permissions[2]).appendTo(this.element);
            this.build_level('Owners', 'admin', permissions[3]).appendTo(this.element);
        },
        
        build_summary: function() {
            var permissions = emen2.caches[this.options.keytype][this.options.name]['permissions'] || [];
            var groups = emen2.caches[this.options.keytype][this.options.name]['groups'] || [];
            var total = permissions[0].length + permissions[1].length + permissions[2].length + permissions[3].length;
            return $('<p />').text('This record is accessible by '+groups.length+' groups and '+total+' users.')
        },
        
        build_controls: function() {
            // Todo: cleaner markup.
            var self = this;
            var controls = $(' \
                <ul class="e2l-controls"> \
                    <li><input type="button" name="save" value="Save permissions" /></li> \
                    <li><input type="button" name="overwrite" value="Save permissions recurisvely" /></li> \
                </ul>');
            // Action buttons
            $('input[name=overwrite]', controls).click(function(){self.save('overwrite')})
            $('input[name=save]', controls).click(function(){self.save()});
            return controls
            // <ul class="e2l-options"> \
            //     <li class="e2-select"></li> \
            // </ul> \
            // <li class="e2-permissions-advanced e2l-hide"><input type="button" name="add" value="Add checked users to children" /></li> \
            // <li class="e2-permissions-advanced e2l-hide"><input type="button" name="remove" value="Remove checked users from children" /></li> \
            // <li class="e2-permissions-advanced e2l-hide"><input type="checkbox" name="filt" value="filt" checked id="e2-permissions-filt"><label for="e2-permissions-filt">Ignore failures</label></li> \
            // Show/hide advanced options
            // $('.e2-permissions-caret', controls).click(function(){
            //     emen2.template.caret('toggle', self.options.controls);
            //     $('.e2-permissions-advanced', self.options.controls).toggle();
            // });
            // $('input[name=add]', controls).click(function(){self.save('add')})
            // $('input[name=remove]', controls).click(function(){self.save('remove')})

            // Selection control
            // $('.e2-select', controls).SelectControl({root: this.element});
                        
        },

        build_level: function(lab, level, items, keytype) {
            // Build a header, controls, and infoboxes for a group of items
            var self = this;
            var keytype = (level == 'groups') ? 'group' : 'user';
            var param = (level == 'groups') ? 'groups' : 'permissions.'+level;

            var ret = $('<div />')
                .addClass('e2l-cf')
                .attr('data-level', level);
            
            var header = $('<h4 />')
                .text(lab)
                .appendTo(ret);
            if (this.options.edit) {
                $('<input type="button" />')
                .attr('data-level', level)
                .attr('data-keytype', keytype)
                .FindControl({
                    keytype: keytype,
                    minimum: 0,
                    selected: function(w, value) {
                        var level = w.element.attr('data-level');
                        self.add(level, value);
                    }
                })
                .val('+')
                .prependTo(header)
            }

            // Add the infoboxes
            for (var i=0;i<items.length;i++) {
                this.build_item(level, items[i], keytype).appendTo(ret);
            }

            // Need to have one last hidden item to make sure it's a list.
            $('<input type="hidden" />')
                .attr('name', param)
                .appendTo(ret);

            return ret
        },
        
        build_item: function(level, name) {
            // Build the infobox for an item
            var self = this;
            var keytype = (level == 'groups') ? 'group' : 'user';
            var param = (level == 'groups') ? 'groups' : 'permissions.'+level;

            // Update the select count when built or checked..
            var d = $('<div />')
                .InfoBox({
                    keytype: keytype,
                    name: name,
                    selectable: this.options.edit,
                    input: ['checkbox', param, true],
                });
            return d
        },
        
        add: function(level, name) {
            var self = this;
            var lvl = $('div[data-level='+$.escape(level)+']');
            if ($('div[data-name="'+$.escape(name)+'"]', lvl).length) {
                return
            }
            this.build_item(level, name).appendTo(lvl);
        },
        
        save: function(action) {
            var self = this;

            // Clear the existing form.
            $('input[name=action]', this.element).remove();            
            // Copy options into the form...
            $('<input type="hidden" />')
                .attr('name', 'action')
                .val(action)
                .appendTo(this.element);
            
            // Submit the actual form
            this.element.submit();            
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