#ifndef PYVRP_EXCHANGE_H
#define PYVRP_EXCHANGE_H

#include "LocalSearchOperator.h"
#include "TimeWindowSegment.h"

#include <cassert>

using TWS = TimeWindowSegment;

/**
 * Template class that exchanges N consecutive nodes from U's route (starting at
 * U) with M consecutive nodes from V's route (starting at V). As special cases,
 * (1, 0) is pure relocate, and (1, 1) pure swap.
 */
template <size_t N, size_t M> class Exchange : public LocalSearchOperator<Node>
{
    using LocalSearchOperator::LocalSearchOperator;

    static_assert(N >= M && N > 0, "N < M or N == 0 does not make sense");

    // Tests if the segment starting at node of given length contains the depot
    inline bool containsDepot(Node *node, size_t segLength) const;

    // Tests if the segments of U and V overlap in the same route
    inline bool overlap(Node *U, Node *V) const;

    // Tests if the segments of U and V are adjacent in the same route
    inline bool adjacent(Node *U, Node *V) const;

    // Special case that's applied when M == 0
    Cost evalRelocateMove(Node *U,
                          Node *V,
                          CostEvaluator const &costEvaluator) const;

    // Applied when M != 0
    Cost
    evalSwapMove(Node *U, Node *V, CostEvaluator const &costEvaluator) const;

    // Enforce salvage sequence constraint
//    bool checkSalvageSequenceConstraint(Node *U,
//                                        Node *V) const;

public:
    Cost
    evaluate(Node *U, Node *V, CostEvaluator const &costEvaluator) override;

    void apply(Node *U, Node *V) const override;
};

//template <size_t N, size_t M>
//bool Exchange<N, M>::checkSalvageSequenceConstraint(Node *U, Node *V) const
//{
//    // These sequences should violate the constraint
//    // S-B
//    // S-D
//    // B-B
//    // B-D
//    // The loops start from U and V respectively and go up to N and M nodes
//    for(size_t uIndex = 0; uIndex < N; ++uIndex, U = n(U)){
//        for(size_t vIndex = 0; vIndex < M; ++vIndex, V = n(V)){
//            bool uIsClientDelivery = (data.client(U->client).demandWeight || data.client(U->client).demandVolume);
//            bool uIsClientSalvage = (data.client(U->client).demandSalvage != Measure<MeasureType::SALVAGE>(0));
//            bool uIsBoth = uIsClientDelivery && uIsClientSalvage;
//        
//            bool vIsClientDelivery = (data.client(V->client).demandWeight || data.client(V->client).demandVolume);
//            bool vIsClientSalvage = (data.client(V->client).demandSalvage != Measure<MeasureType::SALVAGE>(0));
//            bool vIsBoth = vIsClientDelivery && vIsClientSalvage;
//        
//            bool nextUClientDelivery = (data.client(n(U)->client).demandWeight || data.client(n(U)->client).demandVolume);
//            bool nextVClientDelivery = (data.client(n(V)->client).demandWeight || data.client(n(V)->client).demandVolume);
//
//            // S-B or S-D
//            if (uIsClientSalvage && !uIsBoth && ((vIsClientDelivery || vIsBoth) || nextVClientDelivery))
//                return true;
//        
//            // B-B or B-D
//            if (uIsBoth && ((vIsBoth || vIsClientDelivery) || nextUClientDelivery))
//                return true;
//        }
//    }
//
//    return false;
//}

template <size_t N, size_t M>
bool Exchange<N, M>::containsDepot(Node *node, size_t segLength) const
{
    if (node->isDepot())
        return true;

    // size() is the position of the last node in the route. So the segment
    // must include the depot if position + move length - 1 (-1 since we're
    // also moving the node *at* position) is larger than size().
    return node->position + segLength - 1 > node->route->size();
}

template <size_t N, size_t M>
bool Exchange<N, M>::overlap(Node *U, Node *V) const
{
    return U->route == V->route
           // We need max(M, 1) here because when V is the depot and M == 0,
           // this would turn negative and wrap around to a large number.
           && U->position <= V->position + std::max<size_t>(M, 1) - 1
           && V->position <= U->position + N - 1;
}

template <size_t N, size_t M>
bool Exchange<N, M>::adjacent(Node *U, Node *V) const
{
    if (U->route != V->route)
        return false;

    return U->position + N == V->position || V->position + M == U->position;
}

template <size_t N, size_t M>
Cost Exchange<N, M>::evalRelocateMove(Node *U,
                                      Node *V,
                                      CostEvaluator const &costEvaluator) const
{
    std::cout << "Enter evalRelocateMove" << std::endl;
    auto const posU = U->position;
    auto const posV = V->position;

    assert(posU > 0);
    auto *endU = N == 1 ? U : (*U->route)[posU + N - 1];

    Distance const current = U->route->distBetween(posU - 1, posU + N)
                             + data.dist(V->client, n(V)->client);

    Distance const proposed = data.dist(V->client, U->client)
                              + U->route->distBetween(posU, posU + N - 1)
                              + data.dist(endU->client, n(V)->client)
                              + data.dist(p(U)->client, n(endU)->client);

    Cost deltaCost = static_cast<Cost>(proposed - current);

    Store uNumStores = U->route->storeCount();
    Store vNumStores = V->route->storeCount();

    bool uFoundStore = U->route->containsStore(data.client(U->client).clientStore);
    bool vFoundStore = V->route->containsStore(data.client(V->client).clientStore);

    if (U->route != V->route)
    {
        if (U->route->isFeasible() && deltaCost >= 0)
            return deltaCost;

        auto uTWS = TWS::merge(
            data.durationMatrix(), p(U)->twBefore, n(endU)->twAfter);

        deltaCost += costEvaluator.twPenalty(uTWS.totalTimeWarp());
        deltaCost -= costEvaluator.twPenalty(U->route->timeWarp());

        auto const weightDiff = U->route->weightBetween(posU, posU + N - 1);
        auto const volumeDiff = U->route->volumeBetween(posU, posU + N - 1);
        auto const salvageDiff = U->route->salvageBetween(posU, posU + N - 1);
        auto const uStoresDiff = U->route->storesBetween(posU, posU + N - 1);
        // auto const vStoresDiff = V->route->storesBetween(posV, posV + M - 1);

        if(uFoundStore){
            uNumStores = uNumStores - Store(1);
        }

        if(!vFoundStore){
            vNumStores = vNumStores + Store(1);
        }

        deltaCost += costEvaluator.weightPenalty(U->route->weight() - weightDiff, data.weightCapacity());
        deltaCost += costEvaluator.volumePenalty(U->route->volume() - volumeDiff, data.volumeCapacity());
        deltaCost += costEvaluator.salvagePenalty(U->route->salvage() - salvageDiff, data.salvageCapacity());
        deltaCost += costEvaluator.storesPenalty(Store(uNumStores) - uStoresDiff, data.routeStoreLimit());

        deltaCost -= costEvaluator.weightPenalty(U->route->weight(), data.weightCapacity());
        deltaCost -= costEvaluator.volumePenalty(U->route->volume(), data.volumeCapacity());
        deltaCost -= costEvaluator.salvagePenalty(U->route->salvage(), data.salvageCapacity());
        deltaCost -= costEvaluator.storesPenalty(Store(uNumStores), data.routeStoreLimit());

        if (deltaCost >= 0)    // if delta cost of just U's route is not enough
            return deltaCost;  // even without V, the move will never be good.

        deltaCost += costEvaluator.weightPenalty(V->route->weight() + weightDiff, data.weightCapacity());
        deltaCost += costEvaluator.volumePenalty(V->route->volume() + volumeDiff, data.volumeCapacity());
        deltaCost += costEvaluator.salvagePenalty(V->route->salvage() + salvageDiff, data.salvageCapacity());
        deltaCost += costEvaluator.storesPenalty(Store(vNumStores) + uStoresDiff, data.routeStoreLimit());

        deltaCost -= costEvaluator.weightPenalty(V->route->weight(), data.weightCapacity());
        deltaCost -= costEvaluator.volumePenalty(V->route->volume(), data.volumeCapacity());
        deltaCost -= costEvaluator.salvagePenalty(V->route->salvage(), data.salvageCapacity());
        deltaCost -= costEvaluator.storesPenalty(Store(vNumStores), data.routeStoreLimit());

        auto vTWS = TWS::merge(data.durationMatrix(),
                               V->twBefore,
                               U->route->twBetween(posU, posU + N - 1),
                               n(V)->twAfter);

        deltaCost += costEvaluator.twPenalty(vTWS.totalTimeWarp());
        deltaCost -= costEvaluator.twPenalty(V->route->timeWarp());
    }
    else  // within same route
    {
        auto const *route = U->route;

        if (!route->hasTimeWarp() && deltaCost >= 0)
            return deltaCost;

        if (posU < posV)
        {
            auto const tws = TWS::merge(data.durationMatrix(),
                                        p(U)->twBefore,
                                        route->twBetween(posU + N, posV),
                                        route->twBetween(posU, posU + N - 1),
                                        n(V)->twAfter);

            deltaCost += costEvaluator.twPenalty(tws.totalTimeWarp());
        }
        else
        {
            auto const tws = TWS::merge(data.durationMatrix(),
                                        V->twBefore,
                                        route->twBetween(posU, posU + N - 1),
                                        route->twBetween(posV + 1, posU - 1),
                                        n(endU)->twAfter);

            deltaCost += costEvaluator.twPenalty(tws.totalTimeWarp());
        }

        deltaCost -= costEvaluator.twPenalty(route->timeWarp());
    }

    return deltaCost;
}

template <size_t N, size_t M>
Cost Exchange<N, M>::evalSwapMove(Node *U,
                                  Node *V,
                                  CostEvaluator const &costEvaluator) const
{
    std::cout << "Enter evalSwapMove" << std::endl;
    auto const posU = U->position;
    auto const posV = V->position;

    assert(posU > 0 && posV > 0);
    auto *endU = N == 1 ? U : (*U->route)[posU + N - 1];
    auto *endV = M == 1 ? V : (*V->route)[posV + M - 1];

    assert(U->route && V->route);

    Distance const current = U->route->distBetween(posU - 1, posU + N)
                             + V->route->distBetween(posV - 1, posV + M);

    Distance const proposed
        //   p(U) -> V -> ... -> endV -> n(endU)
        // + p(V) -> U -> ... -> endU -> n(endV)
        = data.dist(p(U)->client, V->client)
          + V->route->distBetween(posV, posV + M - 1)
          + data.dist(endV->client, n(endU)->client)
          + data.dist(p(V)->client, U->client)
          + U->route->distBetween(posU, posU + N - 1)
          + data.dist(endU->client, n(endV)->client);

    Cost deltaCost = static_cast<Cost>(proposed - current);

    if (U->route != V->route)
    {
        if (U->route->isFeasible() && V->route->isFeasible() && deltaCost >= 0)
            return deltaCost;

        auto uTWS = TWS::merge(data.durationMatrix(),
                               p(U)->twBefore,
                               V->route->twBetween(posV, posV + M - 1),
                               n(endU)->twAfter);

        deltaCost += costEvaluator.twPenalty(uTWS.totalTimeWarp());
        deltaCost -= costEvaluator.twPenalty(U->route->timeWarp());

        auto const weightU = U->route->weightBetween(posU, posU + N - 1);
        auto const volumeU = U->route->volumeBetween(posU, posU + N - 1);
        auto const salvageU = U->route->salvageBetween(posU, posU + N - 1);
        auto const weightV = V->route->weightBetween(posV, posV + M - 1);
        auto const volumeV = V->route->volumeBetween(posV, posV + M - 1);
        auto const salvageV = V->route->salvageBetween(posV, posV + M - 1);
        auto const weightDiff = weightU - weightV;
        auto const volumeDiff = volumeU - volumeV;
        auto const salvageDiff = salvageU - salvageV;
        auto const storesDiff = U->route->storesBetween(posU, posU + N - 1);
        // auto const storesV = V->route->storesBetween(posV, posV + M - 1);

        deltaCost += costEvaluator.weightPenalty(U->route->weight() - weightDiff,
                                               data.weightCapacity());
        deltaCost += costEvaluator.volumePenalty(U->route->volume() - volumeDiff,
                                               data.volumeCapacity());
        deltaCost += costEvaluator.salvagePenalty(U->route->salvage() - salvageDiff,
                                               data.salvageCapacity());
        deltaCost += costEvaluator.storesPenalty(U->route->storeCount() - storesDiff,
                                               data.routeStoreLimit());
        deltaCost -= costEvaluator.weightPenalty(U->route->weight(),
                                               data.weightCapacity());
        deltaCost -= costEvaluator.volumePenalty(U->route->volume(),
                                               data.volumeCapacity());
        deltaCost -= costEvaluator.salvagePenalty(U->route->salvage(),
                                               data.salvageCapacity());
        deltaCost -= costEvaluator.storesPenalty(U->route->storeCount(),
                                               data.routeStoreLimit());

        auto vTWS = TWS::merge(data.durationMatrix(),
                               p(V)->twBefore,
                               U->route->twBetween(posU, posU + N - 1),
                               n(endV)->twAfter);

        deltaCost += costEvaluator.twPenalty(vTWS.totalTimeWarp());
        deltaCost -= costEvaluator.twPenalty(V->route->timeWarp());

        deltaCost += costEvaluator.weightPenalty(V->route->weight() + weightDiff,
                                               data.weightCapacity());
        deltaCost += costEvaluator.volumePenalty(V->route->volume() + volumeDiff,
                                               data.volumeCapacity());
        deltaCost += costEvaluator.salvagePenalty(V->route->salvage() + salvageDiff,
                                               data.salvageCapacity());
        deltaCost += costEvaluator.storesPenalty(V->route->storeCount() + storesDiff,
                                               data.routeStoreLimit());
        deltaCost -= costEvaluator.weightPenalty(V->route->weight(),
                                               data.weightCapacity());
        deltaCost -= costEvaluator.volumePenalty(V->route->volume(),
                                               data.volumeCapacity());
        deltaCost -= costEvaluator.salvagePenalty(V->route->salvage(),
                                               data.salvageCapacity());
        deltaCost -= costEvaluator.storesPenalty(V->route->storeCount(),
                                               data.routeStoreLimit());
    }
    else  // within same route
    {
        auto const *route = U->route;

        if (!route->hasTimeWarp() && deltaCost >= 0)
            return deltaCost;

        if (posU < posV)
        {
            auto const tws = TWS::merge(data.durationMatrix(),
                                        p(U)->twBefore,
                                        route->twBetween(posV, posV + M - 1),
                                        route->twBetween(posU + N, posV - 1),
                                        route->twBetween(posU, posU + N - 1),
                                        n(endV)->twAfter);

            deltaCost += costEvaluator.twPenalty(tws.totalTimeWarp());
        }
        else
        {
            auto const tws = TWS::merge(data.durationMatrix(),
                                        p(V)->twBefore,
                                        route->twBetween(posU, posU + N - 1),
                                        route->twBetween(posV + M, posU - 1),
                                        route->twBetween(posV, posV + M - 1),
                                        n(endU)->twAfter);

            deltaCost += costEvaluator.twPenalty(tws.totalTimeWarp());
        }

        deltaCost -= costEvaluator.twPenalty(U->route->timeWarp());
    }

    return deltaCost;
}

template <size_t N, size_t M>
Cost Exchange<N, M>::evaluate(Node *U,
                              Node *V,
                              CostEvaluator const &costEvaluator)
{
    //if (checkSalvageSequenceConstraint(U, V))
    //    return std::numeric_limits<Cost>::max() / 1000;

    if (containsDepot(U, N) || overlap(U, V))
        return 0;

    if constexpr (M > 0)
        if (containsDepot(V, M))
            return 0;

    if constexpr (M == 0)  // special case where nothing in V is moved
    {
        if (U == n(V))
            return 0;

        return evalRelocateMove(U, V, costEvaluator);
    }
    else
    {
        if constexpr (N == M)  // symmetric, so only have to evaluate this once
            if (U->client >= V->client)
                return 0;

        if (adjacent(U, V))
            return 0;

        return evalSwapMove(U, V, costEvaluator);
    }
}

template <size_t N, size_t M> void Exchange<N, M>::apply(Node *U, Node *V) const
{
    auto *uToInsert = N == 1 ? U : (*U->route)[U->position + N - 1];
    auto *insertUAfter = M == 0 ? V : (*V->route)[V->position + M - 1];

    // Insert these 'extra' nodes of U after the end of V...
    for (size_t count = 0; count != N - M; ++count)
    {
        auto *prev = p(uToInsert);
        uToInsert->insertAfter(insertUAfter);
        uToInsert = prev;
    }

    // ...and swap the overlapping nodes!
    for (size_t count = 0; count != M; ++count)
    {
        U->swapWith(V);
        U = n(U);
        V = n(V);
    }
}

#endif  // PYVRP_EXCHANGE_H
