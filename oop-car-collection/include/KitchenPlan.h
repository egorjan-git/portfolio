#ifndef OOP_1_1_KITCHENPLAN_H
#define OOP_1_1_KITCHENPLAN_H

#include <vector>
#include <memory>
#include <string>
#include <utility>
#include <iosfwd>

#include "Box3D.h"
#include "Entity.h"
#include "KitchenCabinet.h"
#include "Appliance.h"

class KitchenPlan {
    Box3D room_;
    std::vector<std::unique_ptr<Entity>> entities_;

public:
    KitchenPlan();
    KitchenPlan(double w, double d, double h);

    KitchenPlan(const KitchenPlan& other);
    KitchenPlan& operator=(const KitchenPlan& other);

    void addCabinet(const KitchenCabinet& c);
    void addAppliance(const Appliance& a);

    const Box3D& room() const { return room_; }
    const std::vector<std::unique_ptr<Entity>>& entities() const { return entities_; }

    std::pair<bool, std::string> validate(double minDist, double eps) const;

    friend std::ostream& operator<<(std::ostream& os, const KitchenPlan& kp);
    friend std::istream& operator>>(std::istream& is, KitchenPlan& kp);
};

#endif