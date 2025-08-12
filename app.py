import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

st.set_page_config(page_title="Dealflow AI – Prototype", page_icon="📈", layout="wide")

st.title("Dealflow AI – Prototype")
st.caption("AI-assisted deal origination: ingest → score → enrich CRM → dashboard")

# Load data
DATA_PATH = Path("data/sample_leads.csv")
if not DATA_PATH.exists():
    st.error("Missing data file: data/sample_leads.csv")
    st.stop()

df = pd.read_csv(DATA_PATH)

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    min_score = st.slider("Minimum Lead Score", 0, 100, 70)
    stages = st.multiselect("Stages", sorted(df["stage"].unique().tolist()), default=sorted(df["stage"].unique().tolist()))
    sig_options = sorted({s for row in df["top_signals"].dropna().tolist() for s in row.split("; ")})
    sel_signals = st.multiselect("Must include signals", sig_options, default=[])
    st.markdown("---")
    st.download_button("⬇️ Download current data (CSV)", df.to_csv(index=False).encode("utf-8"), "sample_leads.csv", "text/csv")

# Filter logic
mask = (df["lead_score"] >= min_score) & (df["stage"].isin(stages))
if sel_signals:
    mask &= df["top_signals"].apply(lambda x: any(sig in str(x).split("; ") for sig in sel_signals))

fdf = df[mask].copy().sort_values(["lead_score","propensity_pct"], ascending=[False, False])

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Leads (after filters)", len(fdf))
c2.metric("Avg Lead Score", f"{fdf['lead_score'].mean():.1f}" if len(fdf) else "—")
c3.metric("Avg Propensity %", f"{fdf['propensity_pct'].mean():.1f}" if len(fdf) else "—")
c4.metric("Stages", ", ".join(sorted(fdf['stage'].unique())) if len(fdf) else "—")

# Charts
col1, col2 = st.columns(2)
with col1:
    st.subheader("Pipeline by Stage")
    st.altair_chart(
        alt.Chart(fdf).mark_bar().encode(
            x=alt.X("stage:N", sort="-y", title="Stage"),
            y=alt.Y("count():Q", title="Leads"),
            tooltip=[alt.Tooltip("stage:N"), alt.Tooltip("count():Q", title="Leads")]
        ).properties(height=300),
        use_container_width=True
    )

with col2:
    st.subheader("Top Signals Frequency")
    # explode signals
    sigs = []
    for row in fdf["top_signals"].dropna():
        for s in str(row).split("; "):
            sigs.append(s)
    if sigs:
        sig_df = pd.DataFrame({"signal": sigs})
        st.altair_chart(
            alt.Chart(sig_df).mark_bar().encode(
                x=alt.X("signal:N", sort="-y", title="Signal"),
                y=alt.Y("count():Q", title="Occurrences"),
                tooltip=[alt.Tooltip("signal:N"), alt.Tooltip("count():Q", title="Occurrences")]
            ).properties(height=300),
            use_container_width=True
        )
    else:
        st.info("No signals found for current filter.")

st.subheader("Lead Table")
st.dataframe(
    fdf[["company","lead_score","propensity_pct","stage","top_signals","last_news_date","next_best_action"]]
    .reset_index(drop=True),
    use_container_width=True,
    hide_index=True
)

with st.expander("Architecture Diagram"):
    st.image("images/dealflow_architecture.png")

with st.expander("Dashboard Mock (static)"):
    st.image("images/mock_dashboard.png")

st.markdown("---")
st.caption("Prototype for discussion. Next steps: connect live sources, add LLM signal extraction, and sync to CRM.")
