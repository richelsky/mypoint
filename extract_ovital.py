# -*- coding: utf-8 -*-
"""
解析奥维导出的 KML，把 gx:Track 里的骑行轨迹提出来

142 万个轨迹点，原样塞进网页打不开，按 100 米间隔抽稀。
点位和 Placemark 名称全部保留。
"""

import json
import os
import sys
import time
import xml.etree.ElementTree as ET

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SRC = r"D:\一些杂项\20261116奥维.kml"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ge_ovital.json")

K = "{http://www.opengis.net/kml/2.2}"
GX = "{http://www.google.com/kml/ext/2.2}"
MIN_DIST = 0.0          # 不抽稀，一个点都不丢


def thin(pts, min_dist=MIN_DIST):
    if min_dist <= 0 or len(pts) <= 2:
        return pts
    out = [pts[0]]
    for p in pts[1:-1]:
        if abs(p[0] - out[-1][0]) + abs(p[1] - out[-1][1]) >= min_dist:
            out.append(p)
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return out


def main():
    t0 = time.time()
    items = []
    folders = []
    cur = None          # 当前 Placemark
    depth_folder = []

    for ev, el in ET.iterparse(SRC, events=("start", "end")):
        if ev == "start":
            if el.tag == K + "Folder":
                depth_folder.append("")
            elif el.tag == K + "Placemark":
                cur = {"name": "", "got": False, "pts": [], "desc": "", "segs": [], "seg": []}
            continue

        # end
        if el.tag == K + "name":
            if cur is not None and not cur["got"]:
                cur["name"] = (el.text or "").strip()
                cur["got"] = True
            elif depth_folder and not depth_folder[-1]:
                depth_folder[-1] = (el.text or "").strip()
            el.clear()

        elif el.tag == K + "description":
            if cur is not None and not cur["desc"]:
                cur["desc"] = (el.text or "").strip()[:200]
            el.clear()

        elif el.tag == GX + "coord":
            if cur is not None:
                t = (el.text or "").split()
                if len(t) >= 2:
                    try:
                        cur["seg"].append((float(t[0]), float(t[1])))
                    except ValueError:
                        pass
            el.clear()

        elif el.tag == K + "LineString":
            # 一个 <LineString> 就是独立的一段，收起来，别跟下一段连上
            if cur is not None and cur["seg"]:
                cur["segs"].append(cur["seg"])
                cur["seg"] = []
            el.clear()

        elif el.tag == GX + "Track":
            # 一段轨迹结束，收起来。多条 Track 就是多段，不能连成一条
            if cur is not None and cur["seg"]:
                cur["segs"].append(cur["seg"])
                cur["seg"] = []
            el.clear()

        elif el.tag == K + "coordinates":
            if cur is not None:
                for tok in (el.text or "").replace("\n", " ").split():
                    q = tok.split(",")
                    if len(q) >= 2:
                        try:
                            cur["seg"].append((float(q[0]), float(q[1])))
                        except ValueError:
                            pass
            el.clear()

        elif el.tag == K + "Placemark":
            if cur is not None:
                if cur["seg"]:
                    cur["segs"].append(cur["seg"])
                    cur["seg"] = []
                segs = cur["segs"]
                if segs:
                    parts = []
                    total = 0
                    for sg in segs:
                        o = thin(sg)
                        if not o:
                            continue
                        total += len(o)
                        parts.append(";".join("%.6f,%.6f" % (a, b) for a, b in o))
                    if parts:
                        path = ["奥维轨迹"] + ([depth_folder[-1]] if depth_folder and depth_folder[-1] else [])
                        tp = "P" if (len(parts) == 1 and total == 1) else "L"
                        items.append({"p": path, "n": cur["name"], "d": cur["desc"],
                                      "t": tp, "c": "|".join(parts)})
                cur = None
            el.clear()

        elif el.tag == K + "Folder":
            if depth_folder:
                depth_folder.pop()
            el.clear()

        else:
            el.clear()

        if len(items) % 10 == 0 and len(items) and len(items) != getattr(main, "_last", 0):
            main._last = len(items)
            print("  %d 条轨迹… %.0fs" % (len(items), time.time() - t0), end="\r")

    print()
    total_in = sum(1 for _ in [])
    print("提取 %d 条轨迹，用时 %.0fs" % (len(items), time.time() - t0))

    raw_pts = 0
    out_pts = 0
    for it in items:
        raw_pts += it["c"].count(";") + 1

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, separators=(",", ":"))
    sz = os.path.getsize(OUT) / 1024 / 1024
    multi = sum(1 for it in items if "|" in it["c"])
    print("抽稀后 %d 个点，输出 %s（%.1f MB）" % (raw_pts, OUT, sz))
    print("其中多段轨迹：%d 条（按原样分段，没有首尾相连）" % multi)
    print()
    for it in items[:20]:
        print("  %-50s %d 点" % (it["n"][:50], it["c"].count(";") + 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
