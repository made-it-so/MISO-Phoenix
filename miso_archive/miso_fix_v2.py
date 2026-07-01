import os
import re

# MISO v5.7.2 Directory Mapping
SIDEBAR_PATH = "client/src/components/Sidebar.tsx"
CSS_PATH = "client/src/styles/dashboard.css"
VIEW_PATH = "client/src/pages/ExecutiveLane.tsx"

def repair():
    # FIX 1: Restore Sovereign Button Logic
    if os.path.exists(SIDEBAR_PATH):
        with open(SIDEBAR_PATH, "r") as f:
            content = f.read()
        
        # Injects the button directly into the 'Linked' status block
        if "SovereignResearchButton" not in content:
            pattern = r"\{isLinked && \(.*?\)\}"
            replacement = "{isLinked && <button className='sovereign-research-btn' onClick={handleResearch}>SOVEREIGN RESEARCH</button>}"
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            with open(SIDEBAR_PATH, "w") as f:
                f.write(content)
            print("✅ Sovereign Research Button Restored to Sidebar.")

    # FIX 2: Kill the "Bottom-Start" Scroll & Fix Header
    if os.path.exists(CSS_PATH):
        layout_fix = """
/* MISO REGRESSION FIX */
.executive-lane-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
}
.header-lane {
    position: sticky;
    top: 0;
    z-index: 999;
    background: #ffffff;
    border-bottom: 1px solid #dee2e6;
}
.scrollable-feed {
    overflow-y: auto;
    display: flex;
    flex-direction: column-reverse; /* Keeps new messages at bottom but allows top-down anchor */
    justify-content: flex-end; 
}
"""
        with open(CSS_PATH, "a") as f:
            f.write(layout_fix)
        print("✅ Layout Fixed: Header Stickied & Viewport Locked.")

    # FIX 3: Force scroll to top on component mount
    if os.path.exists(VIEW_PATH):
        with open(VIEW_PATH, "r") as f:
            content = f.read()
        if "window.scrollTo(0, 0)" not in content:
            content = content.replace("useEffect(() => {", "useEffect(() => { window.scrollTo(0, 0);")
            with open(VIEW_PATH, "w") as f:
                f.write(content)
            print("✅ Scroll-to-Top forced for Executive Lane.")

    print("\n🚀 REPAIR COMPLETE. Refresh your browser.")

if __name__ == "__main__":
    repair()
