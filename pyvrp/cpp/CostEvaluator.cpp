#include "CostEvaluator.h"

#include <limits>

CostEvaluator::CostEvaluator(Cost weightCapacityPenalty, 
                             Cost volumeCapacityPenalty, 
                             Cost salvageCapacityPenalty, 
                             Cost storesLimitPenalty, 
                             Cost timeWarpPenalty)
    : weightCapacityPenalty(weightCapacityPenalty), 
      volumeCapacityPenalty(volumeCapacityPenalty), 
      salvageCapacityPenalty(salvageCapacityPenalty), 
      storesLimitPenalty(storesLimitPenalty), 
      timeWarpPenalty(timeWarpPenalty)
{
}

Cost CostEvaluator::penalisedCost(Solution const &solution) const
{
    // Standard objective plus penalty terms for weight, volume, salvage and time-related
    // infeasibilities.
    Cost cur_cost =  static_cast<Cost>(solution.distance()) + solution.uncollectedPrizes()
           + weightPenaltyExcess(solution.excessWeight())
           + volumePenaltyExcess(solution.excessVolume())
           + salvagePenaltyExcess(solution.excessSalvage())
           + storesPenaltyExcess(solution.excessStores())
           + twPenalty(solution.timeWarp());
    return cur_cost;
}

Cost CostEvaluator::cost(Solution const &solution) const
{
    // Penalties are zero when the solution is feasible, so we can fall back to
    // penalised cost in that case.
    return solution.isFeasible() ? penalisedCost(solution)
                                 : std::numeric_limits<Cost>::max();
}
