<%inherit file="/page" />

<h1>e2fhstat</h1>

<form enctype="multipart/form-data" method="post">

<table>
	<tr>
		<td>Isosurface Threshold:</td>
		<td><input type="text" name="threshold" value="10" /></td>
	</tr>
	<tr>
		<td>Transforms:</td>
		<td><input type="text" name="transforms" value="1000" /></td>
	</tr>
	<tr>
		<td>Map:</td>
		<td><input type="file" name="map" /></td>
	</tr>
	<tr>		
		<td>PDB model:</td>
		<td><input type="file" name="pdb" /></td>
	</tr>
	<tr>
		<td />
		<td><input type="submit" value="Submit" /></td>
	</tr>
</table>