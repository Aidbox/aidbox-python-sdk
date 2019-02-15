class Manifest(object):

    def __init__(self, settings):
        self._settings = settings
        self._subscriptions = {}
        self._subscription_handlers = {}
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

    def subscription(self, entity):
        def wrap(func):
            path = func.__name__
            self._subscriptions[entity] = {'handler': path}
            self._subscription_handlers[path] = func
            return func
        return wrap

    def get_subscription_handler(self, path):
        return self._subscription_handlers.get(path)

    # def operation(method, path, entity):
    #     def wrap(func):
    #         self._operations.update(
    #             {entity: {'handler': path}}
    #         )
    #         return routes.post(path)(func)
    #
    #     return wrap
