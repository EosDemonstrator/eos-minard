var STEP, SOURCE, METHOD, SCALE, CRATE_WINDOW;

// js from detector.js
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
function linspace(min, max, N) {
    var a = [];
    for (var i=0; i < N; i++) {
        a[i] = min + (max-min)*i/(N-1);
    }
    return a;
}

var xsnoed1 = ["#4876ff","#32cd32","#ffff00","#ffa500","#ff0000"],
    xsnoed2 = ["#3a5fcd","#2e8b57","#cd9b1d","#ffa500","#ff0000"];

var color_scales1 = {};
color_scales1.xsnoed1 = xsnoed1;
color_scales1.xsnoed2 = xsnoed2;
for (var key in colorbrewer) {
    color_scales1[key] = colorbrewer[key][3];
}

var color_scales = d3.entries(color_scales1);


function change_color_scale() {
    chart.color_scale().range(color_scales[this.selectedIndex].value);
    redraw();
}

var color_menu = d3.select("#color-scale-menu")
    .on("change", change_color_scale);

color_menu.selectAll("option")
    .data(color_scales)
  .enter().append("option")
    .text(function(d) { return d.key; });

color_menu.property("selectedIndex", 12);

var color_scale = d3.scale.linear()
    .domain(linspace(0,1e-3,5))
    .range(color_scales[12].value);

var chart = histogram()
    .on_scale_change(redraw)
    .color_scale(color_scale)
    .bins(50)
    .domain([0,0.01]);

var crate = crate_view().caption(false).scale(color_scale);

var element = $('#hero');
var width   = element.width();
var height  = width/2.0;

var svg = d3.select('#hero').append("svg")
    .attr("width", width)
    .attr("height", height);

var options = [
{name: "Aitoff", projection: d3.geo.aitoff()},
{name: "Albers", projection: d3.geo.albers().scale(145).parallels([20, 50])},
{name: "August", projection: d3.geo.august().scale(60)},
{name: "Baker", projection: d3.geo.baker().scale(100)},
{name: "Boggs", projection: d3.geo.boggs()},
{name: "Bonne", projection: d3.geo.bonne().scale(120)},
{name: "Bromley", projection: d3.geo.bromley()},
{name: "Collignon", projection: d3.geo.collignon().scale(93)},
{name: "Craster Parabolic", projection: d3.geo.craster()},
{name: "Eckert I", projection: d3.geo.eckert1().scale(165)},
{name: "Eckert II", projection: d3.geo.eckert2().scale(165)},
{name: "Eckert III", projection: d3.geo.eckert3().scale(180)},
{name: "Eckert IV", projection: d3.geo.eckert4().scale(180)},
{name: "Eckert V", projection: d3.geo.eckert5().scale(170)},
{name: "Eckert VI", projection: d3.geo.eckert6().scale(170)},
{name: "Eisenlohr", projection: d3.geo.eisenlohr().scale(60)},
{name: "Equirectangular (Plate Carrée)", projection: d3.geo.equirectangular()},
{name: "Hammer", projection: d3.geo.hammer().scale(165)},
{name: "Hill", projection: d3.geo.hill()},
{name: "Goode Homolosine", projection: d3.geo.homolosine()},
{name: "Kavrayskiy VII", projection: d3.geo.kavrayskiy7()},
{name: "Lambert cylindrical equal-area", projection: d3.geo.cylindricalEqualArea()},
{name: "Lagrange", projection: d3.geo.lagrange().scale(120)},
{name: "Larrivée", projection: d3.geo.larrivee().scale(95)},
{name: "Laskowski", projection: d3.geo.laskowski().scale(120)},
{name: "Loximuthal", projection: d3.geo.loximuthal()},
{name: "Mercator", projection: d3.geo.mercator().scale(490 / 2 / Math.PI)},
{name: "Miller", projection: d3.geo.miller().scale(100)},
{name: "McBryde–Thomas Flat-Polar Parabolic", projection: d3.geo.mtFlatPolarParabolic()},
{name: "McBryde–Thomas Flat-Polar Quartic", projection: d3.geo.mtFlatPolarQuartic()},
{name: "McBryde–Thomas Flat-Polar Sinusoidal", projection: d3.geo.mtFlatPolarSinusoidal()},
{name: "Mollweide", projection: d3.geo.mollweide().scale(165)},
{name: "Natural Earth", projection: d3.geo.naturalEarth()},
{name: "Nell–Hammer", projection: d3.geo.nellHammer()},
{name: "Polyconic", projection: d3.geo.polyconic().scale(100)},
{name: "Robinson", projection: d3.geo.robinson()},
{name: "Sinusoidal", projection: d3.geo.sinusoidal()},
{name: "Sinu-Mollweide", projection: d3.geo.sinuMollweide()},
{name: "van der Grinten", projection: d3.geo.vanDerGrinten().scale(75)},
{name: "van der Grinten IV", projection: d3.geo.vanDerGrinten4().scale(120)},
{name: "Wagner IV", projection: d3.geo.wagner4()},
{name: "Wagner VI", projection: d3.geo.wagner6()},
{name: "Wagner VII", projection: d3.geo.wagner7()},
{name: "Winkel Tripel", projection: d3.geo.winkel3()}
];

options.forEach(function(o) {
    o.projection.rotate([0, 0]).center([0, 0])
        .scale((width + 1) / 2 / Math.PI)
        .translate([width / 2, height / 2])
        .precision(0.1);
    });

var coords = [];
for (var i=0; i < pmtinfo['x'].length; i++) {
    var x = pmtinfo.x[i],
        y = pmtinfo.y[i],
        z = pmtinfo.z[i];

    var r = Math.sqrt(x*x + y*y + z*z);

    var theta = -(Math.acos(z/r)*180.0/Math.PI - 90.0);
    var phi   = Math.atan2(y,x)*180.0/Math.PI;

    coords[i] = [phi, theta];
}

var projection = options[16].projection;

var menu = d3.select("#projection-menu")
    .on("change", function() { update_projection(options[this.selectedIndex]); });

menu.selectAll("option")
    .data(options)
  .enter().append("option")
    .text(function(d) { return d.name; });

menu.property("selectedIndex", 16);

function update_projection(option) {
    svg.selectAll("path").transition()
        .duration(1000)
        .attrTween("d", projectionTween(projection, projection = option.projection));

    projection = option.projection;

    for (var i=0; i < coords.length; i++)
        pos[i] = projection(coords[i]);

    svg.selectAll('circle')
        .transition().duration(1000)
        .attr('cx',function(d, i) { return pos[i][0]; })
        .attr('cy',function(d, i) { return pos[i][1]; });
}

function projectionTween(projection0, projection1) {
    return function(d) {
        var t = 0;

        var projection = d3.geo.projection(project)
            .scale(1)
            .translate([width / 2, height / 2]);

        var path = d3.geo.path()
            .projection(projection);

        function project(λ, φ) {
            λ *= 180 / Math.PI, φ *= 180 / Math.PI;
            var p0 = projection0([λ, φ]), p1 = projection1([λ, φ]);
            return [(1 - t) * p0[0] + t * p1[0], (1 - t) * -p0[1] + t * -p1[1]];
        }

        return function(_) {
            t = _;
            return path(d);
        };
    };
}

function redraw() {
    d3.select("#hist").call(chart);
    d3.select("#crate").call(crate);

    svg.selectAll("circle")
        .style('fill',function(d, i) { 
            //if(d<thresholds[0] || d>thresholds[1]){return "#e0e0e0";}
            return d ? SCALE(d) : "#e0e0e0";
        });
 
}

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

function metric(timeseries, crate, card, channel) {
    var label;
    if (card === null)
        label = 'crate ' + crate;
    else if (channel === null)
        label = 'card ' + card;
    else
        label = 'channel ' + channel;

    return timeseries.context.metric(function(start, stop, step, callback) {
        var params = {
            name: SOURCE,
            start: start.toISOString(),
            stop: stop.toISOString(),
            now: new Date().toISOString(),
            step: Math.floor(step/1000),
            crate: crate,
            card: card,
            channel: channel,
            method: METHOD
        };

        d3.json($SCRIPT_ROOT + '/metric_hash?' + $.param(params),
            function(data) {
                if (!data)
                    return callback(new Error('unable to load data'));

                return callback(null,data.values);
            }
        );
    }, label);
}

function draw(timeseries) {
    // create a horizon from timeseries.context and draw horizons
    if (timeseries.horizon) {
        d3.select(timeseries.target).selectAll('.horizon')
        .call(timeseries.horizon.remove)
        .remove();
    }

    timeseries.horizon = timeseries.context.horizon()
        .height(20)
        .colors(SCALE.range().concat(SCALE.range()))
        .extent(SCALE.domain())
        .format(timeseries.format);

    var horizons = d3.select(timeseries.target).selectAll('.horizon')
        .data(timeseries.metrics)
      .enter().insert('div','.bottom')
          .attr('class', 'horizon')
          .call(timeseries.horizon);

    if (timeseries.click)
        horizons.on('click', timeseries.click);
}

function update_metrics(timeseries) {
    if (timeseries.context !== null)
        timeseries.context.stop();

    timeseries.context = create_context(timeseries.target, STEP);
    timeseries.metrics = [];

    if (typeof timeseries.crate === 'undefined') {
        console.log("Updating all crates");
        for (var i=0; i < 2; i++) {
            timeseries.metrics[i] = metric(timeseries, i, null, null);
        }
    } else if (typeof timeseries.card === 'undefined') {
        console.log("Updating cards for crate " + timeseries.crate);
        for (var i=0; i < 16; i++) {
            timeseries.metrics[i] = metric(timeseries, timeseries.crate, i, null);
        }
    } else {
        console.log("Updating channels for crate " + timeseries.crate + " card " + timeseries.card);
        for (var i=0; i < 16; i++) {
            timeseries.metrics[i] = metric(timeseries, timeseries.crate, timeseries.card, i);
        }
    }
}

var default_thresholds = {
    charge: [-10000, -2000],
    nhit: [10, 80],
    sds: [0, 80],
    occupancy: [.1, .5],
    avgs: [0,16000],
    time: [0,500]
};

function set_thresholds(lo, hi) {
    // set thresholds text area
    $('#threshold-lo').val(lo);
    $('#threshold-hi').val(hi);
}

function switch_to_crate(crate) {
    card.crate(crate);
    d3.select('#card').call(card);
    $('#card-7').after('<tr></tr>');
    $('#card-15').after('<tr></tr>');
    $('#card-23').after('<tr></tr>');

    blah.crate = crate;
    blah.state = NEEDS_UPDATE;
    channelts.crate = crate;
    channelts.state = NEEDS_UPDATE;

    $('.carousel').carousel('next');
}

function switch_to_channel(crate, card) {
    channelts.crate = crate;
    channelts.card = card;
    channelts.state = NEEDS_UPDATE;
    $('#carousel').carousel('next');
}

var ACTIVE = 0,
    PAUSED = 1,
    NEEDS_UPDATE = 2;

var spam = {
target: '#timeseries',
context: null,
horizon: null,
metrics:null,
format: my_si_format,
click: function(d, i) {
    if ((i > 0) && (i <= 2))
        switch_to_crate(i-1);
    },
state: NEEDS_UPDATE,
slide: 0
};
    
var blah = {
target: '#timeseries-card',
context: null,
horizon: null,
metrics:null,
format: my_si_format,
crate: 0,
click: function(d, i) {
    switch_to_channel(blah.crate, i);
    },
state: NEEDS_UPDATE,
slide: 3
};
    
var channelts = {
target: '#timeseries-channel',
context: null,
horizon: null,
metrics:null,
format: my_si_format,
crate: 0,
card: 0,
state: NEEDS_UPDATE,
slide: 1
};

function setup() {
    SOURCE = $('#data-source').val();
    METHOD = $('#data-method').val();
    STEP = +$('#data-step').val();
    CRATE_WINDOW = +$('#crate-map-window').val();

    var thresholds = default_thresholds[SOURCE];

    SCALE = d3.scale.threshold()
        .domain(thresholds)
        .range(colorbrewer[$("#colors").val()][3]);

    card = card_view()
        .scale(SCALE);

    crate = crate_view()
        .scale(SCALE)
        .click(function(d, i) {
            switch_to_crate(i);
        });

    update_format();
    update_metrics(spam);
    draw(spam);
    spam.state = ACTIVE;

    // set default thresholds in text area
    $('#threshold-lo').val(thresholds[0]);
    $('#threshold-hi').val(thresholds[1]);

    var path = d3.geo.path().projection(projection);
    console.log('hello');
    var graticule = d3.geo.graticule();

    svg.append("path")
        .datum(graticule)
        .attr("class", "graticule")
        .attr("d", path);

    d3.select(self.frameElement).style("height", height + "px");

    pos = [];
    for (var i=0; i < coords.length; i++)
        pos[i] = projection(coords[i]);

    svg.selectAll('circle').data(pos)
      .enter().append('circle')
        .style('fill', '#e0e0e0')
        .attr('cx', function(d) { return d ? d[0]: null; })
        .attr('cy', function(d) { return d ? d[1]: null; })
        .attr('r', 3);

    // set up histogram
    d3.select('#hist').datum([]).call(chart);

    // collapse histogram panel
    $('#collapseOne').collapse();

    // set up crate view
    d3.select("#crate").datum([]).call(crate);
    // line break after crate 9 to get
    // XSNOED style
    $("#crate9").after("<br>");

}
function update_format() {
    var source = $('#data-source').val();
    var thresholds = default_thresholds[source];

    if (!thresholds) {
        console.error("No thresholds defined for source: " + source);
        return;
    }

    SCALE = d3.scale.threshold()
        .domain(thresholds)
        .range(colorbrewer[$("#colors").val()][3]);

    set_thresholds(thresholds[0], thresholds[1]);
}

var timeseries = [spam, blah, channelts];

setup();

function update_state(call_update_metric) {
    call_update_metric = typeof call_update_metric === 'undefined' ? true : false;

    timeseries.forEach(function(ts) {
        switch (ts.state) {
            case ACTIVE:
                if (call_update_metric)
                    update_metrics(ts);
                draw(ts);
                break;
            case PAUSED:
                if (call_update_metric)
                    ts.state = NEEDS_UPDATE;
                else
                    draw(ts);
        }
    });
}

$('#data-method').change(function() {
    METHOD = this.value;

    update_state();
});

$('#colors').change(function() {
    SCALE.range(colorbrewer[this.value][3]);
    //update_format();
    card.scale(SCALE);
    crate.scale(SCALE);
    update();
    update_state();
});

$('#crate-map-window').change(function() {
    CRATE_WINDOW = this.value;

    update();
});

$('#data-step').change(function() {
    STEP = this.value;

    update_state();
});

$('#data-source').change(function() {
    // update threshold values
    var thresholds = default_thresholds[this.value];
    set_thresholds.apply(this,thresholds);

    SOURCE = this.value;
    SCALE.domain(thresholds);
    card.scale(SCALE);
    crate.scale(SCALE);
    update_format();

    update();

    update_state();
});

$('#threshold-lo').keypress(function(e) {
    if (e.which == 13) {
        SCALE.domain([this.value,SCALE.domain()[1]]);
        card.scale(SCALE);
        crate.scale(SCALE);
        update();
        update_state(false);

        //d3.select("#crate").call(crate);
        //d3.select("#card").call(card);
    }
});

$('#threshold-hi').keypress(function(e) {
    if (e.which == 13) {
        SCALE.domain([SCALE.domain()[0],this.value]);
        card.scale(SCALE);
        crate.scale(SCALE);
        update();
        update_state(false);

        //d3.select("#crate").call(crate);
        //d3.select("#card").call(card);
    }
});

$('.carousel').on('slid.bs.carousel', function(e) {
    var slide = $(e.relatedTarget).index();
    $('#card-heading').text('Crate ' + blah.crate);
    $('#channel-heading').text('Crate ' + channelts.crate + ', Card ' + channelts.card);
    $('.data-source-heading').text($('#data-source :selected').text());

    timeseries.forEach(function(ts) {
        if (ts.slide == slide) {
            if (ts.state == NEEDS_UPDATE) {
                update_metrics(ts);
                draw(ts);
                ts.state = ACTIVE;
            } else if (ts.state == PAUSED) {
                ts.context.start();
                ts.state = ACTIVE;
            } else {
                console.log('timeseries already active');
            }
        } else {
            if (ts.state == ACTIVE) {
                ts.context.stop();
                ts.state = PAUSED;
            }
        }
    });
});

function query(name){
	console.log("Fetching data");
        console.log("query_name"+name) //Samm
	/* return context.metric(function(name, callback) {
	$.getJSON($SCRIPT_ROOT + '/query', {name: SOURCE, step: CRATE_WINDOW})}); */
};

function add_horizon(expressions, format, colors, extent) {
    var horizon = context.horizon().height(Number(height));

    if (typeof format != "undefined") horizon = horizon.format(format);
    if (typeof colors != "undefined" && colors) horizon = horizon.colors(colors);
    if (typeof extent != "undefined") horizon = horizon.extent(extent);

    d3.select('#main').selectAll('.horizon')
        .data(expressions.map(query), String)
      .enter().insert('div','.bottom')
        .attr('class', 'horizon')
        .call(horizon)
        .on('click', function(d, i) {
            var domain = context.scale.domain();
            var params = {
                name: expressions[i],
                start: domain[0].toISOString(),
                stop: domain[domain.length-1].toISOString(),
                step: Math.floor(context.step()/1000)
            };
            window.open($SCRIPT_ROOT + "/graph?" + $.param(params), '_self');
        });
}

var interval = 5000;

function update() {
    $.getJSON($SCRIPT_ROOT + '/query', {name: SOURCE, step: CRATE_WINDOW})
        .done(function(result) {
            d3.select('#crate').datum(result.values).call(crate);
            d3.select('#card').datum(result.values).call(card);
            d3.select('#timeseries-card').datum(result.values);
            //d3.select("#bargraph").selectAll("svg").remove()

            newData = []

            for (value of result.values){
                if(value==null){
                    console.log("Ignoring value")
                    continue
                }else{
                    console.log("Pushing value" + value)
                    newData.push(value)
                }
            }
           console.log(newData)//samm
           console.log("update_name"+SOURCE) //samm
            d3.select('#bargraph')
            .select("svg")
            .html("");

            d3.select("#bargraph")
            .select("svg")
            .selectAll("rect")
            .data(newData)
            .enter()
            .append("rect")
            .attr("width", function(d){
                if(d==0){
                    return 0;
                }else{
                    return widthScale(d);
                }
            })
            .attr("height",10)
            .attr("y", function(d,i){ return i*10});

            d3.select("#bargraph")
            .select("svg").append("g")
            .attr("transform", "translate(0,480)")
            .call(axis);

            ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
            d3.select('#hist').datum(result.values);

            svg.selectAll('circle').data(result.values);

            d3.select('#crate').datum(result.values);

            redraw();
            ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
        });
	update_state(false);
  
  console.log("Updated data");
}
var context = create_context('#main', $('#data-step').val());

add_horizon(["base"], format_rate, null, [0,10000]);

d3.select('#crate').datum([]).call(crate);
d3.select('#card').datum([]).call(card);
// wrap first ten and last ten crates in a div
$('#crate' + [0,1,2,3,4,5,6,7,8,9].join(',#crate')).wrapAll('<div />');
$('#crate' + [0,1,2,3,4].join(',#crate')).wrapAll('<div style="display:inline-block" />');
$('#crate' + [5,6,7,8,9].join(',#crate')).wrapAll('<div style="display:inline-block" />');
$('#crate' + [10,11,12,13,14,15,16,17,18,19].join(',#crate')).wrapAll('<div />');
$('#crate' + [10,11,12,13,14].join(',#crate')).wrapAll('<div style="display:inline-block" />');
$('#crate' + [15,16,17,18,19].join(',#crate')).wrapAll('<div style="display:inline-block" />');
update();
setInterval(update,interval);

var dataArray = [10,30,40,50];

var widthScale = d3.scale.linear()
                .domain([500,600])
                .range([0,500]);

var canvas = d3.select("#bargraph")
.append("svg")
.attr("width", 500)
.attr("height",500);

var axis = d3.svg.axis()
.ticks(5)
.scale(widthScale);

canvas.append("g")
.attr("transform", "translate(0,480)")
.call(axis);

// Attach click handler to <td id="channel"> elements
$(document).on('click', 'td#channel', function(e) {
    var title = $(this).attr('title'); // e.g., "Card 7, Channel 15"
    var match = /Card (\d+), Channel (\d+)/.exec(title);
    if (match) {
        var card = parseInt(match[1], 10);
        // Always call switch_to_channel(0, card)
        console.log('Clicked card', card, 'channel 0');
        switch_to_channel(0, card);
    }
});
