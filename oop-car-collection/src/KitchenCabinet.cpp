#include "KitchenCabinet.h"
#include "Appliance.h"

KitchenCabinet::KitchenCabinet()
    : Entity(Box3D()), material_(Material::Wood) {}

KitchenCabinet::KitchenCabinet(Material m, const Box3D& b)
    : Entity(b), material_(m) {}

Material KitchenCabinet::material() const {
    return material_;
}

void KitchenCabinet::setMaterial(Material m) {
    material_ = m;
}

bool KitchenCabinet::intersectsWith(const KitchenCabinet& other) const {
    return box_.intersects(other.box_);
}

bool KitchenCabinet::intersectsWith(const Appliance& app) const {
    return box_.intersects(app.box());
}