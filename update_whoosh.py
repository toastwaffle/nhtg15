#!/usr/bin/env python2

import os
import sys

from flask.ext.whooshalchemy import whoosh_index

from nhtg15_webapp import app
from nhtg15_webapp import models

sys.stdout  = os.fdopen(sys.stdout.fileno(), 'w', 0)
atatime     = 512

with app.APP.app_context():
    index = whoosh_index(app.APP, models.Area)
    searchable = models.Area.__searchable__

    total = int(models.Area.query.order_by(None).count())
    print 'total rows: {}'.format(total)

    done = 0

    writer = index.writer(limitmb=10000, procs=16, multisegment=True)

    for p in models.Area.query.yield_per(atatime):
        record = dict([(s, p.__dict__[s]) for s in searchable])
        record.update({'id' : unicode(p.id)}) # id is mandatory, or whoosh won't work
        writer.add_document(**record)
        done += 1
        if done % atatime == 0:
            print 'c {}/{} ({}%)'.format(done, total, round((float(done)/total)*100,2) ),

    print '{}/{} ({}%)'.format(done, total, round((float(done)/total)*100,2) )
    writer.commit()
