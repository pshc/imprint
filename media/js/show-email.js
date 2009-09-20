jQuery(document).ready(function() {
	var email_link = $("a[id^=email]");
	email_link.click(function (event) {
		email_link.unbind("click");
		email_link.text("(...)");
		$.get(email_link.attr("id"), {}, function(data, textStatus) {
			if (textStatus == "success") {
				email_link.attr("href", "mailto:"+data);
				email_link.text(data);
			}
			else {
				email_link.text("(Couldn't retrieve email)");
			}
		}, "text");
		return false;
	});
});
