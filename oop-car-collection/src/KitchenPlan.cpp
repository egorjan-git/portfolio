#include "KitchenPlan.h"

#include <cmath>
#include <ostream>
#include <istream>
#include <vector>
#include <stdexcept>

static bool inside(const Box3D& outer, const Box3D& inner, double eps)
{
    return inner.x() >= outer.x() - eps &&
           inner.y() >= outer.y() - eps &&
           inner.z() >= outer.z() - eps &&
           inner.x() + inner.w() <= outer.x() + outer.w() + eps &&
           inner.y() + inner.d() <= outer.y() + outer.d() + eps &&
           inner.z() + inner.h() <= outer.z() + outer.h() + eps;
}

KitchenPlan::KitchenPlan()
    : room_(0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
{
}

KitchenPlan::KitchenPlan(double w, double d, double h)
    : room_(0.0, 0.0, 0.0, w, d, h)
{
}

KitchenPlan::KitchenPlan(const KitchenPlan& other)
    : room_(other.room_)
{
    entities_.reserve(other.entities_.size());
    for (const auto& ptr : other.entities_) {
        if (auto c = dynamic_cast<KitchenCabinet*>(ptr.get())) {
            entities_.push_back(std::make_unique<KitchenCabinet>(*c));
        } else if (auto a = dynamic_cast<Appliance*>(ptr.get())) {
            entities_.push_back(std::make_unique<Appliance>(*a));
        }
    }
}

KitchenPlan& KitchenPlan::operator=(const KitchenPlan& other)
{
    if (this == &other)
        return *this;

    room_ = other.room_;
    entities_.clear();
    entities_.reserve(other.entities_.size());
    for (const auto& ptr : other.entities_) {
        if (auto c = dynamic_cast<KitchenCabinet*>(ptr.get())) {
            entities_.push_back(std::make_unique<KitchenCabinet>(*c));
        } else if (auto a = dynamic_cast<Appliance*>(ptr.get())) {
            entities_.push_back(std::make_unique<Appliance>(*a));
        }
    }
    return *this;
}

void KitchenPlan::addCabinet(const KitchenCabinet& c)
{
    entities_.push_back(std::make_unique<KitchenCabinet>(c));
}

void KitchenPlan::addAppliance(const Appliance& a)
{
    entities_.push_back(std::make_unique<Appliance>(a));
}

std::pair<bool, std::string> KitchenPlan::validate(double minDist, double eps) const
{
    std::vector<const KitchenCabinet*> cabs;
    std::vector<const Appliance*>      apps;

    for (const auto& ptr : entities_) {
        if (auto c = dynamic_cast<KitchenCabinet*>(ptr.get())) {
            cabs.push_back(c);
        } else if (auto a = dynamic_cast<Appliance*>(ptr.get())) {
            apps.push_back(a);
        }
    }

    for (const auto& ptr : entities_) {
        if (!inside(room_, ptr->box(), eps)) {
            return {false, "object_out_of_room"};
        }
    }

    for (std::size_t i = 0; i < entities_.size(); ++i) {
        for (std::size_t j = i + 1; j < entities_.size(); ++j) {
            if (entities_[i]->box().intersects(entities_[j]->box())) {
                return {false, "objects_intersect"};
            }
        }
    }

    for (const auto* app : apps) {
        const Box3D& b = app->box();
        bool supported = std::fabs(b.z() - 0.0) <= eps;

        if (!supported) {
            for (const auto* cab : cabs) {
                const Box3D& cb = cab->box();

                bool sameLevel = std::fabs(b.z() - cb.topZ()) <= eps;
                bool overlapXY =
                    !(b.x() + b.w() <= cb.x() ||
                      cb.x() + cb.w() <= b.x() ||
                      b.y() + b.d() <= cb.y() ||
                      cb.y() + cb.d() <= b.y());

                if (sameLevel && overlapXY) {
                    supported = true;
                    break;
                }
            }
        }

        if (!supported) {
            return {false, "appliance_floating"};
        }
    }

    for (std::size_t i = 0; i < cabs.size(); ++i) {
        for (std::size_t j = i + 1; j < cabs.size(); ++j) {
            if (cabs[i]->material() == cabs[j]->material()) {
                continue;
            }

            const Box3D& A = cabs[i]->box();
            const Box3D& B = cabs[j]->box();

            double dx = 0.0;
            if (A.x() + A.w() < B.x()) {
                dx = B.x() - (A.x() + A.w());
            } else if (B.x() + B.w() < A.x()) {
                dx = A.x() - (B.x() + B.w());
            }

            double dy = 0.0;
            if (A.y() + A.d() < B.y()) {
                dy = B.y() - (A.y() + A.d());
            } else if (B.y() + B.d() < A.y()) {
                dy = A.y() - (B.y() + B.d());
            }

            double dist = std::sqrt(dx * dx + dy * dy);
            if (dist + 1e-12 < minDist) {
                return {false, "different_materials_too_close"};
            }
        }
    }

    return {true, "ok"};
}

std::ostream& operator<<(std::ostream& os, const KitchenPlan& kp)
{
    const Box3D& r = kp.room_;
    os << r.w() << ' ' << r.d() << ' ' << r.h() << '\n';

    std::vector<const KitchenCabinet*> cabs;
    std::vector<const Appliance*>      apps;

    for (const auto& ptr : kp.entities_) {
        if (auto c = dynamic_cast<KitchenCabinet*>(ptr.get())) {
            cabs.push_back(c);
        } else if (auto a = dynamic_cast<Appliance*>(ptr.get())) {
            apps.push_back(a);
        }
    }

    os << cabs.size() << '\n';
    for (const auto* c : cabs) {
        const Box3D& b = c->box();
        os << static_cast<int>(c->material()) << ' '
           << b.x() << ' ' << b.y() << ' ' << b.z() << ' '
           << b.w() << ' ' << b.d() << ' ' << b.h() << '\n';
    }

    os << apps.size() << '\n';
    for (const auto* a : apps) {
        const Box3D& b = a->box();
        os << a->name() << ' '
           << (a->isOn() ? 1 : 0) << ' '
           << b.x() << ' ' << b.y() << ' ' << b.z() << ' '
           << b.w() << ' ' << b.d() << ' ' << b.h() << '\n';
    }

    return os;
}

std::istream& operator>>(std::istream& is, KitchenPlan& kp)
{
    double W, D, H;
    if (!(is >> W >> D >> H)) {
        return is;
    }

    kp.entities_.clear();
    kp.room_.setPos(0.0, 0.0, 0.0);
    kp.room_.setSize(W, D, H);

    std::size_t nC = 0;
    is >> nC;

    for (std::size_t i = 0; i < nC; ++i) {
        int mInt;
        double x, y, z, w, d, h;
        is >> mInt >> x >> y >> z >> w >> d >> h;
        if (!is) return is;

        Material m = static_cast<Material>(mInt);
        Box3D box(x, y, z, w, d, h);
        KitchenCabinet cab(m, box);
        kp.addCabinet(cab);
    }

    std::size_t nA = 0;
    is >> nA;

    for (std::size_t i = 0; i < nA; ++i) {
        std::string name;
        int powered;
        double x, y, z, w, d, h;
        is >> name >> powered >> x >> y >> z >> w >> d >> h;
        if (!is) return is;

        Box3D box(x, y, z, w, d, h);
        Appliance app(name, box);
        if (powered) app.turnOn();
        kp.addAppliance(app);
    }

    return is;
}