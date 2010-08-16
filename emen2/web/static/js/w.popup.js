(function($) {
    $.widget("ui.popup", {
		options: {
		},
				
		_create: function() {
         this.element.wrap('<div class="profile_form_label clickable" style="position:relative;display:block;vertical-align:middle"></div>')
            .after('<div style="position:absolute;clear:both;height:200px;width:200px;border:black thin solid;background:#888;top:100%;display:none;z-index:100">asd</div>').parent()
            .click(function (e) {$(this).children().last().toggle()});
         this.element.removeClass('profile_form_label');
      },
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);
