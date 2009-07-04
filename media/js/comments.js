$("#id_url").focus(function () { $("#id_comment").focus(); }).parent().parent().css("text-indent", "-9001em").find("th").css("text-align", "left");

$(".comments span > a").click(function () {
	var form = $("#comment_form").clone();
	form.find("textarea").val("");
	form.find("#id_url").parent().parent().hide();
	form.find("#id_parent").val(this.href.match(/reply\/(\d+)\//)[1]);
	var box = $('<div><h3>Reply to this post</h3></div>');
	box.append(form);
	box.hide();
	$(this).parent().parent().append(box);
	$(this).fadeOut();
	box.slideDown("fast");
	form.find("textarea").focus();
	form.validate(form_rules);
	return false;
});

var form_rules = {rules: {comment: "required", email: "email"}};
$("#comment_form").validate(form_rules);
