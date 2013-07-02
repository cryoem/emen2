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
        output.push('query')
        $.each(q['c'], function() {
            output.push(this[0]+'.'+(comparators_lookup[this[1]] || this[1])+'.'+this[2]);
        });
        if (postpend) {
            output.push(postpend);
        }
        delete q['c'];
        delete q['boolmode'];
        return emen2.template.uri(output, q);
    }

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
                "gt": "is greater than",
                "lt": "is less than",
                "gte": "is greater or equal than",
                "lte": "is less or equal than",
                "any": "is any value",
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
            if (this.built) {return}
            this.built = 1;
            
            this.container = $('<div />')
                .addClass('e2l-cf')
                .appendTo(this.element);

            // todo: Big ugly markup. Fix this.
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
                            <span class="e2-query-constraint"> \
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
                    <ul class="e2l-nonlist e2-query-param e2-query-constraints"></ul>')
                .appendTo(this.container);
            
            // ugh.
            $('.e2-query-find', this.container)
                .attr('src', emen2.template.uri(['static', 'images', 'query.png']))
                .FindControl({});
                
            $('.e2-query-tree', this.container).TreeBrowseControl({
                root: "0",
                keytype: "record",
                selected: function(ui, name) {
                    // Hacked: fix
                    $('#e2-query-find-record').val(name);
                }
            })

            var save = $('<ul />')
                .addClass('e2l-controls')
                .appendTo(this.container);

            $('<input type="button" />')
                .val('Query')
                .click(function(){self.query()})
                .wrap('<li />')
                .appendTo(save);

            this.update();
        },
        
        event_clear: function(e) {
            var t = $(e.target).parent().parent();
            this.clear(t);
        },
        
        clear: function(t) {
            var base = t.parent().hasClass('e2-query-base');
            $('input[name=value]', t).val('')
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
            return [param, cmp, value];
        },
        
        getquery: function() {
            var self = this;
            var newq = {};
            var c = [];

            // Copy existing options...
            // newq['subset'] = this.options.q['subset'];
            // newq['keytype'] = this.options.q['keytype'];

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
            
            if (boolmode) {newq['boolmode'] = boolmode}
            return newq
        },
        
        query: function() {
            var newq = this.getquery();
            this.options.query(this, newq);
        },
        
        addconstraint: function(param, cmp, value) {
            this.count += 1;
            param = param || '';
            cmp = cmp || 'any';
            value = value || '';
            var self = this;
            
            var constraint = $('<li />')
                .addClass('e2-query-constraint')
                .appendTo(this.container);

            var controls = $('<strong />')
                .addClass('e2-query')
                .appendTo(constraint);

            emen2.template.image('add.png', 'Add')
                .click(function() {self.addconstraint()})
                .appendTo(controls);
            emen2.template.image('cancel.png', 'Remove')
                .click(function(e) {self.event_clear(e)})
                .appendTo(controls);

            $('<input type="text" />')
                .attr('name', 'param')
                .attr('placeholder', 'Select parameter')
                .val('')
                .appendTo(constraint)

            emen2.template.image('query.png')
                .attr('data-keytype', 'paramdef')
                .addClass('e2-query-find')
                .appendTo(constraint)
                .FindControl({});
                
            this.build_cmp(cmp).appendTo(constraint);
            
            $('<input type="text" />')
                .attr('name', 'value')
                .attr('size', 12)
                .attr('placeholder', 'value')
                .appendTo(constraint);    
        },
        
        build_cmp: function(cmp) {
            var cmp2 = this.comparators_lookup[cmp] || cmp;
            var i = $('<select />')
                .attr('name', 'cmp');
            $.each(this.comparators, function(k,v) {
                var r = $('<option />').val(k).text(v);
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
            var recurse_v = false;
            if (value.search('\\*') > -1) { 
                recurse_v = true;
                value = value.replace('*', '');
            }

            cmpi = this.comparators_lookup[cmpi] || cmpi;
            
            // Get the constraint elements.
            var _param = $('input[name=param]', elem);
            var _cmpi = $('input[name=cmp]', elem);
            var _value = $('input[name=value]', elem);
            var _recurse_v = $('input[name=recurse_v]', elem);
            
            // Get the values
            var _param2 = _param.val();
            var _cmpi2 = _cmpi.val();
            var _value2 = _value.val();
            var _recurse_v2 = _recurse_v.attr('checked');

            base = true;
            if (base) {
                _value2 = value;
                _recurse_v2 = recurse_v;
            }
            
            // If this constraint matches, update the element and return True
            if (
                param == _param2
                && cmpi == _cmpi2
                && value == _value2
                && recurse_v == _recurse_v2
            ) {
                _value.val(value);
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
            this.addconstraint();
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
            
            ul.empty();

            // Record count
            $('<li />')
                .addClass('e2-query-length')
                .addClass('e2l-float-left')
                .text('Records')
                .appendTo(ul)
                // needs to come after append...
                
            // Pagination
            $('<li />')
                .addClass('e2-query-pages')
                .addClass('e2l-float-right')
                .addClass('e2-query-extraspacing')
                .appendTo(ul);
            
            // Row count
            var count = $('<select />')
                .attr('name', 'count')
                .change(function() {
                    self.options.q['pos'] = 0;
                    self.query();
                });
            $('<option />')
                .attr('value', '100')
                .text('Rows')
                .appendTo(count);
            $.each([1, 10,100,1000], function() {
                $('<option />')
                    .val(this)
                    .text(""+this)
                    .appendTo(count);
            });

            $('<li />')
                .addClass('e2l-float-right')
                .append(count)
                .appendTo(ul);
            
            // Create new record
            if (this.options.rectype != null && this.options.parent != null) {
                var form = $('<form />')
                    .attr('method','get')
                    .attr('action', emen2.template.uri(['record', this.options.parent, 'new', this.options.rectype]))
                $('<input type="button" />')
                    .val('New '+this.options.rectype)
                    .appendTo(form)
                    .RecordControl({
                        'rectype':this.options.rectype,
                        'parent':this.options.parent
                    });
                $('<li />')
                    .addClass('e2l-float-right')
                    .append(form)
                    .appendTo(ul);    
            }            

            // Awful hack!!
            if (this.options.q['keytype'] == 'binary') {
                $('<li />')
                .addClass('e2l-float-right')
                .appendTo(ul)
                .append(
                    $('<input type="button" class="e2-query-download" />')
                    .val('Download selected')
                    .click(function(){self.download()})
                );
            }

            // Query control
            // $('<li />')
            //    .addClass('e2l-float-right')
            //    .appendTo(ul)
            //    .append(
            //        $('<input type="button" />')
            //        .val('Modify query')
            //    );                                                            

            $('<li />')
            .addClass('e2l-float-right')
            .append(
                $('<input class="e2-query-keywords" type="text" />')
                    .attr('name', 'keywords')
                    .attr('placeholder', 'Filter')
                    .attr('size', 6)
                )
            .append(
                $('<input type="button" value="Go" />')
                    .click(function(){self.keywords()})
                )
            .appendTo(ul);
                                        
            $('<li />')
                .addClass('e2l-float-right')
                .append(emen2.template.spinner().addClass('e2-query-activity'))
                .appendTo(ul);
        },
        
        keywords: function() {
            var keywords = $('.e2-query-keywords', this.element).val();
            console.log("Filtering:", keywords);
            this.options.q['keywords'] = keywords;
            this.query();
        },
        
        download: function() {
            var dialog = $('<div />')
                .attr('title', 'Confirm')
            
                var form = $('<form method="post" />')
                .attr('action', emen2.template.uri(['download']))
                .appendTo(dialog);
            
            var bdos = [];
            var size = 0;
            $('input.e2-query-checkbox:checked', this.element).each(function(){
                bdos.push($(this).val())
                $('<input type="hidden" />')
                    .attr('name', 'name')
                    .val($(this).val())
                    .appendTo(form);
            });
            

            var count = $('<p />')
                .text('Download '+$.escape(bdos.length)+' files?') 
                //', '+emen2.template.prettybytes(size))
                .appendTo(dialog);

            dialog.dialog({
                    resizable: false,
                    draggable: false,
                    modal: true,
                    buttons: {
                        "Confirm": function(e) {
                            $('form', this).submit();
                            $(this).dialog('close');
                        },
                        "Cancel": function() {
                            $(this).dialog("close");
                        }
                    }
                }); 
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
            
            // ... build the pagination controls
            var count = this.options.q['count'];
            var l = this.options.q['stats']['length'];
            if (count == 0 || count > l || l == 0) {
                //pages.append("All Records");
            } else {            
                var current = (this.options.q['pos'] / this.options.q['count']);
                var pagecount = Math.ceil(this.options.q['stats']['length'] / this.options.q['count'])-1;
                var setpos = function() {self.setpos(parseInt($(this).attr('data-pos')))}            

                var p1 = $('<span />')
                    .addClass('e2l-a')
                    .attr('data-pos', 0)
                    .html('&laquo;')
                    .click(setpos)
                var p2 = $('<span />')
                    .addClass('e2l-a')
                    .attr('data-pos', this.options.q['pos'] - this.options.q['count'])
                    .html('&lsaquo;')
                    .click(setpos);
                var p =  $('<span />')
                    .text( (current+1)+' / '+(pagecount+1) );
                var p3 = $('<span />')
                    .addClass('e2l-a')
                    .attr('data-pos', this.options.q['pos'] + this.options.q['count'])
                    .html('&rsaquo;')
                    .click(setpos);
                var p4 = $('<span />')
                    .addClass('e2l-a')
                    .attr('data-pos', pagecount*this.options.q['count'])
                    .html('&raquo;')
                    .click(setpos);

                if (current > 0) {pages.prepend(p2)}
                if (current > 1) {pages.prepend(p1, '')}
                pages.append(p);
                if (current < pagecount) {pages.append(p3)}
                if (current < pagecount - 1) {pages.append('', p4)}
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
            var thead = $('thead', t);
            thead.empty();
            
            var tr = $('<tr />').appendTo(thead);
            var tr2 = $('<tr />').addClass('e2-query-sort').appendTo(thead);
            
            // Build the rest of the column headers
            $.each(keys, function() {
                $('<th />').text(" "+(keys_desc[this] || this)).appendTo(tr);
                // Build the sort button
                var direction = 'able';
                if (self.options.q['sortkey'] == this) {
                    var direction = 1;
                    if (self.options.q['reverse']) {direction = 0}
                }                
                var iw = $('<th />').attr('data-name', this).appendTo(tr2);
                $('<button />')
                    .attr('name', 'sort')
                    .addClass('e2l-float-right')
                    .click(function(e){
                        e.preventDefault();
                        self.resort($(this).parent().attr('data-name'))
                    })
                    .append(emen2.template.image('sort.'+direction+'.png', 'Sort'))
                    .appendTo(iw);
            });
        },
        
        rebuild_tbody: function() {
            // Rebuild the table body
            var self = this;
            var keys = this.options.q['keys'];
            var names = this.options.q['names'];
            var t = $('.e2-query-table', this.element);            
            var tbody = $('tbody', t);
            tbody.empty();
            
            // Empty results
            if (names.length == 0) {
                $('<td />').text('No results.').wrap('<tr />').appendTo(tbody);
            }

            // Build each row
            for (var i=0;i<names.length;i++) {
                // Slower, but safer.
                var row = $('<tr />').appendTo(tbody);
                for (var j=0; j < keys.length; j++) {
                    var rendered = self.options.q['rendered'][names[i]][keys[j]];
                    if (keys[j] == "checkbox()") {
                        var a = $('<input type="checkbox" />')
                            .addClass('e2-query-checkbox')
                            .val(names[i])
                            .attr('checked', this.checkbox[names[i]]);
                    } else if (keys[j] == "thumbnail()") {
                        var a = $('<img />')
                            .addClass('e2l-thumbnail')
                            .attr('src', '/'+rendered);
                    } else {
                        var a = $('<a />')
                            .attr('href', emen2.template.uri(['record', names[i]]))
                            .text(rendered);
                    }
                    $('<td />').append(a).appendTo(row);
                }
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