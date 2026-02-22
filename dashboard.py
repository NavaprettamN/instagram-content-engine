# dashboard.py

import streamlit as st
import sqlite3
import json
import os
from datetime import datetime, timedelta
from PIL import Image

# Page config
st.set_page_config(
    page_title="Instagram Content Engine",
    page_icon="📸",
    layout="wide"
)

# Database connection
def get_db():
    conn = sqlite3.connect("content_engine.db")
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS content_ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT,
            hook TEXT,
            outline TEXT,
            caption_draft TEXT,
            hashtags TEXT,
            status TEXT DEFAULT 'pending_review',
            created_at TEXT,
            engagement_estimate TEXT,
            generated_content TEXT,
            image_paths TEXT,
            published_at TEXT,
            post_id TEXT,
            notes TEXT
        );
        
        CREATE TABLE IF NOT EXISTS analytics_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            followers INTEGER,
            reach INTEGER,
            impressions INTEGER,
            profile_views INTEGER,
            engagement_rate REAL,
            analysis TEXT
        );
        
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    conn.commit()
    conn.close()

init_db()

# ==================== SIDEBAR ====================
st.sidebar.title("📸 Content Engine")
page = st.sidebar.radio("Navigate", [
    "🏠 Dashboard",
    "📋 Content Queue", 
    "✅ Approval Center",
    "📊 Analytics",
    "🔧 Settings",
    "🚀 Run Agents"
])

# ==================== DASHBOARD PAGE ====================
if page == "🏠 Dashboard":
    st.title("Instagram Content Engine — Dashboard")
    
    conn = get_db()
    
    # Key metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    pending = conn.execute(
        "SELECT COUNT(*) FROM content_ideas WHERE status='pending_review'"
    ).fetchone()[0]
    approved = conn.execute(
        "SELECT COUNT(*) FROM content_ideas WHERE status='approved'"
    ).fetchone()[0]
    ready = conn.execute(
        "SELECT COUNT(*) FROM content_ideas WHERE status='designed'"
    ).fetchone()[0]
    published = conn.execute(
        "SELECT COUNT(*) FROM content_ideas WHERE status='published'"
    ).fetchone()[0]
    total = conn.execute(
        "SELECT COUNT(*) FROM content_ideas"
    ).fetchone()[0]
    
    col1.metric("⏳ Pending Review", pending)
    col2.metric("✅ Approved", approved)
    col3.metric("🎨 Ready to Post", ready)
    col4.metric("📤 Published", published)
    col5.metric("📦 Total Ideas", total)
    
    st.divider()
    
    # Content pipeline visualization
    st.subheader("Content Pipeline")
    
    pipeline_data = conn.execute("""
        SELECT status, COUNT(*) as count 
        FROM content_ideas 
        GROUP BY status
    """).fetchall()
    
    if pipeline_data:
        import pandas as pd
        df = pd.DataFrame(pipeline_data, columns=["Status", "Count"])
        st.bar_chart(df.set_index("Status"))
    
    # Recent activity
    st.subheader("Recent Content")
    recent = conn.execute("""
        SELECT id, content_type, hook, status, created_at, engagement_estimate
        FROM content_ideas 
        ORDER BY created_at DESC 
        LIMIT 10
    """).fetchall()
    
    for item in recent:
        status_emoji = {
            "pending_review": "⏳",
            "approved": "✅",
            "rejected": "❌",
            "designed": "🎨",
            "scheduled": "📅",
            "published": "📤"
        }.get(item["status"], "❓")
        
        with st.expander(
            f"{status_emoji} [{item['content_type'].upper()}] {item['hook']}"
        ):
            st.write(f"**Status:** {item['status']}")
            st.write(f"**Created:** {item['created_at']}")
            st.write(f"**Est. Engagement:** {item['engagement_estimate']}")
    
    conn.close()

# ==================== APPROVAL CENTER ====================
elif page == "✅ Approval Center":
    st.title("Content Approval Queue")
    st.write("Review AI-generated content. Approve, edit, or reject.")
    
    conn = get_db()
    pending_items = conn.execute("""
        SELECT * FROM content_ideas 
        WHERE status IN ('pending_review', 'approved')
        ORDER BY 
            CASE status 
                WHEN 'pending_review' THEN 1 
                WHEN 'approved' THEN 2 
            END,
            created_at DESC
    """).fetchall()
    
    if not pending_items:
        st.info("🎉 No content pending review. Run the Research Agent to generate new ideas.")
    
    for item in pending_items:
        st.divider()
        
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader(f"{'⏳' if item['status'] == 'pending_review' else '✅'} {item['hook']}")
            st.caption(f"Type: {item['content_type']} | Created: {item['created_at']}")
            
            # Show caption
            st.write("**Caption Draft:**")
            edited_caption = st.text_area(
                "Edit caption",
                value=item["caption_draft"],
                key=f"caption_{item['id']}",
                height=200
            )
            
            # Show outline
            if item["outline"]:
                st.write("**Content Outline:**")
                outline = json.loads(item["outline"]) if isinstance(item["outline"], str) else item["outline"]
                for point in outline:
                    st.write(f"  • {point}")
            
            # Show hashtags
            if item["hashtags"]:
                st.write("**Hashtags:**")
                hashtags = json.loads(item["hashtags"]) if isinstance(item["hashtags"], str) else item["hashtags"]
                st.write(" ".join(hashtags))
            
            # Show generated images if they exist
            if item["image_paths"]:
                st.write("**Generated Slides:**")
                paths = json.loads(item["image_paths"])
                img_cols = st.columns(min(len(paths), 4))
                for idx, path in enumerate(paths):
                    if os.path.exists(path):
                        with img_cols[idx % 4]:
                            st.image(path, width=250)
        
        with col_right:
            st.write("**Actions:**")
            
            notes = st.text_input("Notes", key=f"notes_{item['id']}")
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                if st.button("✅ Approve", key=f"approve_{item['id']}"):
                    conn.execute("""
                        UPDATE content_ideas 
                        SET status='approved', caption_draft=?, notes=?
                        WHERE id=?
                    """, (edited_caption, notes, item["id"]))
                    conn.commit()
                    st.success("Approved!")
                    st.rerun()
            
            with col_b:
                if st.button("🎨 Generate", key=f"generate_{item['id']}"):
                    # Trigger content + design agents
                    st.info("Generating content... (runs in background)")
                    # In practice, this calls content_agent + design_agent
                    
            with col_c:
                if st.button("❌ Reject", key=f"reject_{item['id']}"):
                    conn.execute("""
                        UPDATE content_ideas 
                        SET status='rejected', notes=?
                        WHERE id=?
                    """, (notes, item["id"]))
                    conn.commit()
                    st.warning("Rejected")
                    st.rerun()
    
    conn.close()

# ==================== ANALYTICS PAGE ====================
elif page == "📊 Analytics":
    st.title("Performance Analytics")
    
    conn = get_db()
    
    # Published content performance
    published = conn.execute("""
        SELECT * FROM content_ideas 
        WHERE status='published' 
        ORDER BY published_at DESC
    """).fetchall()
    
    st.metric("Total Published", len(published))
    
    # Content type breakdown
    type_counts = conn.execute("""
        SELECT content_type, COUNT(*) as count 
        FROM content_ideas 
        WHERE status='published'
        GROUP BY content_type
    """).fetchall()
    
    if type_counts:
        import pandas as pd
        df = pd.DataFrame(type_counts, columns=["Type", "Count"])
        st.bar_chart(df.set_index("Type"))
    
    # Show AI analysis if available
    latest_analysis = conn.execute("""
        SELECT analysis, date FROM analytics_snapshots 
        ORDER BY date DESC LIMIT 1
    """).fetchone()
    
    if latest_analysis:
        st.subheader("Latest AI Analysis")
        st.write(f"*Generated: {latest_analysis['date']}*")
        st.markdown(latest_analysis["analysis"])
    
    conn.close()

# ==================== RUN AGENTS PAGE ====================
elif page == "🚀 Run Agents":
    st.title("Agent Control Panel")
    st.write("Manually trigger agents or set up scheduled runs.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔍 Research Agent")
        st.write("Scans trends, generates 5 new content ideas")
        if st.button("Run Research Agent", type="primary"):
            with st.spinner("Research Agent running..."):
                # Import and run the agent
                from research_agent import ResearchAgent
                config = load_config()  # Load from config.yaml
                agent = ResearchAgent(config)
                ideas = agent.run()
                st.success(f"Generated {len(ideas)} new content ideas!")
                st.rerun()
    
    with col2:
        st.subheader("🎨 Content + Design Agent")
        st.write("Generates full content and designs for approved ideas")
        if st.button("Run Content Agent", type="primary"):
            with st.spinner("Generating content and designs..."):
                from content_agent import ContentAgent
                from design_agent import DesignAgent
                config = load_config()
                
                conn = get_db()
                approved = conn.execute("""
                    SELECT * FROM content_ideas 
                    WHERE status='approved' AND generated_content IS NULL
                """).fetchall()
                
                content_agent = ContentAgent(config)
                design_agent = DesignAgent(config)
                
                for item in approved:
                    idea = dict(item)
                    
                    # Generate content
                    content = content_agent.generate_content(idea)
                    
                    # Generate designs
                    if idea["content_type"] == "carousel":
                        image_paths = design_agent.generate_carousel_images(
                            content, idea["id"]
                        )
                    else:
                        image_paths = []
                    
                    # Update database
                    conn.execute("""
                        UPDATE content_ideas 
                        SET generated_content=?, image_paths=?, status='designed'
                        WHERE id=?
                    """, (
                        json.dumps(content), 
                        json.dumps(image_paths),
                        idea["id"]
                    ))
                
                conn.commit()
                conn.close()
                st.success(f"Generated content for {len(approved)} ideas!")
                st.rerun()
    
    st.divider()
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("📤 Publishing Agent")
        st.write("Publishes designed content to Instagram")
        if st.button("Publish Next Post", type="primary"):
            with st.spinner("Publishing to Instagram..."):
                from publishing_agent import PublishingAgent
                config = load_config()
                
                conn = get_db()
                next_post = conn.execute("""
                    SELECT * FROM content_ideas 
                    WHERE status='designed'
                    ORDER BY created_at ASC
                    LIMIT 1
                """).fetchone()
                
                if next_post:
                    agent = PublishingAgent(config)
                    post = dict(next_post)
                    
                    if post["content_type"] == "carousel":
                        paths = json.loads(post["image_paths"])
                        result = agent.publish_carousel(
                            paths, post["caption_draft"]
                        )
                    else:
                        paths = json.loads(post["image_paths"])
                        result = agent.publish_single_image(
                            paths[0], post["caption_draft"]
                        )
                    
                    conn.execute("""
                        UPDATE content_ideas 
                        SET status='published', 
                            published_at=?,
                            post_id=?
                        WHERE id=?
                    """, (datetime.now().isoformat(), 
                          result.get("id"), post["id"]))
                    conn.commit()
                    st.success(f"Published: {post['hook']}")
                else:
                    st.warning("No designed content ready to publish")
                
                conn.close()
    
    with col4:
        st.subheader("📊 Analytics Agent")
        st.write("Pulls metrics and generates AI analysis")
        if st.button("Run Analytics", type="primary"):
            with st.spinner("Analyzing performance..."):
                from analytics_agent import AnalyticsAgent
                config = load_config()
                agent = AnalyticsAgent(config)
                
                insights = agent.get_account_insights()
                posts = agent.get_recent_posts()
                analysis = agent.generate_weekly_analysis(insights, posts)
                
                conn = get_db()
                conn.execute("""
                    INSERT INTO analytics_snapshots 
                    (date, analysis) VALUES (?, ?)
                """, (datetime.now().isoformat(), analysis))
                conn.commit()
                conn.close()
                
                st.success("Analysis complete!")
                st.markdown(analysis)

# ==================== SETTINGS PAGE ====================
elif page == "🔧 Settings":
    st.title("Configuration")
    
    st.subheader("Niche & Brand")
    niche = st.text_input("Niche", value="AI Productivity Tools")
    brand_voice = st.text_area(
        "Brand Voice Description",
        value="Conversational, slightly witty, data-driven. "
              "Uses short sentences. Avoids corporate speak. "
              "Speaks like a knowledgeable friend, not a professor."
    )
    
    st.subheader("Content Sources")
    rss_feeds = st.text_area(
        "RSS Feeds (one per line)",
        value="https://techcrunch.com/feed/\nhttps://feeds.feedburner.com/TheHackersNews"
    )
    subreddits = st.text_input(
        "Subreddits (comma-separated)",
        value="artificial, productivity, SideProject"
    )
    
    st.subheader("API Keys")
    azure_key = st.text_input("Azure OpenAI API Key", type="password")
    azure_endpoint = st.text_input("Azure OpenAI Endpoint")
    meta_token = st.text_input("Meta Graph API Token", type="password")
    ig_user_id = st.text_input("Instagram User ID")
    
    st.subheader("Brand Colors")
    col1, col2, col3 = st.columns(3)
    bg_color = col1.color_picker("Background", "#1a1a2e")
    accent_color = col2.color_picker("Accent", "#e94560")
    text_color = col3.color_picker("Text", "#ffffff")
    
    if st.button("Save Configuration", type="primary"):
        config = {
            "niche": niche,
            "brand_voice": brand_voice,
            "rss_feeds": rss_feeds.strip().split("\n"),
            "subreddits": [s.strip() for s in subreddits.split(",")],
            "azure_api_key": azure_key,
            "azure_endpoint": azure_endpoint,
            "meta_access_token": meta_token,
            "instagram_user_id": ig_user_id,
            "brand_colors": {
                "background": bg_color,
                "accent": accent_color,
                "text_primary": text_color
            }
        }
        import yaml
        with open("config.yaml", "w") as f:
            yaml.dump(config, f)
        st.success("Configuration saved!")