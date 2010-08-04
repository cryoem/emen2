(function($) {
    $.widget("ui.accordion1", {
		options: {
         active: 0,
         animated: 'slide',
         autoHeight: true,
         clearStyle: false,
         collapsible: false,
         manyOpen: true,
         event: "click",
         fillSpace: false,
         header: "> li > :first-child,> :not(li):even",
         icons: {
            header: "ui-icon-triangle-1-e",
            headerSelected: "ui-icon-triangle-1-s"
         },
         navigation: false,
         navigationFilter: function() {
            return this.href.toLowerCase() == location.href.toLowerCase();
         }

		},
				
		_create: function() {

         var o = this.options, self = this;
         this.running = 0;

         this.element.addClass("ui-accordion ui-widget ui-helper-reset");

         // in lack of child-selectors in CSS we need to mark top-LIs in a UL-accordion for some IE-fix
         this.element.children("li").addClass("ui-accordion-li-fix");

         this.headers = this.element.find(o.header).addClass("ui-accordion-header ui-helper-reset ui-state-default ui-corner-all")
            .bind("mouseenter.accordion", function(){ $(this).addClass('ui-state-hover'); })
            .bind("mouseleave.accordion", function(){ $(this).removeClass('ui-state-hover'); })
            .bind("focus.accordion", function(){ $(this).addClass('ui-state-focus'); })
            .bind("blur.accordion", function(){ $(this).removeClass('ui-state-focus'); });

         this.headers
            .next()
               .addClass("ui-accordion-content ui-helper-reset ui-widget-content ui-corner-bottom");

         if ( o.navigation ) {
            var current = this.element.find("a").filter(o.navigationFilter);
            if ( current.length ) {
               var header = current.closest(".ui-accordion-header");
               if ( header.length ) {
                  // anchor within header
                  this.active = header;
               } else {
                  // anchor within content
                  this.active = current.closest(".ui-accordion-content").prev();
               }
            }
         }

         this.active = $(this.headers.get(0));

         //Append icon elements
         //this._createIcons();

         //this.resize();

         //ARIA
         this.element.attr('role','tablist');

         this.headers
            .attr('role','tab')
            .bind('keydown', function(event) { return self._keydown(event); })
            .next()
            .attr('role','tabpanel');

         this.headers
            .attr('aria-expanded','false')
            .attr("tabIndex", "0")
            .next()
            .hide();
         

         // only need links in taborder for Safari
         if (!$.browser.safari)
            this.headers.find('a').attr('tabIndex','-1');

         if (o.event) {
            this.headers.bind((o.event) + ".accordion", function(event) {
               self._clickHandler.call(self, event, this);
               event.preventDefault();
            });
            this.active.trigger(o.event)
         }

         this.active.focus();
   	},

      _keydown: function(event) {

         var o = this.options, keyCode = $.ui.keyCode;

         if (o.disabled || event.altKey || event.ctrlKey)
            return;

         var length = this.headers.length;
         var currentIndex = this.headers.index(event.target);
         var toFocus = false;

         console.log(keyCode);
         console.log(event.keyCode);
         switch(event.keyCode) {
            case 74: // j
            case keyCode.DOWN:
               toFocus = this.headers[(currentIndex + 1) % length];
               break;
            case keyCode.UP:
            case 75: // k
               toFocus = this.headers[(currentIndex - 1 + length) % length];
               break;
            case keyCode.RIGHT:
            case keyCode.LEFT:
            case keyCode.SPACE:
            case keyCode.ENTER:
               this._clickHandler({ target: event.target }, event.target);
               event.preventDefault();
         }

         if (toFocus) {
            toFocus.focus();
            return false;
         }

         return true;

      },


      _clickHandler: function(event, target) {
         console.log(target);
         $(target).toggleClass("ui-state-default").toggleClass("ui-state-active").toggleClass("ui-corner-all").toggleClass("ui-corner-top")
         $(target).next().addClass('ui-accordion-content-active').toggle('blind', {}, 500);
         
      },
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);
