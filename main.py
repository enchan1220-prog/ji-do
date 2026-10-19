"""2015~2026년 전국 인구 단계구분도."""

import re
from random import Random
from urllib.parse import quote

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


BASE_URL = "https://raw.githubusercontent.com/first2022-cyber/contents/main/"
POPULATION_URL = BASE_URL + "population_ts_yearly_gender.zip"
BOUNDARY_URL = BASE_URL + "sigungu_kr.geojson"
PAPER, INK = "#efe4cd", "#393229"
COLORS = ["#eee2c6", "#d3b88a", "#ad8655", "#7e5734", "#422b1d"]
INDICATORS = {
    "고령화율 (65세 이상)": {
        "column": "고령화율", "count": "고령 인구", "title": "고령화",
        "cuts": [19, 23, 28, 38],
    },
    "유소년 비율 (0~14세)": {
        "column": "유소년 비율", "count": "유소년 인구", "title": "유소년 인구",
        "cuts": [7, 10, 13, 16],
    },
}
def make_paper_texture():
    """길이가 다른 섬유와 닥 껍질 반점을 큰 무늬판 안에 흩어 놓는다."""
    # 같은 배치를 유지하여 연도나 지표를 바꿀 때 무늬가 움직이지 않는다.
    rng = Random(1974)
    width, height = 1400, 1000
    shapes = []

    for index in range(140):
        x, y = rng.uniform(0, width), rng.uniform(0, height)
        length = rng.uniform(150, 340) if index < 24 else rng.uniform(30, 170)
        bend = rng.uniform(-22, 22)
        thickness = rng.uniform(0.8, 2.5)
        opacity = rng.uniform(0.12, 0.27)
        color = rng.choice(["#78582e", "#987342", "#ae8951", "#fff8df"])
        transform = f'translate({x:.1f} {y:.1f}) rotate({rng.uniform(0, 180):.1f})'

        if index % 3:
            # 긴 굽은 섬유와 가늘게 갈라지는 잔가닥.
            shape = (
                f'<path d="M0 0 C{length * .3:.1f} {bend:.1f} '
                f'{length * .7:.1f} {-bend * .6:.1f} {length:.1f} 0" '
                f'fill="none" stroke="{color}" stroke-width="{thickness:.2f}" '
                f'stroke-linecap="round"/>'
            )
            if index % 4 == 0:
                shape += (
                    f'<path d="M{length * .25:.1f} {bend * .2:.1f} '
                    f'Q{length * .6:.1f} {bend + 9:.1f} {length * .9:.1f} 7" '
                    f'fill="none" stroke="{color}" stroke-width=".55"/>'
                )
        else:
            # 양끝이 가늘고 가운데가 넓은 닥 섬유 조각.
            shape = (
                f'<path d="M0 0 Q{length * .4:.1f} {bend - thickness:.1f} '
                f'{length:.1f} 0 Q{length * .55:.1f} {bend + thickness * 2:.1f} '
                f'0 0Z" fill="{color}"/>'
            )
        shapes.append(f'<g transform="{transform}" opacity="{opacity:.2f}">{shape}</g>')

    for _ in range(220):
        x, y = rng.uniform(0, width), rng.uniform(0, height)
        radius = rng.uniform(0.5, 3.2)
        shapes.append(
            f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{radius:.2f}" '
            f'ry="{radius * rng.uniform(.25, 1.4):.2f}" '
            f'transform="rotate({rng.uniform(0, 180):.1f} {x:.1f} {y:.1f})" '
            f'fill="#805e31" opacity="{rng.uniform(.09, .25):.2f}"/>'
        )

    # 가장자리에 걸친 섬유도 반대편에 이어지도록 무늬판을 감싸 그린다.
    copies = "".join(
        f'<use href="#fibers" x="{dx}" y="{dy}"/>'
        for dx in (-width, 0, width) for dy in (-height, 0, height)
    )
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
         viewBox="0 0 {width} {height}">
      <defs>
        <filter id="grain" x="0" y="0" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency=".48" numOctaves="3"
            stitchTiles="stitch" seed="17"/>
          <feColorMatrix type="saturate" values="0"/>
        </filter>
        <filter id="pulp" x="0" y="0" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency=".012 .038" numOctaves="4"
            stitchTiles="stitch" seed="29"/>
          <feColorMatrix type="saturate" values="0"/>
        </filter>
        <g id="fibers">{''.join(shapes)}</g>
      </defs>
      <rect width="100%" height="100%" filter="url(#pulp)" opacity=".18"/>
      <rect width="100%" height="100%" filter="url(#grain)" opacity=".10"/>
      {copies}
    </svg>
    """
    return "data:image/svg+xml," + quote(svg)


# 외부 그림 파일 없이 SVG와 CSS로 한지의 질감을 만든다.
PAPER_TEXTURE = make_paper_texture()
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Gowun+Batang:wght@400;700&display=swap');
.stApp {
    color: #393229;
    background-color: #e5d5b6;
    background-image:
        url("__PAPER_TEXTURE__"),
        radial-gradient(ellipse at 4% 8%, #9d723d24, transparent 43%),
        radial-gradient(ellipse at 96% 86%, #94633226, transparent 48%),
        linear-gradient(102deg, #d9c29b, #efe4cd 18%, #f2e9d7 53%, #ddc8a5);
    background-size: 1680px 1200px, auto, auto, auto;
    background-position: -190px -75px, center, center, center;
}
.stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3,
.stApp label, .stApp input, .stApp button,
[data-baseweb="select"], [data-baseweb="popover"],
[data-testid="stMetricValue"], [data-testid="stCaptionContainer"] {
    font-family: 'Gowun Batang', 'Batang', serif;
}
.stApp p { font-size: 17px; line-height: 1.85; }
.block-container {
    max-width: 1250px;
    margin-top: 1.2rem;
    margin-bottom: 2rem;
    padding: 2rem clamp(18px, 3vw, 48px) 3rem;
    background-color: #efe4cd;
    background-image:
        url("__PAPER_TEXTURE__"),
        radial-gradient(ellipse at 0% 0%, #9e71352b, transparent 38%),
        radial-gradient(ellipse at 100% 97%, #9a6b3329, transparent 36%),
        radial-gradient(ellipse at 18% 72%, #9b702a18, transparent 22%),
        radial-gradient(ellipse at 82% 61%, #96602e16, transparent 19%),
        radial-gradient(ellipse at 72% 28%, #fffaf022, transparent 60%),
        linear-gradient(93deg, #b58c4520, transparent 7%, transparent 94%, #b58c451c);
    background-size: 1400px 1000px, auto, auto, auto, auto, auto, auto;
    background-position: 47px 83px, center, center, center, center, center, center;
    border: 1px solid #a9885140;
    border-radius: 2px 5px 3px 2px;
    box-shadow: 0 9px 32px #50391c24, inset 0 0 65px #a1793320;
}
[data-testid="stHeader"] { background: #e5d5b6ee; }
[data-baseweb="select"] > div {
    background-color: #f5eddc;
    border-color: #a88c605c;
    border-radius: 3px;
}
.stApp hr { border-color: #92744b66; }
.masthead { text-align: center; border-top: 4px double #74634d;
    border-bottom: 4px double #74634d; padding: 16px 0; margin-bottom: 18px;
    background: linear-gradient(90deg, transparent, #fff7df30, transparent); }
.masthead .paper-name { font-size: 22px; letter-spacing: .2em; margin: 0; }
.masthead h1 { font-size: clamp(28px, 3.3vw, 44px); font-weight: 700;
    line-height: 1.5; padding: 10px 5px; letter-spacing: -.03em; }
.masthead .edition { font-size: 15px; }
[data-testid="stMetric"] { border-top: 2px solid #8b785b;
    border-bottom: 1px solid #bba47d; padding: 14px 10px;
    background: linear-gradient(120deg, #fcf5e541, #d1b48214); }
[data-testid="stMetricValue"] { font-size: 32px; font-weight: 700; }
@media (max-width: 640px) {
    .block-container { margin-top: 0; border: 0; box-shadow: none; }
}
</style>
""".replace("__PAPER_TEXTURE__", PAPER_TEXTURE)


def normalize_codes(codes):
    """읍면동 코드의 앞 다섯 자리를 취한 뒤 지정된 개편을 반영한다."""
    codes = codes.astype("string").str.strip()
    if not codes.str.fullmatch(r"\d{5,}").fillna(False).all():
        raise ValueError("행정구역 코드에 결측값 또는 잘못된 문자가 있읍니다.")
    return (
        codes.str[:5].str.replace(r"^42", "51", regex=True)
        .str.replace(r"^45", "52", regex=True).replace({"47720": "27720"})
    )


def aggregate_population(frame):
    """모든 연도를 한 번에 집계하여 화면 조작 때 다시 내려받지 않는다."""
    frame = frame.copy()
    frame.columns = frame.columns.str.strip()
    frame["연도"] = pd.to_numeric(
        frame["연도"].astype("string").str.extract(r"(\d{4})", expand=False),
        errors="raise",
    )
    frame = frame.loc[frame["연도"].between(2015, 2026)].copy()
    if frame.empty:
        raise ValueError("2015~2026년 인구 자료가 없읍니다.")
    frame["연도"] = frame["연도"].astype(int)
    frame["코드"] = normalize_codes(frame["코드"])
    total = [c for c in frame.columns if c.startswith("계_")]
    older, younger = [], []
    for column in total:
        match = re.fullmatch(r"계_(\d+)세(?:\s*이상)?", column)
        if match:
            age = int(match.group(1))
            if 65 <= age <= 100:
                older.append(column)
            if 0 <= age <= 14:
                younger.append(column)
    if not total or len(older) != 36 or len(younger) != 15:
        raise ValueError("집계에 필요한 연령별 인구 항목이 빠져 있읍니다.")
    counts = frame[total].apply(
        lambda c: pd.to_numeric(
            c.astype("string").str.replace(",", "", regex=False), errors="raise"
        )
    )
    if counts.isna().any().any() or (counts < 0).any().any():
        raise ValueError("인구 자료에 결측값 또는 음수가 있읍니다.")
    frame["전체 인구"] = counts.sum(axis=1)
    frame["고령 인구"] = counts[older].sum(axis=1)
    frame["유소년 인구"] = counts[younger].sum(axis=1)
    frame = frame.rename(columns={"시도": "자료 시도", "시군구": "자료 시군구"})
    grouped = frame.groupby(["연도", "코드"], as_index=False).agg({
        "전체 인구": "sum", "고령 인구": "sum", "유소년 인구": "sum",
        "자료 시도": "first", "자료 시군구": "first",
    })
    denominator = grouped["전체 인구"].where(grouped["전체 인구"].gt(0))
    grouped["고령화율"] = grouped["고령 인구"].div(denominator).mul(100)
    grouped["유소년 비율"] = grouped["유소년 인구"].div(denominator).mul(100)
    return grouped


@st.cache_data(ttl=86400, show_spinner=False)
def load_population():
    frame = pd.read_csv(
        POPULATION_URL, compression="zip", encoding="utf-8-sig",
        dtype={"코드": "string"},
        usecols=lambda c: c in {"연도", "시도", "시군구", "코드"} or c.startswith("계_"),
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
        p = feature["properties"]
        p["코드"] = str(p["코드"]).strip()
        if not re.fullmatch(r"\d{5}", p["코드"]):
            raise ValueError("경계 코드는 다섯 자리여야 합니다.")
        rows.append({k: p[k] for k in ["코드", "시군구", "시도"]})
    boundaries = pd.DataFrame(rows).drop_duplicates()
    if boundaries["코드"].duplicated().any():
        raise ValueError("같은 경계 코드에 서로 다른 지역명이 있읍니다.")
    return geojson, boundaries


def interval_labels(cuts):
    return ([f"{cuts[0]}% 미만"]
            + [f"{a}% 이상 {b}% 미만" for a, b in zip(cuts, cuts[1:])]
            + [f"{cuts[-1]}% 이상"])


def make_map(regions, geojson, indicator):
    column, cuts = indicator["column"], indicator["cuts"]
    figure = go.Figure(go.Choropleth(
        geojson=geojson, featureidkey="properties.코드",
        locations=regions["코드"].tolist(), z=[0] * len(regions),
        colorscale=[[0, "#d8d3c8"], [1, "#d8d3c8"]], showscale=False,
        marker_line_color="#897f70", marker_line_width=0.5,
        customdata=regions[["시군구"]].to_numpy(),
        hovertemplate="<b>%{customdata[0]}</b><br>자료 없음<extra></extra>",
    ))
    available = regions.dropna(subset=[column]).copy()
    # 경계값 자체는 윗구간에 속한다. 예: 고령화율 19%는 두 번째 색이다.
    bins = pd.cut(available[column], [0, *cuts, float("inf")], right=False, labels=False)
    scale = []
    for i, color in enumerate(COLORS):
        scale.extend([[i / 5, color], [(i + 1) / 5, color]])
    figure.add_trace(go.Choropleth(
        geojson=geojson, featureidkey="properties.코드",
        locations=available["코드"].tolist(), z=bins.tolist(),
        zmin=-0.5, zmax=4.5, colorscale=scale,
        customdata=available[["시군구", column]].to_numpy(),
        marker_line_color="#897f70", marker_line_width=0.5,
        colorbar={"title": {"text": column}, "tickvals": list(range(5)),
                  "ticktext": interval_labels(cuts), "thickness": 15, "len": 0.65},
        hovertemplate=("<b>%{customdata[0]}</b><br>" + column
                       + ": %{customdata[1]:.2f}%<extra></extra>"),
    ))
    figure.update_geos(
        fitbounds="locations", visible=False, projection_type="mercator", bgcolor="rgba(0,0,0,0)",
    )
    figure.update_layout(
        height=710, margin={"l": 0, "r": 0, "t": 10, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", dragmode="pan",
        font={"family": "Gowun Batang, Batang, serif", "size": 15, "color": INK},
        hoverlabel={"bgcolor": PAPER, "font_color": INK},
    )
    return figure


def main():
    st.set_page_config(page_title="전국 인구 단계구분도 | 인구시보", layout="wide")
    st.markdown(STYLE, unsafe_allow_html=True)
    masthead = st.empty()
    try:
        with st.spinner("전국 인구 및 경계 자료를 집계하고 있읍니다."):
            population = load_population()
            geojson, boundaries = load_boundaries()
    except Exception as error:
        st.error("자료를 불러오지 못하였읍니다. 아래 사유를 확인하여 주십시오.")
        st.caption(str(error))
        st.stop()

    controls = st.columns([2, 2, 2])
    year = controls[0].slider("조사 연도 (매년 6월)", 2015, 2026, 2026, key="year")
    choice = controls[1].selectbox("인구 지표", list(INDICATORS), key="indicator")
    province = controls[2].selectbox("시도별 확대", ["전국", *boundaries["시도"].drop_duplicates()], key="province")
    indicator = INDICATORS[choice]
    column = indicator["column"]
    masthead.markdown(
        f'<div class="masthead"><p class="paper-name">人口時報 (인구시보)</p>'
        f'<h1>전국 {indicator["title"]} 단계구분도</h1>'
        f'<div class="edition">{year}年 六月 基準　│　全國 市郡區 人口特輯</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("읍면동(邑面洞) 인구를 시군구(市郡區)별로 합산하였다. **빛깔이 짙을수록 선택한 인구의 비중이 높다.**")
    selected = population.loc[population["연도"].eq(year)].copy()
    if selected.empty:
        st.warning("선택한 연도의 인구 자료가 없읍니다.")
        st.stop()
    regions = boundaries.merge(selected, on="코드", how="left", validate="one_to_one")
    valid = regions.dropna(subset=[column])
    total = selected["전체 인구"].sum()
    national = selected[indicator["count"]].sum() / total * 100 if total > 0 else None
    cards = st.columns(3)
    cards[0].metric(f"전국 {column}", f"{national:.2f}%" if national is not None else "자료 없음")
    for card, label, ascending in [(cards[1], "전국 최고 시군구", False), (cards[2], "전국 최저 시군구", True)]:
        if valid.empty:
            card.metric(label, "자료 없음")
        else:
            edge = valid[column].min() if ascending else valid[column].max()
            tied = valid.loc[valid[column].eq(edge)]
            card.metric(label, f"{edge:.2f}%")
            card.caption(" / ".join(tied["시도"] + " " + tied["시군구"]))
    st.caption("세 지표는 선택한 연도의 전국 기준이며, 최고와 최저는 경계에 연결된 시군구를 대상으로 하였다.")

    visible = regions if province == "전국" else regions.loc[regions["시도"].eq(province)]
    codes = set(visible["코드"])
    visible_geojson = {"type": "FeatureCollection", "features": [
        f for f in geojson["features"] if f["properties"]["코드"] in codes
    ]}
    st.plotly_chart(make_map(visible, visible_geojson, indicator), width="stretch", theme=None,
                    config={"displayModeBar": False, "scrollZoom": False})
    st.caption(f"【圖面 안내】 {year}년 {province} / {column}. 마우스를 올리면 시군구명과 비율이 나타납니다. 회색은 자료가 없거나 전체 인구가 0인 지역입니다.")
    st.caption("【고정 색 구간】 " + " / ".join(interval_labels(indicator["cuts"])))
    missing = regions.loc[regions[column].isna(), ["시도", "시군구", "코드"]]
    unmatched = selected.loc[~selected["코드"].isin(boundaries["코드"]), ["자료 시도", "자료 시군구", "코드"]]
    if not missing.empty or not unmatched.empty:
        st.warning(f"{year}년 전국 대조 결과, 경계의 {len(missing)}개 지역은 회색으로 표시하였읍니다. "
                   f"인구 자료의 {len(unmatched)}개 코드는 대응 경계가 없어 지도에 표시할 수 없읍니다.")
        with st.expander("대조되지 않은 지역 열람"):
            if not missing.empty:
                st.write("경계는 있으나 비율을 구할 수 없는 지역")
                st.dataframe(missing, hide_index=True)
            if not unmatched.empty:
                st.write("인구는 있으나 대응 경계가 없는 지역")
                st.dataframe(unmatched, hide_index=True)
    with st.expander("선택 지역 집계표(集計表) 열람"):
        table = visible[["시도", "시군구", "코드", "전체 인구", "고령 인구", "유소년 인구", column]]
        st.dataframe(table.sort_values(column, ascending=False).reset_index(drop=True), hide_index=True)
    st.markdown("---")
    st.markdown(f"**【집계 일러두기】** {column} = ({indicator['count']} ÷ 전체 인구) × 100.")
    st.caption("전체 인구는 모든 ‘계_’ 열을 합산하고 남녀 열은 제외하였다. 고령 인구는 65세 이상, 유소년 인구는 0~14세이다. "
               "동 코드의 앞 다섯 자리를 취한 뒤 42는 51로, 45는 52로, 47720은 27720으로 보정하였다. "
               "각 연도의 인구를 제공된 경계에 대조하였으며, 그 밖의 통폐합으로 일치하지 않는 지역은 자료 없음으로 처리하였다. "
               "전국 비율에는 경계와 연결되지 않은 지역의 인구도 포함하였다. 색 구간은 지표마다 정하되 연도에 따라 바꾸지 않았다.")
    st.markdown(f"資料 出處: [인구 원자료]({POPULATION_URL}) / [시군구 경계]({BOUNDARY_URL})")


if __name__ == "__main__":
    main()
