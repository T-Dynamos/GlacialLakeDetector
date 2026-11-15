import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(14, 10), dpi=300)

# Regional bounds for Ladakh, Zanskar, and Karakoram
ax.set_xlim(75.5, 78.8)
ax.set_ylim(32.8, 36.2)
ax.set_aspect('equal')

# Background styling
ax.set_facecolor('#F8F9FA')

sites = [
    {
        "id": "kyagar_shaksgam",
        "name": "1. Kyagar Glacier Lake (Shaksgam)",
        "lat": 35.6774, "lon": 77.1908,
        "rank": "Rank #1 (TOP PICK)",
        "color": "#D90429", "marker": "*", "size": 16,
        "desc": "Ice-dammed surge lake\n>30 historic GLOFs (2018 breach)\nAnnual fill/outburst cycle"
    },
    {
        "id": "rumbak_lake",
        "name": "2. Rumbak Glacial Lake (Hemis)",
        "lat": 33.9997, "lon": 77.4223,
        "rank": "Rank #2 (TOP PICK)",
        "color": "#D90429", "marker": "*", "size": 16,
        "desc": "Moraine-dammed breach lake\n21-22 Aug 2021 GLOF event\nDense S1A/B pre/post coverage"
    },
    {
        "id": "drang_drung_lake",
        "name": "3. Drang-Drung Terminus Lake (Zanskar)",
        "lat": 33.7772, "lon": 76.4094,
        "rank": "Rank #3 (TOP PICK)",
        "color": "#D90429", "marker": "*", "size": 16,
        "desc": "Proglacial lake behind snout\nRapid expansion since 2010\nPadum & Pensi La corridor"
    },
    {
        "id": "gya_lake",
        "name": "4. Gya Glacial Lake (Upper Indus)",
        "lat": 33.6204, "lon": 77.6131,
        "rank": "Rank #4",
        "color": "#2B2D42", "marker": "s", "size": 9,
        "desc": "Moraine breach (Aug 2014)\nHistoric benchmark"
    },
    {
        "id": "parkachik_lake",
        "name": "5. Parkachik Glacier Lake (Suru)",
        "lat": 34.0850, "lon": 75.9650,
        "rank": "Rank #5",
        "color": "#2B2D42", "marker": "^", "size": 9,
        "desc": "Emerging proglacial lake\nWIHG 2023 overdeepenings"
    },
    {
        "id": "phyang_watershed",
        "name": "6. Phyang Watershed (Leh)",
        "lat": 34.2831, "lon": 77.5657,
        "rank": "Rank #6",
        "color": "#8D99AE", "marker": "o", "size": 8,
        "desc": "Cloudburst/debris flow\nDownstream artificial ice stupas"
    },
    {
        "id": "kyagar_tso",
        "name": "7. Kyagar Tso (Rupshu)",
        "lat": 33.1064, "lon": 78.3045,
        "rank": "Rank #7 (UNSUITABLE)",
        "color": "#6C757D", "marker": "X", "size": 10,
        "desc": "Endorheic tectonic lake\nNO glacial/moraine dam (Zero GLOF risk)"
    }
]

# Major regional reference landmarks
landmarks = [
    {"name": "Leh", "lat": 34.1526, "lon": 77.5771},
    {"name": "Kargil", "lat": 34.5539, "lon": 76.1349},
    {"name": "Padum (Zanskar)", "lat": 33.4658, "lon": 76.8833},
    {"name": "Pensi La Pass", "lat": 33.8500, "lon": 76.3500},
    {"name": "Nun-Kun Massif", "lat": 33.9800, "lon": 76.0500},
    {"name": "K2 / Karakoram Crest", "lat": 35.8800, "lon": 76.5100}
]

for lm in landmarks:
    ax.plot(lm['lon'], lm['lat'], 'o', color='#495057', markersize=5)
    ax.annotate(lm['name'], xy=(lm['lon'], lm['lat']), xytext=(lm['lon']+0.05, lm['lat']+0.04),
                fontsize=8.5, fontweight='bold', color='#495057')

# Plot candidate sites
for s in sites:
    ax.plot(s['lon'], s['lat'], s['marker'], color=s['color'], markersize=s['size'], zorder=5)
    
    # Offset annotations to prevent overlap
    offset_x = 0.08
    offset_y = 0.08
    if s['id'] == 'kyagar_shaksgam':
        offset_y = -0.28
    elif s['id'] == 'drang_drung_lake':
        offset_x = -0.75
        offset_y = 0.05
    elif s['id'] == 'parkachik_lake':
        offset_x = -0.75
        offset_y = -0.15
    elif s['id'] == 'kyagar_tso':
        offset_x = -0.75
        offset_y = -0.20
    elif s['id'] == 'rumbak_lake':
        offset_x = 0.08
        offset_y = -0.18

    box_color = '#FFE3E3' if 'TOP PICK' in s['rank'] else ('#F1F3F5' if 'UNSUITABLE' not in s['rank'] else '#E9ECEF')
    border_color = '#D90429' if 'TOP PICK' in s['rank'] else '#6C757D'
    
    ax.annotate(
        f"{s['name']} [{s['rank']}]\n{s['desc']}",
        xy=(s['lon'], s['lat']),
        xytext=(s['lon'] + offset_x, s['lat'] + offset_y),
        arrowprops=dict(facecolor=s['color'], shrink=0.08, width=1.5, headwidth=5),
        fontsize=8.5,
        fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.35', facecolor=box_color, edgecolor=border_color, lw=1.2),
        zorder=10
    )

ax.set_title('GLACIAL FORENSICS: Multi-Site Candidate Evaluation — Ladakh & Karakoram\nRetrospective GLOF Analysis & Multi-Temporal SAR Site Selection', fontsize=13, fontweight='bold', pad=12)
ax.set_xlabel('Longitude (°E)', fontsize=10.5)
ax.set_ylabel('Latitude (°N)', fontsize=10.5)
ax.grid(True, linestyle=':', alpha=0.55)

# Custom legend
p1 = ax.plot([], [], '*', color='#D90429', markersize=14, label='Top 3 Recommended Sites (Kyagar, Rumbak, Drang-Drung)')[0]
p2 = ax.plot([], [], 's', color='#2B2D42', markersize=8, label='Secondary Benchmark Sites (Gya, Parkachik)')[0]
p3 = ax.plot([], [], 'o', color='#8D99AE', markersize=8, label='Debris Flow / Non-Lake Catchment (Phyang)')[0]
p4 = ax.plot([], [], 'X', color='#6C757D', markersize=9, label='Unsuitable Endorheic Tectonic Lake (Kyagar Tso, Rupshu)')[0]
ax.legend(handles=[p1, p2, p3, p4], loc='lower left', fontsize=9.5, framealpha=0.95)

plt.tight_layout()
plt.savefig('GLACIAL_FORENSICS/outputs/maps/ladakh_candidate_sites_overview.png', dpi=300)
print('Saved GLACIAL_FORENSICS/outputs/maps/ladakh_candidate_sites_overview.png successfully.')
