// Bay Area preflop equity engine.
//   eq check                      read 7 card ints per line on stdin, print evaluator value
//   eq table OUT.bin              exact equity of every 2-card keep on every flop class vs a random 2 cards
//   eq mc TABLE REPS OUT N [POOL] all-in equity of each 3-card hand vs a random (or POOL) 3-card hand
// Card = rank*4 + suit, rank 0 is a deuce.
// Build: gcc -O3 -march=native -fopenmp eq.c -o eq
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CLASSES 1755
#define HOLES 1326

static inline int top_bit(uint32_t m) { return 31 - __builtin_clz(m); }
static inline uint32_t keep_top(uint32_t m, int n) {
    uint32_t out = 0;
    while (n-- > 0 && m) { uint32_t b = 1u << top_bit(m); out |= b; m ^= b; }
    return out;
}
static inline int straight_high(uint32_t m) {  // 0 if none, else high rank index + 1
    uint32_t w = (m << 1) | (m >> 12 & 1);     // bit 0 = low ace
    uint32_t s = w & (w >> 1) & (w >> 2) & (w >> 3) & (w >> 4);
    return s ? top_bit(s) + 4 : 0;
}
static inline uint32_t val(int cat, uint32_t a, uint32_t b) { return (uint32_t)cat << 26 | a << 13 | b; }

static inline uint32_t eval7(const uint32_t s[4]) {
    uint32_t c = s[0], d = s[1], h = s[2], p = s[3];
    uint32_t all = c | d | h | p;
    for (int i = 0; i < 4; i++)
        if (__builtin_popcount(s[i]) >= 5) {
            int sf = straight_high(s[i]);
            return sf ? val(8, sf, 0) : val(5, 0, keep_top(s[i], 5));
        }
    uint32_t odd = c ^ d ^ h ^ p;
    uint32_t quad = c & d & h & p;
    uint32_t atleast3 = ((c & d) & (h | p)) | ((h & p) & (c | d));
    uint32_t trips = atleast3 & ~quad;
    uint32_t pairs = all & ~odd & ~quad;
    if (quad) return val(7, quad, keep_top(all & ~quad, 1));
    if (trips && (pairs || (trips & (trips - 1)))) {
        uint32_t t = keep_top(trips, 1);
        return val(6, t, keep_top((trips & ~t) | pairs, 1));
    }
    int st = straight_high(all);
    if (st) return val(4, st, 0);
    if (trips) return val(3, trips, keep_top(all & ~trips, 2));
    if (pairs) {
        uint32_t tp = keep_top(pairs, 2);
        if (pairs & (pairs - 1)) return val(2, tp, keep_top(all & ~tp, 1));
        return val(1, pairs, keep_top(all & ~pairs, 3));
    }
    return val(0, 0, keep_top(all, 5));
}
static inline void add(uint32_t s[4], int card) { s[card & 3] |= 1u << (card >> 2); }

// ---- index helpers
static int HOLE[52][52];
static int FLOP[52][52][52];        // sorted-or-not triple -> flop id
static int FLOP_CLASS[22100];       // flop id -> class
static uint8_t FLOP_PERM[22100][4]; // flop id -> suit map into the class representative
static int CLASS_REP[CLASSES][3];
static const uint8_t PERMS[24][4] = {
    {0,1,2,3},{0,1,3,2},{0,2,1,3},{0,2,3,1},{0,3,1,2},{0,3,2,1},
    {1,0,2,3},{1,0,3,2},{1,2,0,3},{1,2,3,0},{1,3,0,2},{1,3,2,0},
    {2,0,1,3},{2,0,3,1},{2,1,0,3},{2,1,3,0},{2,3,0,1},{2,3,1,0},
    {3,0,1,2},{3,0,2,1},{3,1,0,2},{3,1,2,0},{3,2,0,1},{3,2,1,0}};

static inline int pcard(int c, const uint8_t *perm) { return (c & ~3) | perm[c & 3]; }
static void sort3(int *x) {
    int t;
    if (x[0] > x[1]) { t = x[0]; x[0] = x[1]; x[1] = t; }
    if (x[1] > x[2]) { t = x[1]; x[1] = x[2]; x[2] = t; }
    if (x[0] > x[1]) { t = x[0]; x[0] = x[1]; x[1] = t; }
}
static void init_index(void) {
    int n = 0;
    for (int a = 0; a < 52; a++)
        for (int b = a + 1; b < 52; b++) { HOLE[a][b] = HOLE[b][a] = n++; }
    n = 0;
    int ids[22100][3];
    for (int a = 0; a < 52; a++)
        for (int b = a + 1; b < 52; b++)
            for (int c = b + 1; c < 52; c++) {
                FLOP[a][b][c] = FLOP[a][c][b] = FLOP[b][a][c] = FLOP[b][c][a] = FLOP[c][a][b] = FLOP[c][b][a] = n;
                ids[n][0] = a; ids[n][1] = b; ids[n][2] = c;
                n++;
            }
    static int class_of_canon[22100];
    memset(class_of_canon, -1, sizeof class_of_canon);
    int classes = 0;
    for (int f = 0; f < 22100; f++) {
        int best = -1, bp = 0;
        for (int p = 0; p < 24; p++) {
            int x[3] = {pcard(ids[f][0], PERMS[p]), pcard(ids[f][1], PERMS[p]), pcard(ids[f][2], PERMS[p])};
            int id = FLOP[x[0]][x[1]][x[2]];
            if (best < 0 || id < best) { best = id; bp = p; }
        }
        if (class_of_canon[best] < 0) {
            memcpy(CLASS_REP[classes], ids[best], sizeof(int) * 3);
            class_of_canon[best] = classes++;
        }
        FLOP_CLASS[f] = class_of_canon[best];
        memcpy(FLOP_PERM[f], PERMS[bp], 4);
    }
    if (classes != CLASSES) { fprintf(stderr, "expected 1755 classes, got %d\n", classes); exit(1); }
}

// ---- exact keep table
typedef struct { uint32_t v; int16_t a, b; } Entry;
static int cmp_entry(const void *x, const void *y) {
    uint32_t a = ((const Entry *)x)->v, b = ((const Entry *)y)->v;
    return a < b ? -1 : a > b;
}
static int cmd_table(const char *out) {
    float *tab = malloc(sizeof(float) * CLASSES * HOLES);
#pragma omp parallel for schedule(dynamic)
    for (int k = 0; k < CLASSES; k++) {
        const int *fl = CLASS_REP[k];
        uint32_t base[4] = {0, 0, 0, 0};
        uint8_t used[52] = {0};
        for (int i = 0; i < 3; i++) { add(base, fl[i]); used[fl[i]] = 1; }
        int live[49], nl = 0;
        for (int c = 0; c < 52; c++) if (!used[c]) live[nl++] = c;
        uint32_t *score = calloc(HOLES, sizeof(uint32_t));
        Entry *e = malloc(sizeof(Entry) * 1081);
        for (int t = 0; t < 49; t++)
            for (int r = t + 1; r < 49; r++) {
                uint32_t bd[4]; memcpy(bd, base, sizeof bd);
                add(bd, live[t]); add(bd, live[r]);
                int n = 0;
                for (int i = 0; i < 49; i++) {
                    if (i == t || i == r) continue;
                    for (int j = i + 1; j < 49; j++) {
                        if (j == t || j == r) continue;
                        uint32_t s[4]; memcpy(s, bd, sizeof s);
                        add(s, live[i]); add(s, live[j]);
                        e[n].v = eval7(s); e[n].a = live[i]; e[n].b = live[j]; n++;
                    }
                }
                qsort(e, n, sizeof(Entry), cmp_entry);
                int lower = 0, low_card[52] = {0};
                for (int i = 0; i < n;) {
                    int j = i, grp_card[52] = {0};
                    while (j < n && e[j].v == e[i].v) { grp_card[e[j].a]++; grp_card[e[j].b]++; j++; }
                    int g = j - i;
                    for (int m = i; m < j; m++) {
                        int a = e[m].a, b = e[m].b;
                        int wins = lower - low_card[a] - low_card[b];
                        // Inclusion-exclusion: the hand itself is the one hand holding both a and b,
                        // so this also leaves it out as its own opponent.
                        int ties = g - grp_card[a] - grp_card[b] + 1;
                        score[HOLE[a][b]] += 2 * wins + ties;
                    }
                    for (int c = 0; c < 52; c++) { low_card[c] += grp_card[c]; }
                    lower += g;
                    i = j;
                }
            }
        for (int h = 0; h < HOLES; h++) tab[k * HOLES + h] = -1.0f;
        for (int i = 0; i < 49; i++)
            for (int j = i + 1; j < 49; j++) {
                int h = HOLE[live[i]][live[j]];
                tab[k * HOLES + h] = (float)(score[h] / (2.0 * 990 * 1081));
            }
        free(score); free(e);
    }
    FILE *f = fopen(out, "wb");
    if (!f) { perror(out); return 1; }
    fwrite(tab, sizeof(float), CLASSES * HOLES, f);
    fclose(f);
    return 0;
}

// ---- Monte Carlo over dealt 3-card hands
typedef struct { uint64_t s[2]; } Rng;
static inline uint64_t rng_next(Rng *r) {  // xoroshiro128+
    uint64_t a = r->s[0], b = r->s[1], out = a + b;
    b ^= a;
    r->s[0] = (a << 24 | a >> 40) ^ b ^ (b << 16);
    r->s[1] = b << 37 | b >> 27;
    return out;
}
static inline int rng_below(Rng *r, int n) { return (int)(((rng_next(r) >> 32) * (uint64_t)n) >> 32); }
static uint64_t splitmix(uint64_t *x) {
    uint64_t z = (*x += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}
static const float *TAB;
static inline void best_keep(const int *h, const int *fl, int *k0, int *k1) {
    int f = FLOP[fl[0]][fl[1]][fl[2]], cls = FLOP_CLASS[f];
    const uint8_t *p = FLOP_PERM[f];
    int x = pcard(h[0], p), y = pcard(h[1], p), z = pcard(h[2], p);
    const float *row = TAB + (size_t)cls * HOLES;
    float e01 = row[HOLE[x][y]], e02 = row[HOLE[x][z]], e12 = row[HOLE[y][z]];
    if (e01 >= e02 && e01 >= e12) { *k0 = h[0]; *k1 = h[1]; }
    else if (e02 >= e12) { *k0 = h[0]; *k1 = h[2]; }
    else { *k0 = h[1]; *k1 = h[2]; }
}
static int cmd_mc(const char *table, const char *reps_path, const char *out, long trials, const char *pool_path) {
    static float buf[CLASSES * HOLES];
    FILE *f = fopen(table, "rb");
    if (!f || fread(buf, sizeof(float), CLASSES * HOLES, f) != CLASSES * HOLES) { fprintf(stderr, "bad table\n"); return 1; }
    fclose(f);
    TAB = buf;
    static int reps[22100][3];
    int nr = 0;
    f = fopen(reps_path, "r");
    if (!f) { perror(reps_path); return 1; }
    while (fscanf(f, "%d %d %d", &reps[nr][0], &reps[nr][1], &reps[nr][2]) == 3) nr++;
    fclose(f);
    static int pool[22100][3];
    int np = 0;
    if (pool_path) {
        f = fopen(pool_path, "r");
        if (!f) { perror(pool_path); return 1; }
        while (fscanf(f, "%d %d %d", &pool[np][0], &pool[np][1], &pool[np][2]) == 3) np++;
        fclose(f);
    }
    double *res = calloc(nr, sizeof(double));
    double *keep_share = calloc(nr * 3, sizeof(double));
#pragma omp parallel for schedule(dynamic)
    for (int ri = 0; ri < nr; ri++) {
        uint64_t seed = 0x5EED0000ULL + ri * 2654435761ULL + (pool_path ? 77 : 0);
        Rng rng = {{splitmix(&seed), splitmix(&seed)}};
        const int *hero = reps[ri];
        int deck0[49], n0 = 0;
        for (int c = 0; c < 52; c++) if (c != hero[0] && c != hero[1] && c != hero[2]) deck0[n0++] = c;
        long score = 0, kept[3] = {0, 0, 0};
        int deck[49];
        for (long t = 0; t < trials; t++) {
            int opp[3], bd[5], n = n0;
            memcpy(deck, deck0, sizeof deck);
            if (np) {
                for (;;) {
                    const int *o = pool[rng_below(&rng, np)];
                    if (o[0] != hero[0] && o[0] != hero[1] && o[0] != hero[2] &&
                        o[1] != hero[0] && o[1] != hero[1] && o[1] != hero[2] &&
                        o[2] != hero[0] && o[2] != hero[1] && o[2] != hero[2]) { memcpy(opp, o, sizeof opp); break; }
                }
                for (int i = 0; i < n;) {  // remove the opponent's cards from the deck
                    if (deck[i] == opp[0] || deck[i] == opp[1] || deck[i] == opp[2]) deck[i] = deck[--n];
                    else i++;
                }
                for (int i = 0; i < 5; i++) { int j = rng_below(&rng, n); bd[i] = deck[j]; deck[j] = deck[--n]; }
            } else {
                for (int i = 0; i < 3; i++) { int j = rng_below(&rng, n); opp[i] = deck[j]; deck[j] = deck[--n]; }
                for (int i = 0; i < 5; i++) { int j = rng_below(&rng, n); bd[i] = deck[j]; deck[j] = deck[--n]; }
            }
            int a0, a1, b0, b1;
            best_keep(hero, bd, &a0, &a1);
            best_keep(opp, bd, &b0, &b1);
            kept[(a0 != hero[0]) ? 0 : (a1 == hero[1] ? 2 : 1)]++;  // index = the card thrown away
            uint32_t sb[4] = {0, 0, 0, 0};
            for (int i = 0; i < 5; i++) add(sb, bd[i]);
            uint32_t s1[4], s2[4];
            memcpy(s1, sb, sizeof sb); memcpy(s2, sb, sizeof sb);
            add(s1, a0); add(s1, a1); add(s2, b0); add(s2, b1);
            uint32_t v1 = eval7(s1), v2 = eval7(s2);
            score += v1 > v2 ? 2 : v1 == v2 ? 1 : 0;
        }
        res[ri] = score / (2.0 * trials);
        for (int i = 0; i < 3; i++) keep_share[ri * 3 + i] = kept[i] / (double)trials;
    }
    f = fopen(out, "w");
    if (!f) { perror(out); return 1; }
    for (int i = 0; i < nr; i++)
        fprintf(f, "%d %d %d %.6f %.4f %.4f %.4f\n", reps[i][0], reps[i][1], reps[i][2], res[i],
                keep_share[i * 3], keep_share[i * 3 + 1], keep_share[i * 3 + 2]);
    fclose(f);
    return 0;
}

static int cmd_check(void) {
    int c[7];
    while (scanf("%d %d %d %d %d %d %d", c, c + 1, c + 2, c + 3, c + 4, c + 5, c + 6) == 7) {
        uint32_t s[4] = {0, 0, 0, 0};
        for (int i = 0; i < 7; i++) add(s, c[i]);
        printf("%u\n", eval7(s));
    }
    return 0;
}

int main(int argc, char **argv) {
    init_index();
    if (argc >= 2 && !strcmp(argv[1], "check")) return cmd_check();
    if (argc == 3 && !strcmp(argv[1], "table")) return cmd_table(argv[2]);
    if (argc >= 6 && !strcmp(argv[1], "mc")) return cmd_mc(argv[2], argv[3], argv[4], atol(argv[5]), argc > 6 ? argv[6] : NULL);
    fprintf(stderr, "usage: see header\n");
    return 2;
}
