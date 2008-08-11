// js is stupid at sorting.
function sortNumber(a, b) {
	return a - b;
}


function notify(msg) {
	//$("#alert").empty();
	var msg=$('<li>'+msg+'</li>');
	$("#alert").append(msg).fadeIn();
	setTimeout(function(){msg.fadeOut()},3000)
}


//////////////////////////////////////////
// not used; for testing
function tableinit() {

	var testtable=document.getElementById("testtable");

	var order=1;

	var tr=document.createElement("tr");
	for(var j=0;j<tablekeys.length;j++) {
		var th=document.createElement("th");
		th.innerHTML=tablekeys[j];
		new multiwidget(th,{restrictparams:[tablekeys[j]], rootless:1, controlsroot: $(th)});
		tr.appendChild(th);
	}
	testtable.appendChild(tr);

	for (var i=0;i<recids.length;i++) {
		var tr=document.createElement("tr");
		for (var j=0;j<tablekeys.length;j++) {
			var td=document.createElement("td");
			var sp=document.createElement("span");
			sp.innerHTML=getvalue(recids[i],tablekeys[j]);
			sp.className="editable paramdef___"+tablekeys[j]+" recid___"+recids[i];
			td.appendChild(sp);
			tr.appendChild(td);
		}
		new multiwidget(tr,{restrictparams:["name_first"],rootless:1});
		testtable.appendChild(tr);	
	}
	
}