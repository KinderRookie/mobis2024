#include <iostream>
#include <cmath>

struct Point {
    double x, y, z;
};

struct Line {
    Point point; // 직선이 지나가는 한 점
    Point dir;   // 직선의 방향 벡터

    // 생성자 추가
    Line(Point p, Point d) : point(p), dir(d) {}
};

// 벡터의 외적을 계산하는 함수
Point crossProduct(const Point& a, const Point& b) {
    return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x};
}

// 벡터의 내적을 계산하는 함수
double dotProduct(const Point& a, const Point& b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

// 두 점 사이의 거리를 계산하는 함수
double distance(const Point& a, const Point& b) {
    return sqrt(pow(a.x - b.x, 2) + pow(a.y - b.y, 2) + pow(a.z - b.z, 2));
}

// 두 직선 사이의 최단 거리에 해당하는 지점을 찾는 함수
bool findClosestPoints(const Line& l1, const Line& l2, Point& p1, Point& p2) {
    Point n = crossProduct(l1.dir, l2.dir); // 두 방향 벡터의 외적
    double norm = dotProduct(n, n);

    // 두 직선이 평행한 경우, 최단 거리에 해당하는 지점을 찾을 수 없음
    if (fabs(norm) < 1e-8) return false;

    Point diff = {l2.point.x - l1.point.x, l2.point.y - l1.point.y, l2.point.z - l1.point.z};
    double t1 = dotProduct(crossProduct(diff, l2.dir), n) / norm;
    double t2 = dotProduct(crossProduct(diff, l1.dir), n) / norm;

    p1 = {l1.point.x + l1.dir.x * t1, l1.point.y + l1.dir.y * t1, l1.point.z + l1.dir.z * t1};
    p2 = {l2.point.x + l2.dir.x * t2, l2.point.y + l2.dir.y * t2, l2.point.z + l2.dir.z * t2};

    return true;
}

int main() {
    Line l1 = {{1, 2, 3}, {4, 5, 6}}; // 첫 번째 직선
    Line l2 = {{1, 2, 3}, {10, 11, 12}}; // 두 번째 직선
    Point p1, p2;

    if (findClosestPoints(l1, l2, p1, p2)) {
        std::cout << "Line 1 closest point: (" << p1.x << ", " << p1.y << ", " << p1.z << ")\n";
        std::cout << "Line 2 closest point: (" << p2.x << ", " << p2.y << ", " << p2.z << ")\n";
        std::cout << "Distance between lines: " << distance(p1, p2) << std::endl;
    } else {
        std::cout << "Lines are parallel, no unique closest points."    << std::endl;
    }

    return 0;
}