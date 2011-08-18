(function($) {
    $.widget("emen2.CommentsControl", {
		options: {
			name: null,
			edit: false,
			title: null,
			historycount: false,
			commentcount: false
		},
				
		_create: function() {
			this.built = 0;
			this.element.addClass('e2-comments');
			this.build();
		},
	
		partition: function() {
			var reccomments = caches["recs"][this.options.name]["comments"] || []; 
			this.comments = [];
			this.log = [];
			for (var i=0;i < reccomments.length;i++) {
				if (reccomments[i][2].indexOf("LOG") != 0) {
					this.comments.push(reccomments[i]);
				}
			}
		},
		
		rebuild: function() {
			this.build();
		},
	
		build: function() {	
			var self = this;	
			var users = [];
			this.partition();
			$.each(this.comments, function() {
				var user = this[0];
				if (caches['users'][user]==null) {
					users.push(user);
				}
			});
			// console.log(users);
			if (users.length) {
				$.jsonRPC.request("getuser", [users], {
               success: function(u) {
                  $.each(u.result, function() {
                     caches['users'][this.name] = this;
                     caches['displaynames'][this.name] = this.displayname;
                  });
                  self._build();
               },
               error: function(){console.log(arguments);}
            });
			} else {
				self._build();
			}
			
		},
	
		_build: function() {
			var self=this;
			this.partition();
			this.comments.reverse();
			
			this.element.empty();			
			if (!this.comments.length) {
				this.element.append('<p>No Comments</p>');
			}

			$.each(this.comments, function() {
				// var dname = caches["displaynames"][this[0]] || this[0];
				var user = caches['users'][this[0]];
				var photo = user['userrec']['person_photo'];
				if (photo) {
					photo = EMEN2WEBROOT+'/download/'+photo+'/'+user.name+'.jpg?size=thumb';
				} else {
					photo = EMEN2WEBROOT+'/static/images/nophoto.png';
				}
				
				var time = this[1];
				self.element.append('<div class="e2-comments-comment"><img src="'+photo+'" class="thumbnail" /><h4>'+user.displayname+' @ '+time+'</h4><p>'+this[2].replace(/\n/g,'<br />')+'</p></div>');
			});

			var comments_text = caches["recs"][this.options.name]["comments_text"];
			if (comments_text) {
				this.element.append('<strong>Additional comments:</strong><p>'+comments_text+'</p>');
			}

			if (this.options.edit) {
				var controls = $('<div/>');
				var edit = $('<textarea cols="60" rows="2"></textarea>');
				var commit=$('<input type="submit" class="floatright save" value="Add Comment" />').click(function(e) {self.save()});
				controls.append(edit, commit);
				this.element.append(controls);
			}
			
			// if (self.options.title) {
			// 	if (this.comments.length) {
			// 		$(self.options.title).html(this.comments.length+' Comments');
			// 	} else {
			// 		$(self.options.title).html('Comments');					
			// 	}
			// }						
			if (this.options.historycount) {
				if (this.log.length) {
					$(this.options.historycount).html('('+this.log.length+')');					
				} else {
					$(this.options.historycount).html('');										
				}
			}
			if (this.options.commentcount) {
				if (this.comments.length) {
					$(this.options.commentcount).html(this.comments.length);
				} else {
					$(this.options.commentcount).html('');					
				}
			}
		},

		////////////////////////////
		save: function() {
			var self = this;

			$.jsonRPC.request("addcomment",[this.options.name, $("textarea", this.element).val()],
		 		{success:
               function(rec){
                  //will trigger this rebuild... hopefully.. :)
                  record_update(rec.result);
                  notify("Comment Added");
               },
              error: console.log
		 		}
			)		
		}
	});
})(jQuery);

