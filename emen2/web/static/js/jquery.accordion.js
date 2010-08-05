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
         var is_space = false;
         var result = false;

         switch(event.keyCode) {
            case keyCode.SPACE:
               is_space = true;
               toFocus = this.headers[(currentIndex + 1) % length];
               break;
            case 74: // j
            case 83: // s
            case keyCode.DOWN:
               toFocus = this.headers[(currentIndex + 1) % length];
               break;
            case keyCode.UP:
            case 75: // k
            case 87: // w
               toFocus = this.headers[(currentIndex - 1 + length) % length];
               break;
            case keyCode.RIGHT:
            case 76: // l
            case 68: // l
               this.show(event.target);
               break;
            case keyCode.LEFT:
            case 72: // h
            case 65: // h
               this.hide(event.target);
               break;
            case keyCode.ENTER:
               $(event.target).stop();
               this.toggle(event.target);
               event.preventDefault();
         }

         if (toFocus) {
            //console.log(this.active.next().offset().top + this.active.next().outerHeight());
            //console.log($(window).height()+$(window).scrollTop());
            console.log((this.active.next().offset().top + this.active.next().outerHeight()) > ($(window).height() + $(window).scrollTop()));
            console.log(toFocus);
            var windowBottom = $(window).height() + $(window).scrollTop()
            if (is_space && ((this.active.next().offset().top + this.active.next().outerHeight()) > windowBottom)) {
               result = true;
               toFocus = this.active;
            } else {
               result = false;
               if (!event.shiftKey) this.hide(this.active);
            };
            console.log(toFocus);
            console.log(toFocus == this.active);

            if (toFocus != this.active) {
               this.active = $(toFocus);
               toFocus.focus();
               this.show(this.active);
            }

         } else { result = true; }

         return result;

      },

      show: function(target) {
         var target = $(target);
         target.stop();
         target.removeClass("ui-state-default").addClass("ui-state-active").removeClass("ui-corner-all").addClass("ui-corner-top");
         target.next().show();
      },
      hide: function(target) {
         var target = $(target);
         target.stop();
         target.addClass("ui-state-default").removeClass("ui-state-active").addClass("ui-corner-all").removeClass("ui-corner-top");
         target.next().hide();
      },
      toggle: function(target) {
         var target = $(target);
         target.stop();
         target.toggleClass("ui-state-default").toggleClass("ui-state-active").toggleClass("ui-corner-all").toggleClass("ui-corner-top");
         target.next().toggle();
      },

      _clickHandler: function(event, target) {
         console.log(target);
         this.active = $(target);
         this.active.stop()
         this.active.toggleClass("ui-state-default").toggleClass("ui-state-active").toggleClass("ui-corner-all").toggleClass("ui-corner-top");
         this.active.next().toggle();
         this.active.focus();
         
      },
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);
