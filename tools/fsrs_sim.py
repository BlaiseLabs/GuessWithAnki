"""Free cards with spaced repetition: a learner studies a deck day by day under FSRS, in the deck's own order or in
GuessWithAnki's, and guesses words from the kanji readings they have learned.

Model (one simulated learner):
  day       a session each day: due reviews first, then new cards while the day's budget of card showings lasts (and
            at most the pace's new cards): "steady" = 20 new a day, every review done; "timeboxed" = 150 showings a day,
            new cards fill what the reviews leave. Same-day learning steps (1 and 10 minutes) and relearning (10 minutes) as in
            Anki. Due reviews are always done (past the budget if need be); the budget only limits new cards.
  memory    each card has FSRS-6 memory (stability, difficulty; retrievability R from days since its last review), the
            same formulas as py-fsrs 6.3 (checked against it in --check).
  patterns  each kanji reading (会:かい) has an FSRS memory of its own, reviewed each day a word containing it is shown
            (Good when the word was answered right, Again when not). It counts as learned after `seen` sightings;
            a sighting is a word with it shown on a day (each word once a day, reviews included: two words with it on
            one day are two sightings), or with --sighting words only the first showing of each word (the first
            report's definition).
  guessing  g = rate x the product of R over the word's readings, when the word is judged guessable and all its readings
            are learned; else 0. A new card is right on first sight with probability g (free card). A review is right
            with probability 1 - (1 - R_card)(1 - g): a forgotten word can still be guessed (rescued), and FSRS, seeing
            Good, lengthens its interval. Right = Good, wrong = Again.
  measures  over `days`: words started, words known at the end (sum of R), card showings, free cards, rescued reviews,
            lapses; and the same learner in the deck's order.
  FSRS      Anki's default parameters at 90% or 80% retention, or your own with --params (21 numbers, as Anki's
            deck options show them after Optimize) and --retention.

    python3 tools/fsrs_sim.py COLLECTION.anki2 --files DIR --out OUT.json [--days 60] [--paces steady timeboxed]
                              [--seen 1 3 5 10] [--rate 1 0.8 0.5 0.25] [--seeds 2] [--procs 12]
                              [--params my_fsrs.json --retention 0.9]
    python3 tools/fsrs_sim.py --check        (the FSRS formulas against py-fsrs)"""
import argparse
import heapq
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DEFAULT = (0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334, 3.0194, 0.001, 1.8722, 0.1666, 0.796, 1.4835, 0.0614,
           0.2629, 1.6483, 0.6014, 1.8729, 0.5425, 0.0912, 0.0658, 0.1542)
SETUPS = {"anki-default-90": (DEFAULT, 0.90, "FSRS defaults, 90% retention (Anki's default)"),
          "default-80": (DEFAULT, 0.80, "FSRS defaults, 80% retention (fewer reviews)")}
LEARN, RELEARN, DAY = (1, 10), (10,), 1440
SNAP_DAYS = (7, 14, 30, 60, 90, 180, 365)
DAILY = ("showings", "started", "free", "rescued", "lapses")
PACES = {"steady": (100000, 20, "20 new cards a day, every review done"),
         "timeboxed": (150, 100, "150 card showings a day; new cards fill what reviews leave")}
AGAIN, GOOD = 1, 3


class FSRS:
    def __init__(self, w, retention):
        self.w, self.ret = w, retention
        self.decay = -w[20]
        self.factor = 0.9 ** (1 / self.decay) - 1
        self.d_easy = w[4] - math.exp(w[5] * 3) + 1

    def R(self, s, elapsed_days):
        return (1 + self.factor * elapsed_days / s) ** self.decay

    def init(self, g):
        w = self.w
        return max(w[g - 1], 0.001), min(max(w[4] - math.exp(w[5] * (g - 1)) + 1, 1.0), 10.0)

    def interval(self, s):
        return min(max(round(s / self.factor * (self.ret ** (1 / self.decay) - 1)), 1), 36500)

    def next_d(self, d, g):
        w = self.w
        d2 = d + (10.0 - d) * (-(w[6] * (g - 3))) / 9.0
        return min(max(w[7] * self.d_easy + (1 - w[7]) * d2, 1.0), 10.0)

    def short(self, s, g):
        w = self.w
        inc = math.exp(w[17] * (g - 3 + w[18])) * s ** -w[19]
        if g > 1:
            inc = max(inc, 1.0)
        return max(s * inc, 0.001)

    def next_s(self, d, s, r, g):
        w = self.w
        if g == AGAIN:
            ns = min(w[11] * d ** -w[12] * ((s + 1) ** w[13] - 1) * math.exp((1 - r) * w[14]),
                     s / math.exp(w[17] * w[18]))
        else:
            ns = s * (1 + math.exp(w[8]) * (11 - d) * s ** -w[9] * (math.exp(w[10] * (1 - r)) - 1))
        return max(ns, 0.001)

    def review(self, c, g, now):
        """c = [state, step, s, d, last, due] (state 0 new, 1 learning, 2 review, 3 relearning; times in minutes);
        updates c in place the way py-fsrs's review_card does (calendar days for elapsed time)"""
        state, step, s, d, last = c[0], c[1], c[2], c[3], c[4]
        el = (now // DAY - last // DAY) if last is not None else None
        if state in (0, 1):
            if s is None:
                s, d = self.init(g)
            elif el is not None and el < 1:
                s, d = self.short(s, g), self.next_d(d, g)
            else:
                s, d = self.next_s(d, s, self.R(s, el), g), self.next_d(d, g)
            step = step or 0
            if g == AGAIN:
                state, step, nxt = 1, 0, LEARN[0]
            elif step + 1 == len(LEARN):
                state, step, nxt = 2, None, self.interval(s) * DAY
            else:
                state, step, nxt = 1, step + 1, LEARN[step + 1]
        elif state == 2:
            s = self.short(s, g) if el < 1 else self.next_s(d, s, self.R(s, el), g)
            d = self.next_d(d, g)
            if g == AGAIN:
                state, step, nxt = 3, 0, RELEARN[0]
            else:
                nxt = self.interval(s) * DAY
        else:
            s, d = (self.short(s, g), self.next_d(d, g)) if el < 1 else (self.next_s(d, s, self.R(s, el), g), self.next_d(d, g))
            if g == AGAIN:
                step, nxt = 0, RELEARN[0]
            elif step + 1 == len(RELEARN):
                state, step, nxt = 2, None, self.interval(s) * DAY
            else:
                step, nxt = step + 1, RELEARN[step + 1]
        c[0], c[1], c[2], c[3], c[4], c[5] = state, step, s, d, now, now + nxt

    def recall(self, c, now):
        if c[2] is None or c[4] is None:
            return 0.0
        el = now // DAY - c[4] // DAY
        return 1.0 if el < 1 else self.R(c[2], el)


def check():
    """the formulas against py-fsrs 6.3.2 on random rating sequences at random day gaps"""
    import datetime as dt
    from fsrs import Card, Rating, Scheduler
    rng = random.Random(3)
    worst = 0.0
    for w, ret, _ in SETUPS.values():
        sch = Scheduler(parameters=w, desired_retention=ret, enable_fuzzing=False)
        mine = FSRS(w, ret)
        for _ in range(300):
            card, c = Card(), [0, None, None, None, None, 0]
            t0 = dt.datetime(2026, 1, 1, 9, tzinfo=dt.timezone.utc)
            now = 9 * 60
            for _ in range(12):
                g = rng.choice([1, 3, 3, 3])
                card, _ = sch.review_card(card, Rating(g), review_datetime=t0 + dt.timedelta(minutes=now - 540))
                mine.review(c, g, now)
                assert card.state.value == (c[0] if c[0] else 1), (card.state, c)
                worst = max(worst, abs(card.stability - c[2]) / card.stability, abs(card.difficulty - c[3]))
                due = (card.due - t0).total_seconds() / 60 + 540
                assert abs(due - c[5]) < 1e-6, (due, c[5])
                now = c[5] + rng.choice([0, 0, DAY, 3 * DAY])
    print("py-fsrs check passed: worst relative stability / difficulty difference %.2e" % worst)


def simulate(order, guess, pieces, fs, k, rate, days, budget, max_new, sighting, seed):
    rng = random.Random(seed)
    cards = {}                                   # key -> [state, step, s, d, last, due]
    pmem, pseen = {}, {}                         # pattern memory, sightings
    seen_day = {}                                # card -> last day it gave sightings
    nxt_new = 0
    m = {"showings": 0, "free": 0, "rescued": 0, "lapses": 0, "started": 0, "over_budget": 0}
    snaps, free_at = {}, {}
    daily, prev, known_weekly = {f: [] for f in DAILY}, dict(m), []

    def g_of(key, now):
        if key not in guess:
            return 0.0
        ps = pieces[key]
        if not ps or any(pseen.get(p, 0) < k for p in ps):
            return 0.0
        v = rate
        for p in ps:
            v *= fs.recall(pmem[p], now)
        return v

    def show(key, now, first):
        c = cards[key]
        g = g_of(key, now)
        if first:
            ok = rng.random() < g
            if ok:
                m["free"] += 1
        else:
            mem = rng.random() < fs.recall(c, now)
            gs = rng.random() < g
            ok = mem or gs
            if not mem and gs and c[0] == 2:
                m["rescued"] += 1
        if not ok and c[0] == 2:
            m["lapses"] += 1
        fs.review(c, GOOD if ok else AGAIN, now)
        day = now // DAY
        if sighting == "words" and not first:
            return
        if seen_day.get(key) == day:
            return
        seen_day[key] = day
        for p in set(pieces[key]):
            if p not in pmem:
                pmem[p] = [0, None, None, None, None, 0]
            fs.review(pmem[p], GOOD if ok else AGAIN, now)
            pseen[p] = pseen.get(p, 0) + 1

    for day in range(days):
        now = day * DAY + 9 * 60
        used, new_today = 0, 0
        due = [(min(c[5], now), key) for key, c in cards.items() if c[0] != 0 and c[5] // DAY <= day]
        heapq.heapify(due)
        while True:
            if due and (due[0][0] <= now or used >= budget or nxt_new >= len(order) or new_today >= max_new):
                t, key = heapq.heappop(due)
                now = max(now, t)
                if used >= budget:
                    m["over_budget"] += 1
                show(key, now, False)
            elif used < budget and nxt_new < len(order) and new_today < max_new:
                key = order[nxt_new]
                nxt_new += 1
                new_today += 1
                m["started"] += 1
                cards[key] = [0, None, None, None, None, now]
                show(key, now, True)
                if m["started"] in (100, 250, 500, 1000):
                    free_at[m["started"]] = m["free"]
            else:
                break
            used += 1
            m["showings"] += 1
            now += 0.25
            c = cards[key]
            if c[5] // DAY == day:                  # (still in its steps today)
                heapq.heappush(due, (c[5], key))
        for f in DAILY:
            daily[f].append(m[f] - prev[f])
        prev = dict(m)
        if (day + 1) % 7 == 0:
            end = (day + 1) * DAY + 9 * 60
            known_weekly.append(round(sum(max(fs.recall(c, end), g_of(key, end)) for key, c in cards.items()), 1))
        if day + 1 in SNAP_DAYS:
            end = (day + 1) * DAY + 9 * 60
            snaps[day + 1] = dict(m, known=round(sum(max(fs.recall(c, end), g_of(key, end)) for key, c in cards.items()), 1),
                                  memory_known=round(sum(fs.recall(c, end) for c in cards.values()), 1),
                                  patterns_learned=sum(1 for v in pseen.values() if v >= k))
    return {"snaps": snaps, "free_at": free_at, "daily": daily, "known_weekly": known_weekly}


def plan_job(args):
    from guesswithanki.core.path import plan
    started, before, full, pc, k = args
    o, _ = plan(started, before, full, dict(pc, need=k))
    return k, [it.key for it in o]


def job(args):
    (name, order_keys, guess, pieces, setup, (w, ret), k, rate, days, pace, sighting, seeds) = args
    budget, max_new, _ = PACES[pace]
    fs = FSRS(w, ret)
    runs = [simulate(order_keys, guess, pieces, fs, k, rate, days, budget, max_new, sighting, s) for s in range(seeds)]
    snaps = {d: {key: round(sum(r["snaps"][d][key] for r in runs) / len(runs), 1) for key in runs[0]["snaps"][d]}
             for d in runs[0]["snaps"]}
    free_at = {n: round(sum(r["free_at"].get(n, 0) for r in runs) / len(runs), 1) for n in runs[0]["free_at"]}
    out = {"snaps": snaps, "free_at": free_at}
    if SERIES:
        out["daily"] = {f: [round(sum(r["daily"][f][i] for r in runs) / len(runs), 1) for i in range(days)] for f in DAILY}
        out["known_weekly"] = [round(sum(r["known_weekly"][i] for r in runs) / len(runs), 1) for i in range(len(runs[0]["known_weekly"]))]
    return (name, setup, k, rate, sighting, pace), out


SERIES = False


def _init(series):
    global SERIES
    SERIES = series


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("collection", nargs="?")
    ap.add_argument("--files")
    ap.add_argument("--out")
    ap.add_argument("--days", type=int, default=60)
    ap.add_argument("--paces", nargs="+", default=list(PACES))
    ap.add_argument("--seen", type=int, nargs="+", default=[1, 3, 5, 10])
    ap.add_argument("--rate", type=float, nargs="+", default=[1.0, 0.8, 0.5, 0.25])
    ap.add_argument("--setups", nargs="+", default=list(SETUPS))
    ap.add_argument("--params", help="your own FSRS parameters: a JSON list of 21 numbers (Anki's deck options show "
                                     "them after Optimize), run as the setup 'custom'")
    ap.add_argument("--retention", type=float, default=0.9, help="desired retention for --params")
    ap.add_argument("--sighting", nargs="+", default=["reviews", "words"])
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--procs", type=int, default=12)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--series", action="store_true", help="keep each day's numbers (and words known each week)")
    ap.add_argument("--deck-every", type=int, default=0, help="GuessWithAnki's deck_every setting for the planned orders")
    a = ap.parse_args()
    if a.check:
        return check()
    from multiprocessing import Pool

    from anki.collection import Collection

    from guesswithanki.core import run
    setups = dict(SETUPS)
    if a.params:
        w = json.loads(Path(a.params).read_text())
        w = tuple(w["params"] if isinstance(w, dict) else w)
        if len(w) != 21:
            sys.exit("--params needs the 21 FSRS-6 parameters")
        setups["custom"] = (w, a.retention, "your FSRS parameters, %d%% retention" % round(100 * a.retention))
        a.setups = [x for x in a.setups if x != "custom"] + ["custom"]
    col = Collection(a.collection)
    cfg = run.merged({})
    an = run.analyse(col, cfg, a.files, use_server=True)
    col.close()
    before = run.original_order(a.files, an.new)
    ahead = min(len(before), 60 * a.days)
    pieces = {it.key: list(set(it.pieces)) for it in an.items}
    guess = set(an.full)
    orders = {"deck": [it.key for it in before]}
    with Pool(min(a.procs, len(a.seen))) as pool:
        for k, keys in pool.imap_unordered(plan_job, [(an.started, before, an.full,
                                                        dict(cfg["path"], ahead=ahead, deck_every=a.deck_every), k)
                                                       for k in a.seen]):
            orders["guesswithanki-%d" % k] = keys
    jobs = []
    for setup in a.setups:
        for k in a.seen:
            for rate in a.rate:
                for sighting in a.sighting:
                    for pace in a.paces:
                        for name in ("deck", "guesswithanki-%d" % k):
                            jobs.append((name.split("-")[0], orders[name], guess, pieces, setup, setups[setup][:2], k,
                                         rate, a.days, pace, sighting, a.seeds))
    res = {}
    with Pool(a.procs, initializer=_init, initargs=(a.series,)) as pool:
        for key, avg in pool.imap_unordered(job, jobs):
            res["|".join(map(str, key))] = avg
    out = {"deck": Path(a.collection).parent.name, "words": len(an.items), "judged_guessable": len(an.full),
           "days": a.days, "seeds": a.seeds, "paces": {k: PACES[k][2] for k in a.paces},
           "setups": {k: setups[k][2] for k in a.setups}, "results": res}
    Path(a.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    for setup in a.setups:
        for k in a.seen:
            for sighting in a.sighting:
                d, g = res["deck|%s|%d|0.8|%s|%s" % (setup, k, sighting, a.paces[0])], res["guesswithanki|%s|%d|0.8|%s|%s" % (setup, k, sighting, a.paces[0])]
                dd, gg = d["snaps"][min(30, a.days)], g["snaps"][min(30, a.days)]
                print("%-17s k=%-2d %-7s free@500 %4.0f -> %-4.0f day30: started %5.0f -> %-5.0f showings %6.0f -> %-6.0f known %6.0f -> %-6.0f rescued %4.0f -> %-4.0f lapses %4.0f -> %-4.0f"
                      % (setup, k, sighting, d["free_at"].get(500, 0), g["free_at"].get(500, 0), dd["started"], gg["started"],
                         dd["showings"], gg["showings"], dd["known"], gg["known"], dd["rescued"], gg["rescued"], dd["lapses"], gg["lapses"]))


if __name__ == "__main__":
    main()
