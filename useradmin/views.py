import datetime as date
import useradmin.helpers as h

from useradmin.models import DBSession, User, Group, Permission, Application
from useradmin.authorization import AuthorizationControl
from useradmin.models import MyModel

from pyramid.httpexceptions import HTTPFound

def my_view(request):
#    dbsession = DBSession()
#    root = dbsession.query(MyModel).filter(MyModel.name==u'root').first()
    return { 'h': h, 'project':'user-admin' }

@AuthorizationControl('administer')
def index(request):
    range  = ''
    limit  = 30
    end    = date.datetime.today().strftime(h.getSettings('date.short'))
    start  = (date.datetime.today() - date.timedelta(days=30)).strftime(h.getSettings('date.short'))
    if request.params.has_key('limit') and request.params.get('limit'):
        limit  = request.params.get('limit');
    groups = Group().getAll()
    perms  = Permission().getAll()
    apps   = Application().getAll()
    return { 'h': h, 'start': start, 'end': end, 'groups': groups, 'perms': perms, 'apps': apps, 'limit': limit }

def logout(request):
    request.session.invalidate()
    host = h.getSettings('auth.host')
    if not host:
        host = os.uname()[1]
    return HTTPFound(location='http://'+host+':'+h.getSettings('auth.port')+h.getSettings('auth.path'))
