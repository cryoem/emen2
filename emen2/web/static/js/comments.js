(function($) {
    $.widget("ui.CommentsControl", {
		options: {
			name: null,
			edit: false,
			title: null
		},
				
		_create: function() {
			this.built = 0;
			this.build();
		},
	
		partition: function() {
			var reccomments = caches["recs"][this.options.name]["comments"] || []; 
			this.comments = [];
			this.log = [];
			for (var i=0;i<reccomments.length;i++) {
				if (reccomments[i][2].indexOf("LOG") != 0) {
					this.comments.push(reccomments[i]);
				}
			}
		},
		
		rebuild: function() {
			this.build();
		},
	
		build: function() {
			var self=this;
			this.partition();
			this.comments.reverse();
			
			if (self.options.title) {
				if (this.comments.length) {
					$(self.options.title).html(this.comments.length+' Comments');
				} else {
					$(self.options.title).html('Comments');					
				}
			}			
			
			this.element.empty();			
			if (!this.comments.length) {
				this.element.append('<p>No Comments</p>');
			}

			$.each(this.comments, function() {
				var dname = caches["displaynames"][this[0]] || this[0];
				var time = this[1];	
				self.element.append('<h4>'+dname+' @ '+time+'</h4><p>'+this[2].replace(/\n/g,'<br />')+'</p>');
			});

			var comments_text = caches["recs"][this.options.name]["comments_text"];
			if (comments_text) {
				this.element.append('<strong>Additional comments:</strong><p>'+comments_text+'</p>');
			}

			if (this.options.edit) {
				var controls = $('<div/>');
				var edit = $('<textarea cols="60" rows="2"></textarea>');
				var commit=$('<input type="submit" value="Add Comment" />').click(function(e) {self.save()});
				controls.append(edit, commit);
				this.element.append(controls);
			}

		},

		////////////////////////////
		save: function() {
			var self = this;

			$.jsonRPC("addcomment",[this.options.name, $("textarea", this.element).val()],

		 		function(rec){
					//will trigger this rebuild... hopefully.. :)
					record_update(rec);
					notify("Comment Added");
		 		}
			)		
		},

		destroy: function() {
		},

		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);



(function($) {
    $.widget("ui.HistoryControl", {
		options: {
			name: null,
			title: null
		},
				
		_create: function() {
			var self = this;
			this.built = 0;
			$(this.options.title).click(function(){self.build()});
		},
	
		partition: function() {
			this.reccomments = caches["recs"][this.options.name]["comments"];
			this.rechistory = caches["recs"][this.options.name]["history"];
			this.rhist = [];		
			for (var i=0;i<this.reccomments.length;i++) {
				if (this.reccomments[i][2].indexOf("LOG") > -1) {
					this.rhist.push(this.reccomments[i]);
				}
			}
			for (var i=0;i<this.rechistory.length;i++) {
				this.rhist.push(this.rechistory[i]);
			}
		},
		
		show: function() {
			this.build();
		},
		
		rebuild: function() {
			this.built = 0;
			this.build();
		},
		
		build: function() {
			if (this.built) {
				return
			}
			this.built = 1;

			// This used to build the table itself, but now just calls the history page
			var self = this;
			var l = EMEN2WEBROOT+'/record/'+this.options.name+'/history/?simple=1';
			this.element.load(l);

			this.partition();
			if (self.options.title) {
				$(self.options.title).html('History ('+this.rhist.length+' edits)');
			}
					
		},

		destroy: function() {
		},

		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);

		
