#ifndef OOP_1_1_APPLIANCE_H
#define OOP_1_1_APPLIANCE_H

#include <string>
#include "Entity.h"

class KitchenCabinet;

class Appliance : public Entity {
private:
    std::string name_;
    bool powered_{false};

public:
    Appliance();
    Appliance(const std::string& name, const Box3D& box);

    const std::string& name() const;
    void setName(const std::string& name);

    void turnOn();
    void turnOff();
    void toggle();
    bool isOn() const;

    bool intersectsWith(const KitchenCabinet& cab) const;

    std::string id() const override { return "appliance"; }
};

#endif