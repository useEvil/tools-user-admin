from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from useradmin.models import initialize_sql

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    my_session_factory = UnencryptedCookieSessionFactoryConfig('itsaseekreet')
    initialize_sql(engine)
    config = Configurator(settings=settings, session_factory = my_session_factory)
    config.add_static_view('static', 'useradmin:static', cache_max_age=3600)
    config.add_route('na', '/')
    config.add_route('index', '/index')
    config.add_route('logout', '/logout')

    config.add_route('REST_listing', '/REST/admin/listing')
    config.add_route('REST_create', '/REST/admin/create/{type}')
    config.add_route('REST_get', '/REST/admin/get/{type}')
    config.add_route('REST_edit', '/REST/admin/edit/{type}/{id}')
    config.add_route('REST_view', '/REST/admin/view/{type}/{id}')
    config.add_route('REST_delete', '/REST/admin/delete/{type}/{id}')
    config.add_route('REST_error', '/REST/admin/error/{id}')

    config.add_view('useradmin.views.index', route_name='na', renderer='templates/index.pt')
    config.add_view('useradmin.views.index', route_name='index', renderer='templates/index.pt')
    config.add_view('useradmin.views.logout', route_name='logout')

    config.add_view('useradmin.rest.listing', route_name='REST_listing', renderer='json', request_method='GET')
    config.add_view('useradmin.rest.create', route_name='REST_create', renderer='json', request_method='POST')
    config.add_view('useradmin.rest.get', route_name='REST_get', renderer='json', request_method='GET')
    config.add_view('useradmin.rest.edit', route_name='REST_edit', renderer='json', request_method='POST')
    config.add_view('useradmin.rest.view', route_name='REST_view', renderer='json', request_method='GET')
    config.add_view('useradmin.rest.delete', route_name='REST_delete', renderer='json', request_method='GET')
    config.add_view('useradmin.rest.error', route_name='REST_error', renderer='json', request_method='GET')
    return config.make_wsgi_app()
