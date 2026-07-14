"""
RoadGuard - Simple Deployment Diagram
Output: deployment_diagram_final.png
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.set_facecolor('white')
fig.patch.set_facecolor('white')
ax.axis('off')

# ── Draw a 3D-style node (cuboid) ──────────────────────────────────────────────
def draw_node(ax, x, y, w, h, label, stereotype='device', fc='#F0F4FF', bc='#2255AA'):
    depth = 0.35
    # Right face
    rx = [x+w, x+w+depth, x+w+depth, x+w, x+w]
    ry = [y+h, y+h+depth, y+depth, y, y+h]
    ax.fill(rx, ry, color='#CCCCCC', zorder=1)
    ax.plot(rx, ry, color=bc, lw=1.5, zorder=2)
    # Top face
    tx = [x, x+depth, x+w+depth, x+w, x]
    ty = [y+h, y+h+depth, y+h+depth, y+h, y+h]
    ax.fill(tx, ty, color='#DDDDDD', zorder=1)
    ax.plot(tx, ty, color=bc, lw=1.5, zorder=2)
    # Front face
    front = mpatches.FancyBboxPatch((x, y), w, h,
        boxstyle="square,pad=0", linewidth=2,
        edgecolor=bc, facecolor=fc, zorder=2)
    ax.add_patch(front)
    # Stereotype + label
    ax.text(x + w/2, y + h - 0.18, f'<<{stereotype}>>', fontsize=8,
        ha='center', va='top', color='#555555', style='italic', zorder=5)
    ax.text(x + w/2, y + h - 0.50, label, fontsize=11, fontweight='bold',
        ha='center', va='top', color='#111111', zorder=5)
    # Divider
    ax.plot([x+0.2, x+w-0.2], [y+h-0.85, y+h-0.85],
        color=bc, lw=1, linestyle='--', zorder=3)

# ── Draw inner env box ─────────────────────────────────────────────────────────
def draw_env(ax, x, y, w, h, label, fc='#FFFFFF', bc='#666666'):
    rect = mpatches.FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.08", linewidth=1.5,
        edgecolor=bc, facecolor=fc, linestyle='--', zorder=3)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h - 0.18, label, fontsize=9, fontweight='bold',
        ha='center', va='top', color='#333333', zorder=5)

# ── Draw artifact ──────────────────────────────────────────────────────────────
def draw_artifact(ax, x, y, w, h, name):
    body = mpatches.FancyBboxPatch((x, y), w, h,
        boxstyle="square,pad=0", linewidth=1,
        edgecolor='#888888', facecolor='#FAFAFA', zorder=4)
    ax.add_patch(body)
    # dog-ear
    fold = 0.18
    ax.fill([x+w-fold, x+w, x+w, x+w-fold, x+w-fold],
            [y+h, y+h, y+h-fold, y+h-fold, y+h],
            color='#DDDDDD', zorder=5)
    ax.text(x + w/2, y + h/2, name, fontsize=7.5, ha='center',
        va='center', color='#333333', style='italic', zorder=6)

# ── Draw connection line ───────────────────────────────────────────────────────
def draw_link(ax, x1, y, x2, label='', sublabel=''):
    ax.plot([x1, x2], [y, y], color='#333333', lw=2, zorder=6)
    ax.plot(x1, y, 'o', color='#333333', ms=5, zorder=7)
    ax.plot(x2, y, 'o', color='#333333', ms=5, zorder=7)
    if label:
        ax.text((x1+x2)/2, y+0.22, label, fontsize=9, fontweight='bold',
            ha='center', va='bottom', color='#222222',
            bbox=dict(facecolor='white', edgecolor='none', pad=2))
    if sublabel:
        ax.text((x1+x2)/2, y-0.22, sublabel, fontsize=8,
            ha='center', va='top', color='#666666', style='italic')

# ════════════════════════════════════════════════════════════════════════════════
# TITLE
ax.text(7, 7.80, 'RoadGuard  -  Deployment Diagram',
    fontsize=15, fontweight='bold', ha='center', va='top', color='#111111')

# ════════════════════════════════════════════════════════════════════════════════
# NODE 1 — Mobile Device (left)
draw_node(ax, 0.3, 0.8, 3.8, 6.4, 'Mobile Device\n(Android / iOS)',
    stereotype='device', fc='#EEF4FF', bc='#3366CC')

draw_env(ax, 0.55, 1.2, 3.2, 5.4, 'Expo React Native Runtime',
    fc='#F8FBFF', bc='#3366CC')

ax.text(2.15, 5.9, 'RoadGuard App', fontsize=10, fontweight='bold',
    ha='center', va='top', color='#1144AA', zorder=6)

# App components list
app_items = ['TripScreen', 'MapScreen', 'AuthNavigator',
             'AdminDashboard', 'MaintenanceDashboard', 'AuthContext (JWT)']
for i, item in enumerate(app_items):
    ax.text(2.15, 5.4 - i*0.55, '+ ' + item, fontsize=8.5,
        ha='center', va='top', color='#333333', zorder=6)

# ════════════════════════════════════════════════════════════════════════════════
# NODE 2 — Developer PC (right, contains Flask + PostgreSQL)
draw_node(ax, 5.2, 0.8, 8.1, 6.4, "Developer's PC  (Windows - Local Network)",
    stereotype='device', fc='#F0FFF0', bc='#228B22')

# Flask sub-environment
draw_env(ax, 5.5, 1.2, 3.8, 5.4, 'Flask Server  :8000',
    fc='#FAFFF8', bc='#228B22')

flask_items = ['FlaskApp', 'AuthBlueprint  /api/auth/*',
               'PotholesBlueprint  /api/potholes/*',
               'YOLODetector', 'RCNNDetector', 'ProcessingEngine']
for i, item in enumerate(flask_items):
    ax.text(7.4, 5.85 - i*0.55, item, fontsize=8.5,
        ha='center', va='top', color='#333333', zorder=6)

# Flask artifacts
draw_artifact(ax, 5.7, 1.28, 1.55, 0.52, 'best.pt')
draw_artifact(ax, 7.45, 1.28, 1.65, 0.52, 'rcnn_best.pth')

# PostgreSQL sub-environment
draw_env(ax, 9.55, 1.2, 3.5, 5.4, 'PostgreSQL  :5432',
    fc='#FFF8F8', bc='#AA0000')

pg_items = ['pothole_db', '', 'Table: users',
            'Table: potholes', '', 'SQLAlchemy ORM']
for i, item in enumerate(pg_items):
    ax.text(11.3, 5.85 - i*0.62, item,
        fontsize=8.5 if item != 'pothole_db' else 10,
        fontweight='bold' if item == 'pothole_db' else 'normal',
        ha='center', va='top', color='#333333', zorder=6)

# uploads folder artifact
draw_artifact(ax, 5.75, 1.85, 3.3, 0.52, 'uploads/  (image files)')

# ════════════════════════════════════════════════════════════════════════════════
# COMMUNICATION LINKS

# Mobile <-> Flask
draw_link(ax, 4.1, 5.2, 5.5, 'HTTP REST API + JWT', 'Port 8000 over Wi-Fi')
draw_link(ax, 4.1, 3.8, 5.5, 'GET /api/potholes/', 'JSON response')

# Flask <-> PostgreSQL (internal)
draw_link(ax, 9.3, 5.0, 9.55, 'SQLAlchemy ORM', 'TCP Port 5432')
draw_link(ax, 9.3, 3.5, 9.55, 'SELECT / INSERT', 'UPDATE / DELETE')

# ════════════════════════════════════════════════════════════════════════════════
# NOTE BOX (bottom)
note = mpatches.FancyBboxPatch((0.3, 0.05), 13.3, 0.62,
    boxstyle="round,pad=0.05", lw=1, edgecolor='#AAAAAA',
    facecolor='#FFFFF0', zorder=2)
ax.add_patch(note)
ax.text(7, 0.37,
    'Note: All server components run on the developer\'s local machine. '
    'Mobile device connects via the same Wi-Fi LAN. Server IP is set in src/config.js',
    fontsize=8, ha='center', va='center', color='#555555', style='italic', zorder=5)

plt.tight_layout(pad=0.3)
plt.savefig('deployment_diagram_final.png', dpi=160,
    bbox_inches='tight', facecolor='white')
print("Saved: deployment_diagram_final.png")
