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
			var children = self.elem.children()
			if (children.length > 0) {
				self.first = $(children.get(0)) 
				self.current = self.first
				self.first.siblings().animate({opacity: 'toggle'});
			}
		};
		this.start = function() {
			setInterval(self.rotate, self.timer)
		};
			
		this.rotate = function() {
            function toggle(elem){elem.animate({opacity: 'toggle'})};
            var next = self.current.next();
            if (next.length == 0){var next = self.first};
            toggle(self.current);
            toggle(next);
            self.current = next;
		};
		
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
