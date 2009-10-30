if (!window.google || !google.gears) {
	location.href = "http://gears.google.com/?action=install&message=Drag and drop support requires Gears.&return=" + location.href;
}
var firefox = navigator.userAgent.match(/Firefox/);

var not_garbage = null;

function upload(url, blob, callback, handle_error) {
	var req = google.gears.factory.create('beta.httprequest');
	req.open('POST', url);
	req.upload.onprogress = function(event) {
		//document.title = event.loaded + "/" + event.total + " bytes";
	};
	req.onreadystatechange = function() {
		if (req.readyState == 4) {
			if (req.status >= 200 && req.status < 300)
				callback("NICE."); //req.responseText);
			else
				handle_error(req.status, req.statusText);
		}
	};
	req.send(blob);
	return req;
}

function dropped(jevent) {
	var event = jevent.originalEvent;
	//alert(event.dataTransfer.types);
	//alert(event.dataTransfer.files);
	var desktop = google.gears.factory.create('beta.desktop');
	var data = desktop.getDragData(event, "application/x-gears-files");
	var unknowns = [];
	for (var i in data.files) {
		var file = data.files[i];
		if (file.name.match(/(.png|.jpg|.gif)$/i)) {
			var canvas = google.gears.factory.create('beta.canvas');
			canvas.decode(file.blob);
			//meta = ": " + canvas.width + "x" + canvas.height;
			//canvas.resize(500, 500, "bilinear");
		}
		else if (file.name.match(/.doc$/i)) {
			not_garbage = upload('design/convert', file.blob,
			function (info) {
				alert(info);
			},
			function (httpcode, statusText) {
				alert("Error trying to upload .doc:\n"
					+ httpcode + ": " + statusText);
			});
		}
		else {
			unknowns.push(file.name);
		}
	}
	$(event.target).removeClass('dragover');
	if (unknowns.length)
		alert("Don't know how to handle " + unknowns);
	return cancel(event);
}

function cancel(event) {
	if (event.preventDefault)
		event.preventDefault();
	return false;
}

function denydrop(event) {
	event.originalEvent.dataTransfer.dropEffect = 'none';
	return cancel(event);
}
/*$(nondroppable)
	.bind("dragover", denydrop)
	.bind("dragenter", cancel)
	.bind("drop", cancel);
$("#droptarget")*/

$(document).ready(function() {
	var workspace = $("section.copy");
	var attrs = 'contenteditable="true"'; // draggable="true"';
	$(document)
		.bind("dragover", function(event) {
			event.originalEvent.dataTransfer.dropEffect = 'copy';
			return cancel(event);
		})
		.bind("dragenter", function(event) {
			$(event.target).addClass('dragover');
			return cancel(event);
		})
		.bind("dragleave", function (event) {
			$(event.target).removeClass('dragover');
			return cancel(event);
		})
		.bind("drop", dropped);

	$("#addcopy").click(function (event) {
		workspace.append('<p ' + attrs + '></p>');
	});
});


