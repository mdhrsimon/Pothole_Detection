"""
RoadGuard — Simplified Component Diagram (5 main components)
Run: python generate_component_simple.py
Output: component_diagram_simple.png
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(16, 8))
ax.set_xlim(0, 16)
ax.set_ylim(0, 8)
ax.axis('off')
fig.patch.set_facecolor('white')

# ── Helpers ────────────────────────────────────────────────────────────────────
def comp_box(ax, x, y, w, h, title, subtitle='', color='white', border='#222'):
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.08",
                          linewidth=1.8, edgecolor=border,
                          facecolor=color, zorder=2)
    ax.add_patch(rect)
    # UML component icon — top right corner
    ix, iy = x + w - 0.32, y + h - 0.32
    ax.add_patch(mpatches.Rectangle((ix, iy), 0.26, 0.14,
                 lw=1, edgecolor='#555', facecolor='white', zorder=4))
    ax.add_patch(mpatches.Rectangle((ix-0.09, iy+0.04), 0.10, 0.06,
                 lw=0.8, edgecolor='#555', facecolor='white', zorder=5))
    ax.add_patch(mpatches.Rectangle((ix-0.09, iy-0.05), 0.10, 0.06,
                 lw=0.8, edgecolor='#555', facecolor='white', zorder=5))
    # divider line
    ax.plot([x+0.15, x+w-0.15], [y+h-0.62, y+h-0.62],
            color='#AAAAAA', lw=0.8, zorder=3)
    ax.text(x + w/2 - 0.15, y + h - 0.28,
            title, fontsize=11, fontweight='bold',
            ha='center', va='center', color='#111', zorder=5)
    if subtitle:
        for i, line in enumerate(subtitle.split('\n')):
            ax.text(x + w/2 - 0.1, y + h - 0.82 - i*0.38,
                    line, fontsize=8.5, ha='center', va='center',
                    color='#444', style='italic', zorder=5)

def h_arrow(ax, x1, y, x2, label='', color='#333'):
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='->', color=color,
                                linestyle='dashed', lw=1.4))
    if label:
        ax.text((x1+x2)/2, y+0.14, label, fontsize=8,
                ha='center', va='bottom', color='#333',
                bbox=dict(facecolor='white', edgecolor='none', pad=1))

def v_arrow(ax, x, y1, y2, label='', color='#333'):
    ax.annotate('', xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle='->', color=color,
                                linestyle='dashed', lw=1.4))
    if label:
        ax.text(x+0.12, (y1+y2)/2, label, fontsize=8,
                ha='left', va='center', color='#333',
                bbox=dict(facecolor='white', edgecolor='none', pad=1))

# ── Title ──────────────────────────────────────────────────────────────────────
ax.text(8, 7.72, 'RoadGuard — Component Diagram',
        fontsize=15, fontweight='bold', ha='center', va='top')

# ── 5 Main Component Boxes ─────────────────────────────────────────────────────

# 1. Mobile App  (far left)
comp_box(ax, 0.3, 3.8, 2.8, 3.3,
         'Mobile App',
         'TripScreen\nMapScreen\nAuthNavigator\nAdminDashboard',
         color='#EEF4FF', border='#3366CC')

# 2. Flask Backend  (center)
comp_box(ax, 4.0, 3.8, 3.2, 3.3,
         'Flask Backend',
         'AuthBlueprint\nPotholesBlueprint\nJWT Auth\nFile Upload',
         color='#EFFFEF', border='#228B22')

# 3. AI Detection Engine  (center-right)
comp_box(ax, 8.0, 3.8, 3.2, 3.3,
         'AI Detection Engine',
         'YOLODetector (best.pt)\nRCNNDetector\nProcessingEngine\nSeverity + Haversine',
         color='#FFF8EE', border='#CC6600')

# 4. Database  (right)
comp_box(ax, 12.4, 5.0, 3.1, 2.1,
         'PostgreSQL DB',
         'users table\npotholes table',
         color='#FFF0F0', border='#AA0000')

# 5. File Storage  (right, below DB)
comp_box(ax, 12.4, 2.5, 3.1, 2.1,
         'File Storage',
         'uploads/\nph_yolo_*.jpg\nph_fix_*.jpg',
         color='#F5F0FF', border='#6633CC')

# ── Arrows ─────────────────────────────────────────────────────────────────────

# Mobile → Flask
h_arrow(ax, 3.1, 5.8, 4.0, 'HTTP REST / JWT')
h_arrow(ax, 3.1, 4.8, 4.0, 'POST /detect\nGET /potholes')

# Flask → AI Detection Engine
h_arrow(ax, 7.2, 5.8, 8.0, 'run_inference(frame)')
h_arrow(ax, 7.2, 4.8, 8.0, 'process_severity()\nfind_duplicate()')

# Flask → Database
h_arrow(ax, 7.2, 6.1, 12.4, 'SQLAlchemy ORM')

# Flask → File Storage
h_arrow(ax, 7.2, 4.3, 12.4, 'cv2.imwrite()')

# ── Legend ─────────────────────────────────────────────────────────────────────
ax.plot([0.3, 1.0], [0.55, 0.55], color='#333', linestyle='dashed', lw=1.3)
ax.annotate('', xy=(1.0, 0.55), xytext=(0.3, 0.55),
            arrowprops=dict(arrowstyle='->', color='#333', lw=1.3, linestyle='dashed'))
ax.text(1.15, 0.55, 'Dependency / Uses', fontsize=8.5, va='center', color='#333')

ax.add_patch(FancyBboxPatch((4.5, 0.3), 1.5, 0.5, boxstyle="round,pad=0.05",
             lw=1.5, edgecolor='#333', facecolor='white', zorder=2))
ax.text(5.25, 0.55, '«component»', fontsize=8, ha='center', va='center',
        color='#333', style='italic')
ax.text(7.2, 0.55, '= UML Component Box', fontsize=8.5, va='center', color='#333')

plt.tight_layout(pad=0.3)
plt.savefig('component_diagram_simple.png', dpi=150,
            bbox_inches='tight', facecolor='white')
print("Saved: component_diagram_simple.png")
plt.show()
