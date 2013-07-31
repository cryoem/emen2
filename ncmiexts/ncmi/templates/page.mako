<%inherit file="/base" />

<%block name="css_inline">

html {
  background:#eee;
}
body {
  margin-left:auto;
  margin-right:auto;
  width:95%; 
}

#ncmi-title {
  margin:0px;
  padding:0px;
  background:#fff;
  border-bottom:solid 2px #ccc;
}
#ncmi-title h1 {
  margin:0px;
  padding:0px;
  border:none;
}
  

#ncmi-nav {
  list-style:none;
  height:35px;
  background:#eef;
}
#ncmi-nav > li {
    padding:10px;
    float: left;
    position:relative;
}
#ncmi-nav > li > ul {
    width: 186px;
    z-index: 1000;
    list-style:none;
    padding:0px;
    background:#eef;
    display: none;
    left: 0;
    position: absolute;
    top: 35px;
    z-index: 1000;
}
#ncmi-nav > li > ul > li {
    padding:10px;
}
#ncmi-nav > li:hover > ul {
    display: block;
    z-index: 1000;
}

#ncmi-content {
  background:white;
  padding:20px;
  padding-left:35px;


}

#ncmi-footer {
  background:#eef;
  font-size:.85em;History is off
  padding-bottom:10px;
}

#logo{
  float:left;
  padding-right:10px;
  height:65px

}

.ncmi-person {
  margin:10px;
}
.ncmi-person img {
	float:left;
  width:128px;
  margin:10px;
}
.ncmi-person p {
  padding:10px;
}



</%block>


<div id="ncmi-title">


  <h1><img src="http://ncmi.bcm.edu/ncmi/images/title2.jpg" alt="National Center for Macromolecular Imaging" /></h1>

<ul id="ncmi-nav" class="ncmi-test">
  <li><a href="/about">About</a>
    <ul>
      <li><a href="/about/maps">Maps</a></li>
      <li><a href="/about/mission">Mission Statement</a></li>
      <li><a href="/about/contact">Contact NCMI</a></li>
    </ul>
  </li>

  <li><a href="/people">People</a>
    <ul>
      <li><a href="/people/current">Current faculty &amp; staff</a></li>
      <li><a href="">Alumni</a></li>
    </ul>
  </li>
  
  <li><a href="">Facilities</a>
    <ul>
      <li><a href="">Microscopes</a></li>
      <li><a href="">Support Equipment</a></li>
      <li><a href="">Cluster Resources</a></li>
    </ul>  
  </li>
  
  <li><a href="">Downloads</a>
    <ul>
      <li><a href="">EMAN1</a></li>
      <li><a href="">EMAN2</a></li>
      <li><a href="">Other Software</a></li>
      <li><a href="">Public Data Access</a></li>
      <li><a href="">Movies</a></li>
    </ul>    
  </li>
  
  <li><a href="">Publications</a>
    <ul>
      <li><a href="">Stuff</a></li>
    </ul>    
  </li>
  
  <li><a href="">Events</a>
    <ul>
      <li><a href="">Stuff</a></li>
    </ul>    
  </li>
  
  <li><a href="">Collaborations</a>
    <ul>
      <li><a href="">Stuff</a></li>
    </ul>
    </li>
  </ul>

</div>
  

<%block name="precontent">
</%block>


<div id="ncmi-content">

${next.body()}

</div>


<div id="ncmi-footer">

<a href="http://www.bcm.edu"><img src="http://ncmi.bcm.edu/ncmi/images/bcmLogo" id="logo" alt="Baylor College of Medicine" /></a><br>
<a href="http://www.bcm.edu/">BCM Home</a> | 
<a href="http://intranet.bcm.edu/">BCM Intranet</a> | 
<a href="http://www.bcm.edu/about/privacy/notices.cfm">Privacy Notices</a> | 
<a href="http://www.bcm.edu/about/contact.cfm">Contact BCM</a> | 
<a href="http://www.bcm.edu/sitemap.cfm">BCM Site Map</a><br />
<a href="http://ncmi.bcm.tmc.edu/ncmi">National Center for Macromolecular Imaging</a><br> 
Room N420, 1 Baylor Plaza, Houston, TX 77030 | Phone: 713-798-6989 | Fax: 713-798-162


</div>