from .db import engine_expert
from wtforms import Form, IntegerField, FloatField, validators

FORM_KEYS = ['run', 'source', 'x', 'y', 'z', '']

class GoldInfoForm(Form):

    runnumber = IntegerField('Run Number', [validators.DataRequired()])
    sourcetype = IntegerField('Source Type', [validators.DataRequired()])
    xp = FloatField('x (cm)', [validators.DataRequired()])
    yp = FloatField('y (cm)', [validators.DataRequired()])
    zp = FloatField('z (cm)', [validators.DataRequired()])


def set_gold_information(form):
    """
    Update the database with the gold run information.
    """
    conn = engine_expert.connect()

    result = conn.execute(text("INSERT INTO gold_runs (run_number, "
                 "source_type, x, y, z) "
                 "VALUES (%(run)s, %(sourcetype)s, "
                 "%(x)s, %(y)s, %(z)s)", form.data))
