from abc import ABCMeta, abstractmethod

class EntityId(metaclass=ABCMeta):
    @abstractmethod
    def serialize(self):
        return NotImplemented
    
    @abstractmethod
    def deserialize(self, data):
        return NotImplemented
