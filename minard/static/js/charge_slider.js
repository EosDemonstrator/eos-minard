$(function() {
    a = parseInt(document.getElementById("lowerCharge").innerText)
    b = parseInt(document.getElementById("upperCharge").innerText)
	$("#chargeSlider").slider({
		range: true,
		min: a,
		max: b,
		values: [a,b],
		slide: function(event,ui) {
			updateChargeLabels(ui.values[0], ui.values[1]);
		        updateSliderGradient(ui.values[0], ui.values[1]);
                }
	});
	updateChargeLabels(a,b);
        updateSliderGradient(a,b);
});

function updateChargeLabels(lower, upper) {
    $("#lowerCharge").text(lower);
    $("#upperCharge").text(upper);
}

/*
function updateSliderGradient(lower, upper) {
    let max=b-a;
    upper = upper-lower;
    lower = lower-(-10000);
    let gradient = `linear-gradient(to right,
        blue 0%,
        blue ${lower/max*100}%,
        cyan ${lower/max*100}%, 
        green ${(lower+(upper-lower)/4)/max*100}%,
        yellow ${(lower+3*(upper-lower)/4)/max*100}%,
        red ${upper/max*100}%,
        red 100%)`;
    $("#chargeSlider .ui-slider").css("background", gradient);
    $("#chargeSlider").css("background", gradient);
}*/

function updateSliderGradient(lower, upper) {
    let max=b-a;
    upper = upper-lower;
    lower = lower-(-10000); // -10000 is the initial lower limit of the charge slider
    let gradient = `linear-gradient(to right,
        #440154 0%,
        #440154 ${lower/max*100}%,
        #3B518B ${lower/max*100}%, 
        #21918C ${(lower+(upper-lower)/4)/max*100}%,
        #5EC962 ${(lower+3*(upper-lower)/4)/max*100}%,
        #FDE725 ${upper/max*100}%,
        #FDE725 100%)`;
    $("#chargeSlider .ui-slider").css("background", gradient);
    $("#chargeSlider").css("background", gradient);
}