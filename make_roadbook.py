# -*- coding: utf-8 -*-
"""
我的路书 —— 谷歌地球收藏分类浏览 + 一键导出 KML

数据原样保留（不抽稀、不裁剪、不筛），目录层级照原样一层不落。
底图源取自本机奥维互动地图的图源配置（D:\\omap\\map\\*\\*.txt）。
"""

import base64
import gzip
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "ge_data.json")
OVI = os.path.join(HERE, "ge_ovital.json")
TMP = os.path.join(HERE, "leaflet_tmp")
OUT = os.path.join(HERE, "我的路书.html")


def build_tree(raw):
    """按原样的多级目录建树，一个文件夹都不合并"""
    root = {"name": "我的地点", "kids": {}, "items": []}
    for it in raw:
        path = it.get("p") or ["(未分类)"]
        cur = root
        for seg in path:
            if seg not in cur["kids"]:
                cur["kids"][seg] = {"name": seg, "kids": {}, "items": []}
            cur = cur["kids"][seg]
        cur["items"].append([it.get("n", ""), it.get("d", ""), it.get("t", "P"), it.get("c", "")])
    return root


def to_list(node):
    kids = [to_list(v) for v in node["kids"].values()]
    pts = sum(1 for x in node["items"] if x[2] == "P")
    lns = sum(1 for x in node["items"] if x[2] == "L")
    pgs = sum(1 for x in node["items"] if x[2] == "G")
    for k in kids:
        pts += k["p"]
        lns += k["l"]
        pgs += k["g"]
    return {"name": node["name"], "kids": kids, "items": node["items"],
            "p": pts, "l": lns, "g": pgs}


def main():
    with open(SRC, encoding="utf-8") as f:
        raw = json.load(f)
    n_ge = len(raw)
    if os.path.exists(OVI):
        with open(OVI, encoding="utf-8") as f:
            ovi = json.load(f)
        raw += ovi
        print("谷歌地球 %d 个 + 奥维轨迹 %d 条 = %d" % (n_ge, len(ovi), len(raw)))
    else:
        print("读入 %d 个地标" % n_ge)

    tree = build_tree(raw)
    del raw
    data = to_list(tree)
    print("顶层文件夹 %d 个，合计 点%d 线%d 面%d" % (len(data["kids"]), data["p"], data["l"], data["g"]))

    raw_json = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    payload = base64.b64encode(gzip.compress(raw_json, 9)).decode("ascii")
    print("原始 JSON %.1f MB -> gzip+base64 %.1f MB"
          % (len(raw_json) / 1024 / 1024, len(payload) / 1024 / 1024))

    with open(os.path.join(TMP, "leaflet.js"), encoding="utf-8") as f:
        ljs = f.read()
    with open(os.path.join(TMP, "leaflet.css"), encoding="utf-8") as f:
        lcss = f.read()

    html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>我的路书 · 谷歌地球收藏</title>
<style>__CSS__</style>
<style>
html,body{margin:0;height:100%;font:13px/1.5 "Microsoft YaHei",system-ui,sans-serif;background:#0f1720}
#wrap{display:flex;height:100%}
#side{width:380px;background:#16202b;color:#cfd8dc;display:flex;flex-direction:column;flex-shrink:0}
.hd{padding:11px 13px 9px;border-bottom:1px solid #263341}
.hd h1{font-size:15px;margin:0 0 2px;color:#fff;font-weight:600}
.hd .sub{font-size:10.5px;color:#6b8299;line-height:1.55}
.tools{padding:8px 11px;border-bottom:1px solid #263341;display:flex;gap:7px;align-items:center}
.tools input{flex:1;background:#1e2b36;border:1px solid #2f4150;color:#dfe6e9;padding:4px 8px;
  border-radius:4px;font-size:12px;outline:none;min-width:0}
.tools input:focus{border-color:#4a6a85}
.btn{background:#1e88e5;color:#fff;border:0;padding:4px 9px;border-radius:4px;font-size:11.5px;cursor:pointer;white-space:nowrap}
.btn:hover{background:#1976d2}
.btn.g{background:#243542;color:#9fb3c8}
.btn.g:hover{background:#2e4354;color:#fff}
#list{flex:1;overflow:auto;padding-bottom:6px}
.nd{display:flex;align-items:center;gap:5px;padding:3px 8px 3px 0;cursor:pointer;border-bottom:1px solid #1a2632}
.nd:hover{background:#1c2936}
.nd.on{background:#1d3a4d}
.tw{width:14px;flex-shrink:0;text-align:center;color:#5d7a91;font-size:10px;user-select:none}
.tw.has{cursor:pointer;display:flex;align-items:center;justify-content:center}
.cb{margin:0 0 0 2px;flex-shrink:0;cursor:pointer;width:13px;height:13px}
.nd.it{background:#141e28}
.nd.it .nm{color:#a8bccd;font-size:12px}
.nd.it:hover{background:#1a2733}
.nd.it.on{background:#1b3040}
.del{background:none;border:1px solid #5a3a3a;color:#e08a8a;font-size:10.5px;padding:1px 6px;
  border-radius:3px;cursor:pointer;white-space:nowrap;flex-shrink:0}
.del:hover{background:#c0392b;color:#fff;border-color:#c0392b}
.dl{background:none;border:1px solid #4a3a3a;color:#b08a8a;font-size:10px;padding:0 5px;
  border-radius:3px;cursor:pointer;flex-shrink:0;line-height:15px;opacity:.55}
.nd.it:hover .dl{opacity:1}
.dl:hover{background:#c0392b;color:#fff;border-color:#c0392b}
.ar{width:0;height:0;border-left:5px solid #6b8299;border-top:4px solid transparent;
  border-bottom:4px solid transparent;transition:transform .12s}
.ar.open{transform:rotate(90deg)}
.tw.has:hover{color:#fff}
.nm{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px}
.ct{color:#5d7a91;font-size:10.5px;white-space:nowrap;flex-shrink:0}
.ex{background:none;border:1px solid #2f4150;color:#7fb0d0;font-size:10.5px;padding:1px 6px;
  border-radius:3px;cursor:pointer;white-space:nowrap;flex-shrink:0}
.ex:hover{background:#1e88e5;color:#fff;border-color:#1e88e5}
#map{flex:1}
#bm{position:absolute;right:12px;top:10px;z-index:800;background:rgba(22,32,43,.94);
  border-radius:6px;padding:6px;display:flex;flex-direction:column;gap:4px}
#bm button{background:#243542;color:#9fb3c8;border:0;padding:5px 11px;border-radius:4px;
  font-size:12px;cursor:pointer;text-align:left;white-space:nowrap}
#bm button:hover{background:#2e4354;color:#fff}
#bm button.on{background:#1e88e5;color:#fff}
#bar{position:absolute;left:392px;bottom:12px;z-index:600;background:rgba(255,255,255,.95);
  padding:5px 11px;border-radius:5px;font-size:11.5px;color:#233;box-shadow:0 1px 8px rgba(0,0,0,.25)}
#tip{position:absolute;left:calc(380px + (100vw - 380px)/2);top:50%;transform:translate(-50%,-50%);
  z-index:500;color:#7f97ad;font-size:13px;text-align:center;line-height:2;pointer-events:none}
.leaflet-popup-content{font-size:12px;max-height:260px;overflow:auto}
</style></head><body>
<div id="wrap">
  <div id="side">
    <div class="hd"><h1>我的路书</h1>
      <div class="sub">勾选才显示 · 双击任意名字可改名 · 右侧「删」可删</div></div>
    <div class="tools">
      <input id="q" placeholder="搜文件夹…">
      <button class="btn g" id="expandAll">展开</button>
      <button class="btn g" id="collapseAll">收起</button>
      <button class="btn" id="expAll">导出全部</button>
      <button class="btn" id="impBtn" title="导入 KML / KMZ / GPX">导入</button>
      <button class="btn g" id="clearAll" title="取消地图上所有显示">清空</button>
      <input type="file" id="fileIn" accept=".kml,.kmz,.gpx,application/vnd.google-earth.kml+xml,application/vnd.google-earth.kmz,application/gpx+xml" multiple style="display:none">
    </div>
    <div id="list"></div>
  </div>
  <div id="map"><div id="bm"></div></div>
</div>
<div id="bar"></div>
<div id="tip">左边点一个文件夹<br>地图上就画出来</div>
<script>__LEAFLET__</script>
<script>
var B64 = "__DATA__";
var TREE = null;

/* 底图源全部取自本机奥维互动地图的图源配置 */
var BASEMAPS = [
  {n:'谷歌卫星大字体', l:[
    {u:'https://mt0.google.com/vt/lyrs=s,h&hl=zh-CN&gl=CN&src=app&x={x}&y={y}&z={z}&scale=2',
     o:{tileSize:512, zoomOffset:-1, maxZoom:20}}]},
  {n:'四维地球', l:[
    {u:'https://swapi{s}.siweiearth.com/sj_raster/v6/wmts/tile/10002601/0?ak=&service=wmts&request=gettile&tilematrix={z}&tilecol={x}&tilerow={y}&product_id=',
     o:{subdomains:'1234', maxZoom:18}},
    {u:'https://t{s}.tianditu.gov.cn/DataServer?T=cia_w&tk=915de993ea6873664830bf5d8217723c&x={x}&y={y}&l={z}',
     o:{subdomains:'01234567', maxZoom:18}}]},
  {n:'天地图影像', l:[
    {u:'https://t{s}.tianditu.gov.cn/DataServer?T=img_w&tk=4267820f43926eaf808d61dc07269beb&x={x}&y={y}&l={z}',
     o:{subdomains:'01234567', maxZoom:18}},
    {u:'https://t{s}.tianditu.gov.cn/DataServer?T=cia_w&tk=915de993ea6873664830bf5d8217723c&x={x}&y={y}&l={z}',
     o:{subdomains:'01234567', maxZoom:18}}]},
  {n:'星图地球', l:[
    {u:'https://tiles{s}.geovisearth.com/base/v1/img/{z}/{x}/{y}?format=webp&tmsIds=w&token=26ee8d8d392b1cc49d91cd81ef1c802b6a63651541ac9c3d3d1359d8bf844228',
     o:{subdomains:'1234', maxZoom:18}},
    {u:'https://tiles{s}.geovisearth.com/base/v1/cia/{z}/{x}/{y}?format=png&tmsIds=w&token=26ee8d8d392b1cc49d91cd81ef1c802b6a63651541ac9c3d3d1359d8bf844228',
     o:{subdomains:'1234', maxZoom:18}}]},
  {n:'吉林一号', tk:true, l:[
    {u:'https://api.jl1mall.com/getMap/{z}/{x}/{y}?mk=73ad26c4aa6957eef051ecc5a15308b4&tk=__TK__&vf=0&sch=wmts',
     o:{maxZoom:18}}]},
  {n:'Esri影像', l:[
    {u:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
     o:{maxZoom:19}}]},
  {n:'OSM', l:[
    {u:'https://tile.openstreetmap.de/{z}/{x}/{y}.png', o:{maxZoom:19}}]},
  {n:'Esri街道图', l:[
    {u:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
     o:{maxZoom:19}}]},
  {n:'高德', l:[
    {u:'https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}',
     o:{subdomains:'123', maxZoom:18}}]},
  {n:'高德卫星', l:[
    {u:'https://webst0{s}.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}',
     o:{subdomains:'1234', maxZoom:18}},
    {u:'https://wprd0{s}.is.autonavi.com/appmaptile?x={x}&y={y}&z={z}&lang=zh_cn&size=1&scl=1&style=8',
     o:{subdomains:'1234', maxZoom:18}}]},
  {n:'无底图', l:[]}
];

var map = L.map('map',{preferCanvas:true}).setView([33,102],4);
var curBase=[];
function setBase(i){
  var bm=BASEMAPS[i];
  var tk='';
  if(bm.tk){
    tk=localStorage.getItem('jl1tk')||'';
    if(!tk){
      tk=prompt('吉林一号需要个人密钥 tk。先去 jl1mall.com 注册（免费，实名认证），登录后依次点「买数据」「切片影像套件」「我的套件」「套件管理」，复制 TK 贴到这里：');
      if(!tk) return;
      localStorage.setItem('jl1tk',tk.trim());
      tk=tk.trim();
    }
  }
  curBase.forEach(function(x){ map.removeLayer(x); });
  curBase=[];
  bm.l.forEach(function(b){
    var u=b.u.replace('__TK__', encodeURIComponent(tk));
    curBase.push(L.tileLayer(u,b.o).addTo(map));
  });
  document.querySelectorAll('#bm button').forEach(function(x,k){ x.classList.toggle('on',k===i); });
}
(function(){
  var box=document.getElementById('bm');
  BASEMAPS.forEach(function(b,i){
    var btn=document.createElement('button');
    btn.textContent=b.n;
    btn.onclick=function(){ setBase(i); };
    box.appendChild(btn);
  });
})();

var COLORS=['#e74c3c','#3498db','#2ecc71','#9b59b6','#f39c12','#1abc9c','#e67e22','#34495e',
            '#c0392b','#2980b9','#27ae60','#8e44ad','#d35400','#16a085','#7f8c8d','#c2185b'];

function esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

var nodes=[], PARENT={};
function setOrig(node){
  if(!node.__orig) node.__orig = node.name;
  (node.kids || []).forEach(setOrig);
}
function origPath(n){
  var parts = [], cur = n;
  while(cur){ parts.unshift(cur.__orig || cur.name); cur = PARENT[cur.idx]; }
  return parts.join('/');
}
function applyNodeNames(node, prefix){
  (node.kids || []).forEach(function(k){
    var pth = prefix ? prefix + '/' + (k.__orig || k.name) : (k.__orig || k.name);
    if(NAMES['D:' + pth]) k.name = NAMES['D:' + pth];
    applyNodeNames(k, pth);
  });
}
function renameNode(n){
  var v = prompt('文件夹改名叫什么？（留空取消）', n.name);
  if(v === null) return;
  v = v.trim();
  if(!v || v === n.name) return;
  var k = origPath(n);
  n.name = v;
  NAMES['D:' + k] = v;
  saveNames();
  render();
}

function walk(n, depth){
  n.depth=depth; n.idx=nodes.length; n.open = depth < 1;   // 根展开，二级列出来但收起，再深要点 +
  nodes.push(n);
  n.kids.forEach(function(k){ PARENT[nodes.length]=n; walk(k, depth+1); });
}
function initTree(){ walk(TREE, 0); }

function countOf(n){ return n.p+n.l+n.g; }
function visible(n){
  var cur=PARENT[n.idx];
  while(cur){ if(!cur.open) return false; cur=PARENT[cur.idx]; }
  return true;
}

var curLayer=null, curIdx=0;
function render(){
  var box=document.getElementById('list');
  box.innerHTML='';
  nodes.forEach(function(n){
    if(!visible(n)) return;
    var row=document.createElement('div');
    row.className='nd'+(n.idx===curIdx?' on':'');
    row.dataset.i=n.idx;
    var arrow = (n.kids.length || n.items.length) ? (n.open?'–':'+') : '';
    var cnt=[];
    if(n.p) cnt.push(n.p+'点');
    if(n.l) cnt.push(n.l+'线');
    if(n.g) cnt.push(n.g+'面');
    var tw = (n.kids.length || n.items.length)
      ? '<span class="tw has" style="margin-left:'+(n.depth*13)+'px"><i class="ar'+(n.open?' open':'')+'"></i></span>'
      : '<span class="tw" style="margin-left:'+(n.depth*13)+'px"></span>';
    var on = !!LAYS[n.idx];
    row.innerHTML=tw+
      '<input type="checkbox"'+(on?' checked':'')+' class="cb">'+
      '<span class="nm" title="'+esc(n.name)+'">'+esc(n.name)+'</span>'+
      '<span class="ct">'+cnt.join(' ')+'</span><button class="ex">导出</button>'+
      (n.depth >= 1 ? '<button class="del" title="删除这个文件夹">删</button>' : '');
    if(n.kids.length || n.items.length){
      row.querySelector('.tw').onclick=function(e){ e.stopPropagation(); n.open=!n.open; render(); };
    }
    row.querySelector('.ex').onclick=function(e){ e.stopPropagation(); exportNode(n); };
    row.querySelector('.cb').onclick=function(e){ e.stopPropagation(); toggleNode(n, e.target.checked); };
    var ft = null;
    row.ondblclick=function(e){
      e.stopPropagation();
      if(ft){ clearTimeout(ft); ft = null; }
      renameNode(n);
    };
    var db = row.querySelector('.del');
    if(db) db.onclick=function(e){
      e.stopPropagation();
      if(n.__imp) removeImport(n.__id, n.name);
      else deleteFolder(n);
    };
    row.onclick=function(e){
      if(e.target.tagName==='INPUT' || e.target.className==='del') return;
      if(ft) return;
      ft = setTimeout(function(){
        ft = null;
        var cb=row.querySelector('.cb'); cb.checked=!cb.checked; toggleNode(n, cb.checked);
      }, 240);
    };
    box.appendChild(row);

    // 展开之后，把这一层的每条记录也列出来，可以单独勾
    if(n.open && n.items && n.items.length){
      var lim = Math.min(n.items.length, 800);
      for(var i=0;i<lim;i++) box.appendChild(renderItem(n, n.items[i], i));
      if(n.items.length>lim){
        var more=document.createElement('div');
        more.className='nd';
        more.innerHTML='<span style="margin-left:'+((n.depth+1)*13+16)+'px;color:#5d7a91;font-size:11px">'+
          '还有 '+(n.items.length-lim)+' 条未列出（可整组勾选上面的文件夹）</span>';
        box.appendChild(more);
      }
    }
  });
}

var ITEMLAYS = {};
var NAMES = {};        // 改过的名字，key = 路径#序号
var DELETED = {};      // 删掉的记录

/* 坐标当 key，跟树怎么建、第几层都没关系 */
function geoKey(it){
  return String((it && it[3]) || '').slice(0, 90);
}

function loadDeleted(){
  try{
    var t = localStorage.getItem('rb_deleted');
    if(t) DELETED = JSON.parse(t) || {};
  }catch(e){ DELETED = {}; }
}
function saveDeleted(){
  try{ localStorage.setItem('rb_deleted', JSON.stringify(DELETED)); }catch(e){}
}

/* 启动时把删掉的文件夹剔出去 */
function pruneFolders(node){
  if(!node.kids) return;
  node.kids = node.kids.filter(function(k){
    if(k.__imp) return true;          // 导入的要留着
    return !DELFOLDERS[folderName(k)];
  });
  node.kids.forEach(function(k){
    if(k.__imp) return;               // 但不往导入的里面递归
    pruneFolders(k);
  });
}
function folderName(n){
  var parts=[], cur=n;
  while(cur){ parts.unshift(cur.name); cur=PARENT[cur.idx]; }
  return parts.join('/');
}

/* 启动时把删掉的剔出去 */
function applyDeletes(node){
  if(node.items && node.items.length){
    node.items = node.items.filter(function(it){ return !DELETED[geoKey(it)]; });
  }
  (node.kids || []).forEach(applyDeletes);
}

/* 删除一条记录 */
function deleteItem(n, i){
  var it = n.items[i];
  if(!it) return;
  var nm = it[0] || '（无名）';
  if(!confirm('删除「' + nm + '」？这条只是从页面里去掉，原始文件不动。')) return;
  DELETED[geoKey(it)] = 1;
  saveDeleted();
  node.items.splice(i, 1);
  recount(TREE);
  render();
  updateBar();
}

var DELFOLDERS = {};
function saveDelFolders(){
  try{ localStorage.setItem('rb_delfolders', JSON.stringify(DELFOLDERS)); }catch(e){}
}
function loadDelFolders(){
  try{
    var t = localStorage.getItem('rb_delfolders');
    if(t) DELFOLDERS = JSON.parse(t) || {};
  }catch(e){ DELFOLDERS = {}; }
}
function folderKey(n){
  var parts=[], cur=n;
  while(cur){ parts.unshift(cur.name); cur=PARENT[cur.idx]; }
  return parts.join('/');
}
function deleteFolder(n){
  var p = PARENT[n.idx];
  if(!p){ alert('这一层不能删'); return; }
  var cnt = (n.p||0)+(n.l||0)+(n.g||0);
  if(!confirm('删除文件夹「'+n.name+'」？里面 '+cnt+' 个地标一起删掉，原始文件不动。')) return;
  DELFOLDERS[folderKey(n)] = 1;
  saveDelFolders();
  var i = p.kids.indexOf(n);
  if(i >= 0) p.kids.splice(i, 1);
  recount(TREE);
  nodes = []; PARENT = {};
  initTree();
  LAYS = {}; ITEMLAYS = {};
  render();
  updateBar();
}

function pathKey(n, i){
  var parts = [], cur = n;
  while(cur){ parts.unshift(cur.name); cur = PARENT[cur.idx]; }
  return parts.join('/') + '#' + i;
}

function saveNames(){
  try{ localStorage.setItem('rb_names', JSON.stringify(NAMES)); }catch(e){}
}

function loadNames(){
  try{
    var t = localStorage.getItem('rb_names');
    if(t) NAMES = JSON.parse(t) || {};
  }catch(e){ NAMES = {}; }
}

function applyNames(node){
  (node.items || []).forEach(function(it){
    var k = geoKey(it);
    if(NAMES[k] !== undefined) it[0] = NAMES[k];
  });
  (node.kids || []).forEach(applyNames);
}

function renameItem(n, i){
  var it = n.items[i];
  var cur = it[0] || '';
  var v = prompt('改成什么名字？（留空就是清除改名）', cur);
  if(v === null) return;
  v = v.trim();
  var k = geoKey(it);
  if(v){
    it[0] = v;
    NAMES[k] = v;
  } else {
    it[0] = '';
    delete NAMES[k];
  }
  saveNames();
  render();
  updateBar();
}

function renderItem(n, it, i){
  var key=n.idx+':'+i;
  var on=!!ITEMLAYS[key];
  var row=document.createElement('div');
  row.className='nd it'+(on?' on':'');
  var nm=it[0]||'（无名）';
  var tp=it[2]==='P'?'点':(it[2]==='L'?'线':'面');
  row.innerHTML='<span class="tw" style="margin-left:'+((n.depth+1)*13)+'px"></span>'+
    '<input type="checkbox"'+(on?' checked':'')+' class="cb">'+
    '<span class="nm" title="'+esc(nm)+'">'+esc(nm)+'</span>'+
    '<span class="ct">'+tp+'</span><button class="dl" title="删除这条">删</button>';
  row.querySelector('.cb').onclick=function(e){
    e.stopPropagation(); toggleItem(n, i, e.target.checked);
  };
  var tmr = null;
  row.onclick=function(e){
    if(e.target.tagName==='INPUT' || e.target.className==='dl') return;
    if(tmr) return;
    tmr = setTimeout(function(){
      tmr = null;
      var cb=row.querySelector('.cb'); cb.checked=!cb.checked; toggleItem(n, i, cb.checked);
    }, 240);
  };
  row.ondblclick=function(e){
    e.stopPropagation();
    if(tmr){ clearTimeout(tmr); tmr = null; }
    renameItem(n, i);
  };
  var dl = row.querySelector('.dl');
  if(dl) dl.onclick=function(e){ e.stopPropagation(); deleteItem(n, i); };
  return row;
}

function toggleItem(n, i, on){
  var key=n.idx+':'+i;
  if(on){
    if(!ITEMLAYS[key]){
      ITEMLAYS[key]=buildLayer([n.items[i]], n.depth+1);
      map.addLayer(ITEMLAYS[key]);
    }
    var it=n.items[i];
    if(it && it[3]){
      var b=[];
      it[3].split('|').forEach(function(seg){
        seg.split(';').forEach(function(x){
          var q=x.split(',');
          if(q.length>=2){ var la=+q[1], ln=+q[0]; if(!isNaN(la)&&!isNaN(ln)) b.push([la,ln]); }
        });
      });
      if(b.length) map.fitBounds(L.latLngBounds(b).pad(0.05));
    }
    if(TIP) TIP.style.display='none';
  } else {
    if(ITEMLAYS[key]){ map.removeLayer(ITEMLAYS[key]); delete ITEMLAYS[key]; }
  }
  render();
  updateBar();
}

function flatten(n, out){
  n.items.forEach(function(x){ out.push(x); });
  n.kids.forEach(function(k){ flatten(k, out); });
  return out;
}

var LAYS = {};      // 文件夹序号 -> 已经画在地图上的图层

function buildLayer(items, depth){
  var g = L.layerGroup();
  var color = COLORS[(depth||0) % COLORS.length];
  items.forEach(function(it){
    var nm=it[0], desc=it[1], t=it[2], c=it[3];
    if(!c) return;
    if(t==='P'){
      var p=c.split(';')[0].split(',');
      if(p.length<2) return;
      var la=+p[1], ln=+p[0];
      if(isNaN(la)||isNaN(ln)) return;
      var m=L.circleMarker([la,ln],{radius:3.2,color:color,weight:1,fillColor:color,fillOpacity:.85});
      var h='<b>'+esc(nm||'（无名）')+'</b>';
      if(desc) h+='<div style="color:#666;margin-top:3px">'+esc(desc)+'</div>';
      m.bindPopup(h);
      g.addLayer(m);
    } else if(t==='L'){
      c.split('|').forEach(function(seg){
        var ll=seg.split(';').map(function(x){var q=x.split(',');return [+q[1],+q[0]];})
          .filter(function(p){return !isNaN(p[0])&&!isNaN(p[1]);});
        if(ll.length<2) return;
        g.addLayer(L.polyline(ll,{color:color,weight:2,opacity:.9}));
      });
    } else {
      c.split('|').forEach(function(seg){
        var ll=seg.split(';').map(function(x){var q=x.split(',');return [+q[1],+q[0]];})
          .filter(function(p){return !isNaN(p[0])&&!isNaN(p[1]);});
        if(ll.length<3) return;
        g.addLayer(L.polygon(ll,{color:color,weight:1,fillColor:color,fillOpacity:.2}));
      });
    }
  });
  return g;
}

function boundsOf(n){
  var b=[];
  flatten(n, []).forEach(function(it){
    if(!it[3]) return;
    it[3].split('|').forEach(function(seg){
      seg.split(';').forEach(function(x){
        var q=x.split(',');
        if(q.length>=2){ var la=+q[1], ln=+q[0]; if(!isNaN(la)&&!isNaN(ln)) b.push([la,ln]); }
      });
    });
  });
  return b;
}

function toggleNode(n, on){
  if(on){
    if(!LAYS[n.idx]){
      LAYS[n.idx] = buildLayer(flatten(n, []), n.depth);
      map.addLayer(LAYS[n.idx]);
    }
    var b = boundsOf(n);
    if(b.length) map.fitBounds(L.latLngBounds(b).pad(0.06));
    if(TIP) TIP.style.display='none';
    curIdx = n.idx;
  } else {
    if(LAYS[n.idx]){ map.removeLayer(LAYS[n.idx]); delete LAYS[n.idx]; }
  }
  render();
  updateBar();
}

function countSelected(){
  var layers=0, feats=0;
  for(var k in LAYS){
    layers++;
    feats += countOf(nodes[+k]);
  }
  for(var j in ITEMLAYS){ layers++; feats++; }
  return {l:layers, f:feats};
}

function updateBar(){
  var st = countSelected();
  var el = document.getElementById('bar');
  if(st.l) el.textContent = '已勾选 '+st.l+' 个文件夹 / '+st.f+' 个地标';
  else el.textContent = '全部 '+countOf(TREE)+' 个地标';
}

function toC(seg){ return seg.split(';').map(function(x){return x+',0';}).join(' '); }

function kmlOf(node){
  var o=['<?xml version="1.0" encoding="UTF-8"?>',
    '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
    '<name>'+esc(node.name)+'</name>'];
  (function rec(nd){
    o.push('<Folder><name>'+esc(nd.name)+'</name>');
    nd.items.forEach(function(it){
      var nm=esc(it[0]||'未命名'), desc=it[1], t=it[2], c=it[3];
      if(!c) return;
      if(t==='P'){
        var p=c.split(';')[0];
        o.push('<Placemark><name>'+nm+'</name>');
        if(desc) o.push('<description><![CDATA['+desc+']]></description>');
        o.push('<Point><coordinates>'+p+',0</coordinates></Point></Placemark>');
      } else if(t==='L'){
        c.split('|').forEach(function(seg,k){
          o.push('<Placemark><name>'+nm+(k?' ('+(k+1)+')':'')+'</name>');
          if(desc) o.push('<description><![CDATA['+desc+']]></description>');
          o.push('<LineString><tessellate>1</tessellate><coordinates>'+toC(seg)+'</coordinates></LineString></Placemark>');
        });
      } else {
        c.split('|').forEach(function(seg,k){
          var pts=seg.split(';');
          if(pts.length>2 && pts[0]!==pts[pts.length-1]) pts.push(pts[0]);
          o.push('<Placemark><name>'+nm+(k?' ('+(k+1)+')':'')+'</name>');
          if(desc) o.push('<description><![CDATA['+desc+']]></description>');
          o.push('<Polygon><outerBoundaryIs><LinearRing><coordinates>'+
                 pts.map(function(x){return x+',0';}).join(' ')+
                 '</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>');
        });
      }
    });
    nd.kids.forEach(rec);
    o.push('</Folder>');
  })(node);
  o.push('</Document></kml>');
  return o.join('\\n');
}

function download(name, text){
  var blob=new Blob([text],{type:'application/vnd.google-earth.kml+xml;charset=utf-8'});
  var a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download=String(name).replace(/[\\\\/:*?"<>|]/g,'_')+'.kml';
  document.body.appendChild(a); a.click();
  setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); },2000);
}

function exportNode(n){
  var cnt=countOf(n);
  if(cnt>20000 && !confirm('「'+n.name+'」有 '+cnt+' 个地标，导出的 KML 会比较大，继续？')) return;
  download(n.name, kmlOf(n));
}

document.getElementById('expAll').onclick=function(){ download('我的路书-全部', kmlOf(TREE)); };

/* 清空：把地图上画的全部撤掉 */
var TIP=document.getElementById('tip');
function clearAll(){
  for(var k in LAYS){ map.removeLayer(LAYS[k]); }
  for(var j in ITEMLAYS){ map.removeLayer(ITEMLAYS[j]); }
  LAYS = {};
  ITEMLAYS = {};
  curIdx = -1;
  if(TIP) TIP.style.display='block';
  render();
  updateBar();
}
document.getElementById('clearAll').onclick=clearAll;
document.getElementById('impBtn').onclick=function(){ document.getElementById('fileIn').click(); };
document.getElementById('fileIn').onchange=function(e){
  if(e.target.files && e.target.files.length) importFiles(e.target.files);
  e.target.value='';
};
document.getElementById('expandAll').onclick=function(){ nodes.forEach(function(n){ n.open=true; }); render(); };
document.getElementById('collapseAll').onclick=function(){ nodes.forEach(function(n){ n.open=(n.depth===0); }); render(); };
document.getElementById('q').oninput=function(e){
  var k=e.target.value.trim().toLowerCase();
  if(!k){ nodes.forEach(function(n){ n.open=(n.depth<1); }); render(); return; }
  nodes.forEach(function(n){ n.open=true; });
  render();
  document.querySelectorAll('.nd').forEach(function(r){
    var n=nodes[+r.dataset.i];
    if((n.name||'').toLowerCase().indexOf(k)<0) r.style.display='none';
  });
};

/* ========== 导入 / 删除 ========== */
var IMPORTS = [];      // [{id, name, items}]
var GXN = 'http://www.google.com/kml/ext/2.2';

function idbOpen(){
  return new Promise(function(res,rej){
    var r = indexedDB.open('roadbook_imports', 1);
    r.onupgradeneeded = function(){ r.result.createObjectStore('files', {keyPath:'id'}); };
    r.onsuccess = function(){ res(r.result); };
    r.onerror = function(){ rej(r.error); };
  });
}
async function idbPut(rec){
  var db = await idbOpen();
  return new Promise(function(res,rej){
    var t = db.transaction('files','readwrite');
    t.objectStore('files').put(rec);
    t.oncomplete = res; t.onerror = function(){ rej(t.error); };
  });
}
async function idbAll(){
  var db = await idbOpen();
  return new Promise(function(res,rej){
    var t = db.transaction('files','readonly');
    var rq = t.objectStore('files').getAll();
    rq.onsuccess = function(){ res(rq.result || []); };
    rq.onerror = function(){ rej(rq.error); };
  });
}
async function idbDel(id){
  var db = await idbOpen();
  return new Promise(function(res,rej){
    var t = db.transaction('files','readwrite');
    t.objectStore('files').delete(id);
    t.oncomplete = res; t.onerror = function(){ rej(t.error); };
  });
}

/* KMZ 就是个 zip，抠出里面第一个 .kml */
async function unzipKML(buf){
  var u8 = new Uint8Array(buf), dv = new DataView(buf), n = u8.length;
  var eocd = -1;
  for(var i = n - 22; i >= Math.max(0, n - 65558); i--){
    if(dv.getUint32(i, true) === 0x06054b50){ eocd = i; break; }
  }
  if(eocd < 0) throw new Error('不是有效的 KMZ（找不到 zip 目录）');
  var cdOff = dv.getUint32(eocd + 16, true), cdCount = dv.getUint16(eocd + 10, true);
  var p = cdOff, tgt = null;
  for(var k = 0; k < cdCount; k++){
    if(dv.getUint32(p, true) !== 0x02014b50) break;
    var method = dv.getUint16(p + 10, true);
    var csize  = dv.getUint32(p + 20, true);
    var nlen   = dv.getUint16(p + 28, true);
    var elen   = dv.getUint16(p + 30, true);
    var clen   = dv.getUint16(p + 32, true);
    var lho    = dv.getUint32(p + 42, true);
    var nm     = new TextDecoder().decode(u8.subarray(p + 46, p + 46 + nlen));
    if(/\.kml$/i.test(nm)){ tgt = {method:method, csize:csize, lho:lho}; break; }
    p += 46 + nlen + elen + clen;
  }
  if(!tgt) throw new Error('KMZ 里没有 kml 文件');
  var lh = tgt.lho;
  var lnlen = dv.getUint16(lh + 26, true), lelen = dv.getUint16(lh + 28, true);
  var st = lh + 30 + lnlen + lelen;
  var comp = u8.subarray(st, st + tgt.csize);
  if(tgt.method === 0) return new TextDecoder().decode(comp);
  var ds = new DecompressionStream('deflate-raw');
  var out = await new Response(new Blob([comp]).stream().pipeThrough(ds)).arrayBuffer();
  return new TextDecoder().decode(out);
}

/* 解析 KML，保留 Folder 层级 */
function parseKML(text){
  var doc = new DOMParser().parseFromString(text, 'text/xml');
  var err = doc.getElementsByTagName('parsererror');
  if(err.length) throw new Error('KML 格式有问题');
  var items = [];

  function childText(el, tag){
    for(var i = 0; i < el.children.length; i++){
      if(el.children[i].localName === tag) return (el.children[i].textContent || '').trim();
    }
    return '';
  }
  function coordStr(node){
    var cs = node.getElementsByTagName('coordinates');
    if(!cs.length) return '';
    var out = [];
    var toks = (cs[0].textContent || '').trim().replace(/\s+/g, ' ').split(' ');
    for(var i = 0; i < toks.length; i++){
      var q = toks[i].split(',');
      if(q.length >= 2 && !isNaN(+q[0]) && !isNaN(+q[1])) out.push(q[0] + ',' + q[1]);
    }
    return out.join(';');
  }
  function collect(el){
    // 一个 Placemark 里可能同时有标注点、多段线、面，全部收下
    var pts = [], lines = [], polys = [], tr = [];
    var all = el.getElementsByTagName('*');
    for(var i = 0; i < all.length; i++){
      var t = all[i].localName;
      if(t === 'Point'){
        var c1 = coordStr(all[i]); if(c1) pts.push(c1);
      } else if(t === 'LineString'){
        var c2 = coordStr(all[i]); if(c2) lines.push(c2);
      } else if(t === 'Polygon'){
        var c3 = coordStr(all[i]); if(c3) polys.push(c3);
      } else if(t === 'coord' && all[i].namespaceURI === GXN){
        var m = (all[i].textContent || '').trim().split(/\s+/);
        if(m.length >= 2 && !isNaN(+m[0]) && !isNaN(+m[1])) tr.push(m[0] + ',' + m[1]);
      }
    }
    if(tr.length >= 2) lines.unshift(tr.join(';'));
    return {pts:pts, lines:lines, polys:polys};
  }

  function walk(node, path, isRoot){
    for(var i = 0; i < node.children.length; i++){
      var el = node.children[i], tag = el.localName;
      if(tag === 'Folder' || tag === 'Document'){
        // 谷歌地球的 KMZ 里，收藏夹有的存成 Folder、有的存成 Document，
        // 两种都要算层级；只有最外层那个（通常是文件名）跳过
        var nm = isRoot ? '' : childText(el, 'name');
        walk(el, nm ? path.concat(nm) : path, false);
      } else if(tag === 'Placemark'){
        var nm2 = childText(el, 'name');
        var ds = childText(el, 'description').slice(0, 400);
        var g = collect(el);
        g.pts.forEach(function(c){
          items.push({p:path.slice(), n:nm2, d:ds, t:'P', c:c});
        });
        if(g.lines.length){
          items.push({p:path.slice(), n:nm2, d:ds, t:'L', c:g.lines.join('|')});
        }
        if(g.polys.length){
          items.push({p:path.slice(), n:nm2, d:ds, t:'G', c:g.polys.join('|')});
        }
      }
    }
  }
  walk(doc.documentElement, [], true);
  return items;
}

/* 解析 GPX：wpt 是点，trk/trkseg 是轨迹（每段分开），rte 是路线 */
function parseGPX(text){
  var doc = new DOMParser().parseFromString(text, 'text/xml');
  if(doc.getElementsByTagName('parsererror').length) throw new Error('GPX 格式有问题');
  var items = [];

  function nameOf(el){
    for(var i = 0; i < el.children.length; i++){
      if(el.children[i].localName === 'name') return (el.children[i].textContent || '').trim();
    }
    return '';
  }

  var wpts = doc.getElementsByTagName('wpt');
  for(var i = 0; i < wpts.length; i++){
    var w = wpts[i], la = w.getAttribute('lat'), ln = w.getAttribute('lon');
    if(!la || !ln) continue;
    var ds = '';
    for(var j = 0; j < w.children.length; j++){
      if(w.children[j].localName === 'desc'){ ds = (w.children[j].textContent || '').trim().slice(0,400); break; }
    }
    items.push({p:[], n:nameOf(w), d:ds, t:'P', c:ln + ',' + la});
  }

  var trks = doc.getElementsByTagName('trk');
  for(var i = 0; i < trks.length; i++){
    var tr = trks[i], nm = nameOf(tr), segs = [];
    for(var j = 0; j < tr.children.length; j++){
      var ch = tr.children[j];
      if(ch.localName !== 'trkseg') continue;
      var pts = [];
      for(var k = 0; k < ch.children.length; k++){
        var pt = ch.children[k];
        if(pt.localName !== 'trkpt') continue;
        var la2 = pt.getAttribute('lat'), ln2 = pt.getAttribute('lon');
        if(la2 && ln2 && !isNaN(+la2) && !isNaN(+ln2)) pts.push(ln2 + ',' + la2);
      }
      if(pts.length) segs.push(pts.join(';'));
    }
    if(!segs.length) continue;
    var total = segs.reduce(function(a, b){ return a + b.split(';').length; }, 0);
    var tp = (segs.length === 1 && total === 1) ? 'P' : 'L';
    items.push({p:[], n:nm, d:'', t:tp, c:segs.join('|')});
  }

  var rtes = doc.getElementsByTagName('rte');
  for(var i = 0; i < rtes.length; i++){
    var rt = rtes[i], pts = [];
    for(var j = 0; j < rt.children.length; j++){
      var rp = rt.children[j];
      if(rp.localName !== 'rtept') continue;
      var la3 = rp.getAttribute('lat'), ln3 = rp.getAttribute('lon');
      if(la3 && ln3 && !isNaN(+la3) && !isNaN(+ln3)) pts.push(ln3 + ',' + la3);
    }
    if(pts.length) items.push({p:[], n:nameOf(rt), d:'', t: pts.length === 1 ? 'P' : 'L', c:pts.join(';')});
  }

  return items;
}

/* 把导入的数据挂到树上 */
function applyImports(){
  if(!TREE) return;
  TREE.kids = TREE.kids.filter(function(k){ return !k.__imp; });
  IMPORTS.forEach(function(imp){
    var node = {name: imp.name, kids: [], items: [], __imp: true, __id: imp.id};
    // 按原文件的文件夹层级建子树
    imp.items.forEach(function(it){
      var cur = node;
      var path = it.p || [];
      for(var i = 0; i < path.length; i++){
        var seg = path[i];
        var found = null;
        for(var j = 0; j < cur.kids.length; j++){
          if(cur.kids[j].name === seg){ found = cur.kids[j]; break; }
        }
        if(!found){
          found = {name: seg, kids: [], items: []};
          cur.kids.push(found);
        }
        cur = found;
      }
      cur.items.push([it.n || '', it.d || '', it.t || 'P', it.c || '']);
    });
    node.__imp = true;
    node.__id = imp.id;
    TREE.kids.unshift(node);
  });
  recount(TREE);
}

/* 重新算数量 */
function recount(n){
  var p = 0, l = 0, g = 0;
  n.items.forEach(function(x){ if(x[2]==='P') p++; else if(x[2]==='L') l++; else g++; });
  n.kids.forEach(function(k){
    recount(k);
    p += k.p; l += k.l; g += k.g;
  });
  n.p = p; n.l = l; n.g = g;
  return n;
}

/* 重建树索引（导入/删除后要重来） */
function rebuildTree(){
  applyImports();
  nodes = []; PARENT = {};
  initTree();
  LAYS = {}; ITEMLAYS = {};
  if(curLayer){ map.removeLayer(curLayer); curLayer = null; }
  render();
  updateBar();
}

async function importFiles(files){
  for(var i = 0; i < files.length; i++){
    var f = files[i];
    try{
      var buf = await f.arrayBuffer();
      var isKmz = /\.kmz$/i.test(f.name);
      var isGpx = /\.gpx$/i.test(f.name);
      var text = isKmz ? await unzipKML(buf) : new TextDecoder().decode(buf);
      var items = isGpx ? parseGPX(text) : parseKML(text);
      if(!items.length){ alert(f.name + '：里面没有读到任何地标'); continue; }
      var id = 'imp_' + Date.now() + '_' + i;
      var name = f.name.replace(/\.(kml|kmz|gpx)$/i, '');
      IMPORTS.push({id: id, name: name, items: items});
      await idbPut({id: id, name: name, items: items});
      console.log('导入', f.name, items.length, '个地标');
    }catch(e){
      alert('导入 ' + f.name + ' 失败：' + e.message);
    }
  }
  if(TREE){
    nodes = []; PARENT = {};
    applyImports();
    initTree();
    LAYS = {}; ITEMLAYS = {};
    render();
    updateBar();
  }
}

async function loadImports(){
  try{
    var all = await idbAll();
    IMPORTS = all || [];
  }catch(e){ console.warn('读取导入记录失败', e); }
}

async function removeImport(id, name){
  if(!confirm('删除「' + name + '」？只删这一份导入的数据，原始文件不受影响。')) return;
  IMPORTS = IMPORTS.filter(function(x){ return x.id !== id; });
  try{ await idbDel(id); }catch(e){}
  nodes = []; PARENT = {};
  applyImports();
  initTree();
  LAYS = {}; ITEMLAYS = {};
  render();
  updateBar();
}

/* 数据是 gzip 压过的，打开时用浏览器自带的解压流还原 */
async function boot(){
  var t0=Date.now();
  var bar=document.getElementById('bar');
  if(bar) bar.textContent='正在解压数据…';
  try{
    var bin=atob(B64), n=bin.length, u8=new Uint8Array(n);
    for(var i=0;i<n;i++) u8[i]=bin.charCodeAt(i);
    var ds=new DecompressionStream('gzip');
    var txt=await new Response(new Blob([u8]).stream().pipeThrough(ds)).text();
    TREE=JSON.parse(txt);
    B64=null;
    await loadImports();
    applyImports();
    loadNames();
    setOrig(TREE);
    applyNodeNames(TREE, '');
    loadDeleted();
    loadDelFolders();
    pruneFolders(TREE);
    applyDeletes(TREE);
    applyNames(TREE);
    recount(TREE);
    initTree();
    render();
    setBase(2);
    updateBar();
    document.getElementById('bar').textContent += '（载入 '+((Date.now()-t0)/1000).toFixed(1)+' 秒）';
  }catch(e){
    document.getElementById('bar').textContent='数据解压失败：'+e.message;
    console.error(e);
  }
}
boot();
</script></body></html>"""
    html = html.replace("__CSS__", lcss).replace("__LEAFLET__", ljs).replace("__DATA__", payload)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print("生成：%s（%.1f MB）" % (OUT, os.path.getsize(OUT) / 1024 / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
