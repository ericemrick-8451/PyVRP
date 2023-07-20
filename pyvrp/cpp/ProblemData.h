#ifndef PYVRP_PROBLEMDATA_H
#define PYVRP_PROBLEMDATA_H

#include "Matrix.h"
#include "Measure.h"
#include "XorShift128.h"

#include <iosfwd>
#include <vector>

class ProblemData
{
public:
    struct Client
    {
        Coordinate const x;
        Coordinate const y;
        Load const demandWeight;
        Load const demandVolume;
        Salvage const demandSalvage;
        Duration const serviceDuration;
        Duration const twEarly;      // Earliest possible start of service
        Duration const twLate;       // Latest possible start of service
        Cost const prize = 0;        // Prize for visiting this client
        bool const required = true;  // Must client be in solution?

        Client(Coordinate x,
               Coordinate y,
               Load demandWeight = 0,
               Load demandVolume = 0,
               Salvage demandSalvage = 0,
               Duration serviceDuration = 0,
               Duration twEarly = 0,
               Duration twLate = 0,
               Cost prize = 0,
               bool required = true);
    };

private:
    std::pair<double, double> centroid_;  // Centroid of client locations
    Matrix<Distance> const dist_;         // Distance matrix (+depot)
    Matrix<Duration> const dur_;          // Duration matrix (+depot)
    std::vector<Client> clients_;         // Client (+depot) information

    size_t const numClients_;
    size_t const numVehicles_;
    Load const weightCapacity_;
    Load const volumeCapacity_;
    Salvage const salvageCapacity_;

public:
    /**
     * @param client Client whose data to return.
     * @return A struct containing the indicated client's information.
     */
    [[nodiscard]] inline Client const &client(size_t client) const;

    /**
     * @return A struct containing the depot's information.
     */
    [[nodiscard]] Client const &depot() const;

    /**
     * @return Centroid of client locations.
     */
    [[nodiscard]] std::pair<double, double> const &centroid() const;

    /**
     * Returns the distance between the indicated two clients.
     *
     * @param first  First client.
     * @param second Second client.
     * @return distance from the first to the second client.
     */
    [[nodiscard]] inline Distance dist(size_t first, size_t second) const;

    /**
     * Returns the travel duration between the indicated two clients.
     *
     * @param first  First client.
     * @param second Second client.
     * @return Travel duration from the first to the second client.
     */
    [[nodiscard]] inline Duration duration(size_t first, size_t second) const;

    /**
     * @return The full travel distance matrix.
     */
    [[nodiscard]] Matrix<Distance> const &distanceMatrix() const;

    /**
     * @return The full travel duration matrix.
     */
    [[nodiscard]] Matrix<Duration> const &durationMatrix() const;

    /**
     * @return Total number of clients in this instance.
     */
    [[nodiscard]] size_t numClients() const;

    /**
     * @return Total number of vehicles available in this instance.
     */
    [[nodiscard]] size_t numVehicles() const;

    /**
     * @return Weight capacity of each vehicle in this instance.
     */
    [[nodiscard]] Load weightCapacity() const;

    /**
     * @return Volume capacity of each vehicle in this instance.
     */
    [[nodiscard]] Load volumeCapacity() const;

    /**
     * @return Number of nonterminal salvage pickup capacity for each route in this instance.
     */
    [[nodiscard]] Salvage salvageCapacity() const;

    /**
     * Constructs a ProblemData object with the given data. Assumes the list of
     * clients contains the depot, such that each vector is one longer than the
     * number of clients.
     *
     * @param clients      List of clients (including depot at index 0).
     * @param numVehicles  Number of vehicles.
     * @param weightCap   Vehicle weight capacity.
     * @param volumeCap   Vehicle volume capacity.
     * @param salvageCap   Route nonterminal salvage capacity.
     * @param distMat      Distance matrix.
     * @param durMat       Duration matrix.
     */
    ProblemData(std::vector<Client> const &clients,
                size_t numVehicles,
                Load weightCap,
                Load volumeCap,
                Salvage salvageCap,
                Matrix<Distance> const distMat,
                Matrix<Duration> const durMat);
};

ProblemData::Client const &ProblemData::client(size_t client) const
{
    return clients_[client];
}

Distance ProblemData::dist(size_t first, size_t second) const
{
    return dist_(first, second);
}

Duration ProblemData::duration(size_t first, size_t second) const
{
    return dur_(first, second);
}

#endif  // PYVRP_PROBLEMDATA_H
