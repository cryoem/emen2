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
		
		rebuild: function() {
			this.built = 0;
			this.build();
		},
	
		build: function() {	
			var self = this;	
			if (this.built) {return}

			this.comments = caches['record'][this.options.name]["comments"].slice() || [];
			this.history = caches['record'][this.options.name]['history'].slice() || [];			
			this.comments.push([caches['record'][this.options.name]['creator'], caches['record'][this.options.name]['creationtime'], 'Record created']);

			// Check to see if we need any users or parameters
			var users = [];
			$.each(this.comments, function(){users.push(this[0])})
			$.each(this.history, function(){users.push(this[0])})
			users = $.map(users, function(user){if (!caches['user'][user]){return user}})

			var params = [];
			$.each(this.history, function(){
				if (!caches['paramdef'][this[2]]) {
					params.push(this[2])
				}
			});

			// If we need users or params, fetch them.
			// Todo: find a nice way to chain these together, server side
			if (users && params) {

				$.jsonRPC.call('getuser', [users], function(users) {
						$.each(users, function() {caches['user'][this.name] = this});
						$.jsonRPC.call('getparamdef', [params], function(params) {
							$.each(params, function() {caches['paramdef'][this.name] = this});
							self._build();
						});
					});
			
			} else if (params.length) {

				$.jsonRPC.call("getparamdef", [params], 
					function(params) {
						$.each(params, function() {caches['paramdef'][this.name] = this});
						self._build();
					});
					
			} else if (users.length) {

				$.jsonRPC.call("getuser", [users], 
					function(users) {
						$.each(users, function() {caches['user'][this.name] = this});
						self._build();
					});

			} else {
				self._build();
			}
			this.built = 1;
		},
	
		_build: function() {
			// Build after all data is cached
			var self = this;
			this.element.empty();			
			var total = this.comments.length + this.history.length
			var all = [];
			$.each(this.comments, function(){all.push(this)})
			$.each(this.history, function(){all.push(this)})
			// Break each log event out by date
			var bydate = {};
			$.each(all, function() {
				var user = this[0];
				var date = this[1];
				// Emulate Python collections.defaultdict
				if (!bydate[date]) {bydate[date] = {}}
				if (!bydate[date][user]) {bydate[date][user] = []}
				bydate[date][user].push(this);
			});

			// Sort the keys. JS doesn't support sorted(dict, key=..)
			var keys = [];
			$.each(bydate, function(k,v){keys.push(k)})
			keys.sort();
			// keys.reverse();
			
			$.each(keys, function(i, date) {
				$.each(bydate[date], function(user, events) {
					// var events = $.map(events, self.makebody);
					var d = $('<div />');
					d.InfoBox({
						'keytype':'user',
						'name': user,
						'time': date,
						'autolink': true,
						'body': self.makebody(events) || ' '
					});
					self.element.append(d);
				});
			})

			// var comments_text = caches['record'][this.options.name]["comments_text"];
			// if (comments_text) {
			// 	this.element.append('<strong>Additional comments:</strong><p>'+comments_text+'</p>');
			// }			

			if (this.options.edit) {
				var controls = $('<div/>');
				var edit = $('<textarea name="comment" cols="60" rows="2"></textarea>');
				var commit=$('<input type="submit" class="e2l-float-right e2l-save" value="Add Comment" />').click(function(e) {self.save()});
				controls.append(edit, commit);
				this.element.append(controls);
			}
		},
		
		makebody: function(events) {
			var comments = [];
			var rows = [];
			$.each(events, function(i, event) {
				if (event.length == 3) {'<p>'+comments.push(event[2])+'</p>'}
				if (event.length == 4) {
					var pdname = event[2];
					if (caches['paramdef'][pdname]){pdname=caches['paramdef'][pdname].desc_short}
					var row = '<tr><td style="width:16px"><img src="'+EMEN2WEBROOT+'/static/images/edit.png" /></td><td><a href="'+EMEN2WEBROOT+'/paramdef/'+event[2]+'/">'+pdname+'</a></td></tr><tr><td /><td>Old value: '+event[3]+'</td></tr>';
					rows.push(row);
				}
			});
			comments = comments.join('');
			if (rows) {
				rows = '<table cellpadding="0" cellspacing="0"><tbody>'+rows.join('')+'</tbody></table>';
			} else { rows = ''}
			return comments + rows;
		},
		
		////////////////////////////
		save: function() {	
			var self = this;
			$.jsonRPC.call('addcomment', [this.options.name, $('textarea[name=comment]', this.element).val()], function(rec) {
				$.record_update(rec)
				$.notify('Comment Added');
			});
		}
	});
})(jQuery);

<%!
public = True
headers = {
	'Content-Type': 'application/javascript',
	'Cache-Control': 'max-age=86400'
}
%>