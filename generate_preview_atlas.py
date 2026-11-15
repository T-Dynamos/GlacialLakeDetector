import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 8 Sites Grid Preview
fig, axs = plt.subplots(2, 4, figsize=(20, 10), dpi=300)

sites_preview = [
    {
        "name": "1. South Lhonak (Sikkim)",
        "id": "Primary Benchmark (4 Oct 2023 GLOF)",
        "bbox": [88.16, 27.89, 88.24, 27.94],
        "center": [88.195, 27.915],
        "type": "Moraine-Dammed Lake (~168 ha pre-GLOF)",
        "elev": "5,200 m",
        "downstream": "Teesta River -> Chungthang Dam",
        "color": "#D90429"
    },
    {
        "name": "2. Kyagar Glacier Lake (Shaksgam)",
        "id": "Rank #1 Ladakh/Karakoram Pick",
        "bbox": [77.165, 35.660, 77.215, 35.700],
        "center": [77.1908, 35.6774],
        "type": "Ice-Dammed Surge Lake (0-3.25 ha)",
        "elev": "4,880 m",
        "downstream": "Shaksgam River -> Yarkant Basin",
        "color": "#D90429"
    },
    {
        "name": "3. Rumbak Glacial Lake (Hemis)",
        "id": "Rank #2 Ladakh Pick (21 Aug 2021 GLOF)",
        "bbox": [77.400, 33.980, 77.445, 34.020],
        "center": [77.4223, 33.9997],
        "type": "Moraine-Dammed Lake (~3.0 ha)",
        "elev": "5,268 m",
        "downstream": "Rumbak Nala -> Zingchen -> Indus",
        "color": "#D90429"
    },
    {
        "name": "4. Drang-Drung Terminus (Zanskar)",
        "id": "Rank #3 Ladakh Pick (Proglacial)",
        "bbox": [76.380, 33.755, 76.435, 33.800],
        "center": [76.4094, 33.7772],
        "type": "Proglacial Calving Lake (8.5 -> 12.3 ha)",
        "elev": "4,170 m",
        "downstream": "Doda River -> Padum -> Zanskar",
        "color": "#D90429"
    },
    {
        "name": "5. Gya Glacial Lake (Upper Indus)",
        "id": "Rank #4 (Aug 2014 GLOF Benchmark)",
        "bbox": [77.595, 33.605, 77.635, 33.635],
        "center": [77.6131, 33.6204],
        "type": "Moraine-Dammed Breach Lake (4.5 ha)",
        "elev": "5,411 m",
        "downstream": "Gya Nala -> Miru -> NH-3 Highway",
        "color": "#2B2D42"
    },
    {
        "name": "6. Parkachik Snout (Suru Valley)",
        "id": "Rank #5 (Overdeepening Formation)",
        "bbox": [75.940, 34.065, 75.990, 34.105],
        "center": [75.9650, 34.0850],
        "type": "Proglacial Pond (~1.6 ha -> ~50 ha potential)",
        "elev": "4,200 m",
        "downstream": "Suru River -> Panikhar -> Kargil",
        "color": "#2B2D42"
    },
    {
        "name": "7. Phyang Cirque (Leh Range)",
        "id": "Rank #6 (Debris Flow Catchment)",
        "bbox": [77.545, 34.265, 77.585, 34.305],
        "center": [77.5657, 34.2831],
        "type": "Cirque Melt Ponds (<0.8 ha) [No Lake Dam]",
        "elev": "5,350 m",
        "downstream": "Phyang Tokpo -> Artificial Ice Stupas",
        "color": "#8D99AE"
    },
    {
        "name": "8. Kyagar Tso (Rupshu Plateau)",
        "id": "Rank #7 (DISQUALIFIED: Tectonic)",
        "bbox": [78.280, 33.085, 78.335, 33.130],
        "center": [78.3045, 33.1064],
        "type": "Endorheic Saline Lake (~140 ha) [Zero GLOF]",
        "elev": "4,684 m",
        "downstream": "Closed Endorheic Basin (No Outflow)",
        "color": "#6C757D"
    }
]

for idx, (ax, s) in enumerate(zip(axs.flat, sites_preview)):
    b = s['bbox']
    pad_lon = (b[2] - b[0]) * 0.35
    pad_lat = (b[3] - b[1]) * 0.35
    
    ax.set_xlim(b[0] - pad_lon, b[2] + pad_lon)
    ax.set_ylim(b[1] - pad_lat, b[3] + pad_lat)
    ax.set_aspect('equal')
    ax.set_facecolor('#F8F9FA')
    
    # Draw Search Bounding Box
    rect = patches.Rectangle(
        (b[0], b[1]), b[2] - b[0], b[3] - b[1],
        linewidth=2.0, edgecolor=s['color'], facecolor=s['color'], alpha=0.18, linestyle='--'
    )
    ax.add_patch(rect)
    
    # Mark Lake / Snout Center
    ax.plot(s['center'][0], s['center'][1], 'o', color=s['color'], markersize=8, markeredgecolor='black', zorder=5)
    
    # Annotate details
    ax.set_title(s['name'], fontsize=11, fontweight='bold', color='navy', pad=6)
    ax.annotate(
        f"{s['id']}\nType: {s['type']}\nElev: {s['elev']}\nDrainage: {s['downstream']}",
        xy=(s['center'][0], s['center'][1]),
        xytext=(0.04, 0.06),
        textcoords="axes fraction",
        fontsize=8.5,
        fontweight='medium',
        bbox=dict(boxstyle="round,pad=0.35", facecolor='white', edgecolor=s['color'], alpha=0.92, lw=1.2)
    )
    ax.set_xlabel("Longitude (°E)", fontsize=8)
    ax.set_ylabel("Latitude (°N)", fontsize=8)
    ax.ticklabel_format(useOffset=False, style='plain')
    ax.grid(True, linestyle=':', alpha=0.55)

plt.suptitle("GLACIAL FORENSICS: Multi-Site Candidate Investigation Atlas (Sikkim & Ladakh/Karakoram)", fontsize=14, fontweight='bold')
plt.tight_layout()
preview_map = "GLACIAL_FORENSICS/outputs/maps/candidate_lakes_preview_atlas.png"
plt.savefig(preview_map, dpi=300)
plt.close()
print(f"Saved preview atlas -> {preview_map}")
