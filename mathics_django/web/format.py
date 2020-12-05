"""
Format Mathics objects
"""

import random
import networkx as nx


def hierarchy_pos(
    G, root=None, width=1.0, vert_gap=0.2, vert_loc=0, leaf_vs_root_factor=0.5
):

    """From EoN (Epidemics on Networks): a fast, flexible Python package
    for simulation, analytic approximation, and analysis of epidemics
    on networks
    https://joss.theoj.org/papers/10.21105/joss.01731

    If the graph is a tree this will return the positions to plot this in a
    hierarchical layout.

    Based on Joel's answer at https://stackoverflow.com/a/29597209/2966723,
    but with some modifications.

    We include this because it may be useful for plotting transmission trees,
    and there is currently no networkx equivalent (though it may be coming soon).

    There are two basic approaches we think of to allocate the horizontal
    location of a node.

    - Top down: we allocate horizontal space to a node.  Then its ``k``
      descendants split up that horizontal space equally.  This tends to result
      in overlapping nodes when some have many descendants.
    - Bottom up: we allocate horizontal space to each leaf node.  A node at a
      higher level gets the entire space allocated to its descendant leaves.
      Based on this, leaf nodes at higher levels get the same space as leaf
      nodes very deep in the tree.

    We use use both of these approaches simultaneously with ``leaf_vs_root_factor``
    determining how much of the horizontal space is based on the bottom up
    or top down approaches.  ``0`` gives pure bottom up, while 1 gives pure top
    down.


    :Arguments:

    **G** the graph (must be a tree)

    **root** the root node of the tree
    - if the tree is directed and this is not given, the root will be found and used
    - if the tree is directed and this is given, then the positions will be
      just for the descendants of this node.
    - if the tree is undirected and not given, then a random choice will be used.

    **width** horizontal space allocated for this branch - avoids overlap with other branches

    **vert_gap** gap between levels of hierarchy

    **vert_loc** vertical location of root

    **leaf_vs_root_factor**

    xcenter: horizontal location of root

    """
    if not nx.is_tree(G):
        raise TypeError("cannot use hierarchy_pos on a graph that is not a tree")

    # These get swapped if tree edge directions point to the root.
    decendants = nx.descendants
    out_degree = G.out_degree if hasattr(G, "out_degree") else G.degree
    neighbors = G.neighbors

    if root is None:
        if isinstance(G, nx.DiGraph):
            zero_outs = [n for n in G.out_degree() if n[1] == 0]
            if len(zero_outs) == 1 and len(G) > 2:
                # We unequivocally have a directed that points from leave to the root.
                # The case where we have a one or two node graph is ambiguous.
                root = list(nx.topological_sort(G))[-1]
                # Swap motion functions
                decendants = nx.ancestors
                out_degree = G.in_degree
                neighbors = G.predecessors
            else:
                root = next(
                    iter(nx.topological_sort(G))
                )  # allows back compatibility with nx version 1.11
                # root = next(nx.topological_sort(G))
        else:
            root = random.choice(list(G.nodes))

    def _hierarchy_pos(
        G,
        root,
        leftmost,
        width,
        leafdx=0.2,
        vert_gap=0.2,
        vert_loc=0,
        xcenter=0.5,
        rootpos=None,
        leafpos=None,
        parent=None,
    ):
        """
        see hierarchy_pos docstring for most arguments

        pos: a dict saying where all nodes go if they have been assigned
        parent: parent of this branch. - only affects it if non-directed

        """

        if rootpos is None:
            rootpos = {root: (xcenter, vert_loc)}
        else:
            rootpos[root] = (xcenter, vert_loc)
        if leafpos is None:
            leafpos = {}

        children = list(neighbors(root))
        leaf_count = 0
        if not isinstance(G, nx.DiGraph) and parent is not None:
            children.remove(parent)
        if len(children) != 0:
            rootdx = width / len(children)
            nextx = xcenter - width / 2 - rootdx / 2
            for child in children:
                nextx += rootdx
                rootpos, leafpos, newleaves = _hierarchy_pos(
                    G,
                    child,
                    leftmost + leaf_count * leafdx,
                    width=rootdx,
                    leafdx=leafdx,
                    vert_gap=vert_gap,
                    vert_loc=vert_loc - vert_gap,
                    xcenter=nextx,
                    rootpos=rootpos,
                    leafpos=leafpos,
                    parent=root,
                )
                leaf_count += newleaves

            leftmostchild = min((x for x, y in [leafpos[child] for child in children]))
            rightmostchild = max((x for x, y in [leafpos[child] for child in children]))
            leafpos[root] = ((leftmostchild + rightmostchild) / 2, vert_loc)
        else:
            leaf_count = 1
            leafpos[root] = (leftmost, vert_loc)
        #        pos[root] = (leftmost + (leaf_count-1)*dx/2., vert_loc)
        #        print(leaf_count)
        return rootpos, leafpos, leaf_count

    xcenter = width / 2.0
    if isinstance(G, nx.DiGraph):
        leafcount = len([node for node in decendants(G, root) if out_degree(node) == 0])
    elif isinstance(G, nx.Graph):
        leafcount = len(
            [
                node
                for node in nx.node_connected_component(G, root)
                if G.degree(node) == 1 and node != root
            ]
        )

    rootpos, leafpos, leaf_count = _hierarchy_pos(
        G,
        root,
        0,
        width,
        leafdx=width * 1.0 / leafcount,
        vert_gap=vert_gap,
        vert_loc=vert_loc,
        xcenter=xcenter,
    )
    pos = {}
    for node in rootpos:
        pos[node] = (
            leaf_vs_root_factor * leafpos[node][0]
            + (1 - leaf_vs_root_factor) * rootpos[node][0],
            leafpos[node][1],
        )
    #    pos = {node:(leaf_vs_root_factor*x1+(1-leaf_vs_root_factor)*x2, y1) for ((x1,y1), (x2,y2)) in (leafpos[node], rootpos[node]) for node in rootpos}
    xmax = max(x for x, y in pos.values())
    y_list = {}
    for node in pos:
        x, y = pos[node] = (pos[node][0] * width / xmax, pos[node][1])
        y_list[y] = y_list.get(y, set([]))
        y_list[y].add(x)

    min_sep = xmax
    for y in y_list.keys():
        x_list = sorted(y_list[y])
        n = len(x_list) - 1
        if n <= 0:
            continue
        min_sep = min([x_list[i + 1] - x_list[i] for i in range(n)] + [min_sep])
    return pos, min_sep


node_size = 300  # this is networkx's default size


def tree_layout(G):
    global node_size
    root = G.root if hasattr(G, "root") else None
    pos, min_sep = hierarchy_pos(G, root=root)
    node_size = min_sep * 2000
    return pos


NETWORKX_LAYOUTS = {
    "circular": nx.circular_layout,
    "multipartite": nx.multipartite_layout,
    "planar": nx.planar_layout,
    "random": nx.random_layout,
    "shell": nx.shell_layout,
    "spectral": nx.spectral_layout,
    "spring": nx.spring_layout,
    "tree": tree_layout,
}


def format_graph(G):
    """
    Format a Graph
    """
    # FIXME handle graphviz as well
    import matplotlib.pyplot as plt

    global node_size
    node_size = 300  # This is networkx's default

    graph_layout = G.graph_layout if hasattr(G, "graph_layout") else None
    vertex_labels = G.vertex_labels if hasattr(G, "vertex_labels") else False
    if vertex_labels:
        vertex_labels = vertex_labels.to_python() or False

    if hasattr(G, "title") and G.title.get_string_value():
        fig, ax = plt.subplots()  # Create a figure and an axes
        ax.set_title(G.title.get_string_value())

    if graph_layout:
        if not isinstance(graph_layout, str):
            graph_layout = graph_layout.get_string_value()
        layout_fn = NETWORKX_LAYOUTS.get(graph_layout, None)
    else:
        layout_fn = None

    options = {
        # "font_size": 36,
        "node_size": node_size,
        # "node_color": "white",  # Set below
        # "edgecolors": "black",  # Set below
        # "linewidths": 5,
        # "width": 5,
        "with_labels": vertex_labels,
    }

    if vertex_labels:
        options["node_color"] = "white"
        options["edgecolors"] = "black"

    if layout_fn:
        nx.draw(G, pos=layout_fn(G), **options)
    else:
        nx.draw_shell(G, **options)
    plt.show()
    return None
