function switchpane(target) {
	$('.current').addClass('hidden').removeClass('current');
	$(target).removeClass('hidden').addClass('current')
}

function panes(target) {
	var self = this
	this.elem= $(target);
	this.pane= self.elem.children('.pane');
	this.current= self.elem.children('.current');
	this.switch_= function(target) {
		self.current.addClass('hidden').removeClass('current');
		var n = self.elem.children(target);
		n.removeClass('hidden').addClass('current');
		if (n.hasClass('load')) {
			$.get(n.text(), function (data) { n.empty();n.append(data);n.removeClass('load') } )
		 }
		self.current = n;
		location.hash = target;
	};
}

///////
even = 1
$(document).ready(
	  function() {
		  even = new panes('#panes');
	  }
)


