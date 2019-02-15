class Manifest(object):

    def __init__(self, routes, settings):
        self._settings = settings
        self._routes = routes
        self._subscriptions = {}
        self._operations = {}
        self._manifest = {
            'id': settings.APP_ID,
            'resourceType': 'App',
            'type': 'app',
            'apiVersion': 1,
            'endpoint': {
                'url': settings.APP_URL,
                'type': 'http-rpc',
                'secret': settings.APP_SECRET,
            }
        }

    def build(self):
        if self._subscriptions:
            self._manifest['subscriptions'] = self._subscriptions
        if self._operations:
            self._manifest['operations'] = self._operations
        return self._manifest

    def subscription(self, path, entity):
        def wrap(func):
            self._subscriptions.update(
                {entity: {'handler': path}}
            )
            return self._routes.post(path)(func)
        return wrap

    # def operation(method, path, entity):
    #     def wrap(func):
    #         self._operations.update(
    #             {entity: {'handler': path}}
    #         )
    #         return routes.post(path)(func)
    #
    #     return wrap


