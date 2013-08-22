(function($) {
    
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

            // $('<li />')
            // .addClass('e2l-float-right')
            // .append(
            //     $('<input class="e2-query-keywords" type="text" />')
            //         .attr('name', 'keywords')
            //         .attr('placeholder', 'Filter')
            //         .attr('size', 6)
            //     )
            // .append(
            //     $('<input type="button" value="Go" />')
            //         .click(function(){self.keywords()})
            //     )
            // .appendTo(ul);
                                        
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
            // $('.e2-query-control', this.element).QueryControl('update', this.options.q)                    

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
                    if (self.options.q['rendered'][names[i]] == null) {
                        $('<td>-</td>').appendTo(row);
                    } else {
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
                                .attr('href', emen2.template.uri([self.options.q['keytype'], names[i]]))
                                .text(rendered);
                        }
                        $('<td />').append(a).appendTo(row);
                    }
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