import sqlalchemy
from minard.views import app

engine = sqlalchemy.create_engine('postgresql://%s:%s@%s:%i/%s' %
                                 (app.config['DB_USER'], app.config['DB_PASS'],
                                  app.config['DB_HOST'], app.config['DB_PORT'],
                                  app.config['DB_NAME']),
                                  pool_recycle=3600)

engine_expert = sqlalchemy.create_engine('postgresql://%s:%s@%s:%i/%s' %
                                 (app.config['DB_EXPERT'], app.config['DB_EXPERT_PASS'],
                                  app.config['DB_HOST'], app.config['DB_PORT'],
                                  app.config['DB_NAME']),
                                  pool_recycle=3600)

