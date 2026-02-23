from abc import ABC, abstractmethod

class BaseParser(ABC):

    @abstractmethod
    def parse(self, text: str):
        """
        Debe devolver lista de movimientos normalizados.
        """
        pass