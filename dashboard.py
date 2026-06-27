import streamlit as st
import json
import os
import yaml
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

from agents._db import (
    get_ideas, get_idea, count_ideas, save_idea, update_idea,
    get_analytics, save_analytics, get_config,
)

st.set_page_config(page_title="Instagram Content Engine", page_icon="📸", layout="wide")

def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)

# ==================== SIDEBAR ====================
st.sidebar.title("📸 Content Engine")
page = st.sidebar.radio("Navigate", [
    "🏠 Dashboard",
    "📋 Content Queue",
    "✅ Approval Center",
    "📊 Analytics",
    "🔧 Settings",
    "🚀 Run Agents",
])

# ==================== DASHBOARD ====================
if page == "🏠 Dashboard":
    st.title("Instagram Content Engine — Dashboard")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("⏳ Pending Review", count_ideas("pending_review"))
    col2.metric("✅ Approved",        count_ideas("approved"))
    col3.metric("🎨 Ready to Post",   count_ideas("designed"))
    col4.metric("📤 Published",        count_ideas("published"))
    col5.metric("📦 Total Ideas",      len(get_ideas()))

    st.divider()
    st.subheader("Content Pipeline")
    all_ideas = get_ideas()
    if all_ideas:
        import pandas as pd
        from collections import Counter
        counts = Counter(i["status"] for i in all_ideas)
        df = pd.DataFrame(counts.items(), columns=["Status", "Count"])
        st.bar_chart(df.set_index("Status"))

    st.subheader("Recent Content")
    for item in get_ideas()[:10]:
        emoji = {"pending_review": "⏳", "approved": "✅", "rejected": "❌",
                 "designed": "🎨", "published": "📤"}.get(item["status"], "❓")
        with st.expander(f"{emoji} [{item['content_type'].upper()}] {item['hook']}"):
            st.write(f"**Status:** {item['status']}")
            st.write(f"**Created:** {item['created_at']}")
            st.write(f"**Est. Engagement:** {item['engagement_estimate']}")

# ==================== CONTENT QUEUE ====================
elif page == "📋 Content Queue":
    st.title("Content Queue")
    status_filter = st.selectbox("Filter by status", ["all", "pending_review", "approved", "designed", "published", "rejected"])
    ideas = get_ideas(status=None if status_filter == "all" else status_filter)
    st.write(f"{len(ideas)} items")
    for item in ideas:
        emoji = {"pending_review": "⏳", "approved": "✅", "rejected": "❌",
                 "designed": "🎨", "published": "📤"}.get(item["status"], "❓")
        with st.expander(f"{emoji} {item['hook']}"):
            st.json({k: v for k, v in item.items() if v is not None})

# ==================== APPROVAL CENTER ====================
elif page == "✅ Approval Center":
    st.title("Content Approval Queue")
    st.write("Review AI-generated content. Approve, edit, or reject.")

    pending_items = get_ideas(status=["pending_review", "approved"])

    if not pending_items:
        st.info("No content pending review. Run the Research Agent to generate new ideas.")

    for item in pending_items:
        st.divider()
        col_left, col_right = st.columns([2, 1])

        with col_left:
            status_emoji = "⏳" if item["status"] == "pending_review" else "✅"
            st.subheader(f"{status_emoji} {item['hook']}")
            st.caption(f"Type: {item['content_type']} | Created: {item['created_at']}")

            edited_caption = st.text_area(
                "Caption Draft (editable)", value=item["caption_draft"] or "",
                key=f"caption_{item['id']}", height=200,
            )

            if item.get("outline"):
                st.write("**Content Outline:**")
                outline = json.loads(item["outline"]) if isinstance(item["outline"], str) else item["outline"]
                for point in outline:
                    st.write(f"  • {point}")

            if item.get("hashtags"):
                st.write("**Hashtags:**")
                tags = json.loads(item["hashtags"]) if isinstance(item["hashtags"], str) else item["hashtags"]
                st.write(" ".join(tags))

            if item.get("image_paths"):
                st.write("**Generated Slides:**")
                paths = json.loads(item["image_paths"]) if isinstance(item["image_paths"], str) else item["image_paths"]
                img_cols = st.columns(min(len(paths), 4))
                for idx, path in enumerate(paths):
                    if path.startswith("http") or os.path.exists(path):  # imgbb URL or local file
                        with img_cols[idx % 4]:
                            st.image(path, width=250)

        with col_right:
            st.write("**Actions:**")
            notes = st.text_input("Notes", key=f"notes_{item['id']}")

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("✅ Approve", key=f"approve_{item['id']}"):
                    update_idea(item["id"], status="approved", caption_draft=edited_caption, notes=notes)
                    st.success("Approved!")
                    st.rerun()
            with col_b:
                if st.button("🎨 Generate", key=f"generate_{item['id']}"):
                    with st.spinner("Generating..."):
                        config = load_config()
                        from agents.content_agent import ContentAgent
                        from agents.design_agent import DesignAgent
                        content = ContentAgent(config).generate_content(item)
                        if item["content_type"] == "carousel":
                            paths = DesignAgent(config).generate_carousel_images(content, item["id"])
                        else:
                            # For reels/static_image: generate a single cover slide from the hook
                            cover_content = {
                                "slide_1_hook": item["hook"],
                                "slide_1_subtext": "Tap to learn more",
                                "slides": [],
                                "slide_final_cta": "Follow for more AI productivity tips",
                            }
                            paths = DesignAgent(config).generate_carousel_images(cover_content, item["id"])
                        update_idea(item["id"],
                                    generated_content=json.dumps(content),
                                    image_paths=json.dumps(paths),
                                    status="designed")
                        st.success("Content generated!")
                        st.rerun()
            with col_c:
                if st.button("❌ Reject", key=f"reject_{item['id']}"):
                    update_idea(item["id"], status="rejected", notes=notes)
                    st.warning("Rejected")
                    st.rerun()

# ==================== ANALYTICS ====================
elif page == "📊 Analytics":
    st.title("📊 Performance Analytics")
    import pandas as pd

    @st.cache_data(ttl=600)
    def load_perf():
        from agents.analytics_agent import AnalyticsAgent
        a = AnalyticsAgent(load_config())
        return a.account_summary(), a.post_performance(limit=30)

    if st.button("🔄 Refresh metrics"):
        st.cache_data.clear()
    try:
        summary, perf = load_perf()
    except Exception as e:
        st.error(f"Couldn't load Instagram metrics: {e}")
        summary, perf = {}, []

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Followers", summary.get("followers_count", "–"))
    c2.metric("📦 Posts", summary.get("media_count", len(perf)))
    c3.metric("👁 Total Reach", sum(p["reach"] for p in perf))
    avg_eng = round(sum(p["eng_rate"] for p in perf) / len(perf), 1) if perf else 0
    c4.metric("💞 Avg Eng. Rate", f"{avg_eng}%")

    # Follower growth trend (from weekly analytics snapshots)
    hist = json.loads(get_config("follower_history") or "[]")
    if len(hist) > 1:
        st.subheader("Follower Growth")
        st.line_chart(pd.DataFrame(hist).set_index("date")["count"])

    if perf:
        best = max(perf, key=lambda p: p["score"])
        worst = min(perf, key=lambda p: p["score"])
        col_b, col_w = st.columns(2)
        col_b.success(f"🏆 **Best post** (score {best['score']})\n\n{best['caption']}\n\n"
                      f"{best['saved']} saves · {best['shares']} shares · {best['reach']} reach")
        col_w.warning(f"📉 **Weakest post** (score {worst['score']})\n\n{worst['caption']}\n\n"
                      f"reach {worst['reach']} · {worst['eng_rate']}% eng.")

        st.subheader("Per-Post Performance")
        st.caption("Score weights reach signals: saves & shares ×3, comments ×2, likes ×1.")
        df = pd.DataFrame(perf)[["caption", "type", "reach", "likes", "comments",
                                 "saved", "shares", "eng_rate", "score"]]
        df = df.sort_values("score", ascending=False).reset_index(drop=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No post metrics yet — publish a few posts and check back.")

    st.divider()
    snaps = get_analytics(limit=1)
    if snaps:
        st.subheader("🤖 Latest AI Analysis")
        st.caption(f"Generated: {snaps[0]['date']}")
        st.markdown(snaps[0]["analysis"])
    if st.button("Run AI analysis now"):
        with st.spinner("Analyzing (pulls metrics + Gemini)..."):
            from agents.analytics_agent import AnalyticsAgent
            AnalyticsAgent(load_config()).run()
            st.cache_data.clear()
            st.success("Analysis updated!")
            st.rerun()

# ==================== RUN AGENTS ====================
elif page == "🚀 Run Agents":
    st.title("Agent Control Panel")
    config = load_config()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔍 Research Agent")
        st.write("Scans trends, generates 5 new content ideas.")
        if st.button("Run Research Agent", type="primary"):
            with st.spinner("Running..."):
                from agents.research_agent import ResearchAgent
                ResearchAgent(config).run()
                st.success("New ideas added to the review queue!")
                st.rerun()

    with col2:
        st.subheader("🎨 Content + Design Agent")
        st.write("Generates full content and slides for approved ideas.")
        if st.button("Run Content Agent", type="primary"):
            with st.spinner("Generating..."):
                from agents.content_agent import ContentAgent
                from agents.design_agent import DesignAgent
                approved = get_ideas(status="approved")
                ca = ContentAgent(config)
                da = DesignAgent(config)
                count = 0
                for idea in approved:
                    if not idea.get("generated_content"):
                        content = ca.generate_content(idea)
                        paths = da.generate_carousel_images(content, idea["id"]) if idea["content_type"] == "carousel" else []
                        update_idea(idea["id"],
                                    generated_content=json.dumps(content),
                                    image_paths=json.dumps(paths),
                                    status="designed")
                        count += 1
                st.success(f"Generated content for {count} ideas!")
                st.rerun()

    st.divider()
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("📤 Publishing Agent")
        st.write("Publishes next designed post to Instagram.")
        if st.button("Publish Next Post", type="primary"):
            with st.spinner("Publishing..."):
                from agents.publishing_agent import PublishingAgent
                designed = get_ideas(status="designed")
                if not designed:
                    st.warning("No designed content ready to publish.")
                else:
                    post = designed[-1]  # oldest first
                    agent = PublishingAgent(config)
                    raw_paths = post.get("image_paths") or "[]"
                    paths = json.loads(raw_paths) if isinstance(raw_paths, str) else (raw_paths or [])

                    if not paths:
                        st.error(
                            f"Post '{post['hook']}' has no images. "
                            f"Go to Approval Center and click Generate to create slides."
                        )
                    else:
                        from agents.hashtag_agent import compose_caption
                        caption = compose_caption(post, count_ideas("published"))
                        if len(paths) > 1:
                            result = agent.publish_carousel(paths, caption)
                        else:
                            result = agent.publish_single_image(paths[0], caption)

                        if "error" in result:
                            st.error(f"Instagram API error: {result['error'].get('message', result)}")
                        else:
                            update_idea(post["id"],
                                        status="published",
                                        published_at=datetime.utcnow().isoformat(),
                                        post_id=result.get("id"))
                            st.success(f"Published: {post['hook']}")

    with col4:
        st.subheader("📊 Analytics Agent")
        st.write("Pulls metrics and generates AI analysis.")
        if st.button("Run Analytics", type="primary"):
            with st.spinner("Analyzing..."):
                from agents.analytics_agent import AnalyticsAgent
                agent = AnalyticsAgent(config)
                insights = agent.get_account_insights()
                posts = agent.get_recent_posts()
                analysis = agent.generate_weekly_analysis(insights, posts)
                save_analytics({"date": datetime.utcnow().date().isoformat(), "analysis": analysis})
                st.success("Analysis complete!")
                st.markdown(analysis)

# ==================== SETTINGS ====================
elif page == "🔧 Settings":
    st.title("Configuration")
    config = load_config()

    st.subheader("Niche & Brand")
    niche = st.text_input("Niche", value=config.get("niche", ""))
    brand_voice = st.text_area("Brand Voice", value=config.get("brand_voice", ""), height=120)

    st.subheader("Content Sources")
    rss_feeds = st.text_area("RSS Feeds (one per line)", value="\n".join(config.get("rss_feeds", [])))
    subreddits = st.text_input("Subreddits (comma-separated)", value=", ".join(config.get("subreddits", [])))

    st.subheader("Brand Colors")
    colors = config.get("brand_colors", {})
    col1, col2, col3 = st.columns(3)
    bg_color     = col1.color_picker("Background", colors.get("background", "#1a1a2e"))
    accent_color = col2.color_picker("Accent",     colors.get("accent",     "#e94560"))
    text_color   = col3.color_picker("Text",       colors.get("text_primary", "#ffffff"))

    if st.button("Save Configuration", type="primary"):
        config.update({
            "niche": niche,
            "brand_voice": brand_voice,
            "rss_feeds": [f.strip() for f in rss_feeds.strip().splitlines() if f.strip()],
            "subreddits": [s.strip() for s in subreddits.split(",") if s.strip()],
            "brand_colors": {
                "background": bg_color,
                "accent": accent_color,
                "text_primary": text_color,
                "secondary_bg": colors.get("secondary_bg", "#16213e"),
                "text_secondary": colors.get("text_secondary", "#a0a0a0"),
            },
        })
        with open("config.yaml", "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        st.success("Configuration saved!")
