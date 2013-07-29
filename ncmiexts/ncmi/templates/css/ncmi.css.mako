/* colors */

body {
    background:#ccc;
}
#container {
    width:1020px;
}
#alert,
.precontent
{
    background:none;
}
ul.nav, 
ul.nav ul
{
    border:none;
}
ul.nav.shaded > li {
    padding-top:0px;
}
ul.shaded.nav {
    border:none;
    background:#446699;
}
ul.shaded.nav a {
    color:white;
}
ul.nav.shaded li:hover,
ul.nav.shaded li ul li
{
    background:#AACCFF;
}
#title {
    border:none
}

#buttons_main {
}
.button_main {
    border-top:solid 1px white;
}
.button_main_active {
    outline:solid 1px white;
    border-left:solid 1px #ccc;
    border-right:solid 1px #ccc;
    border-top:solid 1px #ccc;
}
#buttons_map {
    display:none
}

.editbar {
    border-top:solid 1px #ccc;
    margin-left:-10px;
    margin-right:-10px;
}

<%def name="mimetype()">text/css</%def>

<%!
public = True
headers = {
    'Cache-Control': 'max-age=86400',
    'Content-Type': 'text/css'
}
%>


