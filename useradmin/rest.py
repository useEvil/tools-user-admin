import time
import urllib
import logging
import calendar
import datetime as date
import webhelpers.paginate as paginate

from re import findall
from operator import itemgetter, attrgetter

from useradmin.models import DBSession, User, Group, Permission, Application
from useradmin.authorization import AuthorizationControl
from useradmin.helpers import *

Log = logging.getLogger(__name__)


@AuthorizationControl('administer')
def listing(request):
    Log.debug('listing')
    """ json data for deals """
    params       = request.params
    currentPage  = int(params.get('page') or 1)
    itemsPerPage = int(params.get('rp')   or 30)
    sortName     = params.get('sortname')  or 'dealEndDate'
    sortOrder    = params.get('sortorder') or 'desc'
    query        = params.get('query')
    type         = params.get('qtype')  or ''
    qrange       = params.get('range')  or ''
    form         = params.get('format') or None
    if query:
        users = User().getAll(query)
        page  = paginate.Page(users, page=currentPage, items_per_page=itemsPerPage)
        total = page.item_count
    else:
        offset = (currentPage - 1) * itemsPerPage
        users  = User().getSet(itemsPerPage, offset)
        total  = User().getTotal()
        page   = paginate.Page(users, page=1, items_per_page=itemsPerPage)
    result          = { }
    result['rows']  = [ ]
    result['page']  = currentPage
    result['total'] = total
    for user in page.items:
        groups = ''
        for g in user.groups:
            groups = groups + g.groupName + "<br />\n"
        row = {'id': user.id, 'cell': [user.id]}
        row['cell'].append('<a style="color: blue;text-decoration: underline;" href="#" class="admin edit_details" id="user_%d">%s</a>'%(user.id, user.userName))
        row['cell'].append(user.firstName)
        row['cell'].append(user.lastName)
        row['cell'].append('<a style="color: blue;text-decoration: underline;" href="mailto:%s" title="%s">%s</a>'%(user.emailAddress, user.emailAddress, user.emailAddress))
        row['cell'].append(groups)
        row['cell'].append(user.effectiveStart.strftime(getSettings('date.short')))
        row['cell'].append(user.effectiveEnd.strftime(getSettings('date.short')))
        row['cell'].append('<img class="admin edit_details" alt="Edit User" title="Edit User" src="/static/images/edit.png" id="user_%s" />&nbsp;<img class="admin delete_details" alt="Delete User" title="Delete User" src="/static/images/delete.png" id="user_delete_%s" />'%(user.id, user.id))
        result['rows'].append(row)
    return result

@AuthorizationControl('administer')
def create(request):
    type    = request.matchdict['type']
    params  = request.params
    try:
        object = _get_object(type)
        object.create(params)
    except:
        return { 'status': 404, 'message': 'Failed to Create Entry', 'type': type }
    return { 'status': 200, 'message': 'Successfully Created Entry', 'type': type }

@AuthorizationControl('administer')
def get(request):
    type = request.matchdict['type']
    try:
        object  = _get_object(type)
        results = object.getAll()
        objects = [ ]
        for result in results:
            objects.append(result.jsonify())
    except:
        return { 'status': 404, 'message': 'Failed to Get Entries', 'type': type }
    return { 'status': 200, 'results': objects, 'type': type }

@AuthorizationControl('administer')
def view(request):
    type = request.matchdict['type']
    id   = request.matchdict['id']
    try:
        object = _get_object(type)
        result = object.getById(id)
    except:
        return { 'status': 404, 'message': 'Failed to Get Entry', 'type': type }
    return { 'status': 200, 'result': result.jsonify(), 'type': type }

@AuthorizationControl('administer')
def edit(request):
    type   = request.matchdict['type']
    id     = request.matchdict['id']
    params = request.params
    try:
        object = _get_object(type)
        result = object.getById(id)
        result.update(params)
    except:
        return { 'status': 404, 'message': 'Failed to Edit Entry', 'type': type }
    return { 'status': 200, 'message': 'Successfully Edit Entry', 'type': type }

@AuthorizationControl('administer')
def delete(request):
    type = request.matchdict['type']
    id   = request.matchdict['id']
    try:
        object = _get_object(type)
        result = object.getById(id)
        result.delete()
    except:
        return { 'status': 404, 'message': 'Failed to Delete Entry', 'type': type }
    return { 'status': 200, 'message': 'Successfully Delete Entry', 'type': type }

@AuthorizationControl('administer')
def error(request):
    return { 'status': request.matchdict['id'], 'message': 'You Do Not have permissions to Approve Release Ticket' }

def _get_object(type):
    if type == 'application':
        return Application()
    elif type == 'group':
        return Group()
    elif type == 'permission':
        return Permission()
    else:
        return User()

def _message_sql_query(params=None):
    start   = params.get('start')
    end     = params.get('end')
    query   = params.get('query')
    type    = params.get('qtype') or ''
    results = None
    if end and start:
        start, end = getStartEnd(start, end, 'long')
    if start and not end:
        start, end = getStartEnd(start, None, 'long')
    if end and not start:
        start, end = getStartEnd(None, end, 'long')
    results  = HundredPushups().getByCreatedDate(start, end, query, type)
    return results
