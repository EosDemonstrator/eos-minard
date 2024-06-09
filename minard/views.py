from __future__ import division, print_function
from flask import render_template, jsonify, request, redirect, url_for, flash, make_response
from datetime import datetime
import numpy as np
import time
import subprocess
from redis import Redis
from collections import deque
import re
from functools import wraps, update_wrapper
from minard import app
from minard.tools import parseiso, total_seconds
from minard.timeseries import get_timeseries, get_interval, get_hash_timeseries
from minard.timeseries import get_timeseries_field, get_hash_interval
from minard.timeseries import get_cavity_temp
from minard.eos import get_eos_runs, get_eos_settings
from minard.high_voltage import get_all_hvs

TRIGGER_NAMES = ['100L', '100M', '100H']
RUN_TYPES = {0: 'Diagnostic', 1: 'Physics', 2: 'Fiber calibration', 3: 'Deployed calibration'}
SOURCE_TYPES = {0: 'Laserball', 1: 'AmBe', 2: 'PuBe', 3: '137Cs', 4: 'Directional'}


redis = Redis(decode_responses=True)

@app.route('/')
def index():
    return redirect(url_for('eosstream'))

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

@app.route('/cavity-temp')
def cavity_temp():
    if len(request.args) == 0:
        return redirect(url_for('cavity_temp',step=867,height=20,_external=True))
    step = request.args.get('step',1,type=int)
    height = request.args.get('height',40,type=int)
    return render_template('cavity_temp.html',step=step,height=height,_external=True)

@app.route('/digitizer')
def digitizer():
    # Retrieve the data from Redis or any other source
    data = {
        'spam': [1, 2, 3, 4, 5],
        'blah': [6, 7, 8, 9, 10],
        'channels': [11, 12, 13, 14, 15]
    }
    
    if len(request.args) == 0:
        return redirect(url_for('digitizer', step=1, height=20, _external=True))
    step = request.args.get('step', 1, type=int)
    height = request.args.get('height', 40, type=int)

    return render_template('digitizer.html', step=step, height=height, data=data)

@app.route('/eosstream')
def eosstream():
    if len(request.args) == 0:
        return redirect(url_for('eosstream',step=1,height=20,_external=True))
    step = request.args.get('step',1,type=int)
    height = request.args.get('height',40,type=int)
    return render_template('eosstream.html',step=step,height=height)

@app.route('/detector')
def detector():
    return render_template('detector.html')

CHANNELS = np.arange(16*17)

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
    elif expr in ('run'):
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
    elif '-' in expr:
        # e.g. PULGT-nhit, which means the average nhit for PULGT triggers
        # this is not a rate, so we divide by the # of PULGT triggers for
        # the interval instead of the interval length
        trig, value = expr.split('-')
        if trig in TRIGGER_NAMES + ['TOTAL']:
            field = trig if trig in ['TOTAL'] else TRIGGER_NAMES.index(trig)
            values = get_timeseries_field('trig:%s' % value,field,start,stop,step)
            counts = get_timeseries_field('trig',field,start,stop,step)
            values = [float(a)/int(b) if a and b else None for a, b in zip(values,counts)]
        else:
            raise ValueError('unknown trigger type %s' % trig)
    else:
        if expr in TRIGGER_NAMES:
            field = TRIGGER_NAMES.index(expr)
            values = get_timeseries_field('trig',field,start,stop,step)
        elif expr == 'TOTAL':
            values = get_timeseries_field('trig','TOTAL',start,stop,step)
        else:
            values = get_timeseries(expr,start,stop,step)

        interval = get_interval(step)
        if expr in TRIGGER_NAMES or expr in ('TOTAL'):
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

    if ',' in expr:
        return jsonify(values=[get_metric(name, start, stop, step) for name in expr.split(',')])
    else:
        return jsonify(values=get_metric(expr, start, stop, step))

@app.route("/eos_runs")
def eos_runs():
    data = get_eos_runs()
    timestamps = []
    for i in range(len(data)):
        timestamps.append(str(data[i]['timestamp'])[:19])

    return render_template('eos_runs.html', data=data, timestamps=timestamps, run_type=RUN_TYPES, source_type=SOURCE_TYPES)

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

