"""데이터 로딩 및 지표별 분위수 기반 점수 산출."""
import pandas as pd

RAW_ENCODING = "cp949"

KEY_COLS = ["사업단_가상", "조직명_가상", "상호명_가상"]

# 지표별 배점(총 100점)과 방향성 (higher_better=False → 낮을수록 좋은 손해율 지표)
KPI_CONFIG = {
    "보장성NCEV_가상": {"max_score": 20, "higher_better": True},
    "가동5만_가상": {"max_score": 5, "higher_better": True},
    "가동20만_가상": {"max_score": 5, "higher_better": True},
    "실수금률_가상": {"max_score": 5, "higher_better": True},
    "장기위험손해율_가상": {"max_score": 10, "higher_better": False},
    "장기1차년도손해율_가상": {"max_score": 10, "higher_better": False},
    "장기2차년도손해율_가상": {"max_score": 10, "higher_better": False},
    "유지율_4_가상": {"max_score": 10, "higher_better": True},
    "유지율_7_가상": {"max_score": 9, "higher_better": True},
    "유지율_13_가상": {"max_score": 8, "higher_better": True},
    "유지율_25_37_가상": {"max_score": 8, "higher_better": True},
}

KPI_COLS = list(KPI_CONFIG.keys())
SCORE_COLS = [f"{c}_점수" for c in KPI_COLS]

# 5개 카테고리 (군집 프로파일용)
CATEGORY_MAP = {
    "수익성": ["보장성NCEV_가상"],
    "활동성": ["가동5만_가상", "가동20만_가상"],
    "수금": ["실수금률_가상"],
    "손해율": ["장기위험손해율_가상", "장기1차년도손해율_가상", "장기2차년도손해율_가상"],
    "유지율": ["유지율_4_가상", "유지율_7_가상", "유지율_13_가상", "유지율_25_37_가상"],
}


def load_raw(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding=RAW_ENCODING)
    return df


def load_group1(path: str) -> pd.DataFrame:
    df = load_raw(path)
    g1 = df[df["그룹분류"] == "1그룹"].reset_index(drop=True)
    return g1


def add_kpi_scores(df: pd.DataFrame) -> pd.DataFrame:
    """지표별로 rank 기반 등분할(qcut)을 적용해 점수대별 지사 수를 균등하게 배분."""
    df = df.copy()
    for col, cfg in KPI_CONFIG.items():
        max_score = cfg["max_score"]
        higher_better = cfg["higher_better"]
        rank = df[col].rank(method="first")
        bucket = pd.qcut(rank, q=max_score, labels=False, duplicates="drop") + 1
        score = bucket if higher_better else (max_score + 1 - bucket)
        df[f"{col}_점수"] = score.astype(int)
    df["종합점수"] = df[SCORE_COLS].sum(axis=1)
    return df


def add_category_pct(df: pd.DataFrame) -> pd.DataFrame:
    """카테고리별 평균 달성률(0~100%) = 해당 카테고리 지표 점수/배점의 평균."""
    df = df.copy()
    for cat, cols in CATEGORY_MAP.items():
        pct_cols = []
        for col in cols:
            max_score = KPI_CONFIG[col]["max_score"]
            pct_col = f"__pct_{col}"
            df[pct_col] = df[f"{col}_점수"] / max_score * 100
            pct_cols.append(pct_col)
        df[f"{cat}_달성률"] = df[pct_cols].mean(axis=1)
        df.drop(columns=pct_cols, inplace=True)
    return df


def build_score_reference_table(df: pd.DataFrame) -> pd.DataFrame:
    """01_점수산출기준 시트용: 지표별 점수대별 지사 수 및 원자료 범위."""
    rows = []
    for col, cfg in KPI_CONFIG.items():
        max_score = cfg["max_score"]
        direction = "낮을수록 좋음" if not cfg["higher_better"] else "높을수록 좋음"
        score_col = f"{col}_점수"
        for s in range(1, max_score + 1):
            sub = df[df[score_col] == s][col]
            if len(sub) == 0:
                continue
            rows.append(
                {
                    "지표": col,
                    "배점": max_score,
                    "방향성": direction,
                    "점수": s,
                    "지사수": len(sub),
                    "원자료_최소": sub.min(),
                    "원자료_최대": sub.max(),
                }
            )
    return pd.DataFrame(rows)
