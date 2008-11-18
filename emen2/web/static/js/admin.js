//////////////////////////////////////////

function admin_approveusers_checkall(elem) {
	$('input:radio[value=true]',$(elem.form)).each(function(){
		$(this).attr("checked","true");
	});
}
function admin_approveusers_uncheckall(elem) {
	$('input:radio[value=false]',$(elem.form)).each(function(){
		$(this).attr("checked","false");
	});
}


function admin_approveusers_form(elem) {
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
		$.jsonRPC("approveuser",[approve,ctxid],
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
		$.jsonRPC("rejectuser",[reject,ctxid],
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


function list_intersect(a,b) {
	
	for (var i=0;i<b.length;i++) {
		
	}
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
	
	//console.log(enable);
	//console.log(disable);
	//return
	
	if (enable.length > 0) {
		$.jsonRPC("enableuser",[enable,ctxid],
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
		$.jsonRPC("disableuser",[disable,ctxid],
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



function admin_chpasswd_form(elem) {
	var form=$(elem.form);
	var oldpass=form.find("input[name='oldpass']");
	var newpass1=form.find("input[name='newpass1']");
	var newpass2=form.find("input[name='newpass2']");
	
	if (newpass1.val() != newpass2.val()) {
		notify("Passwords do not match");
		newpass1.val("");
		newpass2.val("");
		return false
		}
	if (newpass1.val().length < 6) {
		notify("Minimum 6 chars for password");
		newpass1.val("");
		newpass2.val("");
		return false
	}
	

	$.jsonRPC("setpassword",[username,oldpass.val(),newpass1.val(),ctxid], 
		function(data) {
			//console.log("ok");
			//console.log(data)
			notify_post("/db/home/",["Password Updated Successfully"]);
		},
		function(data) {
			//console.log("fail");
			//console.log(data)
			notify("Incorrect Password");
			form.find("input[name='oldpass']").val("")
		}
	);

}