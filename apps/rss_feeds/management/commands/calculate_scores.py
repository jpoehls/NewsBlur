from django.core.management.base import BaseCommand
from apps.reader.models import UserSubscription
from django.conf import settings
from optparse import make_option
import os
import errno
import re

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("-a", "--all", dest="all", action="store_true", help="All feeds, need it or not (can be combined with a user)"),
        make_option("-s", "--silent", dest="silent", default=False, action="store_true", help="Inverse verbosity."),
        make_option("-u", "--user", dest="user", nargs=1, help="Specify user id or username"),
        make_option("-d", "--daemon", dest="daemonize", action="store_true"),
    )

    def handle(self, *args, **options):
        settings.LOG_TO_STREAM = True
        if options['daemonize']:
            daemonize()
        
        if options['all']:
            feeds = UserSubscription.objects.all()
        else:
            feeds = UserSubscription.objects.filter(needs_unread_recalc=True)

        if options['user']:
            if re.match(r"([0-9]+)", options['user']):
                feeds = feeds.filter(user=int(options['user']))
            else:
                feeds = feeds.filter(user__username=options['user'])
            
        for f in feeds:
            f.calculate_feed_scores(silent=options['silent'])
        
def daemonize():
    """
    Detach from the terminal and continue as a daemon.
    """
    # swiped from twisted/scripts/twistd.py
    # See http://www.erlenstar.demon.co.uk/unix/faq_toc.html#TOC16
    if os.fork():   # launch child and...
        os._exit(0) # kill off parent
    os.setsid()
    if os.fork():   # launch child and...
        os._exit(0) # kill off parent again.
    os.umask(077)
    null = os.open("/dev/null", os.O_RDWR)
    for i in range(3):
        try:
            os.dup2(null, i)
        except OSError, e:
            if e.errno != errno.EBADF:
                raise
    os.close(null)