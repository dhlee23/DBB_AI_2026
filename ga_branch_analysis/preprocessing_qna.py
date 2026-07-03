"""전처리 1~6번 문항: 전체 데이터(1/2/3그룹) 기준 groupby 집계."""
import pandas as pd

Q2_COLS = [
    "보장성NCEV_가상",
    "가동5만_가상",
    "가동20만_가상",
    "실수금률_가상",
    "장기위험손해율_가상",
    "장기1차년도손해율_가상",
    "장기2차년도손해율_가상",
]


def q1_count_by_dept_org(df: pd.DataFrame) -> pd.DataFrame:
    s = df.groupby(["사업단_가상", "조직명_가상"])["상호명_가상"].count()
    return s.reset_index(name="상호명_개수")


def q2_dept_means(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("사업단_가상")[Q2_COLS].mean().reset_index()


def q3_ncev_compare(df: pd.DataFrame, q2: pd.DataFrame):
    ranked = q2[["사업단_가상", "보장성NCEV_가상"]].sort_values(
        "보장성NCEV_가상", ascending=False
    ).reset_index(drop=True)
    top_dept = ranked.iloc[0]["사업단_가상"]
    bottom_dept = ranked.iloc[-1]["사업단_가상"]
    diff = ranked.iloc[0]["보장성NCEV_가상"] - ranked.iloc[-1]["보장성NCEV_가상"]

    top_sub = df[df["사업단_가상"] == top_dept]
    n_orgs = top_sub["조직명_가상"].nunique()
    n_names = top_sub["상호명_가상"].nunique()
    top10 = top_sub.sort_values("보장성NCEV_가상", ascending=False).head(10)[
        ["상호명_가상", "조직명_가상", "보장성NCEV_가상"]
    ].reset_index(drop=True)

    summary = {
        "최고_사업단": top_dept,
        "최고_평균NCEV": ranked.iloc[0]["보장성NCEV_가상"],
        "최저_사업단": bottom_dept,
        "최저_평균NCEV": ranked.iloc[-1]["보장성NCEV_가상"],
        "차이": diff,
        "최고사업단_조직수": n_orgs,
        "최고사업단_상호명수": n_names,
    }
    return ranked, summary, top10


def q4_group_dept_ncev(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["그룹분류", "사업단_가상"])["보장성NCEV_가상"]
        .mean()
        .reset_index(name="평균보장성NCEV")
    )


def q5_group_dept_utilization(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["그룹분류", "사업단_가상"])[["가동5만_가상", "가동20만_가상"]]
        .mean()
        .reset_index()
    )


def q6_loss_ratio_increase(df: pd.DataFrame):
    dept_lr = df.groupby("사업단_가상")[
        ["장기1차년도손해율_가상", "장기2차년도손해율_가상"]
    ].mean()
    dept_lr["증가폭"] = dept_lr["장기2차년도손해율_가상"] - dept_lr["장기1차년도손해율_가상"]
    dept_lr = dept_lr.sort_values("증가폭").reset_index()

    min_dept = dept_lr.iloc[0]["사업단_가상"]
    sub = df[df["사업단_가상"] == min_dept].copy()
    sub["증가폭"] = sub["장기2차년도손해율_가상"] - sub["장기1차년도손해율_가상"]

    cols = ["상호명_가상", "조직명_가상", "장기1차년도손해율_가상", "장기2차년도손해율_가상", "증가폭"]
    top10_min = sub.sort_values("증가폭").head(10)[cols].reset_index(drop=True)
    top10_max = sub.sort_values("증가폭", ascending=False).head(10)[cols].reset_index(drop=True)

    return dept_lr, min_dept, top10_min, top10_max
