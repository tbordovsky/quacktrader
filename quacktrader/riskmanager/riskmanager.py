import abc


class RiskManager(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'get_risk_capital') and
                callable(subclass.get_risk_capital) or
                NotImplemented)

    @abc.abstractmethod
    def calculate_risk_reward_ratio(self) -> float:
        """Calculate the risk/reward ratio of a new trade"""
        raise NotImplementedError

    @abc.abstractmethod
    def calculate_probability_of_success(self) -> float:
        """Calculate the probability of success of a new trade"""
        raise NotImplementedError

    @abc.abstractmethod
    def calculate_maximum_acceptable_loss(self) -> int:
        """Calculate the maximum loss acceptable for a new trade"""
        raise NotImplementedError

    @abc.abstractmethod
    def calculate_expected_return(self) -> float:
        """Calculate the expected return and target profit of a new trade"""
        raise NotImplementedError

    @abc.abstractmethod
    def is_overexposed(self) -> bool:
        """Determine if a new trade maintains the balance or diversification of the portfolio"""
        raise NotImplementedError

    @abc.abstractmethod
    def has_reached_max_allowed_loss(self) -> bool:
        """Determine if a current position has reached the maximum allowed loss"""
        raise NotImplementedError

    @abc.abstractmethod
    def has_reached_target_profit(self) -> bool:
        """Determine if a current trade has reached the target profit"""
        raise NotImplementedError

    @abc.abstractmethod
    def is_within_risk_tolerance(self) -> float:
        """Determine if the reward of keeping the trade open is worth the risk"""
        raise NotImplementedError