from db import engine

def get_all_hvs(slot):
    '''
    Returns the list of Eos PMTs
    '''
    conn = engine.connect()

    result = conn.execute("SELECT * FROM (SELECT * FROM hv_status WHERE slot=%d ORDER BY timestamp DESC LIMIT 48) as t1 ORDER BY channel ASC" % slot)

    keys = result.keys()
    rows = result.fetchall()

    conn.close()

    return [dict(zip(keys, row)) for row in rows]
