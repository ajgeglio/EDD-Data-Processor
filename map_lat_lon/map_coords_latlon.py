import math
import json
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import sys


# -----------------------------
# Argparse / configurable parameters
# -----------------------------
def parse_args():
    p = argparse.ArgumentParser(description="Create map and GeoJSON from CSV of well coordinates")
    p.add_argument("--csv", help="Path to CSV file with columns WellName, LONG, LAT",
                   default=r"C:\\Users\\ageglio\\OneDrive - TRC\\Documents\\Mosaic Hutchinson\\RE_ Well Redundancy Analysis\\mosaic hutchinson data\\MosaicWellCoordinates_all_sampled.csv")
    p.add_argument("--xlim", nargs=2, type=float, metavar=("XMIN", "XMAX"),
                   default=[-97.90, -97.85], help="Longitude extent (min max)")
    p.add_argument("--ylim", nargs=2, type=float, metavar=("YMIN", "YMAX"),
                   default=[38.02, 38.055], help="Latitude extent (min max)")
    p.add_argument("--pad-lon", type=float, default=0.00025, help="Longitude padding (degrees)")
    p.add_argument("--pad-lat", type=float, default=0.00025, help="Latitude padding (degrees)")
    p.add_argument("--lat0", type=float, default=None, help="Reference latitude for scale bar (degrees). If omitted, uses ylim center")
    p.add_argument("--scale-m", type=float, default=1000, help="Scale bar length in meters")
    p.add_argument("--figsize", nargs=2, type=float, default=[18, 10], help="Figure size in inches (width height)")
    p.add_argument("--basemap", choices=["none", "contextily"], default="none",
                   help="Optional basemap backend to use for background tiles")
    return p.parse_args()

args = parse_args()

# -----------------------------
# 1) Input data (edit as needed)
# -----------------------------
df = pd.read_csv(args.csv)
df = df[["WellName", "LONG", "LAT"]].rename(columns={"WellName": "Boring ID", "LONG": "Longitude", "LAT": "Latitude"})
df = df[~df["Boring ID"].str.contains("(-.*S)|(-.*A)", case=False, na=False, regex=True)].reset_index(drop=True)
# ---------------------------------------
# 3) Create GeoJSON (WGS84 / EPSG:4326)
# ---------------------------------------
features = []
for _, r in df.iterrows():
    features.append({
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [r["Longitude"], r["Latitude"]]},
        "properties": {"id": r["Boring ID"]}
    })

geojson = {
    "type": "FeatureCollection",
    "name": "boring_locations",
    "features": features,
    "crs": {"type": "name", "properties": {"name": "EPSG:4326"}}
}

geojson_path = "boring_locations.geojson"
with open(geojson_path, "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)

# -----------------------------
# 4) Make a quick static map
# -----------------------------
fig, ax = plt.subplots(figsize=tuple(args.figsize))

# Category symbology
cats = {
    "MW": {"mask": df["Boring ID"].str.startswith("MW"), "color": "#1f77b4", "marker": "o", "label": "MW"},
    "CMW": {"mask": df["Boring ID"].str.startswith("CMW"), "color": "#ff7f0e", "marker": "s", "label": "CMW"},
    "SWP": {"mask": df["Boring ID"].str.startswith("SWP"), "color": "#2ca02c", "marker": "^", "label": "SWP"},
}
other_mask = ~(cats["MW"]["mask"] | cats["CMW"]["mask"] | cats["SWP"]["mask"])

# Optional basemap support
# if user requests contextily, build a GeoDataFrame, reproject to 3857, plot and add tiles
if args.basemap == "contextily":
    try:
        import geopandas as gpd
        import contextily as ctx
    except Exception as e:
        print("contextily/geopandas not available; install with: pip install geopandas contextily")
        print("Falling back to no-basemap plotting.")
    else:
        # construct GeoDataFrame in lon/lat and convert to web mercator
        gdf = gpd.GeoDataFrame(df.copy(), geometry=gpd.points_from_xy(df["Longitude"], df["Latitude"]), crs="EPSG:4326")
        gdf_3857 = gdf.to_crs(epsg=3857)

        # compute padding in meters
        lat0_local = args.lat0 if args.lat0 is not None else ((args.ylim[0] + args.ylim[1]) / 2.0)
        meters_per_deg_lon = 111320 * math.cos(math.radians(lat0_local))
        pad_lon_m = args.pad_lon * meters_per_deg_lon
        pad_lat_m = args.pad_lat * 111320

        # compute bounds from GeoDataFrame and validate
        minx, miny, maxx, maxy = gdf_3857.total_bounds
        
        # validate bounds and use fallback if invalid (NaN or Inf)
        import numpy as np
        if np.any(np.isnan([minx, miny, maxx, maxy])) or np.any(np.isinf([minx, miny, maxx, maxy])):
            # fallback: compute bounds from args.xlim and args.ylim (convert to Web Mercator)
            from pyproj import Transformer
            transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
            minx_ll, miny_ll = args.xlim[0], args.ylim[0]
            maxx_ll, maxy_ll = args.xlim[1], args.ylim[1]
            minx, miny = transformer.transform(minx_ll, miny_ll)
            maxx, maxy = transformer.transform(maxx_ll, maxy_ll)
        
        minx -= pad_lon_m
        maxx += pad_lon_m
        miny -= pad_lat_m
        maxy += pad_lat_m

        fig, ax = plt.subplots(figsize=tuple(args.figsize))

        # plot categories from reprojected gdf
        for key, spec in cats.items():
            mask = spec["mask"]
            d = gdf_3857[mask]
            ax.scatter(d.geometry.x, d.geometry.y,
                       s=36, c=spec["color"], marker=spec["marker"],
                       label=f"{spec['label']} (n={len(d)})", zorder=3)

        other = gdf_3857[other_mask]
        if not other.empty:
            ax.scatter(other.geometry.x, other.geometry.y, s=36, c="#7f7f7f", marker="D",
                       label=f"Other (n={len(other)})", zorder=3)

        # labels (use reprojected coords)
        for _, r in gdf_3857.iterrows():
            ax.annotate(r["Boring ID"], (r.geometry.x, r.geometry.y),
                        xytext=(3, 3), textcoords="offset points",
                        fontsize=8, color="#222", zorder=4)

        # add basemap tiles; try resolving several provider names safely (handles xyzservices differences)
        def resolve_provider(name):
            # name may be nested like 'Stamen.Terrain'
            parts = name.split(".")
            cur = ctx.providers
            for part in parts:
                try:
                    cur = getattr(cur, part)
                except Exception:
                    try:
                        cur = cur[part]
                    except Exception:
                        return None
            return cur

        tried = []
        candidates = ["Stamen.Terrain", "Stamen.TonerLite", "OpenStreetMap.Mapnik", "OpenStreetMap", "OSM"]
        provider_used = False
        for name in candidates:
            prov = resolve_provider(name)
            if prov is None:
                continue
            tried.append(name)
            try:
                ctx.add_basemap(ax, source=prov, zoom=12)
                provider_used = True
                break
            except Exception:
                continue

        if not provider_used:
            # final fallback: try with explicit zoom to avoid invalid auto-calculated zoom levels
            try:
                prov = resolve_provider("OpenStreetMap.Mapnik")
                if prov is None:
                    prov = resolve_provider("OpenStreetMap")
                if prov is not None:
                    ctx.add_basemap(ax, source=prov, zoom=12)
                else:
                    # proceed without basemap if provider resolution fails
                    pass
            except Exception:
                # silently skip basemap if it fails; plot will proceed without background tiles
                pass

        ax.set_xlim(minx, maxx)
        ax.set_ylim(miny, maxy)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.set_xlabel("Longitude (m, Web Mercator)")
        ax.set_ylabel("Latitude (m, Web Mercator)")
        ax.set_title("Boring Locations (with basemap)")
        ax.legend(loc="upper left", frameon=True)

        # north arrow and scale are omitted for mercator plot (scale bar would need meters coords)
        out_png = "boring_locations_map.png"
        fig.tight_layout()
        fig.savefig(out_png, dpi=180)
        plt.close(fig)
        print("Wrote files:")
        print(f" - {geojson_path}")
        print(f" - {out_png}")
        sys.exit(0)

# Plot categorized points
for key, spec in cats.items():
    d = df[spec["mask"]]
    ax.scatter(
        d["Latitude"], d["Longitude"], 
        s=36, c=spec["color"], marker=spec["marker"],
        label=f"{spec['label']} (n={len(d)})", zorder=3
    )

# Plot others (numeric IDs)
other = df[other_mask]
if not other.empty:
    ax.scatter(other["Latitude"], other["Longitude"], s=36, c="#7f7f7f", marker="D",
               label=f"Other (n={len(other)})", zorder=3)

# Labels
for _, r in df.iterrows():
    ax.annotate(r["Boring ID"], (r["Latitude"], r["Longitude"]),
                xytext=(3, 3), textcoords="offset points",
                fontsize=8, color="#222", zorder=4)

# Extent & axes
pad_lon = args.pad_lon
pad_lat = args.pad_lat
# ax.set_xlim(df["Longitude"].min() - pad_lon, df["Longitude"].max() + pad_lon)
# ax.set_ylim(df["Latitude"].min() - pad_lat,  df["Latitude"].max() + pad_lat)
ylim = tuple(args.ylim)
xlim = tuple(args.xlim)
ax.set_ylim(ylim[0] - pad_lon, ylim[1] + pad_lon)
ax.set_xlim(xlim[0] - pad_lat, xlim[1] + pad_lat)
ax.set_aspect("equal", adjustable="box")
ax.grid(True, linestyle="--", alpha=0.3)
ax.set_xlabel("Longitude (°)")
ax.set_ylabel("Latitude (°)")
ax.set_title("Hypothetical Boring Locations (NAD83 / EPSG:4269)")
ax.legend(loc="upper left", frameon=True)

# North arrow (simple)
x0, x1 = ax.get_xlim()
y0, y1 = ax.get_ylim()
arr_x = x0 + 0.12 * (x1 - x0)
arr_y = y0 + 0.12 * (y1 - y0)
ax.annotate("N",
            xy=(arr_x, arr_y + 0.0012), xycoords="data",
            xytext=(arr_x, arr_y - 0.0012), textcoords="data",
            arrowprops=dict(arrowstyle="-|>", color="black"),
            ha="center", va="center", fontsize=15, fontweight="bold", zorder=5)

# Approximate scale bar (longitude direction)
lat0 = args.lat0 if args.lat0 is not None else ((ylim[0] + ylim[1]) / 2.0)
meters_per_deg_lon = 111_320 * math.cos(math.radians(lat0))  # rough but fine for small extents
scale_m = args.scale_m
scale_deg_lon = scale_m / meters_per_deg_lon if meters_per_deg_lon else 0
sb_x0 = x0 + 0.05 * (x1 - x0)
sb_y  = y0 + 0.05 * (y1 - y0)
ax.plot([sb_x0, sb_x0 + scale_deg_lon], [sb_y, sb_y], color="k", lw=2)
ax.text(sb_x0 + scale_deg_lon / 2, sb_y + 0.00004, f"{scale_m} m (approx)",
        ha="center", va="bottom", fontsize=8)

# Save figure
out_png = "boring_locations_map.png"
fig.tight_layout()
fig.savefig(out_png, dpi=180)
plt.close(fig)

print("Wrote files:")
print(f" - {geojson_path}")
print(f" - {out_png}")