"""

Path planning Sample Code with Randomized Rapidly-Exploring Random Trees (RRT)

author: AtsushiSakai(@Atsushi_twi)

"""

import math
import random

import matplotlib.pyplot as plt
import numpy as np
from timeit import default_timer as timer

show_animation = True
GoalBiased = True
InflationRadius = 0.8

def EuclideanDistanceOfNodes(start, end):
    return math.sqrt(((end.y-start.y)**2)+((end.x-start.x)**2))

class RRT:
    """
    Class for RRT planning
    """

    class Node:
        """
        RRT Node
        """

        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.path_x = []
            self.path_y = []
            self.parent = None

    def __init__(self, start, goal, obstacle_list, rand_area,
                 expand_dis=0.8, path_resolution=0.2, goal_sample_rate=5, max_iter=100000):
        """
        Setting Parameter

        start:Start Position [x,y]
        goal:Goal Position [x,y]
        obstacleList:obstacle Positions [[x,y,size],...]
        randArea:Random Sampling Area [min,max]

        """
        self.start = self.Node(start[0], start[1])
        self.end = self.Node(goal[0], goal[1])
        self.min_rand = rand_area[0]
        self.max_rand = rand_area[1]
        self.expand_dis = expand_dis
        self.path_resolution = path_resolution
        self.goal_sample_rate = goal_sample_rate
        self.max_iter = max_iter
        self.obstacle_list = obstacle_list
        self.node_list = []
        self.SamplingRadius = EuclideanDistanceOfNodes(self.start,self.end)
        self.ExpansionCoeff = 2
        self.ExpansionEps = 0.3

    def planning(self, animation=True):
        """
        rrt path planning

        animation: flag for animation on or off
        """
        

        self.node_list = [self.start]
        for i in range(self.max_iter):
            rnd_node = self.get_random_node()
            if EuclideanDistanceOfNodes(self.end, rnd_node) > self.SamplingRadius :
                continue
            nearest_ind = self.get_nearest_node_index(self.node_list, rnd_node)
            nearest_node = self.node_list[nearest_ind]

            new_node = self.steer(nearest_node, rnd_node, self.expand_dis)

            if self.check_collision(new_node, self.obstacle_list):
                self.node_list.append(new_node)
                self.SamplingRadius = EuclideanDistanceOfNodes(new_node, self.end)
                dont_change_color = True
            else:
                self.SamplingRadius = self.SamplingRadius + (self.ExpansionCoeff * self.ExpansionEps)
                continue

            if animation and i % 5 == 0:
                self.draw_graph(rnd_node)

            if self.calc_dist_to_goal(self.node_list[-1].x, self.node_list[-1].y) <= self.expand_dis:
                final_node = self.steer(self.node_list[-1], self.end, self.expand_dis)
                if self.check_collision(final_node, self.obstacle_list):
                    return self.generate_final_course(len(self.node_list) - 1)

            if animation and i % 5:
                self.draw_graph(rnd_node)

        return None  # cannot find path

    def steer(self, from_node, to_node, extend_length=float("inf")):

        new_node = self.Node(from_node.x, from_node.y)
        d, theta = self.calc_distance_and_angle(new_node, to_node)

        new_node.path_x = [new_node.x]
        new_node.path_y = [new_node.y]

        if extend_length > d:
            extend_length = d

        n_expand = math.floor(extend_length / self.path_resolution)

        for _ in range(n_expand):
            new_node.x += self.path_resolution * math.cos(theta)
            new_node.y += self.path_resolution * math.sin(theta)
            new_node.path_x.append(new_node.x)
            new_node.path_y.append(new_node.y)

        d, _ = self.calc_distance_and_angle(new_node, to_node)
        if d <= self.path_resolution:
            new_node.path_x.append(to_node.x)
            new_node.path_y.append(to_node.y)

        new_node.parent = from_node

        return new_node

    def generate_final_course(self, goal_ind):
        path = [[self.end.x, self.end.y]]
        node = self.node_list[goal_ind]
        while node.parent is not None:
            path.append([node.x, node.y])
            node = node.parent
        path.append([node.x, node.y])

        return path

    def calc_dist_to_goal(self, x, y):
        dx = x - self.end.x
        dy = y - self.end.y
        return math.hypot(dx, dy)

    def get_random_node(self):
        if GoalBiased:
            if random.randint(0, 100) > self.goal_sample_rate:
                rnd = self.Node(random.uniform(self.min_rand, self.max_rand),
                                random.uniform(self.min_rand, self.max_rand))
            else:  # goal point sampling
                rnd = self.Node(self.end.x, self.end.y)
        else:
            rnd = self.Node(random.uniform(self.min_rand, self.max_rand),
                            random.uniform(self.min_rand, self.max_rand))
        return rnd

    def draw_graph(self, rnd=None , dont_cc = False):
        plt.clf()
        # for stopping simulation with the esc key.
        plt.gcf().canvas.mpl_connect('key_release_event',
                                     lambda event: [exit(0) if event.key == 'escape' else None])
        if rnd is not None:
            rnd_point_color = '^k'
            if EuclideanDistanceOfNodes(self.end, rnd) > self.SamplingRadius:
                rnd_point_color = '^r'
            else:
                rnd_point_color = '^g'
            plt.plot(rnd.x, rnd.y, rnd_point_color)

        for node in self.node_list:
            if node.parent:
                plt.plot(node.path_x, node.path_y, "-g")

        sampling_range_circle = plt.Circle((self.end.x, self.end.y), 
                                            self.SamplingRadius, color='r' , 
                                            alpha=0.2,
                                            hatch='x',
                                            linestyle='--',
                                            facecolor='b',
                                            linewidth=3.0)
        fig = plt.gcf()
        ax = fig.gca()
        ax.add_artist(sampling_range_circle)

        for (ox, oy, size) in self.obstacle_list:
            inflation_cir = plt.Circle((ox,oy), size+ InflationRadius, color='g', alpha=0.25, linewidth=0.0)
            ax.add_artist(inflation_cir)
            obst_cir = plt.Circle((ox,oy), size, color='b', alpha=0.8 , linewidth=0.0)
            ax.add_artist(obst_cir)

        plt.plot(self.start.x, self.start.y, "xr")
        plt.plot(self.end.x, self.end.y, "xr")
        plt.axis("equal")
        plt.axis([self.min_rand*2, self.max_rand*2, self.min_rand*2, self.max_rand*2])
        plt.grid(True)
        plt.pause(0.01)

    @staticmethod
    def get_nearest_node_index(node_list, rnd_node):
        dlist = [(node.x - rnd_node.x) ** 2 + (node.y - rnd_node.y)
                 ** 2 for node in node_list]
        minind = dlist.index(min(dlist))

        return minind

    @staticmethod
    def check_collision(node, obstacleList):

        if node is None:
            return False

        for (ox, oy, size) in obstacleList:
            dx_list = [ox - x for x in node.path_x]
            dy_list = [oy - y for y in node.path_y]
            d_list = [dx * dx + dy * dy for (dx, dy) in zip(dx_list, dy_list)]

            if min(d_list) <= (size+InflationRadius) ** 2:
                return False  # collision

        return True  # safe

    @staticmethod
    def calc_distance_and_angle(from_node, to_node):
        dx = to_node.x - from_node.x
        dy = to_node.y - from_node.y
        d = math.hypot(dx, dy)
        theta = math.atan2(dy, dx)
        return d, theta


def main(gx=6.0, gy=10.0):
    print("start " + __file__)

    # ====Search Path with RRT====
    obstacleList = [
        (5, 5, 1),
        (3, 6, 2),
        (3, 8, 2),
        (3, 10, 2),
        (7, 5, 2),
        (9, 5, 2),
        (8, 10, 1)
    ]  # [x, y, radius]
    # Set Initial parameters
    rrt = RRT(start=[-5, -8],
              goal=[gx, gy],
              rand_area=[-15.0, 15.0],
              obstacle_list=obstacleList)
    start = timer()
    path = rrt.planning(animation=show_animation)
    end = timer()

    if path is None:
        print("Cannot find path")
    else:
        print("found path!!")
        print(f"Execution Time: {(end - start)} seconds")
        # Draw final path
        rrt.draw_graph()
        plt.plot([x for (x, y) in path], [y for (x, y) in path], '-r')
        plt.grid(True)
        plt.pause(0.01)  # Need for Mac
        plt.show()


if __name__ == '__main__':
    main()
