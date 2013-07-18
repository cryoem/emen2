// Log wrapper to keep everything from crashing horribly
//        if I forget to comment out a Firebug console.log()
// http://paulirish.com/2009/log-a-lightweight-wrapper-for-consolelog/
window.log = function(){
  log.history = log.history || [];   // store logs to an array for reference
  log.history.push(arguments);
  if(this.console){
    console.log( Array.prototype.slice.call(arguments) );
  }
};

// Plot...
var d3 = null;

// Escape -- todo: switch to emen2.template.uri
$.escape = encodeURIComponent; 
//function(i){return encodeURIComponent(i)};

// Time localize format
$.localize.format = 'mm/dd/yyyy';

// EMEN2 helper methods
var emen2 = {};

// EMEN2 time functions
emen2.time = {};

emen2.time.pad = function(n) {
    return n<10 ? '0'+n : n
};

// Print an ISO Date String in UTC time
emen2.time.UTCISODateString = function(d) {
    return d.getUTCFullYear()+'-'
    + emen2.time.pad(d.getUTCMonth()+1)+'-'
    + emen2.time.pad(d.getUTCDate())+'T'
    + emen2.time.pad(d.getUTCHours())+':'
    + emen2.time.pad(d.getUTCMinutes())+':'
    + emen2.time.pad(d.getUTCSeconds())+'Z'
}

// Print an ISO Date String
emen2.time.ISODateString = function(d) {
    var sep = '-';
    var offset = d.getTimezoneOffset();
    if (offset < 0) {
        sep = '+';
        offset = Math.abs(offset);
    }
    var hours = Math.floor(offset/60);
    var minutes = offset % 60;
    return d.getFullYear() + '-'
    + emen2.time.pad(d.getMonth()+1) +'-'
    + emen2.time.pad(d.getDate()) + 'T'
    + emen2.time.pad(d.getHours()) + ':'
    + emen2.time.pad(d.getMinutes()) + ':'
    + emen2.time.pad(d.getSeconds()) + sep
    + emen2.time.pad(hours) + ':'
    + emen2.time.pad(minutes)
}

emen2.time.now = function() {
    return emen2.time.ISODateString(new Date());
}

emen2.time.range = function(t1, t2, width) {
    var t2 = t2 || new Date();
    var width = width || 'month';
    var f = emen2.time.interval[width];
    var start = f(t1)[0];
    var end = f(t2)[1];
    var cur = start;
    var ret = [];
    var i = 0;
    while (cur<end) {
        var d = f(cur);
        ret.push(d[0]);
        cur = d[1];
    }
    ret.push(end);
    return ret
};
emen2.time.start = function(t1, width) {
    var t1 = t1 || new Date();
    var width = width || 'month';
    return emen2.time.interval[width](t1)[0]
};

// EMEN2 Time interval helpers
emen2.time.interval = {};


// Return year interval
emen2.time.interval.year = function(t1) {
    var t1 = t1 || new Date();
    var start = new Date(t1.getFullYear(), 0, 1, 0, 0, 0, 0);
    var end = new Date(t1.getFullYear()+1, 0, 1, 0, 0, 0, 0);
    return [start, end]
};

emen2.time.interval.month = function(t1) {
    var t1 = t1 || new Date();
    var start = new Date(t1.getFullYear(), t1.getMonth(), 1, 0, 0, 0, 0);
    var end = new Date(t1.getFullYear(), t1.getMonth()+1, 1, 0, 0, 0, 0);
    return [start, end]
};

emen2.time.interval.day = function(t1) {
    var t1 = t1 || new Date();
    var start = new Date(t1.getFullYear(), t1.getMonth(), t1.getDate(), 0, 0, 0, 0);
    var end = new Date(t1.getFullYear(), t1.getMonth(), t1.getDate()+1, 0, 0, 0, 0);
    return [start, end]    
};

emen2.time.interval.hour = function(t1) {
    var t1 = t1 || new Date();
    var start = new Date(t1.getFullYear(), t1.getMonth(), t1.getDate(), t1.getHours(), 0, 0, 0);
    var end = new Date(t1.getFullYear(), t1.getMonth(), t1.getDate(), t1.getHours()+1, 0, 0, 0);
    return [start, end]    
};

emen2.time.interval.minute = function(t1) {
    var t1 = t1 || new Date();
    var start = new Date(t1.getFullYear(), t1.getMonth(), t1.getDate(), t1.getHours(), t1.getMinutes(), 0, 0);
    var end = new Date(t1.getFullYear(), t1.getMonth(), t1.getDate(), t1.getHours(), t1.getMinutes()+1, 0, 0);
    return [start, end]    
};

emen2.time.interval.second = function(t1) {
    var t1 = t1 || new Date();
    var start = new Date(t1.getFullYear(), t1.getMonth(), t1.getDate(), t1.getHours(), t1.getMinutes(), t1.getSeconds(), 0);
    var end = new Date(t1.getFullYear(), t1.getMonth(), t1.getDate(), t1.getHours(), t1.getMinutes(), t1.getSeconds()+1, 0);
    return [start, end]
};



// EMEN2 cache handling
emen2.cache = {};

emen2.caches = {
    'user': {},
    'group': {},
    'record': {'None':{}},
    'paramdef': {},
    'recorddef': {},
    'binary': {},
    'children': {},
    'parents': {},
    'recnames': {}
};

emen2.cache.get = function(key, keytype) {
    var keytype = keytype || 'record';
    return emen2.caches[keytype][key]
};

emen2.cache.update = function(items) {
    $.each(items, function() {
        if (!this.keytype) {return}
        emen2.caches[this.keytype][this.name] = this;
    })
};

emen2.cache.check = function(keytype, items) {
    var ret = [];
    $.each(items, function(i,v) {
        if (v == 'None' || v == null) {
            return
        }
        var item = emen2.caches[keytype][v];
        if (item==null && $.inArray(v,ret)==-1) {ret.push(v)}
    });
    return ret
};

// Alias to $.jsonRPC.call
emen2.db = function(method, args, cb, eb) {
    return $.jsonRPC.call(method, args, cb, eb);
};

// EMEN2 template functions
emen2.template = {};

emen2.template.uri = function(args, q, h) {
    var ret = [""];
    if (ROOT) {ret.push(ROOT)}
    for (var i=0;i<args.length;i++) {
        ret.push(encodeURIComponent(args[i]));
    }
    var src = ret.join("/");
    if (q) {
        src = src + "?" + $.param(q);
    };
    if (h) {
        src = src + "#" + encodeURIComponent(h);
    }
    return src
};

emen2.template.static = function(args) {
    var src = ['static-'+VERSION];
    for (var i=0;i<args.length;i++) {
        src.push(args[i]);
    }
    return emen2.template.uri(src)
};

emen2.template.image = function(name, alt, cls) {
    alt = alt || '';
    cls = cls || '';
    var src = emen2.template.static(['images', name]);
    var img = $('<img />');
    img.attr('alt', alt);
    img.attr('src', src);
    img.addClass(cls);
    return img
};

emen2.template.spinner = function(show) {
    var spinner = emen2.template.image('spinner.gif', 'Loading');
    spinner.addClass('e2l-spinner')
    if (!show) {
        spinner.addClass('e2l-hide')
    }
    return spinner
    
};

emen2.template.notify = function(msg, error, fade) {
    var msg = $('<li />').text(msg);
    if (error!=null) {
        msg.addClass("e2l-error");
    }
    $('<span />')
        .addClass('e2l-float-right')
        .text('X')
        click(function() {
            $(this).parent().fadeOut(function(){
                $(this).remove();
            });        
        })
        .appendTo(msg)
    $('#container .e2-alert').append(msg);
};

// Default error message dialog.
// This gives the user some feedback if an RPC request fails.
emen2.template.error = function(title, text, method, data) {
    var error = $('<div />')
        .attr('title', title)
        .dialog({
            width: 400,
            height: 300,
            modal: true,
            draggable: false,
            resizable: false
        });
    $('<p />').text(text).appendTo(error);
    $('<p />').text("Method: "+method).appendTo(error);
};

emen2.ui = {};

emen2.ui.buttonfeedback = function(elem) {
    var elem = $(elem);
    $('.e2l-spinner', elem).show();
    elem.addClass('e2l-disabled');
}


// Convert a byte count to human friendly
emen2.template.prettybytes = function(bytes) {
    var b = 0;
    if (bytes >= 1099511627776) {
        b = bytes / 1099511627776;
        return b.toFixed(2) + " TB"
    } else if (bytes >= 1073741824) {
        b = bytes / 1073741824;
        return b.toFixed(2) + " GB"
    } else if (bytes >= 1048576) {
        b = bytes / 1048576;
        return b.toFixed(2) + " MB"
    } else if (bytes >= 1024) {
        b = bytes / 1024;
        return b.toFixed(2) + " KB"
    } else if (bytes != null) {
        return bytes + " bytes"
    } else {
        return "Unknown"
    }
};


// EMEN2 Utility functions
emen2.util = {};

// For EMEN2 widgets, check this.options first, then
// this.element.attr('data-'+key)
// This includes a check so that record ID = 0 works
emen2.util.checkopt = function(self, key, dfault) {
    var specified = self.element.attr('data-'+key);	
	if (specified == undefined) {
		return self.options[key];
	}
	return specified
};

emen2.util.checkopts = function(self, keys) {
	for (var i=0;i<keys.length;i++) {
		self.options[keys[i]] = emen2.util.checkopt(self, keys[i]);
	};
};

// Sort a dict's keys based on integer values
// >>> var sortable = [];
// >>> for (var vehicle in maxSpeed)
//       sortable.push([vehicle, maxSpeed[vehicle]])
// >>> sortable.sort(function(a, b) {return a[1] - b[1]})
// [["bike", 60], ["motorbike", 200], ["car", 300],
// ["helicopter", 400], ["airplane", 1000], ["rocket", 28800]]
emen2.util.sortdict = function(o) {
    var sortable = [];
    for (var i in o) {
        sortable.push([i, o[i]])
    }
    var s = sortable.sort(function(a, b) {return b[1] - a[1]})
    result = [];
    for (var i=0;i<s.length;i++) {
        result.push(s[i][0]);
    }
    return result
};

// Sort a dict's keys based on lower-case string values
emen2.util.sortdictstr = function(o) {
    var sortable = [];
    for (var i in o) {
        sortable.push([i, o[i]])
    }
    var s = sortable.sort(function(a, b) {
        return b[1].toLowerCase() > a[1].toLowerCase()
        });
    result = [];
    for (var i=0;i<s.length;i++) {
        result.push(s[i][0]);
    }
    return result
};

emen2.util.set_add = function(i, l) {
    var pos = $.inArray(i, l);
    if (pos == -1) {
        l.push(i);
    }
    return l
};

emen2.util.set_remove = function(i, l) {
    var pos = $.inArray(i, l);
    if (pos > -1) {
        l.splice(pos, 1);
    }
    return l
};

// Utility classes
(function($){

    // These two methods are deprecated.
    // Update controls when a record has changed
    // Todo: Keep these?
    $.record_update = function(rec) {
        if (typeof(rec)=="number") {
            var name = rec;
        } else {
            emen2.caches['record'][rec.name] = rec;
            var name = rec.name;
        }
        $.rebuild_views('.e2-view[data-name="'+$.escape(name)+'"]');
        $('.e2-comments').CommentsControl('rebuild');
        $('.e2-attachments').AttachmentControl('rebuild');    
    }

    // Rebuild a rendered view
    $.rebuild_views = function(selector) {
        selector = selector || '.view';
        var self = this;
        $(selector).each(function() {
            var elem = $(this);
            var name = elem.attr('data-name');
            var viewname = elem.attr('data-viewname');
            var edit = elem.attr('data-edit');
            emen2.db("view", {'names':name, 'viewname': viewname, 'edit': edit}, function(view) {
                elem.html(view);
                $('time', elem).localize();
            },
            function(view){}
            );
        })
    }

    ///////////////////////////////////////////////////
    // Some simple jquery UI widgets that don't really
    //  fit in any other files..
    ///////////////////////////////////////////////////
 
    $.widget('emen2.AutoCompleteControl', {
        options: {
            param: null
        }, 
        
        _create: function() {
            var self = this;
			emen2.util.checkopts(this, ['param']);
            this.element.autocomplete({
                minLength: 0,
                source: function(request, response) {
                    emen2.db("record.findbyvalue", [self.options.param, request.term], function(ret) {
                        var r = $.map(ret, function(item) {
                            return {
                                label: item[0] + " (" + item[1] + " records)",
                                value: item[0]
                            }
                        });
                        response(r);            
                    });
                }
            });
        }
    }),
    
    $.widget('emen2.DatePickerControl', {
        // Basically, just keep all the options for the date picker together.
       options: {           
           showtime: true,
           showtz: true
       },
       _create: function() {
           opts = {
              showButtonPanel: true,
              changeMonth: true,
              changeYear: true,
              showAnim: '',
              yearRange: 'c-100:c+100',
              dateFormat: 'yy-mm-dd',
          }
          if (this.options.showtz && this.options.showtime) {
              opts['showTimezone'] = true;              
              opts['timezone'] = '+0500';
              this.element.datetimepicker(opts);               
          } else if (this.options.showtime) {
              opts['separator'] = 'T';
              opts['timeFormat'] = 'hh:mm:ssz';
              opts['showSecond'] = true;              
              this.element.datetimepicker(opts);           
          } else {
              this.element.datepicker(opts);                         
          }
       }
    }),
 
    // Select utility
    $.widget('emen2.SelectControl', {
        options: {
            root: null,
            selected: 'input[name]:checkbox:checked',
            all: 'input[name]:checkbox',
            show: true
        },
        
        _create: function() {
            this.built = 0;
            if (this.options.show) {
                this.build();
            }
        },
        
        build: function() {
            if (this.built) {return}
            this.built = 1;
            var self = this;

            this.element.empty();            
            var controls = $('<li />')
                .appendTo(this.element);
            $('<span />')
                .text('Select ')
                .appendTo(controls);
            $('<span />')
                .text('all')
                .addClass('e2l-a')
                .click(function() {self.select_all()})
                .appendTo(controls);         
            $('<span />')
                .text(' or ')
                .appendTo(controls);
            $('<span />')
                .text('none')
                .addClass('e2l-a')
                .click(function() {self.select_none()})
                .appendTo(controls);
            $('<span />')
                .addClass('e2-select-count')
                .appendTo(controls);
        },
        
        select_all: function() {
            $('input:checkbox', this.options.root).attr('checked', 'checked');
            this.update();
        },
        
        select_none: function() {
            $('input:checkbox', this.options.root).attr('checked', null);
            this.update();
        },
        
        update: function() {
            var selected = $(this.options.selected, this.options.root);
            var all = $(this.options.all, this.options.root);
            var txt = '('+selected.length+' of '+all.length+' selected)';
            $('.e2-select-count', this.element).text(txt);
        }
    });

    // EMEN2 Tabs
    // Works somewhat like jQuery-UI Tabs.
    $.widget('emen2.TabControl', {
        options: {
            active: 'e2-tab-active',
            absolute: false,
            cbs: {},
            hidecbs: {},
            tabgroup: null
        },
        
        _create: function() {
            this.built = 0;
			emen2.util.checkopts(this, ['tabgroup']);
            this.tablist = this.element.children('ul');
            this.tabpanel = this.element;
            var tablist = $('[data-tabgroup='+$.escape(this.options.tabgroup)+'][role=tablist]');
            var tabpanel = $('[data-tabgroup='+$.escape(this.options.tabgroup)+'][role=tabpanel]');
            if (tablist.length) {this.tablist = tablist}
            if (tabpanel.length) {this.tabpanel = tabpanel}
            this.build();
        },

        // Check the window hash (e.g. "#permissions")
        // and open that tab if it exists
        checkhash: function(_default) {
            var active = window.location.hash.replace("#","");
            // if (!active) {active = _default}
            if (active) {
                this.hide();
                this.show(active);
            }            
        },
        
        build: function() {
            if (this.built){return}
            var self = this;
            $('[data-tab]', this.tablist).click(function(e){
                var tab = $(this).attr('data-tab');
                var hc = $(this).hasClass(self.options.active);
                if (hc) {
                    e.preventDefault();
                    self.hide(tab);
                } else {
                    self.hide(tab);
                    self.show(tab);
                }
            });
            this.built = 1;
        },
        
        setcb: function(tab, cb) {
            this.options.cbs[tab] = cb;
        },
        
        sethidecb: function(tab, cb) {
            this.options.hidecbs[tab] = cb;            
        },
        
        hide: function(tab) {
            var self = this;
            this.tablist.children('[data-tab!='+$.escape(tab)+']').removeClass(this.options.active);
            this.tabpanel.children('[data-tab!='+$.escape(tab)+']').removeClass(this.options.active);
            var cb = this.options.hidecbs[tab];
            var t = $('[data-tab="'+$.escape(tab)+'"]', this.tabpanel);
            if (cb) {cb(t)}
        },

        _hide: function(elem, tab) {
            
        },
        
        show: function(tab) {
            var t = $('[data-tab='+$.escape(tab)+']', this.tablist);
            if (!t.length) {
                return
            }
            var p = $('[data-tab='+$.escape(tab)+']', this.tabpanel);
            if (!p.length) {
                var p = $('<div />')
                    .attr('data-tab', tab)
                    .appendTo(this.tabpanel);
            }            
            // p.addClass('e2l-cf');

            // Menu-style -- float above content
            // if (this.options.absolute) {
            //     // Set the position
            //     var pos = t.position();
            //     var height = t.height();
            //     var width = t.width();
            //     p.css('position', 'absolute');
            //     p.css('top', pos.top + height);
            // 
            //     // Is it right aligned?
            //     var align = t.css('float');                
            //     if (align=='left') {
            //         p.css('left', pos.left-1);                    
            //     } else {
            //         var parentwidth = p.parent().width();
            //         p.css('right', parentwidth-(width+pos.left)-2);
            //     }
            // }
            
            // Run any callbacks
            var cb = this.options.cbs[tab];
            if (cb) {cb(p)}
            if (this.options.cb) {this.options.cb(p)}

            t.addClass(this.options.active);
            p.addClass(this.options.active);
        }        
    });

    // Siblings control
    $.widget('emen2.SiblingsControl', {
        options: {
            name: null,
            prev: null,
            next: null
        },
        
        _create: function() {
            var self = this;
			emen2.util.checkopts(this, ['name','sibling', 'prev', 'next']);
            this.build();
        },
        
        build: function() {
            var self = this;
            var rec = emen2.cache.get(this.options.name);
            this.element.empty();

            var sibs = $('<div />')
                .text('Loading siblings...')
                .prepend(emen2.template.spinner(true))
                .appendTo(this.element);

            emen2.db("rel.siblings", [rec.name, rec.rectype], function(siblings) {
                emen2.db("view", [siblings], function(recnames) {
                    siblings = siblings.sort(function(a,b){return a-b});
                    $.each(recnames, function(k,v) {
                        emen2.caches['recnames'][k] = v;
                    });
                    self._build_siblings(siblings);
                });            
            });
        },
        
        _build_siblings: function(siblings) {
            var self = this;
            var rec = emen2.cache.get(this.options.name);

            this.element.empty();
            
            var prevnext = $('<h4 />')
                .text('Siblings')
                .css('text-align', 'center')
                .addClass('e2l-cf')
                .appendTo(this.element);
            
            if (this.options.prev) {
                $('<a />')
                    .attr('href', emen2.template.uri(['record', this.options.prev], {'sibling':this.options.name}, 'siblings'))
                    .text('Previous')
                    .addClass('e2l-float-left')
                    .prepend(prevnext);
            }
            if (this.options.next) {
                $('<a />')
                    .attr('href', emen2.template.uri(['record', this.options.next], {'sibling':this.options.name}, 'siblings'))
                    .text('Next')
                    .addClass('e2l-float-right')
                    .prepend(prevnext);
            }                    
            
            var ul = $('<ul />')
                .appendTo(this.element);
                
            $.each(siblings, function(i,k) {
                var rn = emen2.cache.get(k, 'recnames') || k;
                if (k != rec.name) {
                    $('<a />')
                        .attr('href', emen2.template.uri(['record', k], {'sibling':self.options.name}))
                        .text(rn)
                        .wrap('<li />')
                        .appendTo(ul);
                } else {
                    $('<li />')
                        .addClass('e2-siblings-active')
                        .text(rn)
                        .appendTo(ul);
                }
            });
        }

    });

    // A simple widget for counting words in a text field
    $.widget("emen2.WordCount", {
        options: {
            min: null,
            max: null
        },    

        _create: function() {
            var self = this;
			emen2.util.checkopts(this, ['min', 'max']);
            this.wc = $('<div />')
                .addClass('e2-wordcount-count');
            this.element.after(this.wc);
            this.update();
            this.element.bind('keyup click blur focus change paste', function() {
                self.update();
            });
        },

        update: function() {
            var wc = $.trim(this.element.val()).split(' ').length;
            var t = wc+' Words';
            if (this.options.max) {
                t = t+' (Maximum: '+this.options.max+')';
            }
            var fault = false;
            if (wc > this.options.max) {fault=true}
            if (fault) {
                this.wc.addClass('e2l-error');
            } else {
                this.wc.removeClass('e2l-error')
            }
            this.wc.text(t);    
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
