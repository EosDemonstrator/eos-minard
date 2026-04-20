$(function() {
	$("#timeSlider").slider({
		range: true,
		min: 0,
		max: 1440,
		values: [0,1440],
		slide: function(event,ui) {
			updateTimeLabels(ui.values[0], ui.values[1]);
		}
	});
	updateTimeLabels(0,1440);
});

function updateTimeLabels(start, end) {
    const startHours = Math.floor(start / 60);
    const startMins = start % 60;
    const startTime = `${String(startHours).padStart(2, '0')}:${String(startMins).padStart(2, '0')}`;
    $("#startLabel").text(startTime);

    const endHours = Math.floor(end / 60);
    const endMins = end % 60;
    const endTime = `${String(endHours).padStart(2, '0')}:${String(endMins).padStart(2, '0')}`;
    $("#endLabel").text(endTime);
}

function exportTimed() {
    const values = $("#timeSlider").slider("values");
    const startHours = Math.floor(values[0] / 60);
    const startMins = values[0] % 60;
    const startTime = `${String(startHours).padStart(2, '0')}:${String(startMins).padStart(2, '0')}`;

    const endHours = Math.floor(values[1] / 60);
    const endMins = values[1] % 60;
    const endTime = `${String(endHours).padStart(2, '0')}:${String(endMins).padStart(2, '0')}`;

    alert(`Start Time: ${startTime} UTC\nEnd Time: ${endTime} U`);
}
