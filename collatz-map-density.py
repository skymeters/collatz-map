#!/usr/bin/env python3
import sys, time

# ================== Config ==================
MAX_VAL   = 2**27 + 5     # change to 10**9 for a full run
BAR_WIDTH = 40

# ANSI colors (optional on Windows: 'pip install colorama')
RESET = "\033[0m"
GREEN = "\033[92m"
BLUE  = "\033[94m"
try:
    # Enable ANSI on Windows terminals that need it
    import colorama
    colorama.just_fix_windows_console()
except Exception:
    pass

# ================ Collatz ===================
def is_pow2(x: int) -> bool:
    return x > 0 and (x & (x - 1)) == 0

def step(n: int) -> int:
    return n // 2 if (n % 2 == 0) else 3*n + 1

def walk_collect_odds(start_n: int, seen_odds: set[int]):
    """
    Walk full Collatz from start_n, collecting only ODD integers visited.
    Stop when:
      - we hit an odd already in seen_odds, OR
      - the chain enters a power-of-two tail (=> goes to 1).
    Returns:
      color: "blue" if start_n already known, else "green"
      odds:  set of odd integers encountered in this walk
    """
    if start_n in seen_odds:
        return "blue", {start_n}

    cur = start_n
    odds = {start_n}
    while True:
        cur = step(cur)
        if cur % 2 == 1:
            if cur in seen_odds:
                odds.add(cur)
                return "green", odds
            odds.add(cur)
        if cur == 1 or is_pow2(cur):
            return "green", odds

# ============== UI helpers =================
def progress_line(done: int, total: int, start_ts: float) -> str:
    done = max(0, done)
    total = max(1, total)
    frac = done / total
    filled = int(frac * BAR_WIDTH)
    bar = "=" * filled + "-" * (BAR_WIDTH - filled)

    elapsed = max(0.0, time.time() - start_ts)
    rate = (done / elapsed) if elapsed > 0 else 0.0
    remain = total - done
    eta = (remain / rate) if rate > 0 else float("inf")

    def fmt_eta(s):
        if s == float("inf"):
            return "ETA ∞"
        s = int(s)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        if h: return f"ETA {h}h{m:02d}m{s:02d}s"
        if m: return f"ETA {m}m{s:02d}s"
        return f"ETA {s}s"

    return f"[{bar}] {frac*100:6.2f}% | {done}/{total} | {fmt_eta(eta)}"

def redraw_bar(done: int, total: int, start_ts: float):
    sys.stdout.write("\r" + progress_line(done, total, start_ts))
    sys.stdout.flush()

def print_above_bar(msg: str, done: int, total: int, start_ts: float):
    if msg != "":
        # Clear current bar line, print msg, then redraw the bar.
        sys.stdout.write("\r\x1b[2K")
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()
    redraw_bar(done, total, start_ts)

# ================== Main ====================
def main():
    seen_odds: set[int] = {1}  # 1 is initially known; don't count it in ratios

    # run-length state
    current_color = None
    previous_color = "green"
    current_len = 0
    pending_green = None  # last completed green-run waiting for a blue-run to pair

    # cumulative (pairs-only) tallies
    total_green = 0
    total_blue  = 0
    total_runs  = 0  # total_green + total_blue (completed pairs only)

    # progress setup
    total_odds = ((MAX_VAL - 1) // 2) + 1   # number of odd starts in [1..MAX_VAL]
    processed  = 0
    start_ts   = time.time()
    next_pow = 2
    print_await_next_pair = False
    redraw_bar(processed, total_odds, start_ts)

    for n in range(1, MAX_VAL + 1, 2):
        color, odds_seen = walk_collect_odds(n, seen_odds)
        seen_odds.update(odds_seen)

        processed += 1

        # Skip counting n=1 in green/blue (but still advance progress)
        if n != 1:
            # Update run-length
            if current_color is None:
                current_color = color
                current_len = 1
            elif color == current_color:
                current_len += 1
            else:
                # Finish previous run
                if current_color == "green":
                    pending_green = current_len
                else:  # previous was blue: we can close a pair
                    if pending_green is not None:
                        g_count = pending_green
                        b_count = current_len
                        total_green += g_count
                        total_blue  += b_count
                        total_runs  += g_count + b_count
                        pending_green = None
                # Start new run
                current_color = color
                current_len = 1

        # Print after every odd (i.e., when (n+1) % 2 == 0)
        # Cumulative percentages from *completed* (green, blue) pairs only.
        if total_runs > 0:
            g_pct = 100.0 * total_green / total_runs
            b_pct = 100.0 * total_blue  / total_runs
        else:
            g_pct = b_pct = 0.0
        # if flagged and last pair completed => print
        if print_await_next_pair and current_color == "blue" and previous_color == "green":
            print_above_bar(
                f"2^{next_pow} {GREEN}{g_pct:.8f}%{RESET} {BLUE}{b_pct:.8f}%{RESET}",
                processed, total_odds, start_ts
            )
            print_await_next_pair = False
        if (n + 1) == (2 ** next_pow):
            if n >= 17:
                print_await_next_pair = True
            else:
                print_above_bar(
                    f"2^{next_pow} {GREEN}{g_pct:.8f}%{RESET} {BLUE}{b_pct:.8f}%{RESET}",
                    processed, total_odds, start_ts
                )
            next_pow += 1
        if n % 16384 == 1:
            print_above_bar(
                "", processed, total_odds, start_ts
            )
        
        previous_color = current_color
    sys.stdout.write("\nDone.\n")

if __name__ == "__main__":
    main()
