// js is stupid at sorting.
function sortNumber(a, b) {
	return a - b;
}


/// switch.js
function switchbutton(type,id) {
	$(".button_"+type).each(function() {
		var elem=$(this);
		if (this.id != "button_"+type+"_"+id) {
			elem.removeClass("button_active");
			elem.removeClass("button_"+type+"_active");
		} else {
			elem.addClass("button_active");
			elem.addClass("button_"+type+"_active");
		}
	});
}


var switchedin=new Array();

function switchin(classname, id) {
	switchedin[classname]=id;
	switchbutton(classname,id);
	$(".page_"+classname).removeClass("page_active");
	$(".page_"+classname).removeClass("page_"+classname+"_active");	
	$("#page_"+classname+"_"+id).addClass("page_active");
	$("#page_"+classname+"_"+id).addClass("page_"+classname+"_active");
}



//////////////////////////////////////////
// access values from cached sources

var caches = {};
caches["paramdefs"] = {};
caches["recorddefs"] = {};
caches["displaynames"] = {};
caches["groupnames"] = {};
caches["users"] = {};
caches["groups"] = {};
caches["recs"] = {};
caches["recnames"] = {};
caches["children"] = {};
caches["parents"] = {};


//////////////////////////////////////////


function notify(msg, fade, error) {
	var msg=$('<li>'+msg+'</li>');

	if (error) {
		msg.addClass("error");
	}

	//var killbutton = $('<img src="'+EMEN2WEBROOT+'/images/delete.png" />');
	var killbutton = $('<span>X</span>');
	killbutton.click(function() {
		$(this).parent().fadeOut(function(){
			//fadeoutcallback; in this context, 'this' is li
			$(this).remove();
			});		
	});
	killbutton.addClass("kill");
	msg.append(killbutton);

	// auto fade if given time value
	//if (!fade) {
	//	setTimeout(function(){msg.fadeOut()},3000)
	//}
	//if (fade > 0) {
	//	setTimeout(function(){msg.fadeOut()},fade*1000)
	//}

	$("#alert").append(msg); //.fadeIn();
	
}


function notify_post(uri,msgs) {
  var postform = document.createElement("form");
  postform.method="POST" ;
  postform.action = uri;
	for (var i=0;i<msgs.length;i++) {
		var note = document.createElement("input") ;
		note.setAttribute("name", "notify___"+i) ;
		note.setAttribute("value", msgs[i]);
		postform.appendChild(note) ;
	}
	document.body.appendChild(postform);
  postform.submit();	
}





function record_init(recid, ptest) {
		$('.editbar .edit').MultiEditControl({});
		$('.editable').EditControl({});
		$('.editable_files').FileControl({});

		$('.editbar .permissions').PermissionControl({recid:recid, edit:ptest[3]});
		$('.editbar .attachments').AttachmentViewerControl({recid:recid, edit:ptest[2]});
		$('.editbar .newrecord').NewRecordSelect({recid:recid});
		$(".editbar .relationships").RelationshipControl({recid:recid});

		$('.selectview select').change(function(){
			var target=$("#rendered");
			target.attr("data-viewtype", $(this).val());
			rebuildviews("#rendered");
		});
		
		$("#page_comments_comments").CommentsControl({recid:recid, edit:ptest[1], title:"#button_comments_comments"});
		$("#page_comments_history").HistoryControl({recid:recid, title:"#button_comments_history"});

}

function record_update(rec) {
	caches["recs"][rec.recid] = rec;
	rebuildviews('.view[data-recid='+rec.recid+']');
	$("#page_comments_comments").CommentsControl('rebuild');
	$("#page_comments_history").HistoryControl('rebuild');
	$('.editbar .attachments').AttachmentViewerControl('rebuild');	
}



function rebuildviews(selector) {
	selector = selector || '.view';
	var self = this;
	$(selector).each(function() {
		var elem = $(this);
		var recid = parseInt(elem.attr('data-recid'));
		var viewtype = elem.attr('data-viewtype');
		var mode = elem.attr('data-mode') || 'html';
		$.jsonRPC("renderview", {'recs':recid, 'viewtype': viewtype, 'mode':mode}, function(view) {
			elem.html(view);
			$('.editable', elem).EditControl({});
			$('.editable_files', elem).FileControl({});
		},
		function(view){}
		);
	})
}







