"""Module for making piecewise linear functions"""
import bisect
import typing

DataPoint: typing.TypeAlias = tuple[float, float]


class PiecewiseLinear:

    def __init__(self, *args: DataPoint):
        points = sorted(
            args,
            key=lambda x: x[0]
        )

        del_inds: list[int] = []
        for ind, point  in enumerate(points):
            if ind == 0:
                continue

            prev_point = points[ind-1]
            if point[0] == prev_point[0]:
                if point[1] != prev_point[1]:
                    raise ValueError(f"Inconsistent Definition at {point[0]}")

                del_inds.insert(0, ind)

        points = [point for ind, point in enumerate(points)
                  if ind not in del_inds]

        self.points = points

    def __call__(self, in_val: float) -> float:

        if in_val <= self.points[0][0]:
            return self.points[0][1]

        ind = bisect.bisect_left(self.points, in_val,
                                 key=lambda x: x[0])

        if ind >= len(self.points):
            return self.points[-1][1]
        elif self.points[ind-1][0] == in_val:
            return self.points[ind-1][1]
        else:
            x_init = self.points[ind-1][0]
            x_final = self.points[ind][0]

            t = (in_val - x_init) / (x_final - x_init)

            y_init = self.points[ind-1][1]
            y_final = self.points[ind][1]
            return y_init + t * (y_final - y_init)


        # for ind, point in enumerate(self.points):
        #     if point[0] > in_val:
        #         if ind == 0:
        #             return point[0]
        #
        #         x_init = self.points[ind-1][0]
        #         x_final = point[0]
        #
        #         t = (in_val-x_init)/(x_final-x_init)
        #
        #         y_init = self.points[ind-1][1]
        #         y_final = point[1]
        #         return y_init + t*(y_final-y_init)

        return self.points[-1][1]

    def add_point(self, new_x: float, new_y: float):
        """
        Add a new point.  Will update an existing point.
        """
        has_inserted = False

        ind = bisect.bisect_left(
            self.points, new_x, key=lambda x:x[0]
        )

        if ind < len(self.points) and self.points[ind][0] == new_x:
            self.points[ind] = (new_x, new_y)
        else:
            self.points.insert(ind, (new_x, new_y))


        # for ind, point in enumerate(self.points):
        #     if point[0] == new_x:
        #         self.points[ind] = (point[0], new_y)
        #         has_inserted = True
        #         break
        #     elif point[0] > new_x:
        #         self.points.insert(ind, (new_x, new_y))
        #         has_inserted = True
        #         break
        #
        # if not has_inserted:
        #     self.points.append((new_x, new_y))