display_part_fields = function(sel) {
	var fields = $(sel).parent().parent().next().nextAll();
	var cond = "div:has(:input.part_fields" + sel.value + ")";
	fields.filter(cond).show();
	fields.not(cond).hide();
};

$(document).ready(function() {
	for (i = 0; true; i++) {
		var order = $("#id_parts-" + i + "-order");
		if (!order.is(":input")) break;
		order.val(i + 1);
		var sel = $("#id_parts-" + i + "-type");
		display_part_fields(sel.get(0));
	}
});


