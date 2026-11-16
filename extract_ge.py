# -*- coding: utf-8 -*-
"""从 KMZ 里提取地标

两个坑：
1. iterparse 里每个元素 end 后 clear，等父元素 Placemark 结束时，
   里面的 <name> <coordinates> 早被清空了。所以必须在该元素自己的
   end 事件里当场把值取走，不能等父元素。
2. 谷歌地球导出的轨迹有的是 <gx:Track>，坐标在 <gx:coord> 里，
   格式是 "经度 纬度 高程"，跟 <coordinates> 的 "经度,纬度,高程" 不一样。
"""

import json
import os
import sys
import time
import zipfile
import xml.etree.ElementTree as ET

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SRC = r"D:\一些杂项\谷歌地球20261019.kmz"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ge_data.json")

NS = "{http://www.opengis.net/kml/2.2}"
GX = "{http://www.google.com/kml/ext/2.2}"

K_NAME = NS + "name"
K_DESC = NS + "description"
K_FOLDER = NS + "Folder"
K_DOC = NS + "Document"
K_PM = NS + "Placemark"
K_COORD = NS + "coordinates"
GX_COORD = GX + "coord"


def parse_coord_str(t):
    pts = []
    for tok in (t or "").replace("\n", " ").split():
        p = tok.split(",")
        if len(p) >= 2:
            try:
                pts.append((float(p[0]), float(p[1])))
            except ValueError:
                pass
    return pts


def main():
    z = zipfile.ZipFile(SRC)
    t0 = time.time()
    items = []
    folders = []
    pm = None
    n_pm = 0
    last = 0

    with z.open("doc.kml") as f:
        for event, el in ET.iterparse(f, events=("start", "end")):
            if event == "start":
                if el.tag in (K_FOLDER, K_DOC):
                    folders.append({"name": "", "got": False})
                elif el.tag == K_PM:
                    pm = {"name": "", "got": False, "desc": "", "desc_got": False,
                          "blocks": [], "track": [], "gt": "L"}
                elif pm is not None:
                    if el.tag == NS + "Point":
                        pm["gt"] = "P"
                    elif el.tag == NS + "LineString":
                        pm["gt"] = "L"
                    elif el.tag == NS + "Polygon":
                        pm["gt"] = "G"
                continue

            # ---- end：每个元素在自己的 end 里处理，绝不留到父元素 ----
            if el.tag == K_NAME:
                txt = (el.text or "").strip()
                if pm is not None and not pm["got"]:
                    pm["name"] = txt
                    pm["got"] = True
                elif folders and not folders[-1]["got"]:
                    folders[-1]["name"] = txt
                    folders[-1]["got"] = True
                el.clear()

            elif el.tag == K_DESC:
                if pm is not None and not pm["desc_got"]:
                    pm["desc"] = (el.text or "").strip()
                    pm["desc_got"] = True
                el.clear()

            elif el.tag == K_COORD:
                # 区分是 Point / LineString / Polygon 的坐标
                if pm is not None:
                    pts = parse_coord_str(el.text)
                    if pts:
                        pm["blocks"].append((pm["gt"], pts))
                el.clear()

            elif el.tag == GX_COORD:
                if pm is not None:
                    t = (el.text or "").split()
                    if len(t) >= 2:
                        try:
                            pm["track"].append((float(t[0]), float(t[1])))
                        except ValueError:
                            pass
                el.clear()

            elif el.tag == K_PM:
                if pm is not None:
                    out = None
                    gm = None
                    segs = []
                    gm = "L"
                    if pm["track"] and len(pm["track"]) >= 2:
                        segs = [pm["track"]]
                        gm = "L"
                    elif pm["blocks"]:
                        gm = pm["blocks"][0][0]
                        if gm == "P":
                            segs = [pm["blocks"][0][1][:1]]
                        else:
                            segs = [b[1] for b in pm["blocks"] if b[1]]
                    if segs:
                        # 每一块单独一段，段与段之间不连线
                        c = "|".join(";".join("%.6f,%.6f" % (a, b) for a, b in sg) for sg in segs)
                        path = [x["name"] for x in folders if x["name"]][2:]
                        items.append({"p": path, "n": pm["name"],
                                      "d": pm["desc"][:400], "t": gm, "c": c})
                        n_pm += 1
                    pm = None
                el.clear()

            elif el.tag in (K_FOLDER, K_DOC):
                if folders:
                    folders.pop()
                el.clear()

            else:
                el.clear()

            if n_pm and n_pm % 10000 == 0 and n_pm != last:
                last = n_pm
                print("  %d … %.0fs" % (n_pm, time.time() - t0), end="\r")

    print()
    print("提取 %d 个地标（%.1fs）" % (len(items), time.time() - t0))
    print("无名：%d" % sum(1 for x in items if not x["n"]))
    from collections import Counter
    tc = Counter(x["t"] for x in items)
    print("类型：", dict(tc))

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, separators=(",", ":"))
    print("写出：%s（%.1f MB）" % (OUT, os.path.getsize(OUT) / 1024 / 1024))

    c = Counter(it["p"][0] if it["p"] else "(无分类)" for it in items)
    print()
    for k, v in c.most_common(10):
        print("  %-42s %6d" % (k[:42], v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
