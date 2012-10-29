import os
import logging
import simplejson

from pyramid.httpexceptions import HTTPFound
from decorator import decorator
from urllib2 import urlopen
from time import time

from useradmin.helpers import *

log   = logging.getLogger(__name__)

class AuthorizationControl(object):
    def __init__(self, permission):
        """
        If there are decorator arguments, the function
        to be decorated is not passed to the constructor!
        """
#        log.debug('Inside __init__()')
        self.permission = permission

    def loadAuthenticationForToken(self,id):
        path = getSettings('auth.url') + '/auth_extended?id=' + id + '&app=toolsuseradmin'
        log.debug('url: ' + path)
        return urlopen(path)

    def isAuthorized(self,id):
        """
        Monkey patch this method during unit testing to return True all the time.
        
        ex:
        def isAuthorized(self,id):
            return True

        AuthorizationControl.isAuthorized = isAuthorized
        """
        if id is None:
            return False
        try:
            log.debug('id: ' + id)
            response = self.loadAuthenticationForToken(id)
            raw_json_data = response.read()
            json_data = simplejson.loads(raw_json_data)
            log.debug('Raw json: ' + raw_json_data)
            log.debug('username: ' + json_data['id'])
            self.session['userId'] = json_data['id']
            self.session['permissions'] = json_data['permissions']
            self.session['meta'] = json_data['meta']
            self.session['last_update'] = time()
            self.session.changed()
            return True
        except Exception as e:
            log.warn(e)
            log.warn('Unable to determine userId')
            return False

    def __call__(self, f):
        """
        If there are decorator arguments, __call__() is only called
        once, as part of the decoration process! You can only give
        it a single argument, which is the function object.
        """
        def wrapped_f(f, *args, **kwargs):
            log.debug('Decorator arguments: ' + self.permission)
            self.session = args[0].session
            self.request = args[0]
            log.debug(self.session)
            
            id = None
            if getSettings('auth.enable') == 'True':
                if 'token' in self.session:
                    id = self.session['token']
                if 'id' in self.request.params:
                    id = self.request.params['id']
                    self.session['token'] = id
                if not self.isAuthorized(id):
                    return self.redirect_to_auth(400)
                if 'permissions' in self.session and self.permission in self.session['permissions']:
                    pass
                else:
                    return self.redirect_to_auth(401)
            value = f(*args, **kwargs)
            log.debug('After f(*args)')
            return value

        """ Note: http://www.siafoo.net/article/68 for this """
        return decorator(wrapped_f)(f)

    def redirect_to_auth(self, error=None):
        host = getSettings('auth.host')
        if not host:
            host = os.uname()[1]
        path = 'http://' + host + ':' + getSettings('auth.port') + getSettings('auth.path')
        if error:
            path = path + '/index?error=' + str(error)
        else:
            path = path + '/index?came_from=' + path + '/toolsuseradmin'
#        print '==== path [%s]'%(path)
        return HTTPFound(location=path)
