(function($) {
    $.widget("emen2.TileControl", {
        options: {
            width: 0,
            height: 0,
            size: 256,
            x: null,
            y: null, 
            scale: 'auto',
            bdo: null,
            displaymode: 'image',
            show: true,
            controlsinset: true,
            name: null
        },
        
        _create: function() {        
            if (this.options.bdo == null) {
                this.options.bdo = this.element.attr('data-bdo');
            }
            this.element.attr('data-bdo', this.options.bdo);            
            if (this.options.show) {
                this.show();
            }
        },
        
        show: function(retry) {
            var self = this;
            this.element.empty();
            
            if (retry==null) {retry = 0}
            if (retry > 10) {
                $('<p />')
                    .text('Could not access tiles.')
                    .appendTo(this.element);
                return
            }

            // Loading animation.
            emen2.template.spinner().appendTo(this.element);
            
            // Get the details about this image
            // TODO: Give a different HTTP response code for generating tiles
            // vs. actual error.
            $.ajax({
                type: 'POST',
                url: emen2.template.uri(['preview', this.options.bdo, 'header']),
                dataType: 'json',
                success: function(d) {
                    self.element.empty();
                    self.options.nx = d['nx'];
                    self.options.ny = d['ny'];
                    self.options.filename = d['filename'];
                    self.options.maxscale = d['maxscale'];
                    console.log("Got response:", self.options);
                    self.build();
                },
                error: function(x,y,z) {
                    self.element.empty();
                    $('<p />')
                        .text('Waiting for tiles...')
                        .prepend(emen2.template.spinner(true))
                        .appendTo(self.element);
                    setTimeout(function(){self.show(retry+1)}, 5000);
                }
            });
        },

        build: function() {
            var self = this;
            this.inner = $('<div />')
                .css('position', 'relative')
                .css('top', 0)
                .css('left', 0)
                .appendTo(this.element);

            // Drag handler
            this.inner.draggable({
                drag:function(){
                    var offset = self.offset_to_center();
                    self.options.x = offset[0];
                    self.options.y = offset[1];
                    self.recalc();
                }
            });

            // Set the display mode
            this.setdisplaymode(this.options.displaymode);
            
            // Click handler
            // this.inner.click(function(e) {
            //     e.stopPropagation();
            //     parentpos = self.inner.position();
            //     var x = (e.clientX - parentpos.left) * self.options.scale;
            //     var y = (e.clientY - parentpos.top) * self.options.scale;
            //     $('div[data-bdo='+$.escape(self.options.bdo)+']').Boxer('addbox', x, y); // callback to the Boxer controller
            // });
            
            this.build_controls().appendTo(this.element);
            
        },
        
        build_controls: function() {                
            // Controls
            var self = this;            
            try {
                var apix = emen2.caches['record'][this.options.name]['angstroms_per_pixel'];                
            } catch(error) {
                var apix = 1.0; 
            }

            var controls = $('<div />')
                .addClass('e2-tile-controls');
                    
            // Zoom in, zoom out, recenter
            $('<h4 />')
                .addClass('e2l-label')
                .text('Image')
                .appendTo(controls);
            
            $('<input type="button" />')
                .val('-')
                .click(function() {self.zoomout()})
                .appendTo(controls);

            $('<input type="button" />')
                .val('+')
                .click(function() {self.zoomin()})
                .appendTo(controls);
            $('<br />').appendTo(controls);

            $('<input type="button" />')
                .val('Center')
                .click(function() {self.autocenter()})
                .appendTo(controls);
            $('<br />').appendTo(controls);
            
            // Download and convert    
            $('<a />')
                .addClass('e2-button')
                .attr('href', emen2.template.uri(['download', this.options.bdo, this.options.filename]))
                .text('Download')
                .appendTo(controls);
            $('<br />').appendTo(controls);
            
            $('<input type="button" />')
                .val('Convert')
                .click(function() {self.convertdialog()})                
                .appendTo(controls);
            $('<br />').appendTo(controls);

            // Mode select
            $('<h4 />')
                .addClass('e2l-label')
                .text('Mode')
                .appendTo(controls);

            $('<input type="radio" />')
                .attr('id', 'e2-tile-display-image')
                .attr('name', 'displaymode')
                .val('image')
                .click(function() {self.setdisplaymode($(this).val())})
                .appendTo(controls);
            $('<label />')
                .attr('for', 'e2-tile-display-image')
                .text('Image')
                .appendTo(controls);
            $('<br />').appendTo(controls);

            $('<input type="radio" />')
                .attr('id', 'e2-tile-display-pspec')
                .attr('name', 'displaymode')
                .val('pspec')
                .click(function() {self.setdisplaymode($(this).val())})
                .appendTo(controls);
            $('<label />')
                .attr('for', 'e2-tile-display-pspec')
                .text('FFT')
                .appendTo(controls);
            $('<br />').appendTo(controls);

            $('<input type="radio" />')
                .attr('id', 'e2-tile-display-1d')
                .attr('name', 'displaymode')
                .val('1d')
                .click(function() {self.setdisplaymode($(this).val())})
                .appendTo(controls);
            $('<label />')
                .attr('for', 'e2-tile-display-1d')
                .text('1D')
                .appendTo(controls);
            $('<br />').appendTo(controls);

            // Apix
            $('<input type="text" />')
                .attr('name', 'apix')
                .attr('size', 1)
                .val(apix)
                .change(function() {
                    if (self.options.displaymode == '1d') {
                        self.setdisplaymode('1d')
                    }
                })
                .appendTo(controls);
            $('<span />')
                .addClass('e2l-small')
                .text('A/px')
                .appendTo(controls);
            return controls
        },
        
        convertdialog: function() {
            var self = this;
            var dialog = $(' \
                <div> \
                    <form method="post" action=""> \
                        <h4>Format</h4> \
                        <ul class="e2l-nonlist"> \
                            <li><input type="radio" name="format" value="tif8" id="format-tif8" checked="checked" /><label for="format-tif8"> TIFF (8-bit)</label></li> \
                            <li><input type="radio" name="format" value="tif" id="format-tif" /><label for="format-tif"> TIFF </label></li> \
                            <li><input type="radio" name="format" value="png" id="format-png" /><label for="format-png"> PNG</label></li> \
                            <li><input type="radio" name="format" value="jpg" id="format-jpg" /><label for="format-jpg"> JPEG</label></li> \
                        </ul> \
                        <h4>Options</h4> \
                        <ul class="e2l-nonlist"> \
                            <li><input type="checkbox" name="normalize" id="options-normalize" checked="checked"><label for="options-normalize"> Normalize</label></li> \
                        </ul> \
                    </form> \
                </div>')
                .dialog({
                    autoOpen: true,
                    modal: true,
                    resizable: false,
                    draggable: false,
                    width: 400,
                    height: 400,
                    title: 'Convert '+this.options.filename,
                    buttons: {
                        'Download': function() {
                            $('form', this).submit();
                        }
                    }
                });
            $('form', dialog).attr('action', emen2.template.uri(['eman2', this.options.bdo, 'convert']))
        },
        
        setdisplaymode: function(mode) {
            var self = this;
            this.options.displaymode = mode;

            // Remove all images
            this.inner.hide();
            $('.e2-tile-pspec', this.element).remove();
            $('.e2-tile-pspec1d', this.element).remove();

            if (mode=="image") {
                // Tiles
                this.plotimage();
            } else if (mode == "pspec") {
                // 2D FFT
                this.plot2d();
            } else if (mode == "1d") {
                // 1D avg FFT
                var apix = $('input[name=apix]', this.element).val();
                $.ajax({
                    type: 'POST',
                    url: emen2.template.uri(['preview', this.options.bdo, 'pspec1d']),
                    dataType: 'json',
                    success: function(d) {
                        self.plot1d(d, apix);
                    }
                });

            }
        },
        
        plotimage: function() {
            // Tiled image
            this.inner.show();
            this.options.scale = this.autoscale();
            this.setscale(this.options.scale);
            this.autocenter();
        },
        
        plot2d: function() {
            // Draw 2D FFT
            var w = this.element.width() / 2;
            $('<img />')
                .addClass('e2-tile-pspec')
                .attr('src', emen2.template.uri(['preview', this.options.bdo, 'pspec']))
                .css('margin-left', w-256)
                .appendTo(this.element);
        },

        plot1d: function(d, apix) {
            // Convert to query format...
            var recs = [];
            var dx = 1.0 / (2.0 * apix * (d.length+1));
            for (var i=0;i<d.length;i++) {
                var rec = {'x':dx*(i+1), y:d[i]}
                recs.push(rec);
            }

            // Plot.
            var w = this.element.width() / 2;

            var plot = $('<div />')
                .addClass('e2-tile-pspec1d')
                .css('width', 512)
                .css('height', 512)
                .css('margin-left', w-256)
                .appendTo(this.element);
            
            $('<strong />')
                .text('Spatial freq. (1/A) vs. Log Intensity (10^x). A/pix set to '+apix)
                .appendTo(plot);
            
            $('<div />')
                .addClass('e2-plot')
                .appendTo(plot)
                .PlotLine({
                    height: 512,
                    q: {
                        recs:recs,
                        x: {key: 'x'},
                        y:  {key: 'y'}
                    }
                });            
        },

        autoscale: function(refresh) {
            return this.options.maxscale
            // var mx = this.options.maxscale;
            // if (mx == null) {mx = 32}
            // this.options.scales = [];
            // for (var i=0; Math.pow(2,i) <= mx; i++) {
            //     this.options.scales.push(Math.pow(2, i));
            // }
            // var sx = this.options.nx / this.element.width();
            // var sy = this.options.ny / this.element.height();
            // if (sy > sx) {sx = sy}
            // var q = 1;
            // for (var i=0; i<this.options.scales.length; i++) {
            //     if ( sx > this.options.scales[i-1] ){
            //         q = this.options.scales[i];
            //     }
            // };
            // return Math.round(q);
        },
        
        autocenter: function() {
            this.move(this.options.nx / 2, this.options.ny / 2);
        },
        
        recenter: function() {
            this.move(this.options.x, this.options.y);
        },
        
        offset_to_center: function() {
            var pos = this.inner.position();
            var v = this.viewsize();
            return [v[0] - (pos.left * this.options.scale), v[1] - (pos.top * this.options.scale)];
        },
        
        center_to_offset: function() {
            var v = this.viewsize();
            var left = this.options.x - v[0];
            var top = this.options.y - v[1];
            return [-left/this.options.scale, -top/this.options.scale]
        },
        
        move: function(x,y) {
            this.options.x = x;
            this.options.y = y;
            var offset = this.center_to_offset();
            this.inner.css('left', offset[0]);
            this.inner.css('top', offset[1]);
            this.recalc();
        },

        setscale: function(scale) {
            var autoscale = this.autoscale();
            if (scale == 'auto' || scale > autoscale) { scale = autoscale } 
            if (scale < 1) { scale = 1 }
            this.options.scale = scale;
            $('img', this.inner).remove();
            $('.e2-box-box', this.inner).each(function(){$(this).BoxBox('option', 'scale', scale).BoxBox('refresh')});
            this.move(this.options.x, this.options.y);
        },
        
        zoomout: function() {
            var scale = this.options.scale * 2;
            this.setscale(scale);
        },
        
        zoomin: function() {
            var scale = this.options.scale / 2;
            this.setscale(scale);
        },

        viewsize: function() {
            return [(this.element.width() / 2) * this.options.scale, (this.element.height() / 2) * this.options.scale]
        },

        get_tile: function(x, y) {            
            var q = {'x':x, 'y':y, 'scale':this.options.scale}
            return emen2.template.uri(['preview', this.options.bdo, 'tiles'], q);
        },
        
        recalc: function() {
            // Get the current viewport boundaries
            var v = this.viewsize();

            // Don't forget to invert Y coords...
            var bounds = [
                this.options.x - v[0], 
                this.options.ny - this.options.y - v[1],
                this.options.x + v[0],
                this.options.ny - this.options.y + v[1] // this.options.y + v[1]
            ];
            // console.log("viewsize:", v);
            // console.log("x,y:", this.options.x, this.options.y);

            // Adjust based on image size
            if (bounds[0] < 0) {bounds[0] = 0}
            if (bounds[1] < 0) {bounds[1] = 0}
            if (bounds[2] >= this.options.nx) {bounds[2] = this.options.nx-1}
            if (bounds[3] >= this.options.ny) {bounds[3] = this.options.ny-1}

            // Convert to tile x,y coordinates
            var stepsize = this.options.size * this.options.scale;
            for (var i=0;i<bounds.length;i++) {
                bounds[i] = Math.floor(bounds[i]/stepsize);
            }
            // console.log("Updated bounds:", bounds);

            for (var x = bounds[0]; x <= bounds[2]; x++) {
                for (var y = bounds[1]; y <= bounds[3]; y++) {
                    // Check if the tile exits; if not, add it.
                    // console.log("tile:", x, y);
                    // Coordinate system inverted
                    var top = (this.options.ny - y*this.options.size*this.options.scale) / this.options.scale - this.options.size;
                    var id = 'tile-'+this.options.scale+'-'+x+'-'+y;
                    var img = document.getElementById(id);
                    if (!img) {
                        $('<img />')
                            .attr('src', this.get_tile(x,y))
                            .attr('id', id)
                            .attr('alt', 'x:'+x+' y:'+y)                        
                            .css('position', 'absolute')
                            .css('width', this.options.size)
                            .css('height', this.options.size)                   
                            .css('left', x * this.options.size)
                            .css('top', top)
                            .appendTo(this.inner);
                    }                    
                }
            }
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
