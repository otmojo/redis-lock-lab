from collections import defaultdict
import json

class Metrics:
    _data = defaultdict(list)

    @classmethod
    def record(cls, name, value):
        cls._data[name].append(value)

    @classmethod
    def get(cls, name):
        return cls._data[name]
        
    @classmethod
    def reset(cls):
        cls._data.clear()

    @classmethod
    def dump(cls):
        return json.dumps(cls._data, indent=2)
