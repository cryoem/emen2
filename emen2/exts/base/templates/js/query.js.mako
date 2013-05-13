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
        if (postpend) {
            output.push(encodeURIComponent(postpend));
        }
        delete q['c'];
        delete q['ignorecase'];
        delete q['boolmode'];
        return ROOT+'/query/'+output.join("/")+'/?'+$.param(q);
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
                var row = $('<tr/>');
                row.append($('<td />').text(name));
                row.append($('<td />').text(v));
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

            this.count = 0; // temporary fix

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
                <h2>Query constraints</h2> \
                <ul class="e2l-nonlist e2-query-base e2-query-constraints"> \
                    <li class="e2-query-constraint"> \
                        <strong class="e2-query-label">Protocol:</strong> \
                        <input type="hidden" name="param" value="rectype" /> \
                        <input type="hidden" name="cmp" value="is" /> \
                        <input type="text" name="value" id="e2-query-find-protocol" placeholder="Select protocol" /> \
                        <img class="e2-query-find" data-keytype="recorddef" data-target="e2-query-find-protocol" src="" /> \
                        <input type="checkbox" name="recurse_v" id="e2-query-id-rectype"/><label for="e2-query-id-rectype">Include child protocols</label> \
                    </li> \
                    <li class="e2-query-constraint"> \
                        <strong class="e2-query-label">Creator:</strong> \
                        <input type="hidden" name="param" value="creator" /> \
                        <input type="hidden" name="cmp" value="is" /> \
                        <input type="text" name="value" id="e2-query-find-user" placeholder="Select user" /> \
                        <img class="e2-query-find" data-keytype="user" data-target="e2-query-find-user" src="" /> \
                    </li> \
                    <li class="e2-query-constraint"> \
                        <strong class="e2-query-label">Child of:</strong> \
                        <input type="hidden" name="param" value="children" /> \
                        <input type="hidden" name="cmp" value="name" /> \
                        <input type="text" name="value" id="e2-query-find-record" placeholder="Select record"/> \
                        <img class="e2-query-tree" data-keytype="record" data-target="e2-query-find-record" src="" /> \
                        <input type="checkbox" name="recurse_v" id="e2-query-paramid-children" /><label for="e2-query-paramid-children">Recursive</label> \
                    </li> \
                    <li> \
                        <strong class="e2-query-label">Created:</strong> \
                        <span  class="e2-query-constraint"> \
                            <input type="hidden" name="param" value="creationtime" /> \
                            <input type="hidden" name="cmp" value=">=" /> \
                            <input type="text" name="value" placeholder="Start date" /> \
                        </span>&nbsp;&nbsp;&nbsp;to&nbsp;&nbsp;&nbsp;<span class="e2-query-constraint"> \
                            <input type="hidden" name="param" value="creationtime" /> \
                            <input type="hidden" name="cmp" value="<=" /> \
                            <input type="text" name="value" placeholder="end date" /> \
                        </span> \
                    </li> \
                </ul> \
                <ul class="e2l-nonlist e2-query-param e2-query-constraints"></ul> \
            ');
            
            $('img.e2-query-find', m).attr('src', ROOT+'/static/images/query.png');
            this.container.append(m);
            
            // ian: todo
            $('.e2-query-find', this.container).FindControl({keytype: 'user'});
            $('.e2-query-tree', this.container).TreeBrowseControl({
                root: "0",
                keytype: "record",
                selected: function(ui, name) {
                    // Hacked: fix
                    //console.log("added:", ui, name)
                    $('#e2-query-find-record').val(name);
                }
            })
            // $('.e2-find-group', this.container).FindControl({keytype: 'group'});
            // $('.e2-find-recorddef', this.container).FindControl({keytype: 'recorddef'});
            // $('.e2-find-paramdef', this.container).FindControl({keytype: 'paramdef'});

            var save = $('<ul class="e2l-controls"><li><input type="button" value="Query" name="save" /></li>');
            this.container.append(save);
            $('input[name=save]', this.container).bind("click", function(e){self.query()});            

            $('.e2-query-clear-all', this.container).click(function(e) {
                $('.e2-query-constraints .e2-query-constraint', this).each(function(){self.clear($(this))});
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

            // Copy existing options...
            // newq['subset'] = this.options.q['subset'];
            // newq['keytype'] = this.options.q['keytype'];

            var ignorecase = $('input[name=ignorecase]', this.container).attr('checked');
            var boolmode = $('input[name=boolmode]:checked', this.container).val();
                                    
            $('.e2-query-base .e2-query-constraint', this.container).each(function() {
                var p = self._getconstraint(this);
                if (p[0] && p[1] && p[2]) {c.push(p)}
            });
            $('.e2-query-param .e2-query-constraint', this.container).each(function() {
                var p = self._getconstraint(this);
                if (p[0]) {c.push(p)}
            });

            newq['c'] = c;
            
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

            var controls = $('<strong class="e2-query-label"></strong>');
            var addimg = emen2.template.image('add.png', 'Add');
            addimg.click(function() {self.addconstraint()});
            var removeimg = emen2.template.image('cancel.png', 'Remove', 'e2-query-clear');
            removeimg.click(function(e) {
                self.event_clear(e);
            });
            controls.append(addimg, removeimg);

            this.count += 1;
            
            var newconstraint = $('<li class="e2-query-constraint" />')
                .append(controls)
                .append(' <input type="text" name="param" value="" placeholder="Select parameter" /> ')
                .append(' <img class="e2-query-find" data-keytype="paramdef" src="" /> ')
                .append(cmpi)
                .append(' <input type="text" name="value" size="12" value="" placeholder="value" />');                
            $('input[name=param]', newconstraint).attr('id', 'e2-query-find-'+escape(this.count)).val(param);
            $('img.e2-query-find', newconstraint).attr('id', 'e2-query-find-'+escape(this.count)).attr('src', ROOT+'/static/images/query.png');
            $('input[name=value]', newconstraint).val(value);

            if (recurse) {$('input[name=recurse_p]', newconstraint).attr('checked', 'checked')}
            $('.e2-query-find', newconstraint).FindControl({keytype: 'paramdef'});
            $('.e2-query-param', this.container).append(newconstraint);
        },
        
        build_cmp: function(cmp) {
            //"!contains":"does not contain",
            // Check the transforms..
            var cmp2 = this.comparators_lookup[cmp] || cmp;
            
            var i = $('<select name="cmp" />');
            $.each(this.comparators, function(k,v) {
                var r = $('<option value="" />').val(k).text(v);
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
            var selector = '.e2-query-param .e2-query-constraint';
            var param_constraints = [];
            if (base) {
                var selector = '.e2-query-base .e2-query-constraint';
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
            // if (new_constraints.length == 0) {
                self.addconstraint();
            //}
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
            this.checkbox = {};
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
            
            // Controls
            ul.append('<li><span class="e2-query-length">Records</span></li>');
            ul.append('<li class="e2l-float-right e2-query-pages"></li>');

            // Row count
            var count = $('<select name="count" class="e2l-small"></select>');
            count.append('<option value="100">Rows</option>');
            $.each([1, 10,100,1000], function() {
                count.append($('<option />').val(this).text(""+this));
            });
            count.change(function() {
                self.options.q['pos'] = 0;
                self.query();
            })            
            count = $('<li class="e2l-float-right" />').append($('<span class="e2l-a"></span>').append(count));
            ul.append(count);

            // Create new record
            if (this.options.rectype != null && this.options.parent != null) {
                var create = $(' \
                    <li class="e2l-float-right"> \
                        <span> \
                        <form action="" method="get"> \
                            <input type="button" data-rectype="'+escape(this.options.rectype)+'" data-parent="'+escape(this.options.parent)+'" value="New '+escape(this.options.rectype)+'" /> \
                        </form> \
                        </span> \
                    </li>');             
                $('form', create).attr('action', ROOT+'/record/'+escape(this.options.parent)+'/new/'+escape(this.options.rectype)+'/')
                ul.append(create);
                $('input[type=button]', create).RecordControl();
            }            

            // Edit
            // var edit = $('<li class="e2l-float-right" data-tab="edit"><span class="e2l-a"><img src="/static/images/edit.png" /></span></li>')
            // edit.click(function() {
            //     self.edit();
            // });
            // ul.append(edit);

            // Modify query
            ul.append('<li class="e2l-float-right" data-tab="controls"><span class="e2l-a"><img src="/static/images/query.png" /></span></li>')

            // Activity spinner
            ul.append('<li class="e2l-float-right e2-query-activity" style="display:none"><span>'+escape(emen2.template.spinner(true))+'</span></li>');

            // Tab control
            tab.TabControl({});
            tab.TabControl('setcb', 'controls', function(page) {
                page.QueryControl({
                    q: self.options.q,
                    keywords: false
                });    
            });                 
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
            newq['rendered'] = true;
            emen2.db("table", newq, function(q){self.update(q)});            
        },
        
        query_bookmark: function(newq) {
        },
        
        edit: function() {
            var self = this;
            this.options.q['options'] = {};
            this.options.q['options']['output'] = 'form';
            this.query();  
        },
        
        setpos: function(pos) {
            // Change the page
            if (pos == this.options.q['pos']) {return}
            var self = this;
            this.options.q['pos'] = pos;
            this.query();
        },
        
        resort: function(sortkey) {
            // Sort by a column key
            if (this.options.q['sortkey'] == sortkey) {
                this.options.q['reverse'] = (this.options.q['reverse']) ? false : true;
            } else {
                this.options.q['reverse'] = false;
            }
            this.options.q['sortkey'] = sortkey;
            this.query();
            // this.query_bookmark();
        },
        
        checkbox_cache: function() {
            var self = this;
            $('input:checkbox.e2-query-checkbox', this.element).each(function() {
                self.checkbox[$(this).val()] = $(this).attr('checked') || false;
            });
        },
        
        update: function(q) {
            // Callback from a query; Update the table and all controls
            this.checkbox_cache();

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
            title = this.options.q['stats']['length']+' results, '+rtkeys.length+' protocols';
            if (rtkeys.length == 0) {
                title = this.options.q['stats']['length']+' results';                
            } else if (rtkeys.length == 1) {
                title = this.options.q['stats']['length']+' '+rtkeys[0]+' results';
            } else if (rtkeys.length <= 5) {
                title = title+": ";
                for (var i=0;i<rtkeys.length;i++) {
                    title = title + self.options.q['stats']['rectypes'][rtkeys[i]]+' '+rtkeys[i];
                    if (i+1<rtkeys.length) {
                        title = title+', ';
                    }
                }
            }
            if (this.options.q['stats']['time']) {
                title = title+' ('+this.options.q['stats']['time'].toFixed(2)+'s)';
            }
            $('.e2-query-header .e2-query-length').text(title);

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
                var p2 = $('<span class="e2l-a" data-pos="'+escape(this.options.q['pos'] - this.options.q['count'])+'">&lsaquo;</span>').click(setpos);
                var p  = $('<span> '+escape(current+1)+' / '+escape(pagecount+1)+' </span>');
                var p3 = $('<span class="e2l-a" data-pos="'+escape(this.options.q['pos'] + this.options.q['count'])+'">&rsaquo;</span>').click(setpos);
                var p4 = $('<span class="e2l-a" data-pos="'+escape(pagecount*this.options.q['count'])+'">&raquo;</span>').click(setpos);

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
            var keys = this.options.q['keys'];
            var keys_desc = this.options.q['keys_desc'];
            
            // Clear out the current header
            $('thead', t).empty();
            
            var tr = $('<tr />');
            var tr2 = $('<tr class="e2-query-sort"/>');
            
            if (this.options.q['checkbox']) {
                // Build the check boxes for selecting records
                tr.append('<th><input type="checkbox" checked="checked" /></th>');
                tr2.append('<th />');
            }

            // Build the rest of the column headers
            $.each(keys, function() {
                tr.append($('<th/>').text(" "+(keys_desc[this] || this)));
                // Build the sort button
                var direction = 'able';
                if (self.options.q['sortkey'] == this) {
                    var direction = 1;
                    if (self.options.q['reverse']) {direction = 0}
                }                
                var sortable = $('<button name="sort" class="e2l-float-right" />').append(emen2.template.image('sort.'+escape(direction)+'.png', 'Sort'));
                var iw = $('<th data-name="" />').attr('data-name', this);         
                iw.append(sortable);
                tr2.append(iw)
            });

            // Connect the sort buttons
            $('button[name=sort]', tr2).click(function(e){
                e.preventDefault();
                self.resort($(this).parent().attr('data-name'))
            });
            
            // Append the title row and control row
            $('thead', t).append(tr, tr2);
        },
        
        rebuild_tbody: function() {
            // Rebuild the table body
            var self = this;
            var keys = this.options.q['keys'];
            var names = this.options.q['names'];
            var checkbox = this.options.q['checkbox'];
            var t = $('.e2-query-table', this.element);            
            var tbody = $('tbody', t);
            tbody.empty();

            // Empty results
            if (names.length == 0) {
                tbody.append('<tr><td>No results for this query.</td</tr>');
            }

            // Build each row
            for (var i=0;i<names.length;i++) {
                // Slower, but safer.
                var row = $('<tr />');
                if (checkbox) {
                    var cb = $('<input class="e2-query-checkbox" type="checkbox" />');
                    cb.val(names[i]);
                    cb.attr('checked', this.checkbox[names[i]]);
                    row.append($('<td />').append(cb));
                }
                
                for (var j=0; j < keys.length; j++) {
                    var td = $('<td />');
                    var a = $('<a href="" />');
                    a.text(self.options.q['rendered'][names[i]][keys[j]]);
                    a.attr('href', ROOT+'/record/'+escape(names[i])+'/');
                    td.append(a);
                    row.append(td);
                }
                tbody.append(row);
            }
            // This needs to rebind several things...
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