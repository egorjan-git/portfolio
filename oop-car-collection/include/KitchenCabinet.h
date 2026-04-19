#ifndef OOP_1_1_KITCHENCABINET_H
#define OOP_1_1_KITCHENCABINET_H

#include "Entity.h"
#include "Material.h"
#include "Appliance.h"

class KitchenCabinet : public Entity {
private:
    Material material_;
public:
    KitchenCabinet();
    KitchenCabinet(Material m, const Box3D& b);

    Material material() const;
    void setMaterial(Material m);

    bool intersectsWith(const KitchenCabinet& other) const;
    bool intersectsWith(const Appliance& app) const;

    std::string id() const override { return "cabinet"; }
};

#endif