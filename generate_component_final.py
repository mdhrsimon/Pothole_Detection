"""
RoadGuard — Simple Component Diagram
Output: component_diagram_final.png
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(14, 7))
ax.set_xlim(0, 14)
ax.set_ylim(0, 7)
ax.set_facecolor('white')
fig.patch.set_facecolor('white')
ax.axis('off')

# ── Draw a clean component box ─────────────────────────────────────────────────
def draw_component(ax, x, y, w, h, title, lines=[], color='#DDEEFF', border='#2255AA'):
    # Main box
    rect = mpatches.FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.1", linewidth=2,
        edgecolor=border, facecolor=color, zorder=2)
    ax.add_patch(rect)

    # UML component icon (top-right corner)
    ix, iy = x + w - 0.45, y + h - 0.42
    ax.add_patch(mpatches.Rectangle((ix, iy), 0.32, 0.18,
        linewidth=1.2, edgecolor=border, facecolor='white', zorder=4))
    ax.add_patch(mpatches.Rectangle((ix - 0.12, iy + 0.04), 0.14, 0.08,
        linewidth=1, edgecolor=border, facecolor='white', zorder=5))
    ax.add_patch(mpatches.Rectangle((ix - 0.12, iy - 0.06), 0.14, 0.08,
        linewidth=1, edgecolor=border, facecolor='white', zorder=5))

    # Title
    ax.text(x + w / 2 - 0.2, y + h - 0.35, title,
        fontsize=12, fontweight='bold', ha='center', va='top',
        color='#111111', zorder=6)

    # Divider line
    ax.plot([x + 0.18, x + w - 0.18], [y + h - 0.6, y + h - 0.6],
        color=border, linewidth=1, zorder=3)

    # Sub-lines
    for i, line in enumerate(lines):
        ax.text(x + w / 2 - 0.1, y + h - 0.95 - i * 0.42, line,
            fontsize=9, ha='center', va='top',
            color='#333333', style='italic', zorder=6)

# ── Draw a labeled arrow ───────────────────────────────────────────────────────
def draw_arrow(ax, x1, y1, x2, y2, label=''):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle='->', color='#333333',
                        lw=1.8, linestyle='dashed',
                        connectionstyle='arc3,rad=0.0'))
    if label:
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        ax.text(mx, my + 0.18, label, fontsize=8.5, ha='center',
            color='#444444',
            bbox=dict(facecolor='white', edgecolor='none', pad=2))

# ════════════════════════════════════════════════════════════════════
# TITLE
ax.text(7, 6.75, 'RoadGuard  —  Component Diagram',
    fontsize=15, fontweight='bold', ha='center', va='top', color='#111')

# ════════════════════════════════════════════════════════════════════
# 5 COMPONENT BOXES

# 1. Mobile App  (left)
draw_component(ax, 0.3, 1.5, 2.6, 4.2,
    'Mobile App',
    ['TripScreen', 'MapScreen', 'AuthNavigator', 'AdminDashboard'],
    color='#EEF4FF', border='#3366CC')

# 2. Flask Backend  (centre-left)
draw_component(ax, 3.6, 1.5, 2.8, 4.2,
    'Flask Backend',
    ['AuthBlueprint', 'PotholesBlueprint', 'JWT Auth', 'File Upload'],
    color='#EFFFEF', border='#228B22')

# 3. AI Detection Engine  (centre-right)
draw_component(ax, 7.1, 1.5, 2.8, 4.2,
    'Detection Engine',
    ['YOLODetector', 'RCNNDetector', 'ProcessingEngine', 'Haversine + Severity'],
    color='#FFF8EE', border='#CC6600')

# 4. PostgreSQL DB  (right-top)
draw_component(ax, 10.7, 3.3, 2.8, 2.4,
    'PostgreSQL DB',
    ['users  table', 'potholes  table'],
    color='#FFF0F0', border='#AA0000')

# 5. File Storage  (right-bottom)
draw_component(ax, 10.7, 0.5, 2.8, 2.4,
    'File Storage',
    ['uploads/', 'ph_yolo_*.jpg', 'ph_fix_*.jpg'],
    color='#F4F0FF', border='#6633CC')

# ════════════════════════════════════════════════════════════════════
# ARROWS

# Mobile → Flask
draw_arrow(ax, 2.9, 4.2, 3.6, 4.2, 'HTTP REST + JWT')
draw_arrow(ax, 2.9, 3.0, 3.6, 3.0, 'POST /detect\nGET /potholes')

# Flask → Detection Engine
draw_arrow(ax, 6.4, 4.2, 7.1, 4.2, 'run_inference()')
draw_arrow(ax, 6.4, 3.0, 7.1, 3.0, 'process_severity()')

# Flask → PostgreSQL
draw_arrow(ax, 9.9, 4.5, 10.7, 4.5, 'SQLAlchemy ORM')

# Flask → File Storage
draw_arrow(ax, 9.9, 2.2, 10.7, 2.2, 'cv2.imwrite()')

# ════════════════════════════════════════════════════════════════════
# LEGEND
ax.plot([0.3, 0.9], [0.22, 0.22], color='#333', linestyle='dashed', lw=1.5)
ax.annotate('', xy=(0.9, 0.22), xytext=(0.3, 0.22),
    arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))
ax.text(1.0, 0.22, '= uses / depends on', fontsize=8.5, va='center', color='#444')

ax.add_patch(mpatches.FancyBboxPatch((5.0, 0.08), 1.5, 0.35,
    boxstyle="round,pad=0.05", lw=1.5, edgecolor='#555', facecolor='white'))
ax.text(5.75, 0.25, '«component»', fontsize=8, ha='center', va='center',
    style='italic', color='#333')
ax.text(6.7, 0.25, '= component box', fontsize=8.5, va='center', color='#444')

# ════════════════════════════════════════════════════════════════════
plt.tight_layout(pad=0.4)
plt.savefig('component_diagram_final.png', dpi=160,
    bbox_inches='tight', facecolor='white')
print("Saved: component_diagram_final.png")
plt.show()
