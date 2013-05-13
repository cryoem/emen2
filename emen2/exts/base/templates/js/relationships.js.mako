(function($) {
    
    $.widget('emen2.RelationshipControl', {
        options: {
            name: null,
            keytype: 'record',
            edit: null,
            show: true,
            summary: false,
            help: false,
        },

        _create: function() {
            this.built = 0;
            var self = this;
			emen2.util.checkopts(this, ['name', 'keytype', 'edit', 'summary']);
            if (this.options.show) {this.show()}            
        },
                
        show: function() {
            this.build();
        },
        
        build: function() {
            if (this.built) {return}
            this.built = 1;
            var self = this;

            // Always empty the element before a rebuild, and place a spinner
            this.element.empty();
            this.element.addClass('e2-relationships');
            this.element.append(emen2.template.spinner(true));
            
            // Load all the parents and children
            var item = emen2.caches[this.options.keytype][this.options.name];
            var names = item.children.concat(item.parents);
            names = emen2.cache.check(this.options.keytype, names);
            
            // Cache rendered views for all the items
            // 1. Get the related items
            emen2.db('get', {names:names, keytype:this.options.keytype}, function(items) {
                emen2.cache.update(items)
                var found = $.map(items, function(k){return k.name});
                
                // 2a. Records need a second callback for pretty rendered text
                if (self.options.keytype == 'record') {
                    emen2.db('view', [found], function(recnames) {
                        $.each(recnames, function(k,v) {emen2.caches['recnames'][k] = v})
                        self._build();
                    });
                } else {
                    // 2b. No additional items needed.
                    self._build();
                }
            });
        }, 
        
        _build: function() {
            var self = this;

            // Remove the spinner
            this.element.empty();
            
            // Get the parents and children from cache
            var rec = emen2.caches[this.options.keytype][this.options.name];
            var parents = rec.parents;
            var children = rec.children;
            
            if (this.options.summary || this.options.help) {
                $('<h2 class="e2l-cf">Relationships</h2>').appendTo(this.element);
            }
            if (this.options.help) {
                $('<div class="e2l-help" role="help"><p> \
                    Records can have an arbitrary number of parent and child relationships. \
                </p><p>To <strong>add parent or child relationships</strong>, click one of the <strong>+</strong> buttons below. \
                    This will show a record chooser. You can either navigate to the record you want to add, or type \
                    the record ID directly into the input box. This will add the chosen record to the list of parents or children. \
                    The changes will take effect when you click <strong>save relationships</strong>. \
                </p><p>To <strong>remove parent or child relationships</strong>, uncheck the relationships you want to remove and click <strong>save relationships</strong>. \
                </p><p> \
                    Additional information is available at the <a href="http://blake.grid.bcm.edu/emanwiki/EMEN2/Help/Relationships">EMEN2 Wiki</a>. \
                </p></div>').appendTo(this.element);
            }
            if (this.options.summary && this.options.keytype == 'record') {
                this.build_summary(parents, children).appendTo(this.element);
            }
            
            // Add the items
            this.build_level('Parents', 'parents', parents).appendTo(this.element);
            this.build_level('Children', 'children', children).appendTo(this.element);
            
            if (this.options.controls && this.options.edit) {
                this.build_controls().appendTo(this.options.controls);
            }
        },
        
        build_summary: function(parents, children) {
            // Make a descriptive summary of the parent and child relationships
            var summary = $('<div />');
            $('<span />').text('This record has ').appendTo(summary);
            this.build_summary_label(parents, 'parents').appendTo(summary);
            $('<span />').text(' and ').appendTo(summary);
            this.build_summary_label(children, 'children').appendTo(summary);
            $('<span />').text('. Click to ').appendTo(summary);
            $('<a />')
                .attr('href', ROOT+'/records/?root='+$.escape(this.options.name))
                .text('view the record tree.')
                .appendTo(summary);
            return summary        
        },
        
        build_summary_label: function(value, label) {
            // Ugly text and markup manipulation to build descriptive summaries of records/rectypes
            var ct = {}
            $.each(value, function(k,v){
                var r = emen2.caches['record'][v] || {};
                if (!ct[r.rectype]){ct[r.rectype]=[]}
                ct[r.rectype].push(this);
            });                

            var elem = $('<span />');
            if (value.length == 0) {
                $('<span />').text('no '+label).appendTo(elem);
            } else {
                $('<span />').text(value.length+' '+label+', including: ').appendTo(elem);
            }

            $.each(ct, function(k,v) {
                var rd = emen2.caches['recorddef'][k] || {};
                var rddesc = rd['desc_short'] || k;
                $('<span />')
                    .text(v.length+' '+rddesc)
                    .appendTo(elem);
                // $('<span />')
                //     .text(' (toggle)')
                //     .attr('data-checked', 'checked')
                //     .attr('data-reltype', label)
                //     .attr('data-rectype', k)
                //     .addClass('e2l-a')
                //     .appendTo(elem)
                //     .click(function() {
                //         var state = $(this).attr('data-checked');
                //         if (state=='checked') {
                //             $(this).attr('data-checked', '');
                //             state = true;
                //         } else {
                //             $(this).attr('data-checked', 'checked');
                //             state = false
                //         }
                //         var rectype = $(this).attr('data-rectype');
                //         var reltype = $(this).attr('data-reltype');
                //         $('.e2-infobox[data-rectype='+$.escape(rectype)+'] input', self.element).attr('checked', state);
                //     });
            });
            return elem
        },
        
        build_level: function(label, level, items) {
            var self = this;
            var boxes = $('<div />')
                .attr('data-level', level);
            $('<input type="hidden" />')
                .attr('name', level)
                .appendTo(boxes);
                
            var header = $('<h4 />')
                .addClass('e2l-cf')
                .text(label)
                .appendTo(boxes);
            if (this.options.edit) {
                $('<input type="button" />')
                    .attr('data-level', level)
                    .val('+')
                    .TreeBrowseControl({
                        root: this.options.name,
                        selectable: this.options.edit,
                        keytype: this.options.keytype,
                        selected: function(browse, name) {
                            self.add(level, name);
                        }})
                    .click(function(){
                        $(this).TreeBrowseControl('show')})
                    .prependTo(header)
            }
            
            for (var i=0;i<items.length;i++) {
                this.build_item(level, items[i], false).appendTo(boxes);
            }
            return boxes
        },
        
        build_item: function(level, name, retry) {
            var self = this;
            return $('<div />')
                .InfoBox({
                    show: true,
                    keytype: this.options.keytype,
                    name: name,
                    selectable: this.options.edit,
                    retry: retry,
                    input: ['checkbox', level, true]
                });
        },
        
        build_controls: function() {
            var self = this;
            var controls = $(' \
                <ul class="e2l-controls"> \
                    <li><input type="submit" value="Save relationships" /></li> \
                </ul>');
            $('input:submit', controls).click(function(e){self.save(e)});
            return controls
        },
        
        add: function(level, name) {
            var boxes = $('div[data-level='+$.escape(level)+']', this.element);
            if ($('.e2-infobox[data-name="'+$.escape(name)+'"]', boxes).length) {
                return
            }
            this.build_item(level, name, true).appendTo(boxes);
        },
        
        save: function(e) {
            e.preventDefault();
            var parents = $('input[type=checkbox][name=parents]', this.element);
            var checkedparents = $('input[type=checkbox][name=parents]:checked', this.element);            
            if (parents.length && !checkedparents.length) {
                var ok = confirm("You are attempting to remove all parents of this record. Continue?");
                if (!ok) {return false}
            }
            this.element.submit();
        }
    });
    
    
    ////////////////////////////
    // Browse for an item
    $.widget('emen2.TreeBrowseControl', {
        options: {
            root: null,
            keytype: 'record',
            selected: function(self, name) {},
            moved: function() {},
        },
        
        _create: function() {
            var self = this;
            this.built = 0;
			emen2.util.checkopts(this, ['mode', 'root', 'keytype']);
            this.element.click(function(e){self.show(e)});
            if (this.options.show) {
                this.show();
            }            
        },
        
        show: function(e) {
            this.build();
            this.dialog.dialog('open');
        },

        build: function() {
            var self = this;
            if (this.built) {return}
            this.built = 1;

            // Build the dialog
            this.dialog = $('<div class="e2-browse" />');
            this.dialog.append(' \
                <div class="e2-browse-controls"></div> \
                <div class="e2l-cf e2-browse-header" style="border-bottom:solid 1px #ccc;margin-bottom:6px;"> \
                    <div class="e2-browse-parents e2l-float-left" style="width:299px;"> Parents </div> \
                    <div class="e2-browse-action e2l-float-left" style="width:299px;">&nbsp;</div> \
                    <div class="e2-browse-children e2l-float-left" style="width:299px;"> Children </div> \
                </div> \
                <div class="e2l-cf e2-browse-tree" style="position:relative" />');

            // Refresh the map area
            this.reroot(this.options.root);

            // Build the browser controls
            this.build_browse();

            // Show the dialog
            this.dialog.attr("title", "Relationship Browser");
            this.dialog.dialog({
                modal: true,
                width: 1000,
                height: 600,
                draggable: false,
                resizable: false,                    
            });            
        },

        build_browse: function() {
            var self = this;
            var controls = $(' \
                <span> \
                    <input style="margin-left:16px;width:120px;" type="text" name="value" value="" /> \
                    <input style="margin-right:16px" type="submit" name="submit" value="Select" /> \
                </span>');
            
            $('input[name=value]', controls).bind('keyup', function(e) {
                $('input[name=submit]', self.dialog).val('Go To');
            });
            
            $('input[name=submit]', controls).click(function(e) {
                var val = $('input[name=value]', self.dialog).val();
                if (val.toString() == self.options.root.toString()) {
                    self.options.selected(self, val);
                    self.dialog.dialog('close');
                } else {
                    self.reroot(val);
                }
            });

            var action = $('.e2-browse-action', this.dialog);
            action.append(controls);
        },
        
        reroot: function(name) {
            var self = this;
            this.options.root = name;
            $('input[name=value]', this.dialog).val(name);

            // Clear the tree.
            var tree = $('.e2-browse-tree', this.dialog);
            tree.empty();
            
            // Callback
            var cb = function(w, elem, name) {self.reroot(name)}
            $('<div class="e2-tree e2l-float-left" style="position:absolute;left:0px;width:300px;">&nbsp;</span>')
                .TreeControl({
                    root: name, 
                    keytype: this.options.keytype, 
                    mode: 'parents',
                    skiproot: true,
                    show: true,
                    selected: cb
                })
                .append(emen2.template.spinner(true))
                .appendTo(tree);
            
            $('<div class="e2-tree e2l-float-left" style="position:absolute;left:300px;" />')
                .TreeControl({
                    root: name, 
                    keytype: this.options.keytype, 
                    mode: 'children',
                    show: true,
                    selected: cb
                })
                .appendTo(tree);
        }        
    });
    
    
    ////////////////////////////    
    // Relationship tree control
    
    $.widget("emen2.TreeControl", {        
        options: {
            root: null,
            keytype: 'record',
            mode: 'children',
            expandable: true,
            show: false,
            attach: false,
            skiproot: false,
            selected: null,
            active: [],
            shiftselect: true,
        },

        _create: function() {
            var self = this;
            this.built = 0;
            
            // Selected/unselected item states
            this.state = {};
            
            // Get options from data- attributes
			emen2.util.checkopts(this, ['children', 'root', 'keytype']);

            this.element.addClass('e2-tree-'+escape(this.options.mode));
            if (this.options.attach) {
                this.bind(this.element);
            } else if (this.options.show) {
                this.build();
            }
            this.init();
        },
        
        init: function() {
            
        },
    
        build: function() {
            var self = this;
            this.element.empty();
            if (this.options.skiproot) {
                // Expand directly off this.element
                this.element.attr('data-name', this.options.root);
                this.expand(this.element, this.options.root);
            } else {
                // Build a root element, then expand it
                this.build_root(this.element, this.options.root);
            }
        },
        
        // Build a tree root
        build_root: function(elem, name) {
            var self = this;
            var name = (name == null) ? elem.attr('data-name') : name;
            if (!emen2.caches[this.options.keytype][name]) {
                this.getviews([name], function(){self.build_root(elem, name)});
                return
            }
            
            var li = $('<li />');
            $('<a />')
                .attr('href','#')
                .text(this.getname(this.options.root))
                .appendTo(li);
            emen2.template.image('bg.open.'+escape(this.options.mode)+'.png', '+', 'e2-tree-expand')
                .appendTo(li);
            li.wrap('<ul />');
            li.appendTo(this.element);
            this.bind(li);
            this.expand(li);
            return

            var root = $('<ul></ul>');
            root.append(' \
                <li data-name="'+escape(name)+'"> \
                    <a href="#">'+escape(this.getname(this.options.root))+'</a>'+
                    emen2.template.image('bg.open.'+escape(this.options.mode)+'.png', '+', 'e2-tree-expand')+
                '</li>');
            this.element.append(root);
            this.bind(root);
            this.expand(root.find('li'));            
        },
        
        // Draw a branch
        build_tree: function(elem, name) {
            // elem is usually an li that will have the new ul added
            // name can be specified, or parsed from data-name            
            var self = this;
            var name = (name == null) ? elem.attr('data-name') : name; 
            
            // Remove any spinners
            elem.find('img.e2l-spinner').remove();
                        
            // Set the image to expanded
            var img = elem.find('img.e2-tree-expand');
            img.addClass('e2-tree-expanded');
            img.attr('src', ROOT+'/static-'+escape(VERSION)+'/images/bg.close.'+escape(this.options.mode)+'.png');
            
            // The new ul
            var ul = $('<ul data-name="'+escape(name)+'"></ul>');

            // Lower-case alpha sort...
            var sortby = {};
            $.each(emen2.caches[this.options.mode][name], function() {
                sortby[this] = self.getname(this);
            });
            var sortkeys = emen2.util.sortdictstr(sortby);
            sortkeys.reverse();            
    
            // If there are no children, hide the expand image
            if (sortkeys.length == 0) {
                img.remove();
            }
            
            // Build each child item
            $.each(sortkeys, function() {
                var li = $(' \
                    <li data-name="'+escape(this)+'"> \
                        <a href="'+ROOT+'/'+escape(self.options.keytype)+'/'+escape(this)+'/">'
                            +self.getname(this)+
                        '</a> \
                    </li>');
                if (emen2.caches[self.options.mode][this] && self.options.expandable) {
                    var expand = emen2.template.image('bg.open.'+escape(self.options.mode)+'.png', emen2.caches[self.options.mode][this].length, 'e2-tree-expand');
                    li.append(expand);
                }
                ul.append(li);
            });
            elem.find('ul').remove();

            // Don't forget to adjust top
            elem.append(ul);
            var h = ul.siblings('a').height();
            ul.css('margin-top', -h);
            ul.css('min-height', h);
            
            // Adjust the heights and bind the img events
            this.bind(ul);
        },        

        // rebuild a branch
        expand: function(elem, name) {
            // elem is the LI
            var self = this;
            var name = (name == null) ? elem.attr('data-name') : name; 

            // Show activity indicator
            var img = elem.children('img');
            img.attr('src', ROOT+'/static-'+escape(VERSION)+'/images/spinner.gif'); 
            
            // Remove any current children
            elem.find('ul').remove();

            // We use rel.childrentree because we want to grab 2 levels of children/parents
            //     to determine if each child is itself expandable...
            var method = "rel.tree";

            emen2.db(method, {names:name, rel:this.options.mode, recurse:2, keytype:this.options.keytype}, function(tree){
                // Cache the result. This should be filtered for permissions
                $.each(tree, function(k,v) {emen2.caches[self.options.mode][k] = v});                
                // Get the items and/or rendered names, then build the tree
                // ... don't forget to use a .slice()'d copy!
                var names = (tree[name] || []).slice();
                names.push(name);
                names.push(self.options.root);
                self.getviews(names, function(){self.build_tree(elem)});
            });                
        },
        
        // expand/contract a branch        
        toggle_expand: function(elem) {
            // elem is the expand image element
            var self = this;
            var elem = $(elem);            
            if (elem.hasClass('e2-tree-expanded')) {
                // Contract this branch
                elem.removeClass('e2-tree-expanded');
                elem.siblings('ul').remove();
                elem.attr('src', ROOT+'/static-'+escape(VERSION)+'/images/bg.open.'+escape(this.options.mode)+'.png');
            } else {
                // Expand this branch
                this.expand(elem.parent());
            }            
        },
        
        bind: function(root) {
            this.bind_expand(root);
            this.bind_state(root);
            this.bind_select(root);
        },
        
        bind_expand: function(root) {
            var self = this;

            // height adjustment
            $('ul', root).each(function() {
                var elem = $(this);
                var h = elem.siblings('a').height();
                elem.css('margin-top', -h);
                elem.css('min-height', h);
            });

            // Click icon to toggle
            $('img.e2-tree-expand', root).click(function(e) {self.toggle_expand(this)});
        },
        
        bind_select: function(root) {
            var self = this;
            if (this.options.selected) {
                $('a', root).click(function(e) {
                    e.preventDefault();
                    var name = $(this).parent().attr('data-name');
                    self.options.selected(self, this, name);
                });
            }
        },

        bind_state: function(root) {
        },
        
        // cache items that we need, then go to the callback
        getviews: function(names, cb) {
            var self = this;
            var names = emen2.cache.check(this.options.keytype, names);
            if (names.length == 0) {
                cb();
                return
            }
            emen2.db('get', {names: names, keytype: this.options.keytype}, function(items) {
                emen2.cache.update(items);
                if (self.options.keytype == 'record') {
                    // For records, we also want to render the names..
                    var found = $.map(items, function(k){return k.name});
                    emen2.db('view', [found], function(recnames) {
                        $.each(recnames, function(k,v) {emen2.caches['recnames'][k]=v});
                        cb();
                    });
                } else {
                    cb();
                }
            });        
        },
        
        // more type-specific handling..
        getname: function(item) {
            if (this.options.keytype == 'record') {
                return emen2.caches['recnames'][item] || '('+String(item)+')'
            } else if (this.options.keytype == 'paramdef') {
                return emen2.caches['paramdef'][item].desc_short || item
            } else if (this.options.keytype == 'recorddef') {
                return emen2.caches['recorddef'][item].desc_short || item
            }            
        }
    });
    
    ////////////////////////////
    // Select items in a tree
    $.widget('emen2.TreeSelectControl', $.emen2.TreeControl, {
        init: function() {
            var self = this;
            // this option name might change; I was already using 'selected'
            if (this.options.active.length) {
                this.add(this.options.active);
            }
            // Bind to the form submit
            this.element.parent('form').submit(function(e){self.submit(e)});
        },
        
        submit: function(e) {
            var self = this;
            // console.log("Submitting -- building inputs");
            $('input[name=state]', this.element).remove();
            $.each(this.state, function(k,v) {
                if (v) {
                    // console.log('adding', k);
                    self.element.append('<input type="hidden" name="state" value="'+escape(k)+'" />');
                }
            });
        },
        
        bind_state: function(root) {
            var self = this;
            $('li', root).each(function() {
                var name = $(this).attr('data-name');
                if (self.state[name]) {
                    $(this).children('a').addClass('e2-browse-selected');
                } else {
                    $(this).children('a').removeClass('e2-browse-selected');                    
                }
            });
        },

        bind_select: function(root) {
            var self = this;
            $('a', root).click(function(e) {
                e.preventDefault();
                var name = $(this).parent().attr('data-name');
                self.toggle_select(e, this, name);
            });
        },
            
        add: function(items) {
            for (var i=0;i<items.length;i++) {
                var name = items[i];
                this.state[name] = true;
                $('li[data-name="'+escape(name)+'"] > a').addClass('e2-browse-selected');
            }
            this.count_selected();        
        },
        
        remove: function(items) {
            for (var i=0;i<items.length;i++) {
                var name = items[i];
                this.state[name] = false;
                $('li[data-name="'+escape(name)+'"] > a').removeClass('e2-browse-selected');
            }
            this.count_selected();        
        },
        
        count_selected: function() {
            var count = 0;
            $.each(this.state, function(k,v) {
                if (v) {count++}
            });
            $(this.options.display_count).text(count);
            return count
        },
        
        toggle_select: function(e, elem, name) {
            var state = this.state[name];
            var self = this;
            if (e.shiftKey && this.options.shiftselect) {
                // This element and all children, recursively
                emen2.db('rel.children', {names: name, recurse:-1}, function(children) {
                    children.push(name);
                    if (state) {
                        self.remove(children);
                    } else {
                        self.add(children);
                    }
                });
            } else {
                // Just this element
                if (state) {
                    this.remove([name]);
                } else {
                    this.add([name]);
                }
            }
        },
    });
    
    
    $.widget('emen2.TreeMoveControl', $.emen2.TreeSelectControl, {
        bind_select: function(root) {
            var self = this;

            $('a', root).click(function(e) {
                e.preventDefault();
                $(this).toggleClass('e2-browse-selected');
                // var name = $(this).parent().attr('data-name');
                // self.toggle_select(e, this, name);
            });

            $('a', root).draggable({
                helper: function() {
                    var count = $('.e2-browse-selected', self.element).length;
                    return '<div class="ui-widget-header" style="z-index:500">Moving '+escape(count)+' items</div>';
                }
            });

            $('a', root).droppable({
                activeClass: 'e2-browse-active',
                hoverClass: 'e2-browse-hover',
                drop: function(e, ui) {
                    var newparent = $(e.target).parent().attr('data-name');
                    var addrels = [];
                    var removerels = [];
                    $('.e2-browse-selected', self.element).each(function() {
                        var name = $(this).parent().attr('data-name');
                        var parent = $(this).parent().parent().attr('data-name');
                        removerels.push([parent, name]);
                        addrels.push([newparent, name]);
                    });

                    // console.log(removerels, addrels);
                    self.confirm_relink(removerels, addrels);
                }
            });
        },

        confirm_relink: function(removerels, addrels) {
            var self = this;

            var dialog = $('<div title="Confirm move">This action will add and remove the following relationships:</div>');
            dialog.append('<h4>Remove</h4>');
            var ulr = $('<ul class="e2l-nonlist" />');
            $.each(removerels, function() {
                ulr.append('<li>'+escape(emen2.caches['recnames'][this[0]]||this[0])+', '+escape(emen2.caches['recnames'][this[1]]||this[1])+'</li>');
            });
            dialog.append(ulr);
            dialog.append('<h4>Add</h4>');
            var ula = $('<ul class="e2l-nonlist" />');
            $.each(addrels, function() {
                ula.append('<li>'+escape(emen2.caches['recnames'][this[0]]||this[0])+', '+escape(emen2.caches['recnames'][this[1]]||this[1])+'</li>');
            });
            dialog.append(ula);


            dialog.dialog({
                resizable: false,
                draggable: false,
                modal: true,
                buttons: {
                    "Confirm": function(e) {
                        $('.ui-button-text', e.target).text("Saving...");
                        self.relink(removerels, addrels);
                    },
                    Cancel: function() {
                        $(this).dialog("close");
                    }
                }
            });            
        },
        
        relink: function(removerels, addrels) {
            var form = $('<div class="e2-browse-relinkform"></div>');
            removerels.map(function(i) {
                form.append('<input type="hidden" name="removerels.'+escape(i[0])+'" value="'+escape(i[1])+'" />');
            });
            addrels.map(function(i) {
                form.append('<input type="hidden" name="addrels.'+escape(i[0])+'" value="'+escape(i[1])+'" />');
            });
            $('.e2-browse-relinkform', this.element).remove();
            this.element.append(form);
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