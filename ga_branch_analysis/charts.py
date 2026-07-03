"""matplotlib 차트 생성 (dataviz 스킬 팔레트 적용, 한글 폰트: NanumGothic)."""
import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = "NanumGothic"
matplotlib.rcParams["axes.unicode_minus"] = False

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# dataviz 스킬 참조 팔레트 (references/palette.md)
CAT_COLORS = {
    "blue": "#2a78d6",
    "aqua": "#1baf7a",
    "yellow": "#eda100",
    "green": "#008300",
    "violet": "#4a3aa7",
    "red": "#e34948",
    "magenta": "#e87ba4",
    "orange": "#eb6834",
}
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#1c5cab", "#0d366b"]

TIER_COLOR_ORDER = ["blue", "aqua", "yellow", "violet", "red"]


def _style_axes(ax):
    ax.set_facecolor(SURFACE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(BASELINE)
    ax.spines["bottom"].set_color(BASELINE)
    ax.tick_params(colors=INK_SECONDARY, labelsize=9)
    ax.yaxis.grid(True, color=GRIDLINE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.title.set_color(INK_PRIMARY)


def _tier_colors(labels):
    uniq = list(dict.fromkeys(labels))  # 입력 순서(보통 점수 내림차순) 보존
    return {lab: CAT_COLORS[TIER_COLOR_ORDER[i % len(TIER_COLOR_ORDER)]] for i, lab in enumerate(uniq)}


def chart_group_counts(df: pd.DataFrame, out_path: str, group_col="그룹유형"):
    counts = df[group_col].value_counts()
    order = sorted(counts.index, key=lambda g: (-df[df[group_col] == g]["종합점수"].mean()))
    counts = counts.reindex(order)
    colors_map = _tier_colors(order)

    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    bars = ax.bar(counts.index, counts.values, color=[colors_map[g] for g in counts.index], width=0.6)
    for b, v in zip(bars, counts.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 1, str(v), ha="center", va="bottom",
                 color=INK_PRIMARY, fontsize=9)
    ax.set_title("그룹유형별 지사 수 (1그룹, n=%d)" % len(df), fontsize=12, fontweight="bold")
    ax.set_ylabel("지사 수")
    plt.xticks(rotation=20, ha="right")
    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE)
    plt.close(fig)


def chart_score_boxplot(df: pd.DataFrame, out_path: str, group_col="그룹유형"):
    order = df.groupby(group_col)["종합점수"].mean().sort_values(ascending=False).index.tolist()
    data = [df[df[group_col] == g]["종합점수"].values for g in order]
    colors_map = _tier_colors(order)

    fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=150)
    bp = ax.boxplot(data, patch_artist=True, tick_labels=order, widths=0.5,
                     medianprops=dict(color=INK_PRIMARY, linewidth=1.5))
    for patch, g in zip(bp["boxes"], order):
        patch.set_facecolor(colors_map[g])
        patch.set_alpha(0.75)
        patch.set_edgecolor(INK_SECONDARY)
    ax.set_title("그룹유형별 종합점수 분포", fontsize=12, fontweight="bold")
    ax.set_ylabel("종합점수 (최대 100점)")
    plt.xticks(rotation=20, ha="right")
    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE)
    plt.close(fig)


def chart_category_radar(profile_df: pd.DataFrame, category_cols, out_path: str):
    labels = [c.replace("_평균달성률", "") for c in category_cols]
    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6.5, 6.5), subplot_kw=dict(polar=True), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    colors_map = _tier_colors(profile_df["그룹유형"].tolist())
    for _, row in profile_df.iterrows():
        values = [row[c] for c in category_cols]
        values += values[:1]
        color = colors_map[row["그룹유형"]]
        ax.plot(angles, values, color=color, linewidth=2, label=row["그룹유형"])
        ax.fill(angles, values, color=color, alpha=0.08)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, color=INK_PRIMARY, fontsize=10)
    ax.tick_params(colors=INK_MUTED)
    ax.spines["polar"].set_color(BASELINE)
    ax.grid(color=GRIDLINE)
    ax.set_title("그룹유형별 카테고리 평균 달성률(%)", fontsize=12, fontweight="bold", color=INK_PRIMARY, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE)
    plt.close(fig)


def chart_score_distribution(df: pd.DataFrame, col: str, out_path: str, title: str):
    fig, ax = plt.subplots(figsize=(6.5, 4), dpi=150)
    max_score = df[col].max()
    bins = np.arange(0.5, max_score + 1.5, 1)
    ax.hist(df[col], bins=bins, color=CAT_COLORS["blue"], edgecolor=SURFACE, linewidth=1.2)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel("점수")
    ax.set_ylabel("지사 수")
    ax.set_xticks(range(1, int(max_score) + 1))
    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE)
    plt.close(fig)


def chart_q4_hist(q4_df: pd.DataFrame, out_path: str):
    groups = sorted(q4_df["그룹분류"].unique())
    colors = [CAT_COLORS["blue"], CAT_COLORS["aqua"], CAT_COLORS["orange"]]
    fig, axes = plt.subplots(1, len(groups), figsize=(13, 4), dpi=150, sharey=False)
    for ax, g, c in zip(axes, groups, colors):
        vals = q4_df[q4_df["그룹분류"] == g]["평균보장성NCEV"]
        ax.hist(vals, bins=6, color=c, edgecolor=SURFACE, linewidth=1.2)
        ax.set_title(f"{g}", fontsize=11, fontweight="bold")
        ax.set_xlabel("사업단 평균 보장성NCEV")
        _style_axes(ax)
    axes[0].set_ylabel("사업단 수")
    fig.suptitle("그룹별 사업단 평균 보장성NCEV 분포", fontsize=13, fontweight="bold", y=1.03)
    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


def chart_q5_box(q5_df: pd.DataFrame, out_path: str):
    groups = sorted(q5_df["그룹분류"].unique())
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), dpi=150)
    metrics = ["가동5만_가상", "가동20만_가상"]
    titles = ["사업단 평균 가동5만", "사업단 평균 가동20만"]
    colors = [CAT_COLORS["blue"], CAT_COLORS["aqua"], CAT_COLORS["orange"]]
    for ax, metric, title in zip(axes, metrics, titles):
        data = [q5_df[q5_df["그룹분류"] == g][metric].values for g in groups]
        bp = ax.boxplot(data, patch_artist=True, tick_labels=groups, widths=0.5,
                         medianprops=dict(color=INK_PRIMARY, linewidth=1.5))
        for patch, c in zip(bp["boxes"], colors):
            patch.set_facecolor(c)
            patch.set_alpha(0.75)
            patch.set_edgecolor(INK_SECONDARY)
        ax.set_title(title, fontsize=11, fontweight="bold")
        _style_axes(ax)
    fig.suptitle("그룹별 사업단 평균 가동률 분포", fontsize=13, fontweight="bold", y=1.03)
    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
