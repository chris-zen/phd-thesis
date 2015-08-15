var interval = getInterval();
var timeout = null;
var updatePage = null;

function getInterval() {
	var interval = location.hash.substring(1);
	if (interval.length == 0) {
		interval = 2000;
	}
	return interval;
}

function getNextInterval() {
	var next_interval = Math.round(interval * 1.2);
	if (next_interval > 60000) {
		next_interval = 60000;
	}
	return next_interval;
}

function ajaxUpdate(args) {
	var url = args.url;
	if (url === undefined)
		url = $(args.selector).data("url");

	if (args.reload_on_error === undefined)
		args.reload_on_error = true;

	$.ajax({
		url: url, cache: false
	}).done(function(html) {
		$(args.selector).html(html);
		if (args.success !== undefined)
			args.success();
	}).fail(function(jqXHR, textStatus) {
		if (args.failed !== undefined)
			args.failed();

		if (args.reload_on_error)
			location.reload(true);
	});
}

function handleTimeout(update_interval) {
	if (update_interval === undefined)
		update_interval = true;

	if (location.hash != interval)
		interval = getInterval();

	if (update_interval)
		location.hash = getNextInterval();

	updatePage("timer");
}

function updateInterval(new_interval) {
	interval = new_interval;
	window.clearTimeout(timeout);
	timeout = window.setTimeout(handleTimeout, interval);
	location.hash = interval;
}

function init(args) {

	updatePage = args.updatePage;
	if (args.afterRemove === undefined)
		args.afterRemove = updatePage;

	$(window).on("hashchange", function () {
		updateInterval(getInterval());
	});

	$(document).ready(function() {
		timeout = window.setTimeout(handleTimeout, interval);

		$(document).on("click", "#refresh-btn", function(event) {
			event.preventDefault();
			updatePage("button");
		});

		$("#confirm-remove-btn").click(function() {
			//event.preventDefault();
			var url = $(this).data("url");
			$.post(url, function(resp) {
				if (resp.status !== "ok")
					window.location = url;
				updateInterval(1000);
				args.afterRemove();
			}).fail(function() {
				window.location = $("#confirm-remove-btn").data("url");
			});
		});
	});

	$(document).on("click", ".remove-btn", function() {
		var name = $(this).data("case");
		var url = $(this).data("url");
		$("#confirm-remove-btn").data("url", url);
		$("#confirm-remove-case-name").text(name);
	});
}