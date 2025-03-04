from dataclasses import dataclass
from statistics import fmean
from typing import List

from pyvrp._CostEvaluator import CostEvaluator


@dataclass
class PenaltyParams:
    """
    The penalty manager parameters.

    Parameters
    ----------
    init_weight_capacity_penalty
        Initial penalty on excess weight capacity. This is the amount by which
        one unit of excess weight capacity is penalised in the objective, at the
        start of the search.
    init_volume_capacity_penalty
        Initial penalty on excess volume capacity. This is the amount by which
        one unit of excess volume capacity is penalised in the objective, at the
        start of the search.
    init_salvage_penalty
        Initial penalty on nonterminal salvage pickups. This is a function of 
        number of salvage pickups that occur before the last delivery stop.
    init_time_warp_penalty
        Initial penalty on time warp. This is the amount by which one unit of
        time warp (time window violations) is penalised in the objective, at
        the start of the search.
    repair_booster
        A repair booster value :math:`r \\ge 1`. This value is used to
        temporarily multiply the current penalty terms, to force feasibility.
        See also
        :meth:`~pyvrp.PenaltyManager.PenaltyManager.get_booster_cost_evaluator`.
    num_registrations_between_penalty_updates
        Number of feasibility registrations between penalty value updates. The
        penalty manager updates the penalty terms every once in a while based
        on recent feasibility registrations. This parameter controls how often
        such updating occurs.
    penalty_increase
        Amount :math:`p_i \\ge 1` by which the current penalties are
        increased when insufficient feasible solutions (see
        :py:attr:`~target_feasible`) have been found amongst the most recent
        registrations. The penalty values :math:`v` are updated as
        :math:`v \\gets p_i v`.
    penalty_decrease
        Amount :math:`p_d \\in [0, 1]` by which the current penalties are
        decreased when sufficient feasible solutions (see
        :py:attr:`~target_feasible`) have been found amongst the most recent
        registrations. The penalty values :math:`v` are updated as
        :math:`v \\gets p_d v`.
    target_feasible
        Target percentage :math:`p_f \\in [0, 1]` of feasible registrations
        in the last :py:attr:`~num_registrations_between_penalty_updates`
        registrations. This percentage is used to update the penalty terms:
        when insufficient feasible solutions have been registered, the
        penalties are increased; similarly, when too many feasible solutions
        have been registered, the penalty terms are decreased. This ensures a
        balanced population, with a fraction :math:`p_f` feasible and a
        fraction :math:`1 - p_f` infeasible solutions.

    Attributes
    ----------
    init_weight_capacity_penalty
        Initial penalty on excess weight capacity.
    init_volume_capacity_penalty
        Initial penalty on excess volume capacity.
    init_salvage_penalty
	Initial penalty on nonterminal salvage pickups.
    init_time_warp_penalty
        Initial penalty on time warp.
    repair_booster
        A repair booster value.
    num_registrations_between_penalty_updates
        Number of feasibility registrations between penalty value updates.
    penalty_increase
        Amount :math:`p_i \\ge 1` by which the current penalties are
        increased when insufficient feasible solutions (see
        :py:attr:`~target_feasible`) have been found amongst the most recent
        registrations.
    penalty_decrease
        Amount :math:`p_d \\in [0, 1]` by which the current penalties are
        decreased when sufficient feasible solutions (see
        :py:attr:`~target_feasible`) have been found amongst the most recent
        registrations.
    target_feasible
        Target percentage :math:`p_f \\in [0, 1]` of feasible registrations
        in the last :py:attr:`~num_registrations_between_penalty_updates`
        registrations.
    """

    init_weight_capacity_penalty: int = 20
    init_volume_capacity_penalty: int = 20
    init_salvage_penalty: int = 20
    init_time_warp_penalty: int = 6
    repair_booster: int = 12
    num_registrations_between_penalty_updates: int = 50
    penalty_increase: float = 1.34
    penalty_decrease: float = 0.32
    target_feasible: float = 0.43

    def __post_init__(self):
        if not self.penalty_increase >= 1.0:
            raise ValueError("Expected penalty_increase >= 1.")

        if not 0.0 <= self.penalty_decrease <= 1.0:
            raise ValueError("Expected penalty_decrease in [0, 1].")

        if not 0.0 <= self.target_feasible <= 1.0:
            raise ValueError("Expected target_feasible in [0, 1].")

        if not self.repair_booster >= 1.0:
            raise ValueError("Expected repair_booster >= 1.")


class PenaltyManager:
    """
    Creates a PenaltyManager instance.

    This class manages time warp and load penalties, and provides penalty terms
    for given time warp and load values. It updates these penalties based on
    recent history, and can be used to provide a temporary penalty booster
    object that increases the penalties for a short duration.

    Parameters
    ----------
    params, optional
        PenaltyManager parameters. If not provided, a default will be used.
    """

    def __init__(
        self,
        params: PenaltyParams = PenaltyParams(),
    ):
        self._params = params
        self._weight_feas: List[bool] = []  # tracks recent volume load feasibility
        self._volume_feas: List[bool] = []  # tracks recent weight load feasibility
        self._salvage_feas: List[bool] = []  # tracks recent salvage feasibility
        self._time_feas: List[bool] = []  # track recent time feasibility
        self._weight_capacity_penalty = params.init_weight_capacity_penalty
        self._volume_capacity_penalty = params.init_volume_capacity_penalty
        self._salvage_penalty = params.init_salvage_penalty
        self._tw_penalty = params.init_time_warp_penalty
        self._cost_evaluator = CostEvaluator(
            self._weight_capacity_penalty, 
            self._volume_capacity_penalty,
            self._salvage_penalty,
            self._tw_penalty
        )
        self._booster_cost_evaluator = CostEvaluator(
            self._weight_capacity_penalty * self._params.repair_booster,
            self._volume_capacity_penalty * self._params.repair_booster,
            self._salvage_penalty * self._params.repair_booster,
            self._tw_penalty * self._params.repair_booster,
        )

    def _update_cost_evaluators(self):
        # Updates the cost evaluators given new penalty values
        self._cost_evaluator = CostEvaluator(
            self._weight_capacity_penalty, 
            self._volume_capacity_penalty,
            self._salvage_penalty,
            self._tw_penalty
        )
        self._booster_cost_evaluator = CostEvaluator(
            self._weight_capacity_penalty * self._params.repair_booster,
            self._volume_capacity_penalty * self._params.repair_booster,
            self._salvage_penalty * self._params.repair_booster,
            self._tw_penalty * self._params.repair_booster,
        )

    def _compute(self, penalty: int, feas_percentage: float) -> int:
        # Computes and returns the new penalty value, given the current value
        # and the percentage of feasible solutions since the last update.
        diff = self._params.target_feasible - feas_percentage
        # TODO make 0.05 a parameter
        if -0.05 < diff < 0.05:
            return penalty

        # +- 1 to ensure we do not get stuck at the same integer values,
        # bounded to [1, 1000] to avoid overflow in cost computations.
        if diff > 0:
            return int(
                min(self._params.penalty_increase * penalty + 1, 1000.0)
            )
        else:
            return int(max(self._params.penalty_decrease * penalty - 1, 1.0))

    def register_weight_feasible(self, is_weight_feasible: bool):
        """
        Registers another capacity feasibility result. The current weight penalty
        is updated once sufficiently many results have been gathered.

        Parameters
        ----------
        is_weight_feasible
            Boolean indicating whether the last solution was feasible w.r.t.
            the capacity constraint.
        """
        self._weight_feas.append(is_weight_feasible)
        if (
            len(self._weight_feas)
            == self._params.num_registrations_between_penalty_updates
        ):
            avg = fmean(self._weight_feas)
            self._weight_capacity_penalty = self._compute(self._weight_capacity_penalty, avg)
            print("REGISTER WEIGHT", self._weight_capacity_penalty)
            self._update_cost_evaluators()
            self._weight_feas.clear()

    def register_volume_feasible(self, is_volume_feasible: bool):
        """
        Registers another capacity feasibility result. The current volume penalty
        is updated once sufficiently many results have been gathered. 
        
        Parameters
        ----------
        is_volume_feasible
            Boolean indicating whether the last solution was feasible w.r.t. 
            the capacity constraint.
        """
        self._volume_feas.append(is_volume_feasible)
        if ( 
            len(self._volume_feas)
            == self._params.num_registrations_between_penalty_updates
        ):
            avg = fmean(self._volume_feas)
            self._volume_capacity_penalty = self._compute(self._volume_capacity_penalty, avg)
            self._update_cost_evaluators()
            self._volume_feas.clear()

    def register_salvage_feasible(self, is_salvage_feasible: bool):
        """
        Registers salvage feasibility result. The current salvage penalty
        is updated once sufficiently many results have been gathered.

        Parameters
        ----------
        is_salvage_feasible
            Boolean indicating whether the last solution was feasible w.r.t.
            the salvage constraint.
        """
        self._salvage_feas.append(is_salvage_feasible)
        if (
            len(self._salvage_feas)
            == self._params.num_registrations_between_penalty_updates
        ):
            avg = fmean(self._salvage_feas)
            self._salvage_penalty = self._compute(self._salvage_penalty, avg)
            print("REGISTER SALVAGE CAP", self._salvage_penalty)
            self._update_cost_evaluators()
            self._salvage_feas.clear()

    def register_time_feasible(self, is_time_feasible: bool):
        """
        Registers another time feasibility result. The current time warp
        penalty is updated once sufficiently many results have been gathered.

        Parameters
        ----------
        is_time_feasible
            Boolean indicating whether the last solution was feasible w.r.t.
            the time constraint.
        """
        self._time_feas.append(is_time_feasible)
        if (
            len(self._time_feas)
            == self._params.num_registrations_between_penalty_updates
        ):
            avg = fmean(self._time_feas)
            self._tw_penalty = self._compute(self._tw_penalty, avg)
            self._update_cost_evaluators()
            self._time_feas.clear()

    def get_cost_evaluator(self) -> CostEvaluator:
        """
        Get a cost evaluator for the current penalty values.

        Returns
        -------
        CostEvaluator
            A CostEvaluator instance that uses the current penalty values.
        """
        return self._cost_evaluator

    def get_booster_cost_evaluator(self):
        """
        Get a cost evaluator for the boosted current penalty values.

        Returns
        -------
        CostEvaluator
            A CostEvaluator instance that uses the booster penalty values.
        """
        return self._booster_cost_evaluator
