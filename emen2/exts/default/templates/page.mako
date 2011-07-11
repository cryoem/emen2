<%inherit file="/base" />

<%self:header />

<%self:alert />

<%self:precontent />

<%self:tabs />

<div id="content">
	${next.body()}
</div>

<%self:footer />
