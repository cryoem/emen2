/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////

skeleton = (function($) { // Localise the $ function

function skeleton(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, skeleton.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
};

skeleton.DEFAULT_OPTS = {
};

skeleton.prototype = {
	
	init: function() {
		this.build();
	},
	
  build: function() {

	}
	
}

$.fn.skeleton = function(opts) {
    return this.each(function() {
		new skeleton(this, opts);
	});
};

return skeleton;

})(jQuery); // End localisation of the $ function
