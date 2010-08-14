(function($) {
    $.widget("ui.CommentsControl", {
		options: {
			recid: null,
			edit: false,
			title: null
		},
				
		_create: function() {
			this.built = 0;
			this.build();
		},
	
		partition: function() {
			var reccomments = caches["recs"][this.options.recid]["comments"];
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
				self.element.append('<h4>'+dname+' @ '+time+'</h4><p>'+this[2]+'</p>');
			});

			var comments_text = caches["recs"][this.options.recid]["comments_text"];
			if (comments_text) {
				self.elem_body.append('<strong>Additional comments:</strong><p>'+comments_text+'</p>');
			}

			if (this.options.edit) {
				var controls = $('<div/>');
				var edit = $('<textarea cols="60" rows="2"></textarea>');
				var commit=$('<input class="editbutton" type="submit" value="Add Comment" />').click(function(e) {self.save()});
				controls.append(edit, commit);
				this.element.append(controls);
			}

		},

		////////////////////////////
		save: function() {
			var self = this;

			$.jsonRPC("addcomment",[this.options.recid, $("textarea", this.element).val()],

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
			recid: null,
			title: null
		},
				
		_create: function() {
			var self = this;
			this.built = 0;
			$(this.options.title).click(function(){self.build()});
		},
	
		partition: function() {
			this.reccomments = caches["recs"][this.options.recid]["comments"];
			this.rechistory = caches["recs"][this.options.recid]["history"];
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

			var self = this;
			var l = EMEN2WEBROOT+'/db/record/'+this.options.recid+'/history/?simple=1';
			this.element.load(l);

			this.partition();
			if (self.options.title) {
				$(self.options.title).html('History ('+this.rhist.length+' changes)');
			}
			// var self = this;
			// this.element.empty();
			// this.rhist.reverse();
			// 
			// var link = $('<p><a href="'+EMEN2WEBROOT+'/db/record/'+this.options.recid+'/history/">Detailed Revisions Page</a></p>')
			// this.element.append(link);
			// 
			// 
			// if (this.rhist == 0) {
			// 	this.element.append('<p>No changes</p>');
			// }
			// 
			// $.each(this.rhist, function() {
			// 	var dname = caches["displaynames"][this[0]] || this[0];
			// 	var time = this[1];
			// 	var rev = '<a href="'+EMEN2WEBROOT+'/db/record/'+self.options.recid+'/history/'+time+'/">View Revision</a>';
			// 
			// 	// Check if old-style comment or new-style comment
			// 	if (this.length == 4) {
			// 		var i = escapeHTML(String(this[3]));
			// 		if (i.length > 50) {
			// 			i = i.slice(0,50) + '...&raquo;';
			// 		}
			// 		self.element.append('<h4>'+dname+' @ '+time+'<span style="float:right">'+rev+'</h4><p>LOG: ' + this[2] + ' updated, was: '+i+'</p>');
			// 	}
			// 	else {
			// 		var i = escapeHTML(String(this[2]));
			// 		if (i.length > 50) {
			// 			i = i.slice(0,50) + '...&raquo';
			// 		}					
			// 		self.element.append('<h4>'+dname+' @ '+time+'<span style="float:right">'+rev+'</h4><p>' + i.slice(0,50) + '</p>');
			// 	}
			// 
			// });		
		
		},

		destroy: function() {
		},

		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);

		
