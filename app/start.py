''' Start of Application. This function is the gunicorn server '''

import os
import re

from dotenv import find_dotenv, load_dotenv

from app.http.providers.request import Request
from app.http.providers.routes import Route

load_dotenv(find_dotenv())

def app(environ, start_response):
    ''' Framework Engine '''
    os.environ.setdefault('REQUEST_METHOD', environ['REQUEST_METHOD'])
    os.environ.setdefault('URI_PATH', environ['PATH_INFO'])

    # if this is a post request
    if environ['REQUEST_METHOD'] == 'POST':
        get_post_params = int(environ.get('CONTENT_LENGTH')) if environ.get(
            'CONTENT_LENGTH') else 0
        body = environ['wsgi.input'].read(get_post_params) if get_post_params > 0 else ''
        environ['QUERY_STRING'] = body

    router = Route(environ)
    import routes.web
    routes = routes.web.ROUTES
    request = Request(environ)

    for route in routes:
        split_given_route = route.route_url.split('/')

        url_list = []
        regex = '^'
        for regex_route in split_given_route:
            if '@' in regex_route:
                if ':int' in regex_route:
                    regex += r'(\d+)'
                elif ':string' in regex_route:
                    regex += r'([a-zA-Z]+)'
                else:
                    # default
                    regex += r'(\w+)'
                regex += r'\/'

                # append the variable name passed @(variable):int to a list
                url_list.append(
                    regex_route.replace('@', '').replace(':int', '').replace(':string', '')
                )
            else:
                regex += regex_route + r'\/'

        regex += '$'
        if route.route_url.endswith('/'):
            matchurl = re.compile(regex.replace(r'\/\/$', r'\/$'))
        else:
            matchurl = re.compile(regex.replace(r'\/$', r'$'))

        try:
            parameter_dict = {}
            for index, value in enumerate(matchurl.match(router.url).groups()):
                parameter_dict[url_list[index]] = value
            request.set_params(parameter_dict)
        except AttributeError:
            pass


        print(request.url_params)

        if matchurl.match(router.url) and route.method_type == environ['REQUEST_METHOD'] and route.continueroute is True:
            print(route.method_type + ' Route: ' + router.url)
            data = router.get(route.route, route.output(request))
            break
        else:
            data = 'Route not found. Error 404'

    if data == 'Route not found. Error 404':
        # look at the API routes files
        import routes.api
        routes = routes.api.routes

        for route in routes:
            if route.url in router.url:
                data = route.fetch(request).output
                if data:
                    break
                else:
                    data = 'Route not found. Error 404'
            else:
                data = 'Route not found. Error 404'

    data = bytes(data, 'utf-8')

    start_response("200 OK", [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Content-Length", str(len(data)))
    ] + request.get_cookies())


    return iter([data])
