#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  @Time    : 2020/12/22 16:16
#  @Author  : Louis Li
#  @Email   : vortex750@hotmail.com


import pandas as pd
import networkx as nx

"""
计算某一条线和地铁的竞合关系
首先两条线路至少1个交点
其次OD满足一定条件 人数？换乘次数>=1一般是合作 otherwise竞争
"""


def calculate(metro):
    grid_station_line = pd.read_csv("data/#grid_station_line_0.5.csv", encoding="ANSI")
    gd_od_cellular_revised = pd.read_csv("data/gd_od_cellular_revised.csv", encoding="ANSI")
    network = pd.read_csv("network/network_0.5.csv", encoding="ANSI")

    # GRAPH
    l1 = network["LINE_A"]
    l2 = network["LINE_B"]
    e = list(zip(l1, l2))
    G = nx.Graph()
    G.add_edges_from(e)

    # 获取符合条件的OD
    gd_od_cellular_revised = gd_od_cellular_revised[gd_od_cellular_revised["PASSENGER"] >= 10]
    # gd_od_cellular_revised = gd_od_cellular_revised[gd_od_cellular_revised["TRANSFER"].isin([0, 1])]

    com = []
    coo = []

    for i in gd_od_cellular_revised.itertuples():
        o = i[1]
        d = i[2]
        p = i[3]

        x = grid_station_line[grid_station_line["GRID_A"] == o]
        y = grid_station_line[grid_station_line["GRID_A"] == d]

        m = eval(x["LINE_B"].values[0])
        n = eval(y["LINE_B"].values[0])

        # 两头必须有1头带M
        if metro in m or metro in n:

            # competition
            if metro in m & n:
                w = m & n - {metro}

                for j in w:
                    com.append([j, p, 1])

            # cooperation
            elif metro in m:  # 此处可以用z去校验w有轻微误差

                for j in n:
                    x = len(nx.shortest_path(G, metro, j))

                    if x == 2:
                        coo.append([j, p, 0])

            else:
                for j in m:
                    x = len(nx.shortest_path(G, metro, j))

                    if x == 2:
                        coo.append([j, p, 0])

    res = com + coo
    competition = pd.DataFrame(res, columns=["LINE", "PASSENGER", "COMPETITION/COOPERATION"])
    competition = competition.groupby(["LINE", "COMPETITION/COOPERATION"])
    competition = competition.sum().reset_index()
    competition.to_csv(f"result/competition_analysis_{metro}.csv", encoding="ANSI", index=False)


def main():
    for m in {"M1", "M2", "M5", "M14"}:
        calculate(m)


if __name__ == '__main__':
    main()
