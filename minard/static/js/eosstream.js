$("#step-menu").on("change", function() {
    window.location.replace($SCRIPT_ROOT + "/snostream?step=" + this.value + "&height=" + height);
});

setInterval(function() {
    $.getJSON($SCRIPT_ROOT + '/query', {'name': 'dispatcher'}, function(reply) {
        $('#dispatcher').text(reply.name);
    });
},1000);

// Function to start the monitor process
function startMonitor() {
    fetch("/start_monitor")
        .then(response => response.text())
        .then(data => {
            console.log(data);
            // Perform any additional actions after starting the monitor
        })
        .catch(error => console.log(error));
}

// Function to stop the monitor process
function stopMonitor() {
    fetch("/stop_monitor")
        .then(response => response.text())
        .then(data => {
            console.log(data);
            // Perform any additional actions after stopping the monitor
        })
        .catch(error => console.log(error));
}
var context = create_context('#main', step);

var TRIGGER_NAMES = ['TOTAL','100L','100M','100H'];

function metric(name) {
    var display = name;

    return context.metric(function(start, stop, step, callback) {
        d3.json($SCRIPT_ROOT + '/metric' + 
                '?expr=' + name +
                '&start=' + start.toISOString() +
                '&stop=' + stop.toISOString() +
                '&now=' + new Date().toISOString() +
                '&step=' + Math.floor(step/1000), function(data) {
                if (!data) return callback(new Error('unable to load data'));
                return callback(null,data.values);
        });
    }, display);
}

function add_horizon(expressions, format, colors, extent) {
    var horizon = context.horizon().height(Number(height));

    if (typeof format != "undefined") horizon = horizon.format(format);
    if (typeof colors != "undefined" && colors) horizon = horizon.colors(colors);
    if (typeof extent != "undefined") horizon = horizon.extent(extent);

    d3.select('#main').selectAll('.horizon')
        .data(expressions.map(metric), String)
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

function add_baseline_horizon(expressions, format, colors, extent, baseline, mv_per_nhit) {
    /* Just like add_horizon except we subtract off 1.8V from the metric. */
    var horizon = context.horizon().height(Number(height));

    if (typeof format != "undefined") horizon = horizon.format(format);
    if (typeof colors != "undefined" && colors) horizon = horizon.colors(colors);
    if (typeof extent != "undefined") horizon = horizon.extent(extent);

    d3.select('#main').selectAll('.horizon')
        .data(expressions.map(function(name) { return metric(name).subtract(baseline).divide(mv_per_nhit/1e3) }), String)
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

add_horizon(TRIGGER_NAMES,format_rate);
add_horizon(["run"],format_int,[]);
add_horizon(["heartbeat"],format_int,null,[0,4]);
add_horizon(["Temperature"],format_temp,null,[0,4]);
add_horizon(["Water"],format_water,null,[0,4]);
add_horizon(["data_rate"],format_rate, null,[0,4]);
add_horizon(["d0_ch0_mean"],format_rate, null,[0,4]);
context.on("focus", function(i) {
  d3.selectAll(".value").style("right", i === null ? null : context.size() - i + "px");
});
