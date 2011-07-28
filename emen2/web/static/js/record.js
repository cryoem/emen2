////////////////  Record page init ///////////////////

function record_init_new(rec, parent) {
	rec.name = "None";
	caches["recs"][rec.name] = rec;

	$('#e2-editbar-newrecord-info').EditbarHelper({show: true, width:640});

	$('#e2-editbar-newrecord-recorddef').EditbarHelper({});

	$('#e2-editbar-newrecord-relationships').EditbarHelper({});

	$('#e2-editbar-newrecord-permissions').EditbarHelper({width: 640});

	$('#rendered').css('margin-top', $('#e2-editbar-newrecord-info div.hidden').height()+10);

	$('#e2-newrecord-save').MultiEditControl({
		name: rec.name,
		show: true,
		newrecordpage: true
		});

	$('#e2-newrecord-permissions').PermissionControl({
		name: rec.name,
		edit: true,
		embed: true
		});	

	// Change the text of file upload elements..
	$('.editable_files .label').html('(The record must be saved before files can be attached)');

	$('#e2-editbar-newrecord-recorddef').EditbarHelper({
		width:300,
		cb: function(self){
			self.popup.NewRecord({
				embedselector: true,
				showselector: true,
				parent: parent.name
				});
			}
	});		

}


function record_init(rec, ptest, edit) {
	caches["recs"][rec.name] = rec;
	
	// Permissions editor
	$('#e2-editbar-record-permissions').EditbarHelper({
		width: 640,
		cb: function(self){
			self.popup.PermissionControl({
				name: rec.name,
				edit: ptest[3],
				embed: true,
				show: true
				});
			}
	});		

	// Attachments editor
	var showattachments = (window.location.hash.search('attachments'));
	if (showattachments>-1){showattachments=true}

	$('#e2-editbar-record-attachments').EditbarHelper({
		width:600,
		cb: function(self) {
			self.popup.AttachmentViewerControl({
				name: rec.name,
				edit: ptest[2] || ptest[3],
				embed: true,
				show: true
				});
			},
		show: showattachments
	});
	
	// New record editor
	$('#e2-editbar-record-newrecord').EditbarHelper({
		width:300,
		cb: function(self){
			self.popup.NewRecord({
				embedselector: true,
				showselector: true,
				parent: rec.name
				});
			}
	});		

	// Relationship editor
	$("#e2-editbar-record-relationships").EditbarHelper({		
		width: 780,
		cb: function(self){
			self.popup.RelationshipControl({
				root: rec.name,
				edit: true,
				embed: true,
				show: true
				});
			}
	});	
	
	$('.editbar [data-viewtype]').click(function(){
		var target = $("#rendered");
		var viewtype = $(this).attr('data-viewtype') || 'recname';
		target.attr("data-viewtype", viewtype);
		rebuildviews("#rendered");
	});

	$('#e2-editbar-tools').EditbarHelper({});

	$('#e2-editbar-helper').EditbarHelper({
		align: 'right',
		cb: function(self) {
			self.popup.load(EMEN2WEBROOT+'/record/'+rec.name+'/history/?simple=1');
		}
	});

	// Comments editor
	$('#e2-editbar-comments').EditbarHelper({
		width: 350,
		align: 'right',
		cb: function(self) {
			// Comments and history
			self.popup.CommentsControl({
				name: rec.name,
				edit: ptest[1] || ptest[2] || ptest[3],
				historycount: "#e2-editbar-commentcount",
				commentcount: '#e2-editbar-historycount'
			});
		}
	});

	// Simple handler for browsing siblings...
	var showsiblings = (window.location.hash.search('siblings'));
	if (showsiblings>-1){showsiblings=true}
	
	$("#e2-editbar-record-siblings").EditbarHelper({
		show: showsiblings,
		width:300,
		align: 'right',
		cb: function(self) {
			self.popup.empty();
			var sibling = self.element.attr('data-sibling') || rec.name;
			var prev = self.element.attr('data-prev') || null;
			var next = self.element.attr('data-next') || null;
			if ($('#siblings', self.popup).length) {
				return
			}
			var sibs = $('<div class="e2-siblings"><img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /></div>');
			self.popup.append(sibs);
			$.jsonRPC2("getsiblings", [rec.name, rec.rectype], function(siblings) {
				$.jsonRPC2("renderview", [siblings, null, "recname"], function(recnames) {
					siblings = siblings.sort(function(a,b){return a-b});
					sibs.empty();
					
					var prevnext = $('<h4 class="clearfix e2-editbar-sibling-prevnext"></h4>');
					if (prev) {
						prevnext.append('<div class="floatleft"><a href="'+EMEN2WEBROOT+'/record/'+prev+'/#siblings">&laquo; Previous</a></div>');
					}
					if (next) {
						prevnext.append('<div class="floatright"><a href="'+EMEN2WEBROOT+'/record/'+next+'/#siblings">Next &raquo;</a></div>');
					}					
					sibs.append(prevnext);
					
					var ul = $('<ul class="nonlist"/>');
					$.extend(caches["recnames"], recnames);
					$.each(siblings, function(i,k) {
						if (k != rec.name) {
							// color:white here is a hack to have them line up
							ul.append('<li><a href="'+EMEN2WEBROOT+'/record/'+k+'/?sibling='+sibling+'#siblings">'+(caches["recnames"][k]||k)+'</a></li>');
						} else {
							ul.append('<li class="e2-siblings-active">'+(caches["recnames"][k]||k)+'</li>');
						}
					});
					sibs.append(ul);
				});
			});
		}
	});	

	// Bind editable widgets
	$('#e2-editbar-record-setbookmark').Bookmarks({'mode':'toggle'});

	// $('.e2-editbar-record-newrecord').NewRecord({});

	$('.editable').EditControl({});
	// $('.editable_files').FileControl({});

	$('#e2-editbar-record-edit .label').MultiEditControl({});
	if (edit) {
		$('#e2-editbar-record-edit .label').MultiEditControl('event_click');
	}
	
	$('.e2-tile').TileMap({'mode':'cached'});
	
	
}



////////////////  Record Update callbacks ///////////////////

function record_update(rec) {
	if (typeof(rec)=="number") {
		var name = rec;
	} else {
		caches["recs"][rec.name] = rec;
		var name = rec.name;
	}
	rebuildviews('.e2-view[data-name='+name+']');
	$(".e2-comments").CommentsControl('rebuild');
	$('.e2-attachments').AttachmentViewerControl('rebuild');	
}


function rebuildviews(selector) {
	selector = selector || '.view';
	var self = this;
	$(selector).each(function() {
		var elem = $(this);
		var name = parseInt(elem.attr('data-name'));
		var viewtype = elem.attr('data-viewtype');
		var edit = elem.attr('data-edit');
		$.jsonRPC2("renderview", {'names':name, 'viewtype': viewtype, 'edit': edit}, function(view) {
			elem.html(view);
			$('.editable', elem).EditControl({});
			//$('.editable_files', elem).FileControl({});
		},
		function(view){}
		);
	})
}
