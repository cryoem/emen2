<html>
<head>
	<title>Redirect</title>
	<meta http-equiv="refresh" content="0; url=${HEADERS.get('Location')}">
</head>

<body>

<h1>Redirect</h1>

<p>Please <a href="${HEADERS.get('Location')}">click here</a> if the page does not automatically redirect.</p>

</body></html>