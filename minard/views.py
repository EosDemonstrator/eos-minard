from __future__ import division, print_function
from minard import app
from flask import render_template, jsonify, request, redirect, url_for, flash, make_response
from itertools import product
import time
import subprocess
from redis import Redis
from os.path import join
import json
#import HLDQTools
import requests
from minard.tools import parseiso, total_seconds
from collections import deque, namedtuple
from minard.timeseries import get_timeseries, get_interval, get_hash_timeseries
from minard.timeseries import get_timeseries_field, get_hash_interval
from minard.timeseries import get_cavity_temp
from math import isnan
import os
import sys
import random
#import minard.detector_state
#import minard.orca
#import minard.nlrat
#import minard.nearline_monitor
#import minard.nearlinedb
#import minard.nearline_settings
#import minard.pingcratesdb
#import minard.triggerclockjumpsdb
#import minard.muonsdb
import minard.redisdb
#import minard.cssProc as cssproc
#import minard.fiber_position
#import minard.occupancy
#import minard.channelflagsdb
#import minard.dropout
#import minard.pmtnoisedb
#import minard.gain_monitor
#import minard.activity
#import minard.scintillator_level
#import minard.burst as burst_f
#import minard.presn as presn_f
#from shifter_information import get_shifter_information, set_shifter_information, ShifterInfoForm, get_experts, get_supernova_experts
#from minard.run_list import golden_run_list
from minard.polling import polling_runs, polling_info, polling_info_card, polling_check, get_cmos_rate_history, polling_summary, get_most_recent_polling_info, get_vmon, get_base_current_history, get_vmon_history
#from minard.channeldb import ChannelStatusForm, upload_channel_status, get_channels, get_channel_status, get_channel_status_form, get_channel_history, get_pmt_info, get_nominal_settings, get_discriminator_threshold, get_all_thresholds, get_maxed_thresholds, get_gtvalid_lengths, get_pmt_types, pmt_type_description, get_fec_db_history
#from minard.ecaldb import ecal_state, penn_daq_ccc_by_test, get_penn_daq_tests
#from minard.mtca_crate_mapping import MTCACrateMappingForm, OWLCrateMappingForm, upload_mtca_crate_mapping, get_mtca_crate_mapping, get_mtca_crate_mapping_form, mtca_relay_status, get_mtca_retriggers, get_mtca_autoretriggers, RETRIGGER_LOGIC
import re
#from minard.resistor import get_resistors, ResistorValuesForm, get_resistor_values_form, update_resistor_values
#from minard.pedestalsdb import get_pedestals, bad_pedestals, qhs_by_channel
from datetime import datetime
from functools import wraps, update_wrapper
#from minard.dead_time import get_dead_time, get_dead_time_runs, get_dead_time_run_by_key
#from minard.radon_monitor import get_radon_monitor
from minard.eos import get_eos_runs, get_eos_settings
from minard.high_voltage import get_all_hvs

TRIGGER_NAMES = \
['100L',
 '100M',
 '100H',
 '20',
 '20LB',
 'ESUML',
 'ESUMH',
 'OWLN',
 'OWLEL',
 'OWLEH',
 'PULGT',
 'PRESCL',
 'PED',
 'PONG',
 'SYNC',
 'EXTA',
 'EXT2',
 'EXT3',
 'EXT4',
 'EXT5',
 'EXT6',
 'EXT7',
 'EXT8',
 'SRAW',
 'NCD',
 'SOFGT',
 'MISS']

class Program(object):
    def __init__(self, name, machine=None, link=None, description=None, expire=10, display_log=True):
        self.name = name
        self.machine = machine
        self.link = link
        self.description = description
        self.expire = expire
        self.display_log = display_log

redis = Redis(decode_responses=True)

PROGRAMS = [#Program('builder','builder1', description="event builder"),
            Program('L2-client','buffer1', description="L2 processor"),
            Program('L2-convert','buffer1',
                    description="zdab -> ROOT conversion"),
            Program('L1-delete','buffer1', description="delete L1 files"),
            Program('mtc','sbc', description="mtc server",
		    display_log=False),
            Program('data','buffer1', description="data stream server",
		    display_log=False),
            Program('xl3','buffer1', description="xl3 server",
		    display_log=False),
            Program('log','minard', description="log server",
		    display_log=False),
            Program('DetectorControl','minard', description="detector control server",
		    display_log=False),
            Program('estop-monitor','sbc', description="estop server",
		    display_log=False),
            Program('tubii','tubii', description="tubii server",
		    display_log=False),
            Program('noel','buffer1', description="noel server",
		    display_log=False)
]

def nocache(view):
    """
    Flask decorator to hopefully prevent Firefox from caching responses which
    are made very often.

    Example:

        @app.route('/foo')
        @nocache
        def foo():
            # do stuff
            return jsonify(*bar)

    Basic idea from https://gist.github.com/arusahni/9434953.

    Required Headers to prevent major browsers from caching content from
    https://stackoverflow.com/questions/49547.
    """
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    return update_wrapper(no_cache, view)

@app.template_filter('timefmt')
def timefmt(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(float(timestamp)))

@app.errorhandler(500)
def internal_error(exception):
    return render_template('500.html'), 500

@app.route('/status')
def status():
    return render_template('status.html', programs=PROGRAMS)

def get_builder_log_warnings(run):
    """
    Returns a list of all the lines in the builder log for a given run which
    were warnings.
    """
    # regular expression matching error messages
    rerr = re.compile('error|warning|jumped|queue head|queue tail|fail|memory|NHIT > 10000|invalid|unknown|missing|collision|unexpected|garbage|sequence|skipped|FIXED|Orphan|Bad data', re.IGNORECASE)

    warnings = []
    with open(os.path.join(app.config["BUILDER_LOG_DIR"], "SNOP_%010i.log" % run)) as f:
        for line in f:
            if rerr.search(line):
                warnings.append(line)
    return warnings

def get_daq_log_warnings(run):
    """
    Returns a list of all the lines in the DAQ log for a given run which were
    warnings.
    """
    warnings = []
    with open(os.path.join(app.config["DAQ_LOG_DIR"], "daq_%08i.log" % run)) as f:
        for line in f:
            # match the log level
            match = re.match('.+? ([.\-*#])', line)

            if match and match.group(1) == '#':
                warnings.append(line)
    return warnings

@app.template_filter('time_from_now')
def time_from_now(dt):
    """
    Returns a human readable string representing the time duration between `dt`
    and now. The output was copied from the moment javascript library.

    See https://momentjs.com/docs/#/displaying/fromnow/
    """
    delta = total_seconds(datetime.now() - dt)

    if delta < 45:
        return "a few seconds ago"
    elif delta < 90:
        return "a minute ago"
    elif delta <= 44*60:
        return "%i minutes ago" % int(round(delta/60))
    elif delta <= 89*60:
        return "an hour ago"
    elif delta <= 21*3600:
        return "%i hours ago" % int(round(delta/3600))
    elif delta <= 35*3600:
        return "a day ago"
    elif delta <= 25*24*3600:
        return "%i days ago" % int(round(delta/(24*3600)))
    elif delta <= 45*24*3600:
        return "a month ago"
    elif delta <= 319*24*3600:
        return "%i months ago" % int(round(delta/(30*24*3600)))
    elif delta <= 547*24*3600:
        return "a year ago"
    else:
        return "%i years ago" % int(round(delta/(365.25*24*3600)))

@app.route('/start_monitor')
def start_monitor():
    global monitor_process
    try:
        if monitor_process is None or monitor_process.poll() is not None:
            monitor_process = subprocess.Popen(['source', '/home/hexnu/tooldaq/ToolApplication/Setup.sh', '&&', '/home/hexnu/tooldaq/dispatch/monitor'])
            return 'Monitor started successfully'
        else:
            return 'Monitor is already running'
    except Exception as e:
        return str(e)

@app.route('/stop_monitor')
def stop_monitor():
    global monitor_process
    try:
        if monitor_process is not None and monitor_process.poll() is None:
            monitor_process.terminate()
            return 'Monitor stopped successfully'
        else:
            return 'Monitor is not running'
    except Exception as e:
        return str(e)

@app.template_filter('format_cmos_rate')
def format_cmos_rate(rate):
    if rate < 1000:
        return '%i' % int(rate)
    elif rate < 10000:
        return '%.1fk' % (rate/1000)
    elif rate < 1e6:
        return '%ik' % (rate//1000)
    else:
        return '%iM' % (rate//1e6)

@app.route('/vmon_history')
def vmon_history():
    crate = request.args.get("crate", 0, type=int)
    slot = request.args.get("slot", 0, type=int)
    keys, data = get_vmon_history(crate, slot)

    return render_template('vmon_history.html', crate=crate, slot=slot, data=data, keys=keys)

@app.route('/graph')
def graph():
    name = request.args.get('name')
    start = request.args.get('start')
    stop = request.args.get('stop')
    step = request.args.get('step',1,type=int)
    return render_template('graph.html',name=name,start=start,stop=stop,step=step)

@app.route('/get_status')
@nocache
def get_status():
    if 'name' not in request.args:
        return 'must specify name', 400

    name = request.args['name']

    up = redis.get('uptime:{name}'.format(name=name))

    if up is None:
        uptime = None
    else:
        uptime = int(time.time()) - int(up)

    return jsonify(status=redis.get('heartbeat:{name}'.format(name=name)),uptime=uptime)

@app.route('/view_log')
def view_log():
    name = request.args.get('name', '???')
    return render_template('view_log.html',name=name)

@app.route('/log', methods=['POST'])
def log():
    """Forward a POST request to the log server at port 8081."""
    import requests

    resp = requests.post('http://127.0.0.1:8081', headers=request.headers, data=request.form)
    return resp.content, resp.status_code, resp.headers.items()

@app.route('/tail')
def tail():
    name = request.args.get('name', None)

    if name is None:
        return 'must specify name', 400

    seek = request.args.get('seek', None, type=int)

    filename = join('/var/log/snoplus', name + '.log')

    try:
        f = open(filename)
    except IOError:
        return "couldn't find log file {filename}".format(filename=filename), 400

    if seek is None:
        # return last 100 lines
        lines = deque(f, maxlen=100)
    else:
        pos = f.tell()
        f.seek(0,2)
        end = f.tell()
        f.seek(pos)

        if seek > end:
            # log file rolled over
            try:
                prev_logfile = open(filename + '.1')
                prev_logfile.seek(seek)
                # add previous log file lines
                lines = prev_logfile.readlines()
            except IOError:
                return 'seek > log file length', 400

            # add new lines
            lines.extend(f.readlines())
        else:
            # seek to last position and readlines
            f.seek(seek)
            lines = f.readlines()

    lines = [line.decode('unicode_escape') for line in lines]

    return jsonify(seek=f.tell(), lines=lines)

@app.route('/')
def index():
    return redirect(url_for('snostream'))

@app.route('/cavity-temp')
def cavity_temp():
    if len(request.args) == 0:
        return redirect(url_for('cavity_temp',step=867,height=20,_external=True))
    step = request.args.get('step',1,type=int)
    height = request.args.get('height',40,type=int)
    return render_template('cavity_temp.html',step=step,height=height)

@app.route('/digitizer')
def digitizer():
    # Retrieve the data from Redis or any other source
    data = {
        'spam': [1, 2, 3, 4, 5],
        'blah': [6, 7, 8, 9, 10],
        'channelts': [11, 12, 13, 14, 15]
    }
    
    if len(request.args) == 0:
        return redirect(url_for('digitizer', step=1, height=20, _external=True))
    step = request.args.get('step', 1, type=int)
    height = request.args.get('height', 40, type=int)

    return render_template('digitizer.html', step=step, height=height, data=data)
@app.route('/snostream')
def snostream():
    if len(request.args) == 0:
        return redirect(url_for('snostream',step=1,height=20,_external=True))
    step = request.args.get('step',1,type=int)
    height = request.args.get('height',40,type=int)
    return render_template('snostream.html',step=step,height=height)

@app.route('/detector')
def detector():
    return render_template('detector.html')

@app.route('/pedestals')
def pedestals():
    crate = request.args.get("crate", 0, type=int)
    slot = request.args.get("slot", -1, type=int)
    channel = request.args.get("channel", -1, type=int)
    cell = request.args.get("cell", -1, type=int)
    charge = request.args.get("charge", "qhs_avg", type=str)
    qmin = request.args.get("qmin", 300, type=int)
    qmax = request.args.get("qmax", 2000, type=int)
    limit = request.args.get("limit", 50, type=int)
    qhs = qhs_by_channel(crate, slot, channel, cell)
    bad_ped = bad_pedestals(crate, slot, channel, cell, charge, qmax, qmin, limit)
    return render_template('pedestals.html', crate=crate, slot=slot, channel=channel, cell=cell, qhs=qhs, bad_ped=bad_ped, qmin=qmin, qmax=qmax, charge=charge, limit=limit)

@app.route('/cmos_rates_check')
def cmos_rates_check():
    high_rate = request.args.get('high_rate',20000.0,type=float)
    low_rate = request.args.get('low_rate',50.0,type=float)
    pct_change = request.args.get('pct_change',200.0,type=float)

    cmos_changes, cmos_high_rates, cmos_low_rates, run_number = \
        polling_check(high_rate, low_rate, pct_change)

    return render_template('cmos_rates_check.html', cmos_changes=cmos_changes, cmos_high_rates=cmos_high_rates, cmos_low_rates=cmos_low_rates, high_rate=high_rate, low_rate=low_rate, run_number=run_number, pct_change=pct_change)

def convert_timestamp(data):

    # Convert datetime objects to strings
    for i in range(len(data)):
        data[i]['timestamp'] = data[i]['timestamp'].isoformat()

    return data

@app.route('/polling_history')
def polling_history():
    crate = request.args.get('crate',0,type=int)
    slot = request.args.get('slot',0,type=int)
    channel = request.args.get('channel',0,type=int)
    # Run when we started keeping polling data
    starting_run = request.args.get('starting_run',0,type=int)
    ending_run = request.args.get('ending_run',0,type=int)
    if ending_run == 0:
        ending_run = detector_state.get_latest_run() + 1
    if starting_run == 0:
        starting_run = ending_run - 1000

    cdata = get_cmos_rate_history(crate, slot, channel, starting_run, ending_run)
    cdata = convert_timestamp(cdata)

    bdata = get_base_current_history(crate, slot, channel, starting_run, ending_run)
    bdata = convert_timestamp(bdata)

    return render_template('polling_history.html', crate=crate, slot=slot, channel=channel, cdata=cdata, bdata=bdata, starting_run=starting_run, ending_run=ending_run)

@app.route('/daq')
def daq():
    return render_template('daq.html')

@app.route('/alarms')
def alarms():
    return render_template('alarms.html')

CHANNELS = [crate << 9 | card << 5 | channel \
            for crate, card, channel in product(range(20),range(16),range(32))]

OWL_TUBES = [2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040, 2041, 2042, 2043, 2044, 2045, 2046, 2047, 7152, 7153, 7154, 7155, 7156, 7157, 7158, 7159, 7160, 7161, 7162, 7163, 7164, 7165, 7166, 7167, 9712, 9713, 9714, 9715, 9716, 9717, 9718, 9719, 9720, 9721, 9722, 9723, 9724, 9725, 9726, 9727]

@app.route('/query_occupancy')
@nocache
def query_occupancy():
    trigger_type = request.args.get('type',0,type=int)
    run = request.args.get('run',0,type=int)

    values = occupancy.occupancy_by_trigger(trigger_type, run, False)

    return jsonify(values=values)

@app.route('/query_polling')
@nocache
def query_polling():
    polling_type = request.args.get('type','cmos',type=str)
    run = request.args.get('run',0,type=int)

    values = polling_info(polling_type, run)
    return jsonify(values=values)

@app.route('/query_polling_crate')
@nocache
def query_polling_crate():
    polling_type = request.args.get('type','cmos',type=str)
    run = request.args.get('run',0,type=int)
    crate = request.args.get('crate',0,type=int)

    values = polling_info_card(polling_type, run, crate)
    return jsonify(values=values)

@app.route('/query')
@nocache
def query():
    name = request.args.get('name','',type=str)

    if name == 'dispatcher':
        return jsonify(name=redis.get('dispatcher'))

    if 'nhit' in name:
        seconds = request.args.get('seconds',type=int)

        now = int(time.time())

        p = redis.pipeline()
        for i in range(seconds):
            p.lrange('ts:1:{ts}:{name}'.format(ts=now-i,name=name),0,-1)
        nhit = map(int,sum(p.execute(),[]))
        return jsonify(value=nhit)

    if name in ('occupancy','cmos','base'):
        now = int(time.time())
        step = request.args.get('step',60,type=int)

        interval = get_hash_interval(step)

        i, remainder = divmod(now, interval)

        def div(a,b):
            if a is None or b is None:
                return None
            return float(a)/float(b)

        if remainder < interval//2:
            # haven't accumulated enough data for this window
            # so just return the last time block
            if redis.ttl('ts:%i:%i:%s:lock' % (interval,i-1,name)) > 0:
                # if ttl for lock exists, it means the values for the last
                # interval were already computed
                values = redis.hmget('ts:%i:%i:%s' % (interval, i-1, name),CHANNELS)
                return jsonify(values=values)
            else:
                i -= 1

        if name in ('cmos', 'base'):
            # grab latest sum of values and divide by the number
            # of values to get average over that window
            sum_ = redis.hmget('ts:%i:%i:%s:sum' % (interval,i,name),CHANNELS)
            len_ = redis.hmget('ts:%i:%i:%s:len' % (interval,i,name),CHANNELS)

            values = list(map(div,sum_,len_))
        else:
            hits = redis.hmget('ts:%i:%i:occupancy:hits' % (interval,i), CHANNELS)
            count = int(redis.get('ts:%i:%i:occupancy:count' % (interval,i)))
            if count > 0:
                values = [int(n)/count if n is not None else None for n in hits]
            else:
                values = [None]*len(CHANNELS)

        return jsonify(values=values)

@app.route('/get_alarm')
@nocache
def get_alarm():
    try:
        count = int(redis.get('alarms:count'))
    except TypeError:
        return jsonify(alarms=[],latest=-1)

    if 'start' in request.args:
        start = request.args.get('start',type=int)

        if start < 0:
            start = max(0,count + start)
    else:
        start = max(count-100,0)

    alarms = []
    for i in range(start,count):
        value = redis.get('alarms:{0:d}'.format(i))

        if value:
            alarms.append(json.loads(value))

    return jsonify(alarms=alarms,latest=count-1)
    
@app.route('/owl_tubes')
@nocache
def owl_tubes():
    """Returns the time series for the sum of all upward facing OWL tubes."""
    name = request.args['name']
    start = request.args.get('start', type=parseiso)
    stop = request.args.get('stop', type=parseiso)
    now_client = request.args.get('now', type=parseiso)
    step = request.args.get('step', type=int)
    method = request.args.get('method', 'avg')
    # start = request.args.get('start', type=parseiso)
    # stop = request.args.get('stop', type=parseiso)
    # now_client = request.args.get('now', type=parseiso)
    # step = request.args.get('step', type=int)
    # method = request.args.get('method', 'avg')

    now = int(time.time())
    
    print(name, start, stop, now_client, step, method, now)

    # adjust for clock skew
    #dt = now_client - now
    #start -= dt
    #stop -= dt

    start = int(start)
    stop = int(stop)
    step = int(step)

    values = []
    for i, id in enumerate(OWL_TUBES):
        crate, card, channel = id >> 9, (id >> 5) & 0xf, id & 0x1f
        values.append(get_hash_timeseries(name,start,stop,step,crate,card,channel,method))

    # transpose time series from (channel, index) -> (index, channel)
    values = zip(*values)

    # filter None values in sub lists
    values = map(lambda x: filter(lambda x: x is not None, x), values)

    # convert to floats
    values = map(lambda x: map(float, x), values)

    if method == 'max':
	# calculate max value in each time bin.
        values = map(lambda x: max(x) if len(x) else None, values)
    else:
	# calculate mean value in each time bin
        values = map(lambda x: sum(x)/len(x) if len(x) else None, values)

    return jsonify(values=values)

@app.route('/metric_hash')
@nocache
def metric_hash():
    """Returns the time series for argument `names` as a JSON list."""
    name = request.args['name']
    start = request.args.get('start', type=parseiso)
    stop = request.args.get('stop', type=parseiso)
    now_client = request.args.get('now', type=parseiso)
    step = request.args.get('step', type=int)
    crate = request.args.get('crate', type=int)
    card = request.args.get('card', None, type=int)
    channel = request.args.get('channel', None, type=int)
    method = request.args.get('method', 'avg')

    now = int(time.time())

    # adjust for clock skew
    dt = now_client - now
    start -= dt
    stop -= dt

    start = int(start)
    stop = int(stop)
    step = int(step)

    values = get_hash_timeseries(name,start,stop,step,crate,card,channel,method)
    return jsonify(values=values)

def get_metric(expr, start, stop, step):
    if expr.split('-')[0] == 'temp':
        sensor = int(expr.split('-')[1])
        values = get_cavity_temp(sensor, start, stop, step)
    elif expr in ('L2:gtid', 'L2:run'):
        values = get_timeseries(expr, start, stop, step)
    elif expr in ('gtid', 'run', 'subrun'):
        values = get_timeseries_field('trig', expr, start, stop, step)
    elif 'heartbeat' in expr:
        values = get_timeseries(expr,start,stop,step)
    elif 'Temperature' in expr:
        values = get_timeseries(expr,start,stop,step)
    elif 'Water' in expr:
        values = get_timeseries(expr,start,stop,step)    
    elif 'data_rate' in expr:
        values = get_timeseries(expr,start,stop,step)
    elif 'd0_ch0_mean' in expr:
        values = get_timeseries(expr,start,stop,step)
    elif 'packets' in expr:
        values = get_timeseries(expr,start,stop,step)
    elif expr == u"0\u03bd\u03b2\u03b2":
        import random
        total = get_timeseries('TOTAL',start,stop,step)
        values = [int(random.random() < step/315360) if i else 0 for i in total]
    elif '-' in expr:
        # e.g. PULGT-nhit, which means the average nhit for PULGT triggers
        # this is not a rate, so we divide by the # of PULGT triggers for
        # the interval instead of the interval length
        trig, value = expr.split('-')
        if trig in TRIGGER_NAMES + ['TOTAL', 'polling']:
            if value == 'Baseline':
                values = get_timeseries(expr,start,stop,step)
                counts = get_timeseries('baseline-count',start,stop,step)
            else:
                field = trig if trig in ['TOTAL', 'polling'] else TRIGGER_NAMES.index(trig)
                values = get_timeseries_field('trig:%s' % value,field,start,stop,step)
                counts = get_timeseries_field('trig',field,start,stop,step)
            values = [float(a)/int(b) if a and b else None for a, b in zip(values,counts)]
        else:
            raise ValueError('unknown trigger type %s' % trig)
    elif 'FECD' in expr:
        field = expr.split('/')[1]
        values = get_timeseries_field('trig:fecd',field,start,stop,step)

        interval = get_interval(step)

        values = map(lambda x: int(x)/interval if x else 0, values)
    else:
        if expr in TRIGGER_NAMES:
            field = TRIGGER_NAMES.index(expr)
            values = get_timeseries_field('trig',field,start,stop,step)
        elif expr == 'TOTAL':
            values = get_timeseries_field('trig','TOTAL',start,stop,step)
        elif expr == 'polling':
            values = get_timeseries_field('trig','polling',start,stop,step)
        else:
            values = get_timeseries(expr,start,stop,step)

        interval = get_interval(step)
        if expr in TRIGGER_NAMES or expr in ('TOTAL','L1','L2','ORPHANS','BURSTS', 'polling'):
            # trigger counts are zero by default
            values = map(lambda x: int(x)/interval if x else 0, values)
        else:
            values = map(lambda x: int(x)/interval if x else None, values)

    return list(values)
@app.route('/metric')
@nocache
def metric():
    """Returns the time series for argument `expr` as a JSON list."""
    args = request.args

    expr = args['expr']
    start = args.get('start',type=parseiso)
    stop = args.get('stop',type=parseiso)
    now_client = args.get('now',type=parseiso)
    step = args.get('step',type=int)

    now = int(time.time())

    # adjust for clock skew
    dt = now_client - now
    start -= dt
    stop -= dt

    start = int(start)
    stop = int(stop)
    step = int(step)

    print(start, stop, step)

    if ',' in expr:
        return jsonify(values=[get_metric(name, start, stop, step) for name in expr.split(',')])
    else:
        return jsonify(values=get_metric(expr, start, stop, step))

@app.route('/occupancy_by_trigger')
def occupancy_by_trigger():
    limit = request.args.get("limit", 25, type=int)
    selected_run = request.args.get("run", 0, type=int)
    run_range_low = request.args.get("run_range_low", 0, type=int)
    run_range_high = request.args.get("run_range_high", 0, type=int)
    gold = request.args.get("gold_runs", 0, type=int)

    gold_runs = 0
    if gold:
        gold_runs = golden_run_list()

    if not selected_run:
        runs = occupancy.run_list(limit, run_range_low, run_range_high, gold_runs)
    else:
        runs = [selected_run]

    status, crates, slots = occupancy.occupancy_by_trigger_limit(limit, selected_run, run_range_low, run_range_high, gold_runs)

    # If no data for selected run
    if len(status) == 0:
        status[selected_run] = -1

    return render_template('occupancy_by_trigger.html', runs=runs, limit=limit, crates=crates, slots=slots, status=status, selected_run=selected_run, run_range_low=run_range_low, run_range_high=run_range_high, gold=gold)

@app.route('/occupancy_by_trigger_run/<run_number>')
def occupancy_by_trigger_run(run_number):

    # ESUMH is 6th trigger bit
    issues = occupancy.occupancy_by_trigger(6, run_number, True)

    return render_template('occupancy_by_trigger_run.html', run_number=run_number, issues=issues)

@app.route('/nearline_monitoring_summary')
def nearline_monitoring_summary():
    limit = request.args.get("limit", 25, type=int)
    selected_run = request.args.get("run", 0, type=int)
    run_range_low = request.args.get("run_range_low", 0, type=int)
    run_range_high = request.args.get("run_range_high", 0, type=int)
    runtype = request.args.get("runtype", -1, type=int)
    gold = request.args.get("gold_runs", 0, type=int)

    # Select only golden runs
    gold_runs = 0
    if gold:
        gold_runs = golden_run_list()

    # Get the run type and run list from the nearline database
    runTypes, runs = nearline_monitor.get_run_types(limit, selected_run, run_range_low, run_range_high, gold_runs)

    # Get the data for each of the nearline tools
    clock_jumps, ping_crates, channel_flags, occupancy, muons, crate_gain = \
        nearline_monitor.get_run_list(limit, selected_run, run_range_low, run_range_high, runs, gold_runs)

    # Allow sorting by run type
    allrunTypes = nlrat.RUN_TYPES

    displayed_runs = []
    if runtype == -1:
        selectedType = "All"
        displayed_runs = runs
    else:
        selectedType = allrunTypes[runtype]

        if run_range_high:
            run_list = detector_state.get_runs_with_run_type(run_range_low, (1<<runtype), run_range_high)
        elif selected_run:
            run_list = detector_state.get_runs_with_run_type(selected_run-1, (1<<runtype), selected_run+1)
        else:
            run = detector_state.get_latest_run()
            run_list = detector_state.get_runs_with_run_type(run - limit, (1<<runtype))

        # Apply the run type to the failure list
        for run in runs:
            if run in run_list:
                displayed_runs.append(run)

    return render_template('nearline_monitoring_summary.html', runs=displayed_runs, selected_run=selected_run, limit=limit, clock_jumps=clock_jumps, ping_crates=ping_crates, channel_flags=channel_flags, occupancy=occupancy, muons=muons, crate_gain=crate_gain, runTypes=runTypes, run_range_low=run_range_low, run_range_high=run_range_high, allrunTypes=allrunTypes, selectedType=selectedType, gold=gold)


@app.route("/eos_runs")
def eos_runs():
    return render_template('eos_runs.html', data=get_eos_runs(), run_type=RUN_TYPES)

@app.route("/eos_run")
def eos_run():
    key = request.args.get("key", 1, type=int)

    data = get_eos_settings(key, 'run_settings')
    data = data[0]

    hvs = []
    for i in range(6):
        hv_str = "hv"+str(i)
        hvs.append(get_eos_settings(int(data[hv_str]), 'high_voltage'))

    caens = []
    for i in range(17):
        caen_str = "caen"+str(i)
        caens.append(get_eos_settings(int(data[caen_str]), 'caen'))

    hvsss = []
    for i in range(17):
        hvss_str = "hvss"+str(i)
        hvsss.append(get_eos_settings(int(data[hvss_str]), 'hvss'))

    ptb = get_eos_settings(int(data["ptb"]), 'ptb')[0]

    return render_template('eos_run.html', data=data, hvs=hvs, caens=caens, hvsss=hvsss, ptb=ptb)

@app.route("/hv")
def hv():
    data = []
    ts = []
    for slot in range(6):
        data.append(get_all_hvs(slot))
        try:
            timestamp = data[slot][0]["timestamp"]
            timestamp = str(timestamp)[0:19]
            ts.append(timestamp)
        except Exception as e:
            pass

    return render_template("hv.html", data=data, ts=ts)

