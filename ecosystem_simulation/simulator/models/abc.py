from abc import ABCMeta, abstractmethod

class EntityId(metaclass=ABCMeta):
    @abstractmethod
    def serialize(self):
        return NotImplemented
    
    @staticmethod
    @abstractmethod
    def deserialize(data):
        return NotImplemented
