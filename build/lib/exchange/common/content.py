import json


class Content:
    def __init__(self):
        self._keys = []

    def get(self, param):
        if param in self._items():
            value = getattr(self, param, None)
            return value
        return None

    def set(self, param, value):
        if param in self._items():
            setattr(self, param, value)
            return True
        return False

    def _items(self, dic=False, filter_keys=False):
        if filter_keys:
            _keys = self._keys
        else:
            _keys = self.__dict__.keys()
        if dic:
            _items = dict([(i, self.__dict__[i]) for i in _keys if i[:1] != '_'])
        else:
            _items = [i for i in _keys if i[:1] != '_']
        return _items

    def default(self, o):
        return o.__dict__

    def to_json(self, _items=None, filter_keys=False):
        if _items and type(_items) == dict:
            pass
        else:
            _items = self.items(dic=True, filter_keys=filter_keys)
        return json.dumps(_items, default=self.default,
                          sort_keys=True, indent=4)

    def items(self, dic=True, filter_keys=False):
        return self._items(dic=dic, filter_keys=filter_keys)

    @classmethod
    def from_json(cls, msg):
        obj = cls()
        json_ = json.loads(msg)
        for (k, v) in json_.items():
            if k in obj._items():
                obj.set(k, v)
        return obj

    @classmethod
    def _parse(cls, msg, _map=None):
        obj = cls.from_json(msg)
        return obj

    def __iter__(self):
        for key,value in self.items(dic=True):
            yield (key, value)
