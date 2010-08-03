MapSelect = (function($) { // Localise the $ function

function MapSelect(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, MapSelect.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
};

MapSelect.DEFAULT_OPTS = {
};

MapSelect.prototype = {
	
	init: function() {
		this.build();
	},
	
	build: function() {
		var self=this;
		this.elems = [];
		this.ext_elems = $("a.map", this.elem);

		this.ext_elems.each(function(){
			var target = $(this).attr('data-recid');
			checkbox = $('<input type="checkbox" value="'+target+'" checked="checked" />');
			self.elems.push(checkbox);
			$(this).before(checkbox);
		});	
	},
	
	value: function() {
		
	}	
}

$.fn.MapSelect = function(opts) {
  return this.each(function() {
		return new MapSelect(this, opts);
	});
};

return MapSelect;

})(jQuery);