slideshow = ( function($) { // Localise the $ function
	slideshow = function(elem, opts) {
		this.elem = $(elem);
		this.DEFAULT_OPTS = {
				timer: 1500,
				current: null
		};
		if (typeof (opts) != "object") opts = {};
		$.extend(this, this.DEFAULT_OPTS, opts);
		
		var self = this
		this.init = function() { self.build() };

		this.build = function() {
			console.log(self.elem);
			children = self.elem.children();
			if (children.length > 0) {
				self.first = $(children.get(0));
				self.first.css({'z-index': 2});
				self.current = self.first;
				self.first.siblings().animate({opacity: 'toggle', width:'toggle'});
				if (self.controls != undefined && self.name != undefined) {
					var counter = 0;
					children.each(function (){
						var new_control = $('<div class="control" onclick='
											+self.name+'.switchto('+counter+');>'
											+counter+'</div>')
						self.controls.append(new_control);
						counter ++;
					});
				}
			}
		};
		this.start = function() {
			self.pid = setInterval(self.rotate, self.timer)
		};
			
		this.toggle = function (elem){
            self.current.css({'z-index': 0});
            self.current.animate({width:'toggle'}, 'slow')
            elem.css({'z-index': 1});
            elem.animate({width:'toggle'}, 'slow')
            self.current = elem;
		};
		
		this.rotate = function() {
			var next = self.current.next();
            if (next.length == 0){var next = self.first};
            self.toggle(next);
		};
		
		this.switchto = function(frameno) {
			var next = self.elem.children()[frameno]
			if (next != undefined) {                                
				if (self.pid != undefined) { clearInterval(self.pid); }
				self.toggle($(next));
			}
		}
		
		this.addFrame = function(elem) {
			var n = $('<div class="frame" />');
			n.append(elem);
			self.elem.append(n);
			if ( self.first === undefined ) {
				self.first = elem;
				self.current = elem;
			}
		};

		save = function() {
		};

		revert = function() {
		};

		commit = function(values) {
		};

		bindToObj = function(fn) {
			var self = self;
			return function() {
				return fn.apply(self, arguments)
			};
		};
		this.init();
	};

	$.fn.slideshow = function(opts) {
		return (new slideshow(this, opts));
	};

	
	return slideshow;
})(jQuery); // End localisation of the $ function
