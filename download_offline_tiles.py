"""
Offline Map Tile Downloader for LoRa PLB Gateway
Downloads OpenStreetMap tiles for offline dashboard usage.
Saves tiles in: app/static/maps/{z}/{x}/{y}.png
"""
import math
import os
import sys
import time
import urllib.request
import argparse

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "app", "static", "maps")
USER_AGENT = "LoRa-PLB-Gateway/1.0 (Emergency Response; offline-map-cache)"

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def download_tile(z, x, y, output_dir):
    tile_dir = os.path.join(output_dir, str(z), str(x))
    os.makedirs(tile_dir, exist_ok=True)
    tile_path = os.path.join(tile_dir, f"{y}.png")

    if os.path.exists(tile_path) and os.path.getsize(tile_path) > 0:
        return True  # Already cached

    url = f"https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read()
            with open(tile_path, "wb") as f:
                f.write(content)
        return True
    except Exception as e:
        print(f"Failed {z}/{x}/{y}: {e}", file=sys.stderr)
        return False

def download_region(min_lat, max_lat, min_lon, max_lon, min_zoom, max_zoom, output_dir):
    total_tiles = 0
    tile_tasks = []

    for z in range(min_zoom, max_zoom + 1):
        x_min, y_max = deg2num(min_lat, min_lon, z)
        x_max, y_min = deg2num(max_lat, max_lon, z)
        
        # Ensure order
        x_start, x_end = min(x_min, x_max), max(x_min, x_max)
        y_start, y_end = min(y_min, y_max), max(y_min, y_max)

        for x in range(x_start, x_end + 1):
            for y in range(y_start, y_end + 1):
                tile_tasks.append((z, x, y))

    print(f"Total tiles to download: {len(tile_tasks)} (Zoom levels: {min_zoom} to {max_zoom})")
    print(f"Destination: {output_dir}")
    
    success = 0
    for idx, (z, x, y) in enumerate(tile_tasks):
        if download_tile(z, x, y, output_dir):
            success += 1
        # Throttle slightly to respect OSM usage policy (max 2 requests/sec)
        time.sleep(0.08)
        if (idx + 1) % 25 == 0 or (idx + 1) == len(tile_tasks):
            print(f"Progress: {idx + 1}/{len(tile_tasks)} tiles processed...")

    print(f"\nDone! Successfully saved {success}/{len(tile_tasks)} tiles into: {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Download offline map tiles for LoRa PLB Gateway")
    parser.add_argument("--lat", type=float, default=21.1458, help="Center latitude (default: 21.1458)")
    parser.add_argument("--lon", type=float, default=79.0882, help="Center longitude (default: 79.0882)")
    parser.add_argument("--radius", type=float, default=0.15, help="Bounding box half-width in degrees (~15km, default: 0.15)")
    parser.add_argument("--min-zoom", type=int, default=11, help="Minimum zoom level (default: 11)")
    parser.add_argument("--max-zoom", type=int, default=15, help="Maximum zoom level (default: 15)")
    parser.add_argument("--include-world", action="store_true", default=True, help="Download country overview tiles zoom 3-6")

    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.include_world:
        print("Downloading base overview tiles (Zoom 3-6) for India...")
        # India bounds approx: Lat 8 to 36, Lon 68 to 97
        download_region(8.0, 36.0, 68.0, 97.0, 3, 6, OUTPUT_DIR)

    print(f"\nDownloading local high-res tiles around ({args.lat}, {args.lon}) ± {args.radius}°...")
    download_region(
        args.lat - args.radius,
        args.lat + args.radius,
        args.lon - args.radius,
        args.lon + args.radius,
        args.min_zoom,
        args.max_zoom,
        OUTPUT_DIR
    )

if __name__ == "__main__":
    main()
