from .db import engine_expert
from wtforms import Form, IntegerField, FloatField, StringField, validators
from sqlalchemy import text

class GoldInfoForm(Form):

    runnumber = IntegerField('Run Number', [validators.InputRequired()])
    runtype = IntegerField('Run Type', [validators.InputRequired()])
    sourcetype = IntegerField('Source Type', [validators.InputRequired()])
    z = FloatField('z (cm)', [validators.InputRequired()])

def set_gold_information(form):
    """
    Update the database with the gold run information.
    """
    conn = engine_expert.connect()

    command = "INSERT INTO gold_runs (run_number, run_type, source_type, source_z_pos) " \
              "VALUES (%d, %d, %d, %f)" % \
              (form.runnumber.data, form.runtype.data, form.sourcetype.data, form.z.data)

    conn.execute(text(command))

