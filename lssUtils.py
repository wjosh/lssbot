from datetime import datetime
from dateutil.relativedelta import relativedelta

def currentGameTime():
    return datetime.utcnow() - relativedelta(hours=2)
