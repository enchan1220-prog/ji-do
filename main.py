"""2026년 6월 읍면동 인구로 작성한 전국 고령화 단계구분도."""

import re

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


POPULATION_URL = (
    "https://raw.githubusercontent.com/first2022-cyber/contents//main/"
    "population_ts_yearly_gender.zip"
)
BOUNDARY_URL = (
    "https://raw.githubusercontent.com/first2022-cyber/contents//main/"
    "sigungu_kr.geojson"
)
YEAR = 2026
PAPER = "#f3eddf"
INK = "#29251f"


def aggregate_population(frame):
    """동별 비율의 평균 대신, 시군구별 인구 합계로 비율을 구한다."""
    frame = frame.copy()
    frame.columns = frame.columns.str.strip()
    if not {"연도", "코드"}.issubset(frame.columns):
        raise ValueError("인구 자료에서 연도 또는 코드 항목을 찾을 수 없읍니다.")

    # 숫자 2026과 문자열 '2026년'을 모두 처리한다.
    years = frame["연도"].astype("string").str.extract(r"(\d{4})", expand=False)
    frame = frame.loc[years.eq(str(YEAR))].copy()
    if frame.empty:
        raise ValueError("2026년 인구 자료가 없어 지도를 작성할 수 없읍니다.")

    total_columns = [column for column in frame.columns if column.startswith("계_")]
    older_columns = []
    for column in total_columns:
        match = re.fullmatch(r"계_(\d+)세(?:\s*이상)?", column)
        if match and 65 <= int(match.group(1)) <= 100:
            older_columns.append(column)
    if not total_columns or not older_columns:
        raise ValueError("전체 인구 또는 65세 이상 인구 항목이 없읍니다.")

    # 원자료의 코드는 읽을 때부터 문자열로 보존한다.
    codes = frame["코드"].astype("string").str.strip()
    if not codes.str.fullmatch(r"\d{5,}").fillna(False).all():
        raise ValueError("읍면동 코드에 결측값 또는 숫자 이외의 문자가 있읍니다.")
    frame["코드"] = codes.str[:5]

    counts = frame[total_columns].apply(
        lambda column: pd.to_numeric(
            column.astype("string").str.replace(",", "", regex=False).str.strip(),
            errors="raise",
        )
    )
    if counts.isna().any().any() or (counts < 0).any().any():
        raise ValueError("인구 자료에 결측값 또는 음수가 있어 집계를 중단하였읍니다.")
    frame["전체 인구"] = counts.sum(axis=1)
    frame["65세 이상 인구"] = counts[older_columns].sum(axis=1)
    grouped = frame.groupby("코드", as_index=False)[
        ["전체 인구", "65세 이상 인구"]
    ].sum()
    # 인구가 없는 지역은 0%로 오인되지 않도록 결측값으로 남긴다.
    denominator = grouped["전체 인구"].where(grouped["전체 인구"].gt(0))
    grouped["고령화율"] = grouped["65세 이상 인구"].div(denominator).mul(100)
    return grouped


@st.cache_data(ttl=86400, show_spinner=False)
def load_population():
    # 성별 열을 읽지 않아 메모리 사용을 줄인다. ZIP은 pandas가 직접 읽는다.
    frame = pd.read_csv(
        POPULATION_URL,
        compression="zip",
        dtype={"코드": "string"},
        usecols=lambda column: column in {"연도", "코드"} or column.startswith("계_"),
        encoding="utf-8-sig",
    )
    return aggregate_population(frame)


@st.cache_data(ttl=86400, show_spinner=False)
def load_boundaries():
    response = requests.get(BOUNDARY_URL, timeout=(10, 90))
    response.raise_for_status()
    geojson = response.json()
    if geojson.get("type") != "FeatureCollection" or not geojson.get("features"):
        raise ValueError("경계 자료의 GeoJSON 형식이 올바르지 않읍니다.")
    rows = []
    for feature in geojson["features"]:
        properties = feature["properties"]
        code = str(properties["코드"]).strip()
        if not re.fullmatch(r"\d{5}", code):
            raise ValueError("경계 자료의 시군구 코드는 다섯 자리여야 합니다.")
        properties["코드"] = code
        rows.append({"코드": code, "시군구": properties["시군구"], "시도": properties["시도"]})
    regions = pd.DataFrame(rows).drop_duplicates()
    if regions["코드"].duplicated().any():
        raise ValueError("경계 자료에 같은 코드로 서로 다른 지역명이 실려 있읍니다.")
    return geojson, regions


def make_map(regions, geojson):
    # 모든 경계를 옅은 회색으로 먼저 그려 결측 지역도 경계가 남도록 한다.
    base = go.Choropleth(
        geojson=geojson,
        featureidkey="properties.코드",
        locations=regions["코드"].tolist(),
        z=[0] * len(regions),
        colorscale=[[0, "#d8d3c8"], [1, "#d8d3c8"]],
        showscale=False,
        marker_line_color="#817767",
        marker_line_width=0.5,
        customdata=regions[["시군구"]].to_numpy(),
        hovertemplate="<b>%{customdata[0]}</b><br>고령화율: 자료 없음<extra></extra>",
    )
    available = regions.dropna(subset=["고령화율"])
    colored = go.Choropleth(
        geojson=geojson,
        featureidkey="properties.코드",
        locations=available["코드"].tolist(),
        z=available["고령화율"].tolist(),
        customdata=available[["시군구"]].to_numpy(),
        colorscale=[
            [0.0, "#eee2c6"], [0.25, "#d3b88a"], [0.5, "#ad8655"],
            [0.75, "#7e5734"], [1.0, "#422b1d"],
        ],
        zmin=0,
        zmax=max(1, float(available["고령화율"].max())),
        marker_line_color="#817767",
        marker_line_width=0.45,
        colorbar={"title": {"text": "고령화율(%)"}, "ticksuffix": "%", "thickness": 14, "len": 0.65},
        hovertemplate="<b>%{customdata[0]}</b><br>고령화율: %{z:.2f}%<extra></extra>",
        name="고령화율",
    )
    figure = go.Figure([base, colored])
    figure.update_geos(
        fitbounds="locations", visible=False, projection_type="mercator",
        bgcolor=PAPER,
    )
    figure.update_layout(
        height=760,
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        paper_bgcolor=PAPER,
        font={"family": "Batang, Noto Serif CJK KR, serif", "color": INK},
        hoverlabel={"bgcolor": PAPER, "font_color": INK},
        dragmode="pan",
    )
    return figure


def main():
    st.set_page_config(page_title="전국 고령화 단계구분도 | 인구시보", layout="wide")
    st.markdown(
        """
        <style>
        .stApp { background: #f3eddf; color: #29251f; }
        .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3 {
            font-family: 'Batang', '바탕', 'Noto Serif CJK KR', serif;
        }
        .block-container { max-width: 1200px; padding-top: 2rem; }
        .masthead { text-align: center; border-top: 5px double #29251f;
                    border-bottom: 5px double #29251f; padding: 18px 0 12px; }
        .masthead .paper-name { font-size: 22px; letter-spacing: .5em; margin: 0; }
        .masthead h1 { font-size: clamp(27px, 4vw, 49px); font-weight: 900;
                       padding: 12px 8px; line-height: 1.35; }
        .edition { text-align: center; font-size: 14px; border-bottom: 1px solid #29251f;
                   padding: 9px 0; margin-bottom: 22px; }
        [data-testid="stMetric"] { border-top: 2px solid #29251f;
            border-bottom: 1px solid #91836c; padding: 13px 8px; }
        [data-testid="stMetricValue"] { font-family: 'Batang', '바탕', serif; }
        </style>
        <div class="masthead">
          <p class="paper-name">人口時報 (인구시보)</p>
          <h1>전국 고령화 단계구분도</h1>
        </div>
        <div class="edition">二〇二六年 六月 基準　│　全國 市郡區 人口特輯　│　統計圖</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "전국 읍면동(邑面洞)의 인구를 시군구(市郡區)별로 모아, 전체 인구 가운데 "
        "65세 이상이 차지하는 비율을 조사하였다. **빛깔이 짙을수록 고령 인구의 비중이 높다.**"
    )
    try:
        with st.spinner("전국 인구 및 행정구역 경계 자료를 집계하고 있읍니다."):
            population = load_population()
            geojson, boundaries = load_boundaries()
            regions = boundaries.merge(population, on="코드", how="left", validate="one_to_one")
    except Exception as error:
        st.error("자료를 불러오지 못하여 도면 작성을 중단하였읍니다. 아래 사유를 확인하여 주십시오.")
        st.caption(str(error))
        st.stop()

    if regions["고령화율"].notna().sum() == 0:
        st.error("인구 자료와 경계 자료에서 일치하는 유효 시군구 코드를 찾을 수 없읍니다.")
        st.stop()

    national_rate = population["65세 이상 인구"].sum() / population["전체 인구"].sum() * 100
    first, second, third = st.columns(3)
    first.metric("전국 고령화율(高齡化率)", f"{national_rate:.2f}%")
    second.metric("전국 65세 이상 인구", f"{population['65세 이상 인구'].sum():,.0f}명")
    third.metric("지도에 실린 시군구", f"{regions['고령화율'].notna().sum():,}곳")

    st.plotly_chart(
        make_map(regions, geojson),
        width="stretch",
        theme=None,
        config={"displayModeBar": False, "scrollZoom": False},
    )
    st.caption("【圖面 안내】 지역에 마우스를 올리면 시군구명과 고령화율이 나타납니다. 회색은 자료가 없는 지역입니다.")

    missing = regions.loc[regions["고령화율"].isna(), ["시도", "시군구", "코드"]]
    unmatched = population.loc[~population["코드"].isin(boundaries["코드"]), ["코드", "전체 인구"]]
    if not missing.empty or not unmatched.empty:
        st.warning(
            f"자료 대조 결과, 경계의 {len(missing)}개 지역은 인구 자료가 없거나 전체 인구가 0이며, "
            f"인구 자료의 {len(unmatched)}개 코드는 대응 경계가 없읍니다. 전국 수치는 모든 인구 자료를 포함합니다."
        )
        with st.expander("대조되지 않은 지역 및 코드"):
            if not missing.empty:
                st.write("경계는 있으나 고령화율을 구할 수 없는 지역")
                st.dataframe(missing, hide_index=True)
            if not unmatched.empty:
                st.write("인구는 있으나 대응 경계가 없는 코드")
                st.dataframe(unmatched, hide_index=True)

    with st.expander("시군구별 집계표(集計表) 열람"):
        table = regions[["시도", "시군구", "코드", "전체 인구", "65세 이상 인구", "고령화율"]]
        st.dataframe(table.sort_values("고령화율", ascending=False).reset_index(drop=True), hide_index=True)

    st.markdown("---")
    st.markdown("**【집계 일러두기】** 고령화율 = (65세 이상 인구 ÷ 전체 인구) × 100.")
    st.caption(
        "2026년 자료만 취하였다. 전체 인구는 ‘계_’로 시작하는 모든 연령 열을, "
        "고령 인구는 ‘계_65세’부터 ‘계_100세 이상’까지를 합산하였다. "
        "남녀 열은 중복 합산하지 않았다. 동 코드의 앞 다섯 자리와 경계 코드로 대조하였다."
    )
    st.markdown(f"資料 出處: [인구 원자료]({POPULATION_URL}) / [시군구 경계]({BOUNDARY_URL})")


if __name__ == "__main__":
    main()
