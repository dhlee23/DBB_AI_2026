"""1그룹 지사 그룹화: 1차(우수/중간/부진) + 중간형 세분화(데이터 기반 k 자동 선택)."""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from scoring import CATEGORY_MAP, SCORE_COLS

RANDOM_STATE = 42
CATEGORY_COLS = [f"{c}_달성률" for c in CATEGORY_MAP]


def assign_primary_tier(df: pd.DataFrame) -> pd.DataFrame:
    """11개 지표 점수를 표준화해 KMeans(k=3)로 우수형/중간형/부진형 분류."""
    df = df.copy()
    X = StandardScaler().fit_transform(df[SCORE_COLS])
    km = KMeans(n_clusters=3, n_init=10, random_state=RANDOM_STATE)
    raw_labels = km.fit_predict(X)

    order = (
        df.assign(_c=raw_labels)
        .groupby("_c")["종합점수"]
        .mean()
        .sort_values(ascending=False)
        .index.tolist()
    )
    tier_names = ["우수형", "중간형", "부진형"]
    mapping = {cluster_id: tier_names[i] for i, cluster_id in enumerate(order)}
    df["1차그룹"] = [mapping[c] for c in raw_labels]
    return df


def _describe_subcluster(sub_df: pd.DataFrame, all_mid_df: pd.DataFrame) -> str:
    """중간형 전체 평균 대비 강점/약점 카테고리 1~2개로 서술형 특징 생성."""
    diff = sub_df[CATEGORY_COLS].mean() - all_mid_df[CATEGORY_COLS].mean()
    diff.index = [c.replace("_달성률", "") for c in diff.index]
    strengths = diff.sort_values(ascending=False)
    top_strength = strengths.index[0]
    top_weakness = strengths.index[-1]
    if strengths.iloc[0] < 2 and abs(strengths.iloc[-1]) < 2:
        return "전반적 평이형"
    if strengths.iloc[-1] > -2:
        return f"{top_strength} 우수형"
    return f"{top_strength} 강점·{top_weakness} 약점형"


def refine_middle_tier(df: pd.DataFrame, k_range=range(2, 5)) -> pd.DataFrame:
    """중간형만 추출해 카테고리 달성률 기준 재군집, 실루엣 스코어로 k 자동 선택."""
    df = df.copy()
    df["그룹유형"] = df["1차그룹"]

    mid_mask = df["1차그룹"] == "중간형"
    mid_df = df[mid_mask]
    X = StandardScaler().fit_transform(mid_df[CATEGORY_COLS])

    best_k, best_score, best_labels = None, -1, None
    for k in k_range:
        km = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE)
        labels = km.fit_predict(X)
        score = silhouette_score(X, labels)
        if score > best_score:
            best_k, best_score, best_labels = k, score, labels

    sub_ids = sorted(set(best_labels))
    sub_mean_scores = {
        sid: mid_df.iloc[best_labels == sid]["종합점수"].mean() for sid in sub_ids
    }
    ordered_ids = sorted(sub_ids, key=lambda s: -sub_mean_scores[s])
    letters = [chr(ord("A") + i) for i in range(len(ordered_ids))]
    id_to_letter = {sid: letters[i] for i, sid in enumerate(ordered_ids)}

    subgroup_labels = np.array([id_to_letter[l] for l in best_labels])
    df.loc[mid_mask, "세부그룹"] = subgroup_labels

    descriptions = {}
    for sid in sub_ids:
        letter = id_to_letter[sid]
        sub_df = mid_df.iloc[best_labels == sid]
        descriptions[letter] = _describe_subcluster(sub_df, mid_df)

    df.loc[mid_mask, "그룹유형"] = "중간형-" + subgroup_labels
    df.loc[mid_mask, "그룹특징"] = [descriptions[l] for l in subgroup_labels]
    df.loc[~mid_mask, "세부그룹"] = ""
    df.loc[df["1차그룹"] == "우수형", "그룹특징"] = "전 지표 상위권 고르게 우수"
    df.loc[df["1차그룹"] == "부진형", "그룹특징"] = "전 지표 하위권, 종합 개선 필요"

    meta = {
        "선택된_k": best_k,
        "실루엣스코어": round(best_score, 4),
        "하위그룹설명": descriptions,
    }
    return df, meta


def build_group_profile(df: pd.DataFrame) -> pd.DataFrame:
    """03 시트용: 그룹유형별 지사수·카테고리 평균·특징."""
    agg = df.groupby("그룹유형").agg(
        지사수=("상호명_가상", "count"),
        평균종합점수=("종합점수", "mean"),
        **{f"{c}_평균달성률": (f"{c}_달성률", "mean") for c in CATEGORY_MAP},
        그룹특징=("그룹특징", "first"),
    )
    agg = agg.sort_values("평균종합점수", ascending=False).reset_index()
    return agg
