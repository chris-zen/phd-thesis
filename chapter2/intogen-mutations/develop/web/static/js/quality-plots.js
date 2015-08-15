// Defined in the html inside an script tag:
// var quality_data = ...

var zu = function(value) { return value != 0 ? value : undefined; };

function hist_size(data) {
	if (data == undefined || data.length == 0)
		return 0;
	return data[data.length - 1][0];
}

function hist1(data, max) {
	if (data.length == 0)
		return [];
	if (max === undefined)
		max = hist_size(data);
	hdata = Array.apply(null, new Array(max)).map(Number.prototype.valueOf, 0.0);
	for (var i = 0; i < Math.min(max, data.length); i++) {
		var x = data[i][0];
		if (x < max)
			hdata[x] = data[i][1];
	}
	return hdata;
}

function hist(data, max, n) {
	if (data.length == 0)
		return [];
	if (max === undefined)
		max = hist_size(data);
	var bin_width = max / n;
	var bin_max = Array.apply(null, new Array(n)).map(Number.prototype.valueOf, 0.0);
	var x = bin_width;
	for (var i = 0; i < n; i++) {
		bin_max[i] = x;
		x += bin_width;
	}
	var hdata = Array.apply(null, new Array(n)).map(Number.prototype.valueOf, 0.0);
	for (var i = 0; i < Math.min(max, data.length); i++) {
		var x = data[i][0];
		if (x < max) {
			var y = data[i][1];
			var j = 0;
			while (x > bin_max[j]) j++;
			if (j < n)
				hdata[j] += y;
		}
	}
	return hdata;
}

function search(array, callback, offset) {
	var size = array.length;

	offset = offset || 0;
	if (offset >= size || offset <= -size) {
		return -1;
	} else if (offset < 0) {
		offset = size - offset;
	}

	while (offset < size) {
	  if (callback(array[offset], offset, array)) {
		return offset;
	  }
	  ++offset;
	}
	return -1;
}

(function ( $ ) {

	$.fn.plot = function(options) {
		var opts = $.extend({
			width: 360,
			height: 340
		}, options);

		this.addClass("qc-figure").outerWidth(opts.width).outerHeight(opts.height);

		var header = $("<div></div>").addClass("qc-figure-header").appendTo(this);

		var plot = $("<div></div>").addClass("qc-plot").appendTo(this);

		plot.height(this.height() - header.outerHeight());

		if (opts.data !== undefined) {
			try {
				plot.jqplot(opts.data, opts.options || {});
			}
			catch (err) {
			}
		}

		return this;
	};

	$.fn.table = function(data, options) {
		/*
		* Data: [ [cell, cell, cell], [...], ...]
		*
		* Cell: number or "" or { ... }
		*
		* class: "" or ["", "", ...]
		* css: {"propName" : "value", ...}
		* rowspan, colspan: n
		* header: true or false: whether to use <td> or <th>
		* data
		*
		* Options: { ... }
		*
		* width: px or "1.2em"
		* height: px or "1.2em"
		* class: "" or ["", "", ...]
		* css: {"propName" : "value", ...}
		* colDefaults: {} or [{}, {}, ...]
		* rowDefaults: {} or [{}, {}, ...]
		* cellDecorator: function(row, column, cell) { ... }
		**/

		var opts = $.extend({
			width: 360,
			height: 340,
			rowDefaults: [],
			colDefaults: []
		}, options);

		this.addClass("qc-figure").outerWidth(opts.width).outerHeight(opts.height);

		var table = $("<table></table>").addClass("table").appendTo(this);

		if (opts["class"] !== undefined)
			table.addClass(opts["class"]);

		if (opts.css !== undefined)
			table.css(opts.css);

		for (var ri = 0; ri < data.length; ri++) {
			var rowData = data[ri];
			var row = $("<tr></tr>").appendTo(table);
			if (! $.isArray(rowData))
				rowData = [rowData];

			var rowDefaults = $.isPlainObject(opts.rowDefaults) ? opts.rowDefaults : opts.rowDefaults[ri];

			for (var ci = 0; ci < rowData.length; ci++) {
				var cell = rowData[ci];
				if (! $.isPlainObject(cell))
					cell = {data: cell};

				var colDefaults = $.isPlainObject(opts.colDefaults) ? opts.colDefaults : opts.colDefaults[ci];
				if (colDefaults !== undefined)
					cell = $.extend({}, colDefaults, cell);

				if (rowDefaults !== undefined)
					cell = $.extend({}, rowDefaults, cell);

				if ($.isFunction(opts.cellDecorator))
					cell = opts.cellDecorator(ri, ci, cell);

				var col;
				if (cell.header === true)
					col = $("<th></th>");
				else
					col = $("<td></td>");

				if (cell.colspan != undefined)
					col.attr("colspan", cell.colspan);

				if (cell.rowspan != undefined)
					col.attr("rowspan", cell.rowspan);

				if (cell["class"] !== undefined)
					col.addClass(cell["class"]);

				if (cell.css !== undefined)
					col.css(cell.css);

				if (cell.data !== undefined)
					col.html(cell.data);

				col.appendTo(row);
			}
		}

		return this;
	};

}( jQuery ));

function plot_variants(data) {
	if (data === undefined)
		return;

	// For each data source
	for (var i = 0; i < data.length; i++) {
		//var source = data[i][0];
		var counts = data[i][1];

		// Plot passed and lost variants bar plot

		var d1 = [
				counts.source_passed,
				counts.parser_passed,
				counts.liftover_passed,
				counts.vep_passed];

		var d2 = [0,
				counts.parser_lost,
				counts.liftover_lost,
				counts.vep_lost];

		$("#variants-counts-" + i).plot({
			data: [ d1, d2 ],
			options: {
				title: "Mutations count by stage",
				seriesDefaults: {
					renderer: $.jqplot.BarRenderer,
					rendererOptions: { fillToZero: true },
					shadow: false,
					pointLabels: {show: true, hideZeros: true}
				},
				seriesColors: ["#7AB300", "#CC1616"],
				stackSeries: true,
				axesDefaults: {
					labelRenderer: $.jqplot.CanvasAxisLabelRenderer
				},
				axes: {
					xaxis: {
						renderer: $.jqplot.CategoryAxisRenderer,
						ticks: ["Source", "Parser", "LiftOver", "VEP"]
					},
					yaxis: { label: "Number of mutations" }
				}
			}
		});

		var d3 = [
			["", "Passed", "Discarded"],
			["Source", counts.source_passed, ""],
			["Parser", counts.parser_passed, counts.parser_lost],
			["LiftOver", counts.liftover_passed, counts.liftover_lost],
			["VEP", counts.vep_passed, counts.vep_lost],
			["Total", "", counts.total_lost]];

		$("#variants-counts-table").table(d3, {
			"class" : "table-bordered table-hover table-condensed",
			css: {"text-align" : "right"},
			colDefaults: [{ header: true}],
			rowDefaults: [{ header: true}],
			cellDecorator: function(row, column, cell) {
				if (row > 0 && column == 2 && $.isNumeric(cell.data) && cell.data > 0)
					$.extend(cell, { "class" : "danger" });
				return cell;
			}
		});
	}
}

function plot_oncodrivefm(data) {
	if (data === undefined)
		return;

	var genes_count = [
		data.source.genes_count,
		data.selected.genes_count,
		data.filter.genes_count,
		data.threshold.genes_count];
	var genes_lost_count = [0,
		data.selected.genes_lost_count,
		data.filter.genes_lost_count,
		data.threshold.genes_lost_count];

	var tooltipContentEditor = function(str, series, point) {
		return (100.0 * genes_count[point] / data.source.genes_count).toFixed(1) + " %";
	};

	$("#ofm-genes").plot( {
		data: [ genes_count, genes_lost_count ],
		options: {
			title: "Genes count by stage",
			seriesDefaults: {
				renderer: $.jqplot.BarRenderer,
				rendererOptions: { fillToZero: true },
				shadow: false,
				pointLabels: {show: true, hideZeros: true}
			},
			seriesColors: ["#7AB300", "#CC1616"],
			stackSeries: true,
			axesDefaults: {
				labelRenderer: $.jqplot.CanvasAxisLabelRenderer
			},
			axes: {
				xaxis: {
					renderer: $.jqplot.CategoryAxisRenderer,
					ticks: ["Source", "Selected", "Filter", "Threshold"]
				},
				yaxis: { label: "Number of genes" }
			},
			highlighter: {
				show: true,
				showMarker: false,
				tooltipContentEditor: tooltipContentEditor
			}
		}
	});

	tooltipContentEditor = function(str, series, point) {
		return (100.0 * samples_count[point] / data.source.samples_count).toFixed(1) + " %";
	};

	var samples_count = [
		data.source.samples_count,
		data.selected.samples_count,
		data.filter.samples_count,
		data.threshold.samples_count];
	var samples_lost_count = [0,
		data.selected.samples_lost_count,
		data.filter.samples_lost_count,
		data.threshold.samples_lost_count];

	$("#ofm-samples").plot( {
		data: [ samples_count, samples_lost_count ],
		options: {
			title: "Samples count by stage",
			seriesDefaults: {
				renderer: $.jqplot.BarRenderer,
				rendererOptions: { fillToZero: true },
				shadow: false,
				pointLabels: {show: true, hideZeros: true}
			},
			seriesColors: ["#7AB300", "#CC1616"],
			stackSeries: true,
			axesDefaults: {
				labelRenderer: $.jqplot.CanvasAxisLabelRenderer
			},
			axes: {
				xaxis: {
					renderer: $.jqplot.CategoryAxisRenderer,
					ticks: ["Source", "Selected", "Filter", "Threshold"]
				},
				yaxis: { label: "Number of samples" }
			},
			highlighter: {
				show: true,
				showMarker: false,
				tooltipContentEditor: tooltipContentEditor
			}
		}
	});

	var table_data = [
		[{rowspan: 2}, {colspan: 2, data: "Genes"}, {colspan: 2, data: "Samples"}],
		["Passed", "Discarded", "Passed", "Discarded"],
		["Source", data.source.genes_count, "", data.source.samples_count, ""],
		["Selected", data.selected.genes_count, data.selected.genes_lost_count, data.selected.samples_count, data.selected.samples_lost_count],
		["Filter", data.filter.genes_count, data.filter.genes_lost_count, data.filter.samples_count, data.filter.samples_lost_count],
		["Threshold<sup>*</sup>", data.threshold.genes_count, data.threshold.genes_lost_count, data.threshold.samples_count, data.threshold.samples_lost_count],
		["Total", "", data.source.genes_lost_count, "", data.source.samples_lost_count]];

	$("#ofm-counts-table").table(table_data, {
		"class" : "table-bordered table-hover table-condensed",
		css: {"text-align" : "right", "margin-bottom" : "8px"},
		colDefaults: [{ header: true}],
		rowDefaults: [{ header: true}, { header: true}],
		cellDecorator: function(row, column, cell) {
			if (row > 1 && (column == 2 || column == 4) && $.isNumeric(cell.data) && cell.data > 0)
				$.extend(cell, { "class" : "danger" });
			return cell;
		}
	}).append("<sup>*</sup> " + data.threshold.samples_threshold + " samples");

	if (data.threshold.genes_count > 0) {
		var len = search(data.filter.genes_sample_count, function(value) { return value < data.threshold.samples_threshold });
		var genes_sample_count = new Array(len);
		for (var i = 0; i < len; i++)
			genes_sample_count[i] = [i, data.filter.genes_sample_count[i]];

		var tooltipContentEditor = function(str, series, point) {
			return data.source.genes[data.filter.genes[point]] + ", " + data.filter.genes_sample_count[point] + " samples";
		};

		$("#ofm-genes-sample-count").plot( {
			width: 720,
			data: [	genes_sample_count ],
			options: {
				title: "Number of samples per gene (threshold = " + data.threshold.samples_threshold + ")",
				seriesDefaults: {
					//renderer: $.jqplot.BarRenderer,
					rendererOptions: {
						fillToZero: true
					},
					shadow: false,
					showMarker: { show: true, size: 1, lineWidth: 1 }
				},
				seriesColors: ["#0E608B"],
				axesDefaults: {
					pad: 0,
					labelRenderer: $.jqplot.CanvasAxisLabelRenderer
				},
				axes: {
					xaxis: {
						show: false,
						min: -1,
						max: len,
						tickOptions: {
							show: false,
							showGridline: false
						},
						//renderer: $.jqplot.CategoryAxisRenderer,
						label: "Genes"
					},
					yaxis: {
						min: 0,
						label: "Number of samples"
					}
				},
				highlighter: {
					show: true,
					sizeAdjust: 5,
					tooltipContentEditor: tooltipContentEditor
				},
				cursor: {
					show: false,
					tooltipLocation:'ne'
				}
			}
		});

		/*var points = new Array(data.results.sig_thresholds.length - 1);
		for (var i = 0; i < points.length; i++)
			points[i] = [data.results.sig_thresholds[i], data.results.sig_count[i]]*/

		var ticks = data.results.sig_thresholds.slice(0, data.results.sig_thresholds.length - 1).map(function(v){return v.toFixed(3);});

		tooltipContentEditor = function(str, series, point) {
			var v = data.results.sig_count[point];
			return (100.0 * v / data.threshold.genes_count).toFixed(1) + " % (" + v + " genes)";
		};

		var sig_counts = data.results.sig_count.slice(0, data.results.sig_count.length - 1);
		$("#ofm-sig-count").plot( {
			data: [ sig_counts ],
			options: {
				title: "Number of significant genes",
				seriesDefaults: {
					renderer: $.jqplot.BarRenderer,
					rendererOptions: {
						fillToZero: true,
						barMargin: 0
					},
					shadow: false,
					showMarker: false
				},
				axesDefaults: {
					labelRenderer: $.jqplot.CanvasAxisLabelRenderer,
					tickRenderer: $.jqplot.CanvasAxisTickRenderer ,
					tickOptions: {
					  angle: -90,
					  fontSize: '10pt'
					}
				},
				axes: {
					xaxis: {
						renderer: $.jqplot.CategoryAxisRenderer,
						ticks: ticks,
						label: "q-value threshold"
					},
					yaxis: {
						min: 0,
						label: "Number of genes"
					}
				},
				highlighter: {
					show: true,
					sizeAdjust: 7.5,
					showMarker: false,
					tooltipContentEditor: tooltipContentEditor
				}
			}
		});
	}
}

function plot_oncodriveclust(data) {
	if (data === undefined)
		return;

	var genes_count = [
		data.source.genes_count,
		data.synonymous.genes_count,
		data.selected.genes_count,
		data.filter.genes_count,
		data.threshold.genes_count];
	var genes_lost_count = [0, 0,
		data.selected.genes_lost_count,
		data.filter.genes_lost_count,
		data.threshold.genes_lost_count];

	var tooltipContentEditor = function(str, series, point) {
		var tooltip = (100.0 * genes_count[point] / data.source.genes_count).toFixed(1) + " %";
		if (point == 1)
			tooltip += " (ratio = " + data.synonymous.ratio.toFixed(3) + ")";
		return tooltip;
	};

	$("#oclust-genes").plot( {
		data: [ genes_count, genes_lost_count ],
		options: {
			title: "Genes count by stage",
			seriesDefaults: {
				renderer: $.jqplot.BarRenderer,
				rendererOptions: { fillToZero: true },
				shadow: false,
				pointLabels: {show: true, hideZeros: true}
			},
			seriesColors: ["#7AB300", "#CC1616"],
			stackSeries: true,
			axesDefaults: {
				labelRenderer: $.jqplot.CanvasAxisLabelRenderer
			},
			axes: {
				xaxis: {
					renderer: $.jqplot.CategoryAxisRenderer,
					ticks: ["Source", "Syn", "Selected", "Filter", "Threshold"]
				},
				yaxis: { label: "Number of genes" }
			},
			highlighter: {
				show: true,
				showMarker: false,
				tooltipContentEditor: tooltipContentEditor
			}
		}
	});

	var samples_count = [
		data.source.samples_count,
		data.selected.samples_count,
		data.filter.samples_count,
		data.threshold.samples_count];
	var samples_lost_count = [0,
		data.selected.samples_lost_count,
		data.filter.samples_lost_count,
		data.threshold.samples_lost_count];

	tooltipContentEditor = function(str, series, point) {
		return (100.0 * samples_count[point] / data.source.samples_count).toFixed(1) + " %";
	};

	$("#oclust-samples").plot( {
		data: [ samples_count, samples_lost_count ],
		options: {
			title: "Samples count by stage",
			seriesDefaults: {
				renderer: $.jqplot.BarRenderer,
				rendererOptions: { fillToZero: true },
				shadow: false,
				pointLabels: {show: true, hideZeros: true}
			},
			seriesColors: ["#7AB300", "#CC1616"],
			stackSeries: true,
			axesDefaults: {
				labelRenderer: $.jqplot.CanvasAxisLabelRenderer
			},
			axes: {
				xaxis: {
					renderer: $.jqplot.CategoryAxisRenderer,
					ticks: ["Source", "Selected", "Filter", "Threshold"]
				},
				yaxis: { label: "Number of samples" }
			},
			highlighter: {
				show: true,
				showMarker: false,
				tooltipContentEditor: tooltipContentEditor
			}
		}
	});

	var table_data = [
		[{rowspan: 2}, {colspan: 2, data: "Genes"}, {colspan: 2, data: "Samples"}],
		["Passed", "Discarded", "Passed", "Discarded"],
		["Source", data.source.genes_count, "", data.source.samples_count, ""],
		["Selected", data.selected.genes_count, data.selected.genes_lost_count, data.selected.samples_count, data.selected.samples_lost_count],
		["Filter", data.filter.genes_count, data.filter.genes_lost_count, data.filter.samples_count, data.filter.samples_lost_count],
		["Threshold<sup>*</sup>", data.threshold.genes_count, data.threshold.genes_lost_count, data.threshold.samples_count, data.threshold.samples_lost_count],
		["Total", "", data.source.genes_lost_count, "", data.source.samples_lost_count]];

	$("#oclust-counts-table").table(table_data, {
		"class" : "table-bordered table-hover table-condensed",
		css: {"text-align" : "right", "margin-bottom" : "8px"},
		colDefaults: [{ header: true}],
		rowDefaults: [{ header: true}, { header: true}],
		cellDecorator: function(row, column, cell) {
			if (row > 1 && (column == 2 || column == 4) && $.isNumeric(cell.data) && cell.data > 0)
				$.extend(cell, { "class" : "danger" });
			return cell;
		}
	}).append("<sup>*</sup> " + data.threshold.samples_threshold + " samples");

	if (data.threshold.genes_count > 0) {
		var len = search(data.filter.genes_sample_count, function(value) { return value < data.threshold.samples_threshold });
		var genes_sample_count = new Array(len > 0 ? len : 0);
		for (var i = 0; i < len; i++)
			genes_sample_count[i] = [i, data.filter.genes_sample_count[i]];

		tooltipContentEditor = function(str, series, point) {
			return data.source.genes[data.filter.genes[point]] + ", " + data.filter.genes_sample_count[point] + " samples";
		};

		$("#oclust-genes-sample-count").plot( {
			width: 720,
			data: [	genes_sample_count ],
			options: {
				title: "Number of samples per gene (threshold = " + data.threshold.samples_threshold + ")",
				seriesDefaults: {
					//renderer: $.jqplot.BarRenderer,
					rendererOptions: {
						fillToZero: true
					},
					shadow: false,
					showMarker: { show: true, size: 0.5 }
				},
				seriesColors: ["#0E608B"],
				axesDefaults: {
					pad: 0,
					labelRenderer: $.jqplot.CanvasAxisLabelRenderer
				},
				axes: {
					xaxis: {
						show: false,
						min: -1,
						max: len,
						tickOptions: {
							show: false,
							showGridline: false
						},
						//renderer: $.jqplot.CategoryAxisRenderer,
						label: "Genes"
					},
					yaxis: {
						min: 0,
						label: "Number of samples"
					}
				},
				highlighter: {
					show: true,
					sizeAdjust: 5,
					tooltipContentEditor: tooltipContentEditor
				},
				cursor: {
					show: false,
					tooltipLocation:'ne'
				}
			}
		});

		var ticks = data.results.sig_thresholds.slice(0, data.results.sig_thresholds.length - 1)
						.map(function(v) { return v.toFixed(3); });

		tooltipContentEditor = function(str, series, point) {
			var v = data.results.sig_count[point];
			return (100.0 * v / data.threshold.genes_count).toFixed(1) + " % (" + v + " genes)";
		};

		var sig_counts = data.results.sig_count.slice(0, data.results.sig_count.length - 1);
		$("#oclust-sig-count").plot( {
			data: [ sig_counts ],
			options: {
				title: "Number of significant genes",
				seriesDefaults: {
					renderer: $.jqplot.BarRenderer,
					rendererOptions: {
						fillToZero: true,
						barMargin: 0
					},
					shadow: false,
					showMarker: false
				},
				axesDefaults: {
					labelRenderer: $.jqplot.CanvasAxisLabelRenderer,
					tickRenderer: $.jqplot.CanvasAxisTickRenderer ,
					tickOptions: {
					  angle: -90,
					  fontSize: '10pt'
					}
				},
				axes: {
					xaxis: {
						renderer: $.jqplot.CategoryAxisRenderer,
						ticks: ticks,
						label: "q-value threshold"
					},
					yaxis: { label: "Number of genes" }
				},
				highlighter: {
					show: true,
					sizeAdjust: 7.5,
					showMarker: false,
					tooltipContentEditor: tooltipContentEditor
				}
			}
		});
	}
}

function updateQualityPlots(quality) {
	if (quality === undefined || quality === null)
		return;

	plot_variants(quality.variants);
	plot_oncodrivefm(quality.oncodrivefm);
	plot_oncodriveclust(quality.oncodriveclust);
}
