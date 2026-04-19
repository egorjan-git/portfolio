#ifndef OOP_1_1_BOX3D_H
#define OOP_1_1_BOX3D_H

#include <stdexcept>


class Box3D {
private:
    double x_, y_, z_;
    double w_, d_, h_;

    static void requirePositive(double v, const char* name);

public:
    Box3D();
    Box3D(double x, double y, double z, double w, double d, double h);


    double x() const; double y() const; double z() const;
    double w() const; double d() const; double h() const;


    void setPos(double x, double y, double z);
    void setSize(double w, double d, double h);


    bool intersects(const Box3D& rhs) const;


    double topZ() const;
};

#endif