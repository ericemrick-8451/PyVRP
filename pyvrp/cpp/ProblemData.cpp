#include "ProblemData.h"

#include <cmath>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

ProblemData::Client::Client(Coordinate x,
                            Coordinate y,
                            Load demandWeight,
                            Load demandVolume,
                            Salvage demandSalvage,
                            Order clientOrder,
                            Store clientStore,
                            Duration serviceDuration,
                            Duration twEarly,
                            Duration twLate,
                            Cost prize,
                            bool required)
    : x(x),
      y(y),
      demandWeight(demandWeight),
      demandVolume(demandVolume),
      demandSalvage(demandSalvage),
      clientOrder(clientOrder),
      clientStore(clientStore),
      serviceDuration(serviceDuration),
      twEarly(twEarly),
      twLate(twLate),
      prize(prize),
      required(required)
{
    if (demandWeight < 0)
        throw std::invalid_argument("demandWeight must be >= 0");

    if (demandVolume < 0)
        throw std::invalid_argument("demandVolume must be >= 0");

    if (demandSalvage < 0)
        throw std::invalid_argument("demandSalvage must be >= 0");

    if (clientOrder < -1)
        throw std::invalid_argument("clientOrder must be >= -1");

    if (clientStore < -1)
        throw std::invalid_argument("clientStore must be >= -1");

    if (serviceDuration < 0)
        throw std::invalid_argument("service_duration must be >= 0");

    if (twEarly > twLate)
        throw std::invalid_argument("tw_early must be <= tw_late");

    if (prize < 0)
        throw std::invalid_argument("prize must be >= 0");
}

ProblemData::Client const &ProblemData::depot() const { return client(0); }

std::pair<double, double> const &ProblemData::centroid() const
{
    return centroid_;
}

Matrix<Distance> const &ProblemData::distanceMatrix() const { return dist_; }

Matrix<Duration> const &ProblemData::durationMatrix() const { return dur_; }

size_t ProblemData::numClients() const { return numClients_; }

size_t ProblemData::numVehicles() const { return numVehicles_; }

Load ProblemData::weightCapacity() const { return weightCapacity_; }

Load ProblemData::volumeCapacity() const { return volumeCapacity_; }

Salvage ProblemData::salvageCapacity() const { return salvageCapacity_; }

Order ProblemData::orderRouteLimit() const { return orderRouteLimit_; }

Store ProblemData::routeStoreLimit() const { return routeStoreLimit_; }

ProblemData::ProblemData(std::vector<Client> const &clients,
                         size_t numVehicles,
                         Load weightCap,
                         Load volumeCap,
                         Salvage salvageCap,
                         Order orderRouteLim,
                         Store routeStoreLim,
                         Matrix<Distance> const distMat,
                         Matrix<Duration> const durMat)
    : centroid_({0, 0}),
      dist_(std::move(distMat)),
      dur_(std::move(durMat)),
      clients_(clients),
      numClients_(std::max<size_t>(clients.size(), 1) - 1),
      numVehicles_(numVehicles),
      weightCapacity_(weightCap),
      volumeCapacity_(volumeCap),
      salvageCapacity_(salvageCap),
      orderRouteLimit_(orderRouteLim),
      routeStoreLimit_(routeStoreLim)
{
    for (size_t idx = 1; idx <= numClients(); ++idx)
    {
        centroid_.first += static_cast<double>(clients[idx].x) / numClients();
        centroid_.second += static_cast<double>(clients[idx].y) / numClients();
    }
}
