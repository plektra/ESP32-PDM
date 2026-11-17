/* Decision 215: core of the one-pass signal router (negotiated congestion, "PathFinder") for pdm-4ch.
 * Grid: 0.05 mm cells, three signal layers (F.Cu, In2.Cu, B.Cu). Built and driven by pf_route.py (ctypes).
 * Static maps per layer (int16 per cell): P = 0 free for every net, n > 0 only net n may put a track centre here,
 * -1 nobody; O = n where the cell lies inside net n's own fixed copper (always passable for n). VM: the same for a
 * via centre (all layers at once). CM: cost multiplier * 16.
 * Dynamic: occ_t[l] / occ_v count the OTHER routed nets whose copper forbids a track / via centre in the cell
 * (exact lattice distances: forbidden when d^2 <= D^2, D = the centre distance the clearance needs, in cells). */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

static int W, H, N;
static void grow_init(void);
static int16_t *P[3], *O[3], *VM;
static uint8_t *CM[3];
static uint16_t *occ_t[3], *occ_v;
static float *hist_t[3], *hist_v;
static float *gcost;
static int32_t *par;
static uint32_t *mark, *tmark, epoch = 0, tepoch = 0;
static uint8_t *scr_t[3], *scr_v;
static int32_t *touch_t[3], *touch_v; static int ntouch_t[3], ntouch_v, captouch;

typedef struct { int n; int32_t *s; } Cells;
typedef struct {
    int id, grow, ncl; Cells *cl; int *order;
    int nleg; Cells *leg; int nfail; int *failcl;
    int nvc; int32_t *vc;      /* via cells of the legs routed so far */
    int dtt, dtv, dvt, dvv;   /* forbidden centre distances (cells): track-track, track-via, via-track, via-via */
} Net;
static Net *nets; static int nnets = 0, capnets = 0;

typedef struct { float f; int32_t s; } HE;
static HE *heap; static int hn = 0, hcap = 0;
static void hpush(float f, int32_t s) {
    if (hn == hcap) { hcap = hcap ? hcap * 2 : 1 << 20; heap = realloc(heap, hcap * sizeof(HE)); }
    int i = hn++;
    while (i > 0) { int p = (i - 1) >> 1; if (heap[p].f <= f) break; heap[i] = heap[p]; i = p; }
    heap[i].f = f; heap[i].s = s;
}
static HE hpop(void) {
    HE top = heap[0], last = heap[--hn];
    int i = 0;
    for (;;) {
        int c = 2 * i + 1; if (c >= hn) break;
        if (c + 1 < hn && heap[c + 1].f < heap[c].f) c++;
        if (last.f <= heap[c].f) break;
        heap[i] = heap[c]; i = c;
    }
    heap[i] = last; return top;
}

int pf_init(int w, int h, int16_t *p0, int16_t *p1, int16_t *p2, int16_t *o0, int16_t *o1, int16_t *o2,
            int16_t *vm, uint8_t *c0, uint8_t *c1, uint8_t *c2) {
    W = w; H = h; N = w * h;
    P[0] = p0; P[1] = p1; P[2] = p2; O[0] = o0; O[1] = o1; O[2] = o2; VM = vm; CM[0] = c0; CM[1] = c1; CM[2] = c2;
    for (int l = 0; l < 3; l++) {
        occ_t[l] = calloc(N, 2); hist_t[l] = calloc(N, 4); scr_t[l] = calloc(N, 1);
    }
    occ_v = calloc(N, 2); hist_v = calloc(N, 4); scr_v = calloc(N, 1);
    gcost = malloc(3 * (size_t)N * 4); par = malloc(3 * (size_t)N * 4);
    mark = calloc(3 * (size_t)N, 4); tmark = calloc(3 * (size_t)N, 4);
    grow_init();
    captouch = N;
    for (int l = 0; l < 3; l++) touch_t[l] = malloc((size_t)captouch * 4);
    touch_v = malloc((size_t)captouch * 4);
    return 0;
}

int pf_add_net(int id, int grow) {
    if (nnets == capnets) { capnets = capnets ? capnets * 2 : 256; nets = realloc(nets, capnets * sizeof(Net)); }
    Net *n = &nets[nnets]; memset(n, 0, sizeof(Net));
    n->id = id; n->grow = grow;
    n->dtt = 8 + grow; n->dtv = 12 + grow; n->dvt = 12; n->dvv = 16;
    return nnets++;
}

void pf_add_cluster(int ni, int cnt, int32_t *states) {
    Net *n = &nets[ni];
    n->cl = realloc(n->cl, (n->ncl + 1) * sizeof(Cells));
    n->cl[n->ncl].n = cnt; n->cl[n->ncl].s = malloc((size_t)cnt * 4);
    memcpy(n->cl[n->ncl].s, states, (size_t)cnt * 4);
    n->ncl++;
}

static void centroid(Cells *c, double *x, double *y) {
    double sx = 0, sy = 0;
    for (int i = 0; i < c->n; i++) { int cc = c->s[i] % N; sx += cc % W; sy += cc / W; }
    *x = sx / c->n; *y = sy / c->n;
}

/* Prim order over the cluster centroids, starting at cluster 0 */
void pf_finalize(int ni) {
    Net *n = &nets[ni];
    int k = n->ncl; n->order = malloc(k * sizeof(int));
    double *cx = malloc(k * 8), *cy = malloc(k * 8), *d = malloc(k * 8); char *in = calloc(k, 1);
    for (int i = 0; i < k; i++) { centroid(&n->cl[i], &cx[i], &cy[i]); d[i] = 1e30; }
    int cur = 0; in[0] = 1; n->order[0] = 0;
    for (int j = 1; j < k; j++) {
        int best = -1;
        for (int i = 0; i < k; i++) if (!in[i]) {
            double dd = hypot(cx[i] - cx[cur], cy[i] - cy[cur]);
            if (dd < d[i]) d[i] = dd;
            if (best < 0 || d[i] < d[best]) best = i;
        }
        in[best] = 1; n->order[j] = best; cur = best;
    }
    free(cx); free(cy); free(d); free(in);
}

static inline int pass1(int id, int l, int c) { int16_t p = P[l][c]; return p == 0 || p == id; }
static const int NB8[8][2] = {{1,0},{-1,0},{0,1},{0,-1},{1,1},{1,-1},{-1,1},{-1,-1}};
/* a wide net (grow > 0 cells of extra half width) tests every cell within grow of the centre */
static int goff[8][64], ngoff[8];
static void grow_init(void) {
    for (int g = 1; g < 8; g++) { ngoff[g] = 0;
        for (int dy = -g; dy <= g; dy++) for (int dx = -g; dx <= g; dx++)
            if ((dx || dy) && dx * dx + dy * dy <= g * g + 1 && ngoff[g] < 64) goff[g][ngoff[g]++] = dx + dy * W; }
}
static inline int passT(Net *n, int l, int c) {
    if (O[l][c] == n->id) return 1;
    if (!pass1(n->id, l, c)) return 0;
    for (int k = 0; k < ngoff[n->grow]; k++) { int q = c + goff[n->grow][k]; if (q < 0 || q >= N) return 0; if (!pass1(n->id, l, q) && O[l][q] != n->id) return 0; }
    return 1;
}
static inline int occT(Net *n, int l, int c) {
    int o = occ_t[l][c];
    for (int k = 0; k < ngoff[n->grow]; k++) { int q = c + goff[n->grow][k]; if (q >= 0 && q < N && occ_t[l][q] > o) o = occ_t[l][q]; }
    return o;
}

static void disk(uint8_t *scr, int32_t *touch, int *nt, int c, int r) {
    int x = c % W, y = c / W, r2 = r * r;
    for (int dy = -r; dy <= r; dy++) {
        int yy = y + dy; if (yy < 0 || yy >= H) continue;
        int span = (int)floor(sqrt((double)(r2 - dy * dy)));
        int x0 = x - span, x1 = x + span; if (x0 < 0) x0 = 0; if (x1 >= W) x1 = W - 1;
        uint8_t *row = scr + (size_t)yy * W;
        for (int xx = x0; xx <= x1; xx++) if (!row[xx]) { row[xx] = 1; touch[(*nt)++] = yy * W + xx; }
    }
}

/* add (sign=+1) or remove (-1) the net's routed copper from the occupancy maps */
static void stamp(Net *n, int sign) {
    for (int l = 0; l < 3; l++) ntouch_t[l] = 0;
    ntouch_v = 0;
    for (int g = 0; g < n->nleg; g++) {
        Cells *p = &n->leg[g];
        for (int i = 0; i < p->n; i++) {
            int s = p->s[i], l = s / N, c = s % N;
            if (O[l][c] == n->id && !(i > 0 && p->s[i - 1] / N != l) && !(i + 1 < p->n && p->s[i + 1] / N != l)) continue;
            disk(scr_t[l], touch_t[l], &ntouch_t[l], c, n->dtt);
            disk(scr_v, touch_v, &ntouch_v, c, n->dtv);
            if (i > 0 && p->s[i - 1] / N != l) {   /* via at c */
                for (int l2 = 0; l2 < 3; l2++) disk(scr_t[l2], touch_t[l2], &ntouch_t[l2], c, n->dvt);
                disk(scr_v, touch_v, &ntouch_v, c, n->dvv);
            }
        }
    }
    for (int l = 0; l < 3; l++) for (int i = 0; i < ntouch_t[l]; i++) { int c = touch_t[l][i]; occ_t[l][c] += sign; scr_t[l][c] = 0; }
    for (int i = 0; i < ntouch_v; i++) { int c = touch_v[i]; occ_v[c] += sign; scr_v[c] = 0; }
}

static void drop_legs(Net *n) {
    for (int g = 0; g < n->nleg; g++) free(n->leg[g].s);
    free(n->leg); n->leg = NULL; n->nleg = 0;
    free(n->failcl); n->failcl = NULL; n->nfail = 0;
    free(n->vc); n->vc = NULL; n->nvc = 0;
}

void pf_clear(int ni) { Net *n = &nets[ni]; stamp(n, -1); drop_legs(n); }

static float PRES, VIAC; static int HARD; static long MAXEXP = 40000000;
void pf_set_maxexp(long m) { MAXEXP = m; }

/* a via at cell c would sit closer than 0.55 mm (hole to hole 0.25 mm) to another via of the same net */
static int own_via_near(Net *n, int s, int c) {
    int x = c % W, y = c / W;
    for (int i = 0; i < n->nvc; i++) {
        int dx = n->vc[i] % W - x, dy = n->vc[i] / W - y, d2 = dx * dx + dy * dy;
        if (d2 > 0 && d2 < 121) return 1;
    }
    for (int k = 0, p = s; k < 14 && par[p] >= 0; k++, p = par[p]) {
        if (par[p] / N != p / N) {
            int dx = (p % N) % W - x, dy = (p % N) / W - y, d2 = dx * dx + dy * dy;
            if (d2 > 0 && d2 < 121) return 1;
        }
    }
    return 0;
}

/* A* from the marked source states (pushed by the caller) to any state with tmark == tepoch */
static int search(Net *n, int tx0, int ty0, int tx1, int ty1) {
    long expd = 0;
    while (hn) {
        HE e = hpop();
        int s = e.s, l = s / N, c = s % N;
        float g = gcost[s];
        int x = c % W, y = c / W;
        int dx = x < tx0 ? tx0 - x : x > tx1 ? x - tx1 : 0, dy = y < ty0 ? ty0 - y : y > ty1 ? y - ty1 : 0;
        float hh = (dx > dy ? dx + 0.4142f * dy : dy + 0.4142f * dx);
        if (e.f > g + hh + 1e-3f) continue;   /* stale */
        if (tmark[s] == tepoch) return s;
        if (++expd > MAXEXP) return -1;
        for (int k = 0; k < 8; k++) {
            int nx = x + NB8[k][0], ny = y + NB8[k][1];
            if (nx < 1 || ny < 1 || nx >= W - 1 || ny >= H - 1) continue;
            int nc = ny * W + nx, ns = l * N + nc;
            if (!passT(n, l, nc)) continue;
            int oc = (O[l][nc] == n->id) ? 0 : occT(n, l, nc);
            if (HARD && oc) continue;
            float step = (k < 4 ? 1.0f : 1.4142f) * CM[l][nc] * (1.0f / 16);
            if (O[l][nc] != n->id) step *= (1.0f + hist_t[l][nc]) * (1.0f + PRES * oc);
            float ng = g + step;
            if (mark[ns] != epoch || ng < gcost[ns]) {
                mark[ns] = epoch; gcost[ns] = ng; par[ns] = s;
                int ddx = nx < tx0 ? tx0 - nx : nx > tx1 ? nx - tx1 : 0, ddy = ny < ty0 ? ty0 - ny : ny > ty1 ? ny - ty1 : 0;
                hpush(ng + (ddx > ddy ? ddx + 0.4142f * ddy : ddy + 0.4142f * ddx), ns);
            }
        }
        /* via */
        int16_t v = VM[c];
        if ((v == 0 || v == n->id) && !(HARD && occ_v[c]) && !own_via_near(n, s, c)) {
            float vc = VIAC * (1.0f + hist_v[c]) * (1.0f + PRES * occ_v[c]);
            for (int l2 = 0; l2 < 3; l2++) {
                if (l2 == l || !passT(n, l2, c)) continue;
                if (HARD && O[l2][c] != n->id && occT(n, l2, c)) continue;
                int ns = l2 * N + c; float ng = g + vc;
                if (mark[ns] != epoch || ng < gcost[ns]) {
                    mark[ns] = epoch; gcost[ns] = ng; par[ns] = s;
                    hpush(ng + hh, ns);
                }
            }
        }
    }
    return -1;
}

/* route every leg of the net (its old copper is removed first). Returns the number of clusters left unconnected. */
int pf_route(int ni, float pres, int hard, float viacost) {
    Net *n = &nets[ni];
    stamp(n, -1); drop_legs(n);
    PRES = pres; HARD = hard; VIAC = viacost;
    if (n->ncl < 2) return 0;
    char *done = calloc(n->ncl, 1);
    n->failcl = malloc(n->ncl * sizeof(int));
    n->leg = malloc(n->ncl * sizeof(Cells));
    done[n->order[0]] = 1;
    for (int j = 1; j < n->ncl; j++) {
        int t = n->order[j];
        Cells *tc = &n->cl[t];
        tepoch++; epoch++;
        int tx0 = W, ty0 = H, tx1 = 0, ty1 = 0;
        for (int i = 0; i < tc->n; i++) {
            tmark[tc->s[i]] = tepoch;
            int c = tc->s[i] % N, x = c % W, y = c / W;
            if (x < tx0) tx0 = x; if (x > tx1) tx1 = x; if (y < ty0) ty0 = y; if (y > ty1) ty1 = y;
        }
        hn = 0;
#define SRC(S) do { int s_ = (S); if (mark[s_] != epoch) { mark[s_] = epoch; gcost[s_] = 0; par[s_] = -1; \
            int c_ = s_ % N, x_ = c_ % W, y_ = c_ / W; \
            int dx_ = x_ < tx0 ? tx0 - x_ : x_ > tx1 ? x_ - tx1 : 0, dy_ = y_ < ty0 ? ty0 - y_ : y_ > ty1 ? y_ - ty1 : 0; \
            hpush(dx_ > dy_ ? dx_ + 0.4142f * dy_ : dy_ + 0.4142f * dx_, s_); } } while (0)
        for (int q = 0; q < n->ncl; q++) if (done[q]) for (int i = 0; i < n->cl[q].n; i++) SRC(n->cl[q].s[i]);
        for (int g = 0; g < n->nleg; g++) for (int i = 0; i < n->leg[g].n; i++) SRC(n->leg[g].s[i]);
        int end = search(n, tx0, ty0, tx1, ty1);
        if (end < 0) { n->failcl[n->nfail++] = t; continue; }
        int len = 0; for (int s = end; s >= 0; s = par[s]) len++;
        Cells *p = &n->leg[n->nleg++]; p->n = len; p->s = malloc((size_t)len * 4);
        int i = len; for (int s = end; s >= 0; s = par[s]) p->s[--i] = s;
        for (i = 1; i < len; i++) if (p->s[i] / N != p->s[i - 1] / N) {
            n->vc = realloc(n->vc, (size_t)(n->nvc + 1) * 4); n->vc[n->nvc++] = p->s[i] % N;
        }
        done[t] = 1;
    }
    free(done);
    stamp(n, +1);
    return n->nfail;
}

/* path cells of the net inside another net's forbidden area; add_hist > 0 raises the history cost there */
int pf_conflicts(int ni, float add_hist) {
    Net *n = &nets[ni];
    stamp(n, -1);
    int bad = 0;
    for (int g = 0; g < n->nleg; g++) {
        Cells *p = &n->leg[g];
        for (int i = 0; i < p->n; i++) {
            int s = p->s[i], l = s / N, c = s % N;
            int isvia = i > 0 && p->s[i - 1] / N != l;
            if (O[l][c] != n->id && occT(n, l, c)) { bad++; if (add_hist > 0) hist_t[l][c] += add_hist; }
            if (isvia && occ_v[c]) { bad++; if (add_hist > 0) hist_v[c] += add_hist; }
        }
    }
    stamp(n, +1);
    return bad;
}

int pf_nleg(int ni) { return nets[ni].nleg; }
int pf_leg_len(int ni, int g) { return nets[ni].leg[g].n; }
void pf_leg_get(int ni, int g, int32_t *out) { memcpy(out, nets[ni].leg[g].s, (size_t)nets[ni].leg[g].n * 4); }
int pf_nfail(int ni) { return nets[ni].nfail; }
int pf_fail_get(int ni, int i) { return nets[ni].failcl[i]; }
/* number of cells the net could reach from cluster q through static obstacles only (diagnosis), capped */
long pf_reach(int ni, int q, long cap) {
    Net *n = &nets[ni];
    epoch++; hn = 0; long cnt = 0;
    int *st = malloc((size_t)(cap + 16) * 4 * 12); long sp = 0;
    for (int i = 0; i < n->cl[q].n; i++) { int s = n->cl[q].s[i]; if (mark[s] != epoch) { mark[s] = epoch; st[sp++] = s; } }
    while (sp && cnt < cap) {
        int s = st[--sp], l = s / N, c = s % N, x = c % W, y = c / W; cnt++;
        for (int k = 0; k < 4; k++) {
            int nx = x + NB8[k][0], ny = y + NB8[k][1];
            if (nx < 1 || ny < 1 || nx >= W - 1 || ny >= H - 1) continue;
            int nc = ny * W + nx, ns = l * N + nc;
            if (mark[ns] != epoch && passT(n, l, nc)) { mark[ns] = epoch; st[sp++] = ns; }
        }
        int16_t v = VM[c];
        if (v == 0 || v == n->id) for (int l2 = 0; l2 < 3; l2++) {
            int ns = l2 * N + c;
            if (l2 != l && mark[ns] != epoch && passT(n, l2, c)) { mark[ns] = epoch; st[sp++] = ns; }
        }
    }
    free(st);
    return cnt;
}

/* conflict cells of a net (cell index, layer 0-2 or 3 for a via) for diagnosis; returns the count written */
int pf_conflict_cells(int ni, int32_t *out, int cap) {
    Net *n = &nets[ni];
    stamp(n, -1);
    int k = 0;
    for (int g = 0; g < n->nleg; g++) {
        Cells *p = &n->leg[g];
        for (int i = 0; i < p->n && k + 2 <= cap; i++) {
            int s = p->s[i], l = s / N, c = s % N;
            if (O[l][c] != n->id && occT(n, l, c)) { out[k++] = c; out[k++] = l; }
            else if (i > 0 && p->s[i - 1] / N != l && occ_v[c]) { out[k++] = c; out[k++] = 3; }
        }
    }
    stamp(n, +1);
    return k / 2;
}

/* snapshot / restore of a net's routed legs (rip-up trials) */
typedef struct { int nleg; Cells *leg; int nfail; int *failcl; int nvc; int32_t *vc; } Snap;
static Snap *snaps = NULL; static int nsnaps = 0;
static void snap_free(Snap *s) {
    for (int g = 0; g < s->nleg; g++) free(s->leg[g].s);
    free(s->leg); free(s->failcl); free(s->vc); memset(s, 0, sizeof(Snap));
}
void pf_save(int ni) {
    if (nsnaps < nnets) { snaps = realloc(snaps, nnets * sizeof(Snap)); memset(snaps + nsnaps, 0, (nnets - nsnaps) * sizeof(Snap)); nsnaps = nnets; }
    Net *n = &nets[ni]; Snap *s = &snaps[ni];
    snap_free(s);
    s->nleg = n->nleg; s->leg = malloc((n->ncl + 1) * sizeof(Cells));
    for (int g = 0; g < n->nleg; g++) { s->leg[g].n = n->leg[g].n; s->leg[g].s = malloc((size_t)n->leg[g].n * 4); memcpy(s->leg[g].s, n->leg[g].s, (size_t)n->leg[g].n * 4); }
    s->nfail = n->nfail; s->failcl = malloc((n->ncl + 1) * sizeof(int)); if (n->nfail) memcpy(s->failcl, n->failcl, n->nfail * sizeof(int));
    s->nvc = n->nvc; s->vc = malloc((size_t)(n->nvc + 1) * 4); if (n->nvc) memcpy(s->vc, n->vc, (size_t)n->nvc * 4);
}
void pf_restore(int ni) {
    Net *n = &nets[ni]; Snap *s = &snaps[ni];
    stamp(n, -1); drop_legs(n);
    n->nleg = s->nleg; n->leg = s->leg; n->nfail = s->nfail; n->failcl = s->failcl; n->nvc = s->nvc; n->vc = s->vc;
    memset(s, 0, sizeof(Snap));
    stamp(n, +1);
}
