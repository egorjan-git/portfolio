#include "Appliance.h"
#include "KitchenCabinet.h"

Appliance::Appliance() : Entity(Box3D()), name_("Unknown") {}

Appliance::Appliance(const std::string& name, const Box3D& box)
    : Entity(box), name_(name) {}

const std::string& Appliance::name() const { return name_; }
void Appliance::setName(const std::string& name) { name_ = name; }

void Appliance::turnOn()  { powered_ = true; }
void Appliance::turnOff() { powered_ = false; }
void Appliance::toggle()  { powered_ = !powered_; }
bool Appliance::isOn() const { return powered_; }

bool Appliance::intersectsWith(const KitchenCabinet& cab) const {
    return box_.intersects(cab.box());
}