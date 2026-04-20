$(function() {
	$("#sampleSlider").slider({
		range: true,
		min: 0,
		max: 100,
		values: [0,100],
		slide: function(event,ui) {
			updateSampleLabels(ui.values[0], ui.values[1]);
		}
	});
	updateSampleLabels(0,100);
});

function updateSampleLabels(lower, upper) {
    $("#lowerTime").text(lower);

    $("#upperTime").text(upper);
}
