from minard.db import engine

def get_eos_runs():
    '''
    Returns the list of Eos PMTs
    '''
    conn = engine.connect()

    result = conn.execute("SELECT key, timestamp, events, files, run_type, run_number, filename, fiber_number, laser_intensity, power_meter, comment FROM run_settings ORDER BY timestamp DESC LIMIT 50")

    keys = result.keys()
    rows = result.fetchall()

    conn.close()

    return [dict(zip(keys, row)) for row in rows]


def get_eos_settings(key, tab):
    '''
    Returns the list of Eos PMTs
    '''
    conn = engine.connect()

    result = conn.execute("SELECT * FROM %s WHERE key=%d" % (tab, key))

    keys = result.keys()
    rows = result.fetchall()

    conn.close()

    return [dict(zip(keys, row)) for row in rows]

