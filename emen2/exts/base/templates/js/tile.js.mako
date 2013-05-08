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
        
        show: function() {
            var self = this;
            this.element.append(emen2.template.spinner());
            // Get the details about this image
            $.ajax({
                type: 'POST',
                url: ROOT+'/preview/'+this.options.bdo+'/header/',
                dataType: 'json',
                success: function(d) {
                    self.element.empty();
                    // $('.e2l-spinner', self.element).remove();
                    self.options.nx = d['nx'];
                    self.options.ny = d['ny'];
                    self.options.filename = d['filename'];
                    self.options.maxscale = d['maxscale'];
                    self.build();
                },
                error: function(x,y,z) {
                    $('.e2l-spinner', self.element).remove();
                    self.element.empty();
                    self.element.append('<p style="text-align:center">'+emen2.template.spinner(true)+' Waiting for tiles...</p>');
                    setTimeout(function(){self.show()}, 2000);

                }
            });
        },

        
        build: function() {
            var self = this;
            this.inner = $('<div style="position:relative;top:0px;left:0px" />');
            this.element.append(this.inner);

            this.element.attr('data-bdo', this.options.bdo);            

            // Set the display mode
            this.setdisplaymode(this.options.displaymode);
            
            // Drag handler
            this.inner.draggable({
                drag:function(){
                    var offset = self.offset_to_center();
                    self.options.x = offset[0];
                    self.options.y = offset[1];
                    self.recalc();
                }
            });
            
            // Click handler
            // this.inner.click(function(e) {
            //     e.stopPropagation();
            //     parentpos = self.inner.position();
            //     var x = (e.clientX - parentpos.left) * self.options.scale;
            //     var y = (e.clientY - parentpos.top) * self.options.scale;
            //     $('div[data-bdo='+self.options.bdo+']').Boxer('addbox', x, y); // callback to the Boxer controller
            // });
            
            this.build_controls();
            
        },
        
        build_controls: function() {                
            // Controls
            var self = this;            
            var apix = null; //emen2.caches['record'][this.options.name]['angstroms_per_pixel'];
            if (!apix) {
                apix = 1.0;
            }

            var controls = $('<div class="e2-tile-controls"> \
                <h4 class="e2l-label">Image</h4> \
                <input type="button" name="zoomout" value="-" /> \
                <input type="button" name="zoomin" value="+" /><br /> \
                <input type="button" name="autocenter" value="Center" /><br /> \
                <a class="e2-button" href="'+ROOT+'/download/'+self.options.bdo+'/'+self.options.filename+'">Download</a><br /> \
                <button name="convert">Convert</button> \
                <h4 class="e2l-label">Mode</h4> \
                <div style="text-align:left"> \
                <input type="radio" name="displaymode" value="image" id="displaymode_image" checked="checked" /><label for="displaymode_image"> Image</label><br /> \
                <input type="radio" name="displaymode" value="pspec" id="displaymode_pspec" /><label for="displaymode_pspec"> FFT</label><br /> \
                <input type="radio" name="displaymode" value="1d" id="displaymode_1d" /><label for="displaymode_1d"> 1D</label> <br />\
                <input type="text" name="apix" value="'+apix+'" size="1" /> \
                <span class="e2l-small">A/px</span><br /> \
                </div> \
            </div>');

            this.element.append(controls);            

            controls.find("input[name=displaymode]").click(function() {
                self.setdisplaymode($(this).val());
            });
            controls.find("input[name=zoomin]").click(function() {
                self.zoomin();
            });
            controls.find("input[name=zoomout]").click(function() {
                self.zoomout();
            });            
            controls.find("input[name=autocenter]").click(function() {
                self.autocenter();
            });            
            controls.find("input[name=apix]").change(function() {
                if (self.options.displaymode == '1d') {
                    self.setdisplaymode('1d')
                }
            });
            controls.find('button[name=convert]').click(function() {
                self.convertdialog();
            })
        },
        
        convertdialog: function() {
            var self = this;
            var dialog = $(' \
                <div> \
                <form method="post" action="'+ROOT+'/eman2/'+self.options.bdo+'/convert/"> \
                    <h4>Format</h4> \
                    <ul class="e2l-nonlist"> \
                        <li><input type="radio" name="format" value="tif" id="format-tif" checked="checked"  /><label for="format-tif"> TIFF</label></li> \
                        <li><input type="radio" name="format" value="png" id="format-png"  /><label for="format-png"> PNG</label></li> \
                        <li><input type="radio" name="format" value="jpg" id="format-jpg" /><label for="format-jpg"> JPEG</label></li> \
                    </ul> \
                    <h4>Options</h4> \
                    <ul class="e2l-nonlist"> \
                        <li><input type="checkbox" name="normalize" id="options-normalize" checked="checked"><label for="options-normalize"> Normalize</label></li> \
                        <li><input type="checkbox" name="depth" value="8" id="options-depth" checked="checked"><label for="options-depth"> 8-bit</label></li> \
                    </ul> \
                </form> \
            </div>');
            dialog.dialog({
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
                        //$(this).dialog('close');
                    }
                }
            });    
        },
        
        setdisplaymode: function(mode) {
            var self = this;
            this.options.displaymode = mode;

            // Remove all images
            this.inner.hide();
            $('.e2-tile-pspec', this.element).remove();
            $('.e2-tile-pspec1d', this.element).remove();

            if (mode=="image") {
                // Tiled image
                this.inner.show();
                this.options.scale = this.autoscale();
                this.setscale(this.options.scale);
                this.autocenter();
            } else if (mode == "pspec") {
                // Draw 2D FFT
                var modeimg = $('<img class="e2-tile-pspec" src="'+ROOT+'/preview/'+this.options.bdo+'/pspec/" alt="pspec" />');
                var w = this.element.width() / 2;
                modeimg.css('margin-left', w-256);
                this.element.append(modeimg);            
            } else if (mode == "1d") {
                var apix = $('input[name=apix]', this.element).val();
                $.ajax({
                    type: 'POST',
                    url: ROOT+'/preview/'+this.options.bdo+'/pspec1d/',
                    dataType: 'json',
                    success: function(d) {
                        self.plot1d(d, apix);
                    }
                });

            }
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
            var plot = $('<div class="e2-tile-pspec1d"></div>')
            plot.css('width', 512);
            plot.css('height', 512);
            
            var w = this.element.width() / 2;
            plot.css('margin-left', w-256);
            
            plot.append('<strong class="e2-tile-pspec1d">Spatial freq. (1/A) vs. Log Intensity (10^x). A/pix set to '+apix+'</strong>');            
            var plotelem = $('<div class="e2-plot"></div>');
            plot.append(plotelem);
            this.element.append(plot);

            plotelem.PlotLine({
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
            return ROOT+'/preview/'+this.options.bdo+'/tiles/?x='+x+'&y='+y+'&scale='+this.options.scale
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
                    var id = 'tile-'+this.options.scale+'-'+x+'-'+y;
                    var img = document.getElementById(id);
                    if (!img) {
                        // console.log("Building:", x, y);
                        var src = this.get_tile(x,y);
                        var img = $('<img src="'+src+'" id="'+id+'" alt="Tile x:'+x+' y:'+y+'" />');
                        // Coordinate system inverted
                        var top = (this.options.ny - y*this.options.size*this.options.scale) / this.options.scale - this.options.size;
                        // img.css('border', 'solid red 1px');
                        img.css('position', 'absolute');
                        img.css('width', this.options.size);
                        img.css('height', this.options.size);                    
                        img.css('left', x * this.options.size);
                        img.css('top', top);
                        this.inner.append(img);                            
                    }                    
                }
            }
        },

    });
    
})(jQuery);



<%!
public = True
headers = {
    'Content-Type': 'application/javascript',
    'Cache-Control': 'max-age=86400'
}
%>
