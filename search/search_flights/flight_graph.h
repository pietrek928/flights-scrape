#include <set>
#include <vector>
#include <algorithm>


class FlightGraph {
    typedef int vertex_t;
    typedef int edge_pos_t;
    constexpr static int edge_pos_none = -1;

    typedef struct {
        float start_t;
        float duration;
        float cost;
    } Edge;

    typedef struct {
        vertex_t src;
        vertex_t dst;
        edge_pos_t pos;
    } EdgePos;

    struct EdgePosCompare {
        bool operator()(const EdgePos& a, const EdgePos& b) const {
            if (a.src != b.src) {
                return a.src < b.src;
            }
            if (a.dst != b.dst) {
                return a.dst < b.dst;
            }
            return a.pos < b.pos;
        }
    };

    std::vector<Edge> edges;
    std::set<EdgePos, EdgePosCompare> edges_pos;

    typedef struct {
        edge_pos_t begin;
        edge_pos_t end;
    } EdgePosRange;

    inline EdgePosRange find_vertex_edge_pos(vertex_t v) {
        EdgePos s = {
            .src = v,
            .dst = 0,
            .pos = 0,
        };
        auto it = edges_pos.lower_bound(s);
        if (it == edges_pos.end() || it->src != v) {
          return {
              .begin = edge_pos_none,
              .end = edge_pos_none,
          };
        }
        edge_pos_t begin = it->pos;

        s.src ++;
        it = edges_pos.lower_bound(s);
        edge_pos_t end;
        if (it != edges_pos.end()) {
            end = it->pos;
        } else {
            end = edges.size();
        }

        return {
            .begin = begin,
            .end = end,
        };
    }

    inline EdgePosRange find_edge_pos_between(vertex_t src, vertex_t dst) {
        EdgePos s = {
            .src = src,
            .dst = dst,
            .pos = 0,
        };
        auto it = edges_pos.lower_bound(s);
        if (it == edges_pos.end() || it->src != src || it->dst != dst) {
          return {
              .begin = edge_pos_none,
              .end = edge_pos_none,
          };
        }
        
        edge_pos_t begin = it->pos;

        s.dst ++;
        it = edges_pos.lower_bound(s);
        edge_pos_t end;
        if (it != edges_pos.end()) {
            end = it->pos;
        } else {
            end = edges.size();
        }

        return {
            .begin = begin,
            .end = end,
        };
    }
};
