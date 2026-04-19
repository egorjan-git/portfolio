#ifndef OOP_1_1_ENTITY_H
#define OOP_1_1_ENTITY_H

#include <string>
#include "Box3D.h"

class Entity {
protected:
    Box3D box_;

public:
    explicit Entity(const Box3D& b) : box_(b) {}
    virtual ~Entity() = default;

    const Box3D& box() const { return box_; }
    void setBox(const Box3D& b) { box_ = b; }

    virtual std::string id() const = 0;
};

#endif