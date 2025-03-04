#include "SwapStar.h"

using TWS = TimeWindowSegment;

void SwapStar::updateRemovalCosts(Route *R1, CostEvaluator const &costEvaluator)
{
    for (Node *U = n(R1->depot); !U->isDepot(); U = n(U))
    {
        auto twData
            = TWS::merge(data.durationMatrix(), p(U)->twBefore, n(U)->twAfter);

        Distance const deltaDist = data.dist(p(U)->client, n(U)->client)
                                   - data.dist(p(U)->client, U->client)
                                   - data.dist(U->client, n(U)->client);

        removalCosts(R1->idx, U->client)
            = static_cast<Cost>(deltaDist)
              + costEvaluator.twPenalty(twData.totalTimeWarp())
              - costEvaluator.twPenalty(R1->timeWarp());
    }
}

void SwapStar::updateInsertionCost(Route *R,
                                   Node *U,
                                   CostEvaluator const &costEvaluator)
{
    auto &insertPositions = cache(R->idx, U->client);

    insertPositions = {};
    insertPositions.shouldUpdate = false;

    // Insert cost of U just after the depot (0 -> U -> ...)
    auto twData = TWS::merge(
        data.durationMatrix(), R->depot->twBefore, U->tw, n(R->depot)->twAfter);

    Distance deltaDist = data.dist(0, U->client)
                         + data.dist(U->client, n(R->depot)->client)
                         - data.dist(0, n(R->depot)->client);

    Cost deltaCost = static_cast<Cost>(deltaDist)
                     + costEvaluator.twPenalty(twData.totalTimeWarp())
                     - costEvaluator.twPenalty(R->timeWarp());

    insertPositions.maybeAdd(deltaCost, R->depot);

    for (Node *V = n(R->depot); !V->isDepot(); V = n(V))
    {
        // Insert cost of U just after V (V -> U -> ...)
        twData = TWS::merge(
            data.durationMatrix(), V->twBefore, U->tw, n(V)->twAfter);

        deltaDist = data.dist(V->client, U->client)
                    + data.dist(U->client, n(V)->client)
                    - data.dist(V->client, n(V)->client);

        deltaCost = static_cast<Cost>(deltaDist)
                    + costEvaluator.twPenalty(twData.totalTimeWarp())
                    - costEvaluator.twPenalty(R->timeWarp());

        insertPositions.maybeAdd(deltaCost, V);
    }
}

std::pair<Cost, Node *> SwapStar::getBestInsertPoint(
    Node *U, Node *V, CostEvaluator const &costEvaluator)
{
    auto &best_ = cache(V->route->idx, U->client);

    if (best_.shouldUpdate)  // then we first update the insert positions
        updateInsertionCost(V->route, U, costEvaluator);

    for (size_t idx = 0; idx != 3; ++idx)  // only OK if V is not adjacent
        if (best_.locs[idx] && best_.locs[idx] != V && n(best_.locs[idx]) != V)
            return std::make_pair(best_.costs[idx], best_.locs[idx]);

    // As a fallback option, we consider inserting in the place of V
    auto const twData = TWS::merge(
        data.durationMatrix(), p(V)->twBefore, U->tw, n(V)->twAfter);

    Distance const deltaDist = data.dist(p(V)->client, U->client)
                               + data.dist(U->client, n(V)->client)
                               - data.dist(p(V)->client, n(V)->client);
    Cost const deltaCost = static_cast<Cost>(deltaDist)
                           + costEvaluator.twPenalty(twData.totalTimeWarp())
                           - costEvaluator.twPenalty(V->route->timeWarp());

    return std::make_pair(deltaCost, p(V));
}

void SwapStar::init(Solution const &solution)
{
    LocalSearchOperator<Route>::init(solution);
    std::fill(updated.begin(), updated.end(), true);
}

Cost SwapStar::evaluate(Route *routeU,
                        Route *routeV,
                        CostEvaluator const &costEvaluator)
{
    best = {};

    if (updated[routeV->idx])
    {
        updateRemovalCosts(routeV, costEvaluator);
        updated[routeV->idx] = false;

        for (size_t idx = 1; idx != data.numClients() + 1; ++idx)
            cache(routeV->idx, idx).shouldUpdate = true;
    }

    if (updated[routeU->idx])
    {
        updateRemovalCosts(routeU, costEvaluator);
        updated[routeV->idx] = false;

        for (size_t idx = 1; idx != data.numClients() + 1; ++idx)
            cache(routeU->idx, idx).shouldUpdate = true;
    }

    for (Node *U = n(routeU->depot); !U->isDepot(); U = n(U))
        for (Node *V = n(routeV->depot); !V->isDepot(); V = n(V))
        {
            //if (checkSalvageSequenceConstraint(U, V)) {
            //    return std::numeric_limits<Cost>::max() / 1000;
            //}

            Cost deltaCost = 0;

            auto const uWeightDemand = data.client(U->client).demandWeight;
            auto const vWeightDemand = data.client(V->client).demandWeight;
            auto const weightDiff = uWeightDemand - vWeightDemand;

            auto const uVolumeDemand = data.client(U->client).demandVolume;
            auto const vVolumeDemand = data.client(V->client).demandVolume;
            auto const volumeDiff = uVolumeDemand - vVolumeDemand;

            auto const uSalvageDemand = data.client(U->client).demandSalvage;
            auto const vSalvageDemand = data.client(V->client).demandSalvage;
            auto const salvageDiff = uSalvageDemand - vSalvageDemand;

            auto const uStores = routeU->storeCount();
            auto const vStores = routeV->storeCount();
            auto const storesDiff = uStores - vStores;

            deltaCost += costEvaluator.weightPenalty(routeU->weight() - weightDiff,
                                                   data.weightCapacity());
            deltaCost += costEvaluator.volumePenalty(routeU->volume() - volumeDiff,
                                                   data.volumeCapacity());
            deltaCost += costEvaluator.salvagePenalty(routeU->salvage() - salvageDiff,
                                                   data.salvageCapacity());
            deltaCost += costEvaluator.storesPenalty(routeU->storeCount() - storesDiff,
                                                   data.routeStoreLimit());

            deltaCost -= costEvaluator.weightPenalty(routeU->weight(),
                                                   data.weightCapacity());
            deltaCost -= costEvaluator.volumePenalty(routeU->volume(),
                                                   data.volumeCapacity());
            deltaCost -= costEvaluator.salvagePenalty(routeU->salvage(),
                                                   data.salvageCapacity());
            deltaCost -= costEvaluator.storesPenalty(routeU->storeCount(),
                                                   data.routeStoreLimit());

            deltaCost += costEvaluator.weightPenalty(routeV->weight() + weightDiff,
                                                   data.weightCapacity());
            deltaCost += costEvaluator.volumePenalty(routeV->volume() + volumeDiff,
                                                   data.volumeCapacity());
            deltaCost += costEvaluator.salvagePenalty(routeV->salvage() + salvageDiff,
                                                   data.salvageCapacity());
            deltaCost += costEvaluator.storesPenalty(routeV->storeCount() + storesDiff,
                                                   data.routeStoreLimit());

            deltaCost -= costEvaluator.weightPenalty(routeV->weight(),
                                                   data.weightCapacity());
            deltaCost -= costEvaluator.volumePenalty(routeV->volume(),
                                                   data.volumeCapacity());
            deltaCost -= costEvaluator.salvagePenalty(routeV->salvage(),
                                                   data.salvageCapacity());
            deltaCost -= costEvaluator.storesPenalty(routeV->storeCount(),
                                                   data.routeStoreLimit());

            deltaCost += removalCosts(routeU->idx, U->client);
            deltaCost += removalCosts(routeV->idx, V->client);

            if (deltaCost >= 0)  // an early filter on many moves, before doing
                continue;        // costly work determining insertion points

            auto [extraV, UAfter] = getBestInsertPoint(U, V, costEvaluator);
            deltaCost += extraV;

            if (deltaCost >= 0)  // continuing here avoids evaluating another
                continue;        // costly insertion point below

            auto [extraU, VAfter] = getBestInsertPoint(V, U, costEvaluator);
            deltaCost += extraU;
            if (deltaCost < best.cost)
            {
                best.cost = deltaCost;

                best.U = U;
                best.UAfter = UAfter;

                best.V = V;
                best.VAfter = VAfter;
            }
        }

    // It is possible for positive delta costs to turn negative when we do a
    // complete evaluation. But in practice that almost never happens, and is
    // not worth spending time on.
    if (best.cost >= 0)
        return best.cost;

    // Now do a full evaluation of the proposed swap move. This includes
    // possible time warp penalties.
    Distance const current = data.dist(p(best.U)->client, best.U->client)
                             + data.dist(best.U->client, n(best.U)->client)
                             + data.dist(p(best.V)->client, best.V->client)
                             + data.dist(best.V->client, n(best.V)->client);

    Distance const proposed = data.dist(best.VAfter->client, best.V->client)
                              + data.dist(best.UAfter->client, best.U->client);

    Distance deltaDist = proposed - current;

    if (best.VAfter == p(best.U))
        // Insert in place of U
        deltaDist += data.dist(best.V->client, n(best.U)->client);
    else
        deltaDist += data.dist(best.V->client, n(best.VAfter)->client)
                     + data.dist(p(best.U)->client, n(best.U)->client)
                     - data.dist(best.VAfter->client, n(best.VAfter)->client);

    if (best.UAfter == p(best.V))
        // Insert in place of V
        deltaDist += data.dist(best.U->client, n(best.V)->client);
    else
        deltaDist += data.dist(best.U->client, n(best.UAfter)->client)
                     + data.dist(p(best.V)->client, n(best.V)->client)
                     - data.dist(best.UAfter->client, n(best.UAfter)->client);

    Cost deltaCost = static_cast<Cost>(deltaDist);

    // It is not possible to have UAfter == V or VAfter == U, so the positions
    // are always strictly different
    if (best.VAfter->position + 1 == best.U->position)
    {
        // Special case
        auto uTWS = TWS::merge(data.durationMatrix(),
                               best.VAfter->twBefore,
                               best.V->tw,
                               n(best.U)->twAfter);

        deltaCost += costEvaluator.twPenalty(uTWS.totalTimeWarp());
    }
    else if (best.VAfter->position < best.U->position)
    {
        auto uTWS = TWS::merge(
            data.durationMatrix(),
            best.VAfter->twBefore,
            best.V->tw,
            routeU->twBetween(best.VAfter->position + 1, best.U->position - 1),
            n(best.U)->twAfter);

        deltaCost += costEvaluator.twPenalty(uTWS.totalTimeWarp());
    }
    else
    {
        auto uTWS = TWS::merge(
            data.durationMatrix(),
            p(best.U)->twBefore,
            routeU->twBetween(best.U->position + 1, best.VAfter->position),
            best.V->tw,
            n(best.VAfter)->twAfter);

        deltaCost += costEvaluator.twPenalty(uTWS.totalTimeWarp());
    }

    if (best.UAfter->position + 1 == best.V->position)
    {
        // Special case
        auto vTWS = TWS::merge(data.durationMatrix(),
                               best.UAfter->twBefore,
                               best.U->tw,
                               n(best.V)->twAfter);

        deltaCost += costEvaluator.twPenalty(vTWS.totalTimeWarp());
    }
    else if (best.UAfter->position < best.V->position)
    {
        auto vTWS = TWS::merge(
            data.durationMatrix(),
            best.UAfter->twBefore,
            best.U->tw,
            routeV->twBetween(best.UAfter->position + 1, best.V->position - 1),
            n(best.V)->twAfter);

        deltaCost += costEvaluator.twPenalty(vTWS.totalTimeWarp());
    }
    else
    {
        auto vTWS = TWS::merge(
            data.durationMatrix(),
            p(best.V)->twBefore,
            routeV->twBetween(best.V->position + 1, best.UAfter->position),
            best.U->tw,
            n(best.UAfter)->twAfter);

        deltaCost += costEvaluator.twPenalty(vTWS.totalTimeWarp());
    }

    deltaCost -= costEvaluator.twPenalty(routeU->timeWarp());
    deltaCost -= costEvaluator.twPenalty(routeV->timeWarp());

    auto const uWeightDemand = data.client(best.U->client).demandWeight;
    auto const vWeightDemand = data.client(best.V->client).demandWeight;
    auto const uVolumeDemand = data.client(best.U->client).demandVolume;
    auto const vVolumeDemand = data.client(best.V->client).demandVolume;
    auto const uSalvageDemand = data.client(best.U->client).demandSalvage;
    auto const vSalvageDemand = data.client(best.V->client).demandSalvage;
    auto const uStores = routeU->storeCount();
    auto const vStores = routeV->storeCount();


    deltaCost += costEvaluator.weightPenalty(routeU->weight() - uWeightDemand + vWeightDemand,
                                           data.weightCapacity());
    deltaCost += costEvaluator.volumePenalty(routeU->volume() - uVolumeDemand + vVolumeDemand,
                                           data.volumeCapacity());
    deltaCost += costEvaluator.salvagePenalty(routeU->salvage() - uSalvageDemand + vSalvageDemand,
                                           data.salvageCapacity());
    deltaCost += costEvaluator.storesPenalty(routeU->storeCount() - uStores + vStores,
                                           data.routeStoreLimit());

    deltaCost
        -= costEvaluator.weightPenalty(routeU->weight(), data.weightCapacity());
    deltaCost
        -= costEvaluator.volumePenalty(routeU->volume(), data.volumeCapacity());
    deltaCost
        -= costEvaluator.salvagePenalty(routeU->salvage(), data.salvageCapacity());
    deltaCost
        -= costEvaluator.storesPenalty(routeU->storeCount(), data.routeStoreLimit());

    deltaCost += costEvaluator.weightPenalty(routeV->weight() + uWeightDemand - vWeightDemand,
                                           data.weightCapacity());
    deltaCost += costEvaluator.volumePenalty(routeV->volume() + uVolumeDemand - vVolumeDemand,
                                           data.volumeCapacity());
    deltaCost += costEvaluator.salvagePenalty(routeV->salvage() + uSalvageDemand - vSalvageDemand,
                                           data.salvageCapacity());
    deltaCost += costEvaluator.storesPenalty(routeV->storeCount() + uStores - vStores,
                                           data.routeStoreLimit());

    deltaCost
        -= costEvaluator.weightPenalty(routeV->weight(), data.weightCapacity());
    deltaCost
        -= costEvaluator.volumePenalty(routeV->volume(), data.volumeCapacity());
    deltaCost
        -= costEvaluator.salvagePenalty(routeV->salvage(), data.salvageCapacity());
    deltaCost
        -= costEvaluator.storesPenalty(routeV->storeCount(), data.routeStoreLimit());

    return deltaCost;
}

//bool SwapStar::checkSalvageSequenceConstraint(Node *U, Node *V) const
//{
//    // These sequences should violate the constraint
//    // S-B
//    // S-D
//    // B-B
//    // B-D
//    bool uIsClientDelivery = (data.client(U->client).demandWeight || data.client(U->client).demandVolume);
//    bool uIsClientSalvage = (data.client(U->client).demandSalvage != Measure<MeasureType::SALVAGE>(0));
//    bool uIsBoth = uIsClientDelivery && uIsClientSalvage;
//
//    bool vIsClientDelivery = (data.client(V->client).demandWeight || data.client(V->client).demandVolume);
//    bool vIsClientSalvage = (data.client(V->client).demandSalvage != Measure<MeasureType::SALVAGE>(0));
//    bool vIsBoth = vIsClientDelivery && vIsClientSalvage;
//
//    bool nextUClientDelivery = (data.client(n(U)->client).demandWeight || data.client(n(U)->client).demandVolume);
//    bool nextVClientDelivery = (data.client(n(V)->client).demandWeight || data.client(n(V)->client).demandVolume);
//
//    // S-B or S-D
//    if (uIsClientSalvage && !uIsBoth && ((vIsClientDelivery || vIsBoth) || nextVClientDelivery))
//        return true;
//
//    // B-B or B-D
//    if (uIsBoth && ((vIsBoth || vIsClientDelivery) || nextUClientDelivery))
//        return true;
//
//    return false;
//}

void SwapStar::apply([[maybe_unused]] Route *U, [[maybe_unused]] Route *V) const
{
    if (best.U && best.UAfter && best.V && best.VAfter)
    {
        best.U->insertAfter(best.UAfter);
        best.V->insertAfter(best.VAfter);
    }
}

void SwapStar::update(Route *U) { updated[U->idx] = true; }
