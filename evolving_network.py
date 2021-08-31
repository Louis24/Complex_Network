import igraph
import json
import networkx
import numpy
import operator
import random
import sys

def betweennessAttack(G, sequentialMode):
    """ 
    Returns the robustness value of the given network G, computed using 
    betweenness-attack strategy and the given attack mode (sequential 
    or simultaneous).
    """
    Gcopy = G.copy()
    Vcount = len(Gcopy)
    V = sorted(networkx.betweenness_centrality(Gcopy).items(), 
               key = operator.itemgetter(1), reverse = True)
    R = 0.0
    for i in range(1, Vcount - 1):
        Gcopy.remove_node(V.pop(0)[0])
        if sequentialMode:
            V = sorted(networkx.betweenness_centrality(Gcopy).items(), 
                       key = operator.itemgetter(1), reverse = True)
        giantComponent = max(networkx.connected_components(Gcopy), key = len)
        R += 1.0 * len(giantComponent) / Vcount
    return R / Vcount

def closenessAttack(G, sequentialMode):
    """ 
    Returns the robustness value of the given network G, computed using 
    closeness-attack strategy and the given attack mode (sequential 
    or simultaneous).
    """
    Gcopy = G.copy()
    Vcount = len(Gcopy)
    V = sorted(networkx.closeness_centrality(Gcopy).items(), 
               key = operator.itemgetter(1), reverse = True)
    R = 0.0
    for i in range(1, Vcount - 1):
        Gcopy.remove_node(V.pop(0)[0])
        if sequentialMode:
            V = sorted(networkx.closeness_centrality(Gcopy).items(), 
                       key = operator.itemgetter(1), reverse = True)
        giantComponent = max(networkx.connected_components(Gcopy), key = len)
        R += 1.0 * len(giantComponent) / Vcount
    return R / Vcount

def degreeAttack(G, sequentialMode):
    """ 
    Returns the robustness value of the given network G, computed using 
    degree-attack strategy and the given attack mode (sequential 
    or simultaneous).
    """
    Gcopy = G.copy()
    Vcount = len(Gcopy)
    V = sorted(networkx.degree_centrality(Gcopy).items(), 
               key = operator.itemgetter(1), reverse = True)
    R = 0.0
    for i in range(1, Vcount - 1):
        Gcopy.remove_node(V.pop(0)[0])
        if sequentialMode:
            V = sorted(networkx.degree_centrality(Gcopy).items(), 
                       key = operator.itemgetter(1), reverse = True)
        giantComponent = max(networkx.connected_components(Gcopy), key = len)
        R += 1.0 * len(giantComponent) / Vcount
    return R / Vcount

def eigenvectorAttack(G, sequentialMode):
    """ 
    Returns the robustness value of the given network G, computed using 
    eigenvector-attack strategy and the given attack mode (sequential 
    or simultaneous).
    """

    def eigenvector_centrality(G):
        """
        Returns a map that maps a vertex id to the eigenvector centrality of 
        that vertex, calculated using igraph.
        """
        tempG = igraph.Graph()
        tempG.add_vertices([str(v) for v in G.nodes()])
        tempG.add_edges([(str(u), str(v)) for u, v in G.edges()])
        return {int(tempG.vs[i]["name"]): v for i, v in 
                enumerate(tempG.eigenvector_centrality())}

    Gcopy = G.copy()
    Vcount = len(Gcopy)
    V = sorted(eigenvector_centrality(Gcopy).items(), 
               key = operator.itemgetter(1), reverse = True)
    R = 0.0
    for i in range(1, Vcount - 1):
        Gcopy.remove_node(V.pop(0)[0])
        if sequentialMode:
            V = sorted(eigenvector_centrality(Gcopy).items(), 
                       key = operator.itemgetter(1), reverse = True)
        giantComponent = max(networkx.connected_components(Gcopy), key = len)
        R += 1.0 * len(giantComponent) / Vcount
    return R / Vcount

def randomAttack(G, sequentialMode):
    """ 
    Returns the robustness value of the given network G, computed using 
    random-attack strategy; the attack mode is irrelevant.
    """
    Gcopy = G.copy()
    Vcount, V = len(Gcopy), Gcopy.nodes()
    random.shuffle(V)
    R = 0.0
    for i in range(1, Vcount - 1):
        Gcopy.remove_node(V.pop())
        R += 1.0 * len(max(networkx.connected_components(Gcopy), 
                           key = len)) / Vcount
    return R / Vcount

def robustness(G, attackStrategy, sequentialMode):
    """ 
    Returns the robustness value of the given network G, computed using 
    the given attack strategy and attack mode (sequential or simultaneous).
    """
    attacks = {"betweenness" : betweennessAttack, 
               "closeness" : closenessAttack, 
               "degree" : degreeAttack, 
               "eigenvector" : eigenvectorAttack, 
               "random" : randomAttack}
    return attacks[attackStrategy](G, sequentialMode)

def genMutants(G, params):
    """ 
    Returns a list of mutant networks obtained from the given network G, 
    using mutation parameters in params.
    """
    Vcount = len(G)
    Ecount = len(G.edges())
    mutants = []
    for i in range(params["mutantsPerEpoch"]):
        mutantG = G.copy()
        rewirings = 0
        while rewirings <= params["rewiringsPerMutant"]:
            u, v = mutantG.edges()[random.randrange(Ecount)]
            uNew = random.choice([u, v])
            vNew = random.randrange(Vcount)
            if uNew == vNew or mutantG.has_edge(uNew, vNew):
                continue
            mutantG.remove_edge(u, v)
            mutantG.add_edge(uNew, vNew)
            if networkx.number_connected_components(mutantG) > 1:
                mutantG.remove_edge(uNew, vNew)
                mutantG.add_edge(u, v)
            else:
                rewirings += 1
        mutants.append(mutantG)
    return mutants

def main():
    """ 
    Entry point. 
    """
    if len(sys.argv) == 1:
        sys.exit("Usage: python evolving_network.py <params file>")

    # Load the parameters.
    params = json.load((open(sys.argv[1], "r")))
    seedNetwork = params["seedNetwork"]

    # Setup the seed network.
    if seedNetwork["name"] == "read_graphml":
        G = networkx.convert_node_labels_to_integers(\
            networkx.read_graphml(seedNetwork["args"]["path"]))
    else:
        G = getattr(networkx, seedNetwork["name"])(**seedNetwork["args"])

    # Evolve G.
    R = robustness(G, params["attackStrategy"], params["sequentialMode"])
    countDown = params["stagnantEpochs"]
    while countDown > 0:
        if params["verbose"]:
            v = numpy.var(G.degree().values())               # degree variance
            l = networkx.average_shortest_path_length(G)     # avg. path length
            C = networkx.average_clustering(G)                 # clustering
            r = networkx.degree_assortativity_coefficient(G)   # assortativity
            print("%.4f %.4f %.4f %.4f %.4f" %(R, v, l, C, r))
        mutants = genMutants(G, params)
        prevR = R
        for mutant in mutants:
            mutantR = robustness(mutant, params["attackStrategy"], 
                                 params["sequentialMode"])
            if params["maximizeRobustness"] and mutantR > R or \
               not params["maximizeRobustness"] and mutantR < R:
                R = mutantR
                G = mutant
        if params["maximizeRobustness"] and R > prevR or \
           not params["maximizeRobustness"] and R < prevR:
            countDown = params["stagnantEpochs"]
        else:
            countDown -= 1

    # Save G.
    networkx.write_graphml(G, params["outFile"])

if __name__ == '__main__':
    main()
