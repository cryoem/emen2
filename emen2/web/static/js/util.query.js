// var inband=[];
// 
// $(document).ready(function() {
// 
// 	$("#form_query_protocol").change(
// 		function() {
// 			var pn=$(this).val();
// 			form_query_setrecorddef(pn);
// 		}
// 	);
// 
// });
// 
// 
// function form_query_setinband(recorddef) {
// 	var newqp=[];
// 	for (var i=0;i<queryparams.length;i++) {
// 		if (paramsK[recorddef].indexOf(queryparams[i][0]) > -1) {
// 			inband[i]=1;
// 		} else {
// 			inband[i]=0;
// 		}
// 	}
// }
// 
// function form_query_setrecorddef(nrecorddef) {
// 	recorddef=nrecorddef;
// 	form_query_paramsgetstate();
// 	//form_query_cleanup();
// 
// 	form_query_setinband(nrecorddef);
// 	//if (inband[1] != 1) {
// 	//	queryparams.splice(1,0,["","=",""]);
// 	//}
// 	form_query_setinband(nrecorddef);
// 	inband[1]=1;
// 
// 	//param_text[1]='<img src="/static/images/branch_up.reverse.png" height="32" width="32" />';
// 	form_query_paramsredraw();
// }
// 
// 
// function form_query_paramsgetstate() {
// 	var f=$("#form_query");
// 	var pn=f.find("[name^=params_]");
// 	var pc=f.find("[name^=paramcompare_]");	
// 	var pv=f.find("[name^=paramvalue_]");	
// 	queryparams=[];
// 	for (var i=0;i<pn.length;i++) {
// 		var index=parseInt($(pn[i]).attr("name").split("_").pop());
// 		queryparams[index]=[$(pn[i]).val(), $(pc[i]).val(), $(pv[i]).val()];
// 	}
// }
// 
// function form_query_cleanup() {
// 	var newqp=[];
// 	for (var i=0;i<queryparams.length;i++) {
// 		var q=queryparams[i];
// 		if (q[0] != "") {
// 			newqp.push([q[0],q[1],q[2]]);
// 		}
// 	}
// 	queryparams=newqp.slice();
// }
// 
// 
// function form_query_paramsredraw() {
// 	var qp=$("#form_query_params");
// 	qp.empty();	
// 	for (var i=1;i<queryparams.length;i++) {
// 		if (inband[i]==1) {
// 			form_query_paramaddmarkup(i,null,queryparams[i][0],null,queryparams[i][1],queryparams[i][2]);
// 		}
// 	}
// 	
// 	for (var i=1;i<queryparams.length;i++) {
// 		if (inband[i]!=1) {
// 			form_query_paramaddmarkup(i,null,queryparams[i][0],null,queryparams[i][1],queryparams[i][2]);
// 		}
// 	}			
// 	
// }
// 
// 
// function form_query_paramadd(param, choices, compare, value) {
// 	form_query_paramsgetstate();
// 	//form_query_cleanup();
// 	queryparams.push(["","=",""]);
// 	form_query_paramsredraw();
// }
// 
// 
// function form_query_paramaddmarkup(index, ptext, param, choices, compare, value) {
// 
// 	if (inband[index] == 1) {
// 		ptext='<img src="'+EMEN2WEBROOT+'/static/images/branch_up.reverse.png" height="32" width="32" />';
// 	} else {
// 		ptext="Parameter ";
// 	}
// 	
// 	if (inband[index] == 1) {
// 		choices=paramsK[recorddef];
// 	} else {
// 		choices=pdn;
// 	}
// 
// 	var qp=$("#form_query_params");
// 	var p=$("<p></p>");
// 
// 	p.html(ptext);
// 
// 	var pn=$("<select />");
// 	pn.attr("name","params___0"+index);
// 	pn.append("<option />");
// 	for (var i=0;i<choices.length;i++) {
// 		var z=$('<option value="'+choices[i]+'">'+choices[i]+' --- '+paramdef_desc[choices[i]]+'</option>');
// 		if (param==choices[i]) {z.attr("selected","selected");}
// 		pn.append(z);
// 	}
// 
// 	var pc=$("<select />");
// 	pc.attr("name","paramcompare___0"+index);
// 	$.each(comparators, function(k,v) {
// 		var z=$('<option value="'+k+'">'+v+'</option>');
// 		if (compare==k) {z.attr("selected","selected");}
// 		pc.append(z);
// 	});
// 	
// 	
// 	var pv=$('<input type="text" />');
// 	pv.attr("name","paramvalue___0"+index);
// 	pv.val(value);
// 	
// 	p.append(pn," ",pc," ",pv);
// 
// 	qp.append(p);
// 	
// }