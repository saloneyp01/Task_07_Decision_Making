import pandas as pd
import os

df = pd.read_csv("wlax.csv")

# clean columns
df.columns = [c.strip().lower() for c in df.columns]

# extract GP from "gp-gs" like "19-19"
if "gp-gs" in df.columns:
    gp = df["gp-gs"].astype(str).str.split("-", n=1, expand=True)[0]
    df["gp"] = pd.to_numeric(gp, errors="coerce")
else:
    # fallback if your header is different, e.g., "gp_gs"
    gp = df["gp_gs"].astype(str).str.split("-", n=1, expand=True)[0]
    df["gp"] = pd.to_numeric(gp, errors="coerce")

# Convert numeric stat columns (coerce errors to NaN, treat NaN as 0 for sums)
num_cols = ["g","a","pts","sh","sog","gb","to","ct","dc","fouls"]
for c in num_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

# team totals and games
games = int(df["gp"].max())  # season games (e.g., 19)
goals_total   = int(df["g"].sum())
assists_total = int(df["a"].sum())
points_total  = int(df["pts"].sum())
shots_total   = int(df["sh"].sum())
sog_total     = int(df["sog"].sum())
shot_pct_team = (sog_total / shots_total) if shots_total else 0.0

# per game rates
goals_pg = goals_total / games
shots_pg = shots_total / games
assists_pg = assists_total / games
sog_pg = sog_total / games

summary = pd.DataFrame([{
    "Games": games,
    "Goals_total": goals_total,
    "Assists_total": assists_total,
    "Points_total": points_total,
    "Shots_total": shots_total,
    "Shots_on_goal_total": sog_total,
    "Shot_pct_team": round(shot_pct_team, 3),
    "Goals_per_game": round(goals_pg, 2),
    "Shots_per_game": round(shots_pg, 1),
    "Assists_per_game": round(assists_pg, 2),
    "SOG_per_game": round(sog_pg, 1),
}])

summary.to_csv("team_summary.csv", index=False)
print(summary)
print("Summary saved to team_summary.csv")

# where to save
out_dir = os.path.join(os.path.dirname(__file__), "ra")
os.makedirs(out_dir, exist_ok=True)

# per-player rates & tidy columns
player_summary = (
    df.assign(
        goals_pg=(df["g"] / df["gp"]).replace([float("inf")], 0).fillna(0).round(2),
        assists_pg=(df["a"] / df["gp"]).replace([float("inf")], 0).fillna(0).round(2),
        shot_pct=(df["sog"] / df["sh"]).replace([float("inf")], 0).fillna(0).round(3),
    )[["player", "gp", "g", "a", "pts", "sh", "sog", "shot_pct", "goals_pg", "assists_pg"]]
     .sort_values(["g", "a", "pts"], ascending=False)
)

# write the full per-player table
player_summary.to_csv(os.path.join(out_dir, "player_summary.csv"), index=False)

# small ranked summaries
top3_goals   = player_summary.nlargest(3, "g")
top3_assists = player_summary.nlargest(3, "a")
top5_shotpct = (player_summary[player_summary["sh"] >= 20]  # avoid tiny samples
                .sort_values("shot_pct", ascending=False)
                .head(5))

top3_goals.to_csv(os.path.join(out_dir, "top3_goals.csv"), index=False)
top3_assists.to_csv(os.path.join(out_dir, "top3_assists.csv"), index=False)
top5_shotpct.to_csv(os.path.join(out_dir, "top5_shotpct_min20shots.csv"), index=False)

# "facts" file 
def table_lines(df_small, title):
    lines = [f"{title}", "Player | GP | G | A | Shots | SOG | Shot% | G/GP | A/GP"]
    for _, r in df_small.iterrows():
        lines.append(
            f"{r['player']} | {int(r['gp']) if pd.notna(r['gp']) else 0} | "
            f"{int(r['g'])} | {int(r['a'])} | {int(r['sh'])} | {int(r['sog'])} | "
            f"{r['shot_pct']:.3f} | {r['goals_pg']:.2f} | {r['assists_pg']:.2f}"
        )
    return "\n".join(lines)

facts_path = os.path.join(out_dir, "facts_players.txt")
with open(facts_path, "w") as f:
    f.write("PLAYER-LEVEL FACTS (derived from wlax.csv)\n\n")
    f.write(table_lines(top3_goals,   "Top 3 by Goals"));   f.write("\n\n")
    f.write(table_lines(top3_assists, "Top 3 by Assists")); f.write("\n\n")
    f.write(table_lines(top5_shotpct, "Top 5 Shot% (min 20 shots)")); f.write("\n")

print(f" Wrote player summaries to: {out_dir}")
print("   - player_summary.csv")
print("   - top3_goals.csv")
print("   - top3_assists.csv")
print("   - top5_shotpct_min20shots.csv")
print("   - facts_players.txt")

# ---------- EXTRA SUMMARIES FOR TASK 7 ----------

# Per-game extras used below
df["pts_pg"] = (df["pts"] / df["gp"]).replace([float("inf")], 0).fillna(0)
df["gb_pg"]  = (df["gb"]  / df["gp"]).replace([float("inf")], 0).fillna(0)
df["ct_pg"]  = (df["ct"]  / df["gp"]).replace([float("inf")], 0).fillna(0)
df["to_pg"]  = (df["to"]  / df["gp"]).replace([float("inf")], 0).fillna(0)

# 1) Efficient scorers: blend volume (goals) and accuracy (shot_pct)
# Normalize goals and shot_pct to 0-1 (min-max across roster) to make a simple composite
g_min, g_max = df["g"].min(), df["g"].max()
sp_min, sp_max = (player_summary["shot_pct"].min(), player_summary["shot_pct"].max())

def minmax(x, lo, hi):
    rng = (hi - lo) if (hi - lo) else 1.0
    return (x - lo) / rng

eff_df = player_summary.copy()
eff_df["g_norm"] = player_summary["g"].apply(lambda x: minmax(x, g_min, g_max))
eff_df["sp_norm"] = player_summary["shot_pct"].apply(lambda x: minmax(x, sp_min, sp_max))

# weights: 0.6 volume, 0.4 accuracy (adjustable but state it in the report)
eff_df["efficiency_score"] = 0.6 * eff_df["g_norm"] + 0.4 * eff_df["sp_norm"]
efficient_scorers = (eff_df.sort_values("efficiency_score", ascending=False)
                          [["player","gp","g","sh","sog","shot_pct","goals_pg","efficiency_score"]]
                          .head(5))
efficient_scorers.to_csv(os.path.join(out_dir, "efficient_scorers.csv"), index=False)

# 2) Points per game (consistency proxy) with a small GP floor
points_per_game = (player_summary
                   .assign(ppg=(player_summary["g"]+player_summary["a"])/player_summary["gp"])
                   .query("gp >= 10")                    # simple floor to avoid tiny samples
                   .sort_values("ppg", ascending=False)
                   [["player","gp","g","a","pts","goals_pg","assists_pg","ppg"]])
points_per_game.to_csv(os.path.join(out_dir, "points_per_game.csv"), index=False)

# 3) Defensive Contribution Index (DCI)
# Simple: DCI = 1.0*GB_pg + 1.2*CT_pg - 0.8*TO_pg  (declare these weights in report)
defense_index = (df[["player","gp","gb_pg","ct_pg","to_pg"]]
                 .copy()
                 .assign(DCI = 1.0*df["gb_pg"] + 1.2*df["ct_pg"] - 0.8*df["to_pg"])
                 .sort_values("DCI", ascending=False))
defense_index.to_csv(os.path.join(out_dir, "defense_index.csv"), index=False)
df[["player","gp","to","to_pg"]]