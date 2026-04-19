#include "Box3D.h"
#include <string>

void Box3D::requirePositive(double v, const char* name) {
    if (!(v > 0.0))
        throw std::invalid_argument(
            std::string("Size must be > 0 for: ") + name);
}

Box3D::Box3D()
    : x_(0.0), y_(0.0), z_(0.0), w_(1.0), d_(1.0), h_(1.0) {}

Box3D::Box3D(double x, double y, double z,
             double w, double d, double h)
    : x_(x), y_(y), z_(z), w_(w), d_(d), h_(h) {
    requirePositive(w_, "w");
    requirePositive(d_, "d");
    requirePositive(h_, "h");
}

double Box3D::x() const { return x_; }
double Box3D::y() const { return y_; }
double Box3D::z() const { return z_; }
double Box3D::w() const { return w_; }
double Box3D::d() const { return d_; }
double Box3D::h() const { return h_; }

void Box3D::setPos(double x, double y, double z) {
    x_ = x; y_ = y; z_ = z;
}

void Box3D::setSize(double w, double d, double h) {
    requirePositive(w, "w");
    requirePositive(d, "d");
    requirePositive(h, "h");
    w_ = w; d_ = d; h_ = h;
}

bool Box3D::intersects(const Box3D& rhs) const {
    bool sepX = (x_ + w_) <= rhs.x_ || (rhs.x_ + rhs.w_) <= x_;
    bool sepY = (y_ + d_) <= rhs.y_ || (rhs.y_ + rhs.d_) <= y_;
    bool sepZ = (z_ + h_) <= rhs.z_ || (rhs.z_ + rhs.h_) <= z_;
    return !(sepX || sepY || sepZ);
}

double Box3D::topZ() const { return z_ + h_; }