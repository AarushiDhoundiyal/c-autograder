# graph_components

Count the connected components of a simple undirected graph on vertices 1 to `N`. The first line holds
`N` and `M`; each of the next `M` lines holds an undirected edge `U V` (endpoints in either order). Print the
number of connected components, followed by a newline.

Constraints: 1 <= N <= 120; 0 <= M <= N(N-1)/2; 1 <= U, V <= N; U != V; no duplicate edges.

Sample input:

    5 3
    1 2
    2 3
    4 5

Sample output: `2`

**Specification decisions.** Every edge is undirected, and a vertex without edges is a component of its
own. Required time complexity: O(N^2) (an adjacency-matrix DFS or BFS); an adjacency list or a disjoint-set
union is faster and also accepted.
