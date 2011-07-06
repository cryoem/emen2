<%inherit file="/page" />

<script type="text/javascript">
	$(function() {
		$(".boxer").Boxer({});
	});
</script>

<div class="boxer" data-bdo="${bdo.name}" data-name="${rec.name}" />
