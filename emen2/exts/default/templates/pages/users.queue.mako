<%inherit file="/page" />
<%namespace name="pages_user_util" file="/pages/user.util"  /> 

<%block name="javascript_inline">
	${parent.javascript_inline()}

	// Approve / Reject Users
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

		if (approve.length > 0) {
			$.jsonRPC.call("user.queue.approve",[approve],
				function(names) {
					//var names = [];
					//$.each(data, function(){names.push(this.name)});
					$.notify("Approved users: "+names);
					for (var i=0;i<names.length;i++) {
						$(".userqueue_"+names[i]).remove();
					}
					var count=parseInt($("#admin_userqueue_count").html());
					count -= names.length;
					$("#admin_userqueue_count").html(String(count))
				}
			);
		};

		if (reject.length > 0) {
			$.jsonRPC.call("user.queue.reject",[reject],
				function(names) {
					//var names = [];
					//$.each(data, function(){names.push(this.name)});				
					$.notify("Rejected users: "+names);
					for (var i=0;i<names.length;i++) {
						$(".userqueue_"+names[i]).remove();
					}
					var count=parseInt($("#admin_userqueue_count").html());
					count -= names.length;
					$("#admin_userqueue_count").html(String(count));							
				}
			);
		};
	}

	function admin_userstate_form(elem) {
		var enable=[];
		var disable=[];
		var form=$(elem.form);
		$('input:checked', form).each(function() {
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
			$.jsonRPC.call("user.enable",[enable],
				function(data) {
					if (data) {
						$.notify("Enabled users: "+data);
						for (var i=0;i<data.length;i++) {
							admin_userstate_cache[data[i]]=0;
						}
					}
				}
			)
		}

		if (disable.length > 0) {
			$.jsonRPC.call("user.disable",[disable],
				function(data) {
					if (data) {
						$.notify("Disabled users: "+data);
						for (var i=0;i<data.length;i++) {
							admin_userstate_cache[data[i]]=1;
						}					
					}
				}
			);
		}	
	}
</%block>

${pages_user_util.userqueue(admin_queue,0)}