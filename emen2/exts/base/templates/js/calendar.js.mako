(function($) {
    $.widget("emen2.DateRepeatControl", {
		options: {
		},
				
		_create: function() {
			var self = this;
			this.element.click(function(){self.show()});
		},
		
		show: function() {
			this.build();
		},
		
		build: function() {
			var self = this;
			this.dialog = $('<div title="Event Details"></div>');

			// Main settings
			var t = $(' \
				<table> \
					<tbody> \
						<tr> \
							<td>Title:</td> \
							<td><input type="text" name="title" /></td> \
						</tr> \
						<tr> \
							<td>Details:</td> \
							<td> \
								<textarea name="details"></textarea> \
							</td> \
						</tr> \
						<tr> \
							<td>Start:</td> \
							<td> \
								<input type="text" name="dtstart_date" size="8"/> \
								<input type="text" name="dtstart_time" size="10"/> \
							</td> \
						</tr> \
						<tr> \
							<td>End:</td> \
							<td> \
								<input type="text" name="dtstart_date" size="8"/> \
								<input type="text" name="dtstart_time" size="10"/> \
							</td> \
						</tr> \
					</tbody> \
				</table> \
			');

			this.dialog.append(t);			
			
			this.build_options();
			
			this.element.append(this.dialog)
			this.dialog.dialog({
				draggable: false,
				resizable: false,				
				width: 600,
				height: 600, 
				autoOpen: true,
				modal: true
			});			
		},
		
		build_options: function() {
			var self = this;
			var options = $(' \
				<ul class="e2l-tab-buttons e2l-cf"> \
					<li class="e2l-button e2l-tab-active">Repeat</li> \
					<li class="e2l-button">Alerts</li> \
					<li class="e2l-button">Permissions</li> \
					<li class="e2l-button">Attachments</li> \
				</ul> \
				<div class="e2l-tab-pages"> \
					<div class="e2-daterepeat-options-repeat e2l-tab-page e2l-tab-active">Loading</div> \
				</div> \
			');
			this.dialog.append(options);
			this.build_repeat();
		},
		
		build_repeat: function(freq) {
			var self = this;
			var target = $('.e2-daterepeat-options-repeat', this.dialog);
			target.empty();

			var t = $('<table></table>');
			var tbody = $(' \
				<tbody> \
					<tr> \
						<td>Repeat:</td> \
						<td> \
							<select name="freq"> \
								<option value="" selected="selected"></option> \
								<option value="yearly">Yearly</option> \
								<option value="monthly">Monthly</option> \
								<option value="weekly">Weekly</option> \
								<option value="daily">Daily</option> \
								<option value="hourly">Hourly</option> \
							</select> \
						</td> \
					</tr> \
				</tbody> \
			');
			
			$('select[name=freq]', tbody).val(freq);
			$('select[name=freq]', tbody).change(function(){self.build_repeat($(this).val())});
			
			t.append(tbody);
			target.append(t);
			
			if (!freq) {return}
			
			var d = new Date();			
			var id = 'e2-daterepeat-id'+d.getTime();
			var interval = $(' \
				<tr> \
					<td>Repeat every:</td> \
					<td> \
						<select name="interval"> \
							<option>1</option> \
							<option>2</option> \
							<option>3</option> \
						</select> '+freq+' \
					</td> \
				</tr> \
			');

			// Common options: dtstart, count, dtend
			var startend = $(' \
				<tr> \
					<td>Ends:</td> \
					<td> \
						<ul> \
							<li><input type="radio" name="dtopts" checked="checked" /> Never</li> \
							<li><input type="radio" name="dtopts" /> After <input type="text" name="count" size="4" /> occurrences</li> \
							<li><input type="radio" name="dtopts" /> On <input type="text" name="dtend" /></li> \
						</ul> \
					</td> \
				</tr> \
			');
			
			// daily options (none)
			if (freq == 'daily') {
				tbody.append(interval);
				tbody.append(startend);				
			} else if (freq == 'weekly') {
				var weekly = $(' \
					<tr> \
						<td>Repeat on:</td> \
						<td> \
							<input type="checkbox" value="su" id="'+id+'-su"/> <label for="'+id+'-su">S</label> \
							<input type="checkbox" value="mo" id="'+id+'-mo"/> <label for="'+id+'-mo">M</label> \
							<input type="checkbox" value="tu" id="'+id+'-tu"/> <label for="'+id+'-tu">T</label> \
							<input type="checkbox" value="we" id="'+id+'-we"/> <label for="'+id+'-we">W</label> \
							<input type="checkbox" value="th" id="'+id+'-th"/> <label for="'+id+'-th">T</label> \
							<input type="checkbox" value="fr" id="'+id+'-fr"/> <label for="'+id+'-fr">F</label> \
							<input type="checkbox" value="sa" id="'+id+'-sa"/> <label for="'+id+'-sa">S</label> \
						</td> \
					</tr> \
				');
				tbody.append(interval);
				tbody.append(weekly);
				tbody.append(startend);				
			} else if (freq == 'monthly') {
				var repeatby = $(' \
					<tr> \
						<td>Repeat by:</td> \
						<td> \
							<input type="radio" name="repeatby" id="'+id+'-repeatby-day" checked="checked" /><label for="'+id+'-repeatby-day">day of the month</label> \
							<input type="radio" name="repeatby" id="'+id+'-repeatby-week" /><label for="'+id+'-repeatby-week">day of the week</label> \
						</td> \
					</tr> \
				');
				tbody.append(interval);				
				tbody.append(repeatby);
				tbody.append(startend);
			} else {
				tbody.append(interval);
				tbody.append(startend);				
			}
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