//////////////////////////////////////////

function admin_approveuser_form(elem) {
	var approve=[];
	var reject=[];
	var form=$(elem.form);
	$('input:checked', form).each(function() {
		if ($(this).val() == "true") {
			approve.push($(this).attr("name"));
		} else {
			reject.push($(this).attr("name"));
		}
	});
	//console.log(approve);
	//console.log(reject);

	if (approve.length > 0) {
		$.jsonRPC("approveuser_sendmail",[approve], //wrapper_approveuser_sendmail ian:mustfix
			function(data) {
				notify("Approved users: "+data);
				for (var i=0;i<data.length;i++) {
					$(".userqueue_"+data[i]).remove();
				}
				var count=parseInt($("#admin_userqueue_count").html());
				count -= data.length;
				$("#admin_userqueue_count").html(String(count))
			},
			function(data) {
				
			}
		);
	};

	if (reject.length > 0) {
		$.jsonRPC("rejectuser_sendmail",[reject],
			function(data) {
				notify("Rejected users: "+data);
				for (var i=0;i<data.length;i++) {
					$(".userqueue_"+data[i]).remove();
				}
				var count=parseInt($("#admin_userqueue_count").html());
				count -= data.length;
				$("#admin_userqueue_count").html(String(count));							
			},
			function(data) {
				
			}
		);
	};
}




function admin_userstate_form(elem) {
	var enable=[];
	var disable=[];
	var form=$(elem.form);
	$('input:checked', form).each(function() {
		//console.log(this);
		var un=$(this).attr("name");
		var unv=parseInt($(this).val());
		if (unv == 0 &&  admin_userstate_cache[un] != unv) {
			enable.push(un);
		}
		if (unv == 1 &&  admin_userstate_cache[un] != unv) {
			disable.push(un);
		}
	});
	
	if (enable.length > 0) {
		$.jsonRPC("enableuser",[enable],
			function(data) {
				if (data) {
					notify("Enabled users: "+data);
					for (var i=0;i<data.length;i++) {
						admin_userstate_cache[data[i]]=0;
						//console.log(admin_userstate_cache[data[i]]);
					}
				}
			}
		)
	}

	if (disable.length > 0) {
		$.jsonRPC("disableuser",[disable],
			function(data) {
				if (data) {
					notify("Disabled users: "+data);
					for (var i=0;i<data.length;i++) {
						admin_userstate_cache[data[i]]=1;
						//console.log(admin_userstate_cache[data[i]]);						
					}					
				}
			}
		);
	}
	
}
