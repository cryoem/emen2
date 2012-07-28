<%inherit file="/page" />

<%block name="js_ready">
    ${parent.js_ready}
    $(".boxer").Boxer({});
</%block>

<div class="boxer" data-bdo="${bdo.name}" data-name="${rec.name}" />
