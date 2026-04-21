from .db import engine_expert, engine
from wtforms import Form, IntegerField, FloatField, StringField, validators
from sqlalchemy import text

class GoldInfoForm(Form):

    runnumber = IntegerField('Run Number', [validators.InputRequired()])
    runtype = IntegerField('Run Type', [validators.InputRequired()])
    sourcetype = IntegerField('Source Type', [validators.InputRequired()])
    z = FloatField('z (mm)', [validators.InputRequired()])

def set_gold_information(form):
    """
    Update the database with the gold run information.
    """
    conn = engine_expert.connect()

    command = "INSERT INTO gold_runs (run_number, run_type, source_type, source_z_pos) " \
              "VALUES (%d, %d, %d, %f)" % \
              (form.runnumber.data, form.runtype.data, form.sourcetype.data, form.z.data)

    conn.execute(text(command))
    conn.commit()


def get_gold_runs_by_timestamp():
    '''
    Returns the list of Eos PMTs
    '''
    conn = engine.connect()

    result = conn.execute(text("SELECT * FROM gold_runs ORDER BY timestamp DESC LIMIT 10"))

    keys = result.keys()
    rows = result.fetchall()

    print (rows)

    conn.close()

    return [dict(zip(keys, row)) for row in rows]

