import abc


class MoneyManager(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'get_risk_capital') and
                callable(subclass.get_risk_capital) or
                NotImplemented)

    @abc.abstractmethod
    def get_risk_capital(self) -> int:
        """Determine the total capital that can be allocated to new positions"""
        raise NotImplementedError