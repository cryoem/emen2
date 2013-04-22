<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="query"  file="/pages/query"  />

<%
projects = DB.view(DB.record.findbyrectype("project"))
microscopes = DB.view(DB.record.findbyrectype("microscope"))
recorddefs = DB.recorddef.get(DB.recorddef.names())
users = DB.user.get(DB.user.names())

worksheets = {} # DB.view(DB.record.findbyrectype("grid_imaging"))

%>

<h1>Query</h1>

<table class="e2l-kv">

	<p>Project:
		<select>
			<option></option>
			% for k,v in sorted(projects.items(), key=lambda x:x[1].lower()):
				<option value="${k}">${v}</option>
			% endfor
		</select>
	</p>
	
	<p>Instrument:
		<select>
			<option></option>
			% for k,v in sorted(microscopes.items(), key=lambda x:x[1].lower()):
				<option value="${k}">${v}</option>
			% endfor
		</select>	
	</p>
	
	<p>Record type:
		<select>
			<option></option>
			% for k in sorted(recorddefs, key=lambda x:x.desc_short.lower()):
				<option value="${k.name}">${k.desc_short}</option>
			% endfor
		</select>
	</p>
	
	<p>NanoPEAS Worksheet:
		<select>
			<option></option>
			% for k,v in sorted(worksheets.items(), key=lambda x:x[1].lower()):
			<option value="${k}">${v}</option>
			% endfor
		</select>
	</p>
	
	<p>Created by:
		<select>
			<option></option>
			% for k in sorted(users, key=lambda x:x.getdisplayname(lnf=True).lower()):
				<option value="${k.name}">${k.getdisplayname(lnf=True)}</option>
			% endfor
		</select>		
	</p>
	
	<p>Date: <input type="text" /> to <input type="text" /></p>

</table>

<br /><br />

${query.table(q)}

