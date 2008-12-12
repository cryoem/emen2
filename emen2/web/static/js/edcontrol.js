function ParamNameControl(form, paramnames) {
	var box = document.createElement('div')
	box.className = "form_box";
	var select = document.createElement('select');
	select.id = 'select_paramdef';
	var apply = document.createElement('input');
	apply.id = 'add_paramdef';
	apply.type = 'button';
	apply.value = 'Add';
	
	for ( var x in paramnames ) {
		var option = document.createElement('option');
		option.defaultValue = paramnames[x];
		option.value = paramnames[x];
		option.textContent  = paramnames[x];
		select.appendChild(option);
	}
	
	apply.onclick = function selectOnClick() {
		$.ajax({
			url: '/db/pd/'+select.options[select.selectedIndex].text+'/',
			type: 'GET',
			dataType: 'json',
			timeout: 0,
			error: function() {
				alert('ERROR in AJAX');
			},
			success: function(json) {
				var new_param = document.createElement('div');
				new_param.innerHTML = json.field;
				form.appendChild(new_param);
			}
		});
	}
	box.appendChild(select);
	box.appendChild(apply);	
	form.appendChild(box);
	
	this.onSubmit = function onSubmit() {
	  form.removeChild(box);
	  form.submit();
	}
}


function Multiparam(form, paramnames) {
	this.box = document.createElement('div');
	var box = this.box
	this.newRow = function newRow() {
		for (var x in paramnames) {
			var param = paramnames[x]
			var suffix = box.childNodes.length
			$.ajax({
				url: '/db/pd/'+param+'/',
				type: 'GET',
				dataType: 'json',
				timeout: 1000,
				error: function() {
					alert('ERROR in AJAX');
				},
				success: function(json) {
					var new_param = document.createElement('div');
					new_param.innerHTML = json.field;
					var xm = new XML(json.field);
					alert(xm);
					box.appendChild(new_param);
				}
			});
		}
	}
	this.newRow()
	var apply = document.createElement('input');
	apply.id = 'newrow';
	apply.type = 'button';
	apply.value = 'NewRow';
	apply.onclick = this.newRow;
	this.box.appendChild(apply);
	form.appendChild(this.box);
}