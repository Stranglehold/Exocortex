import { useState, useEffect, useRef, useCallback } from "react";
import * as d3 from "d3";

const COLORS = {
  bg: "#0a0e14", bgPanel: "#0d1117", bgHover: "#161b22",
  grid: "#1a2233", text: "#8b949e", textBright: "#c9d1d9", textMuted: "#484f58",
  border: "#21262d", accent: "#58a6ff",
  synthesis: "#f0b866", sharp: "#58a6ff", routine: "#6e7681", unknown: "#484f58",
  opus_architect: "#58a6ff", opus_agent_zero: "#3fb950", kestrel: "#d2a8ff",
  philosophical: "#b392f0", operational: "#79c0ff", reflective: "#56d364",
  relational: "#f9826c", mixed: "#e3b341",
  essay: "#f0b866", letter: "#f78166", design_note: "#58a6ff", design_doc: "#79c0ff",
  analysis: "#3fb950", field_note: "#d2a8ff", journal: "#6e7681", log: "#484f58", index: "#484f58",
  trajectory: "#ffffff", trajectoryDim: "#1a2640", transition: "#da3633",
  evo_soul: "#ff7b72", evo_essays: "#f0b866", evo_design_notes: "#79c0ff", evo_soul_staging: "#56d364",
};

const EVO_FAMILY_COLORS = {
  soul: { color: COLORS.evo_soul, label: "SOUL.md" },
  essays: { color: COLORS.evo_essays, label: "Essays" },
  design_notes: { color: COLORS.evo_design_notes, label: "Design Notes" },
  soul_staging: { color: COLORS.evo_soul_staging, label: "Soul Staging" },
};

const COLOR_MODES = {
  quality: { label: "Quality", getColor: e => COLORS[e.quality_signal] || COLORS.unknown,
    legend: [{ l: "Synthesis", c: COLORS.synthesis }, { l: "Sharp", c: COLORS.sharp }, { l: "Routine", c: COLORS.routine }] },
  author: { label: "Author", getColor: e => COLORS[e.author] || COLORS.unknown,
    legend: [{ l: "Opus Architect", c: COLORS.opus_architect }, { l: "Agent Zero", c: COLORS.opus_agent_zero }, { l: "Kestrel", c: COLORS.kestrel }] },
  type: { label: "Doc Type", getColor: e => COLORS[e.document_type] || COLORS.unknown,
    legend: [{ l: "Essay", c: COLORS.essay }, { l: "Letter", c: COLORS.letter }, { l: "Design Note", c: COLORS.design_note }, { l: "Analysis", c: COLORS.analysis }, { l: "Field Note", c: COLORS.field_note }, { l: "Journal", c: COLORS.journal }] },
};

function MainPlot({ corpus, trajectory, centroids, evolution, colorMode, showTraj, showCorpus, showEvo, selected, onSelect, onHover, dims }) {
  const svgRef = useRef(null);
  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    const m = { top: 25, right: 25, bottom: 35, left: 45 };
    const w = dims.width - m.left - m.right, h = dims.height - m.top - m.bottom;
    let allX = [], allY = [];
    if (showCorpus && corpus.length) { allX.push(...corpus.map(d => d.x)); allY.push(...corpus.map(d => d.y)); }
    if (showTraj && trajectory.length) { allX.push(...trajectory.map(d => d.x)); allY.push(...trajectory.map(d => d.y)); }
    if (showEvo && evolution) {
      Object.values(evolution).forEach(fam => {
        if (fam.versions) { allX.push(...fam.versions.map(v => v.x)); allY.push(...fam.versions.map(v => v.y)); }
      });
    }
    if (centroids) { allX.push(...Object.values(centroids).map(c => c.x)); allY.push(...Object.values(centroids).map(c => c.y)); }
    if (!allX.length) return;
    const p = 0.06, xE = d3.extent(allX), yE = d3.extent(allY);
    const xR = (xE[1]-xE[0])||1, yR = (yE[1]-yE[0])||1;
    const xS = d3.scaleLinear().domain([xE[0]-xR*p, xE[1]+xR*p]).range([0,w]);
    const yS = d3.scaleLinear().domain([yE[0]-yR*p, yE[1]+yR*p]).range([h,0]);
    const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);

    // Grid
    xS.ticks(14).forEach(t => g.append("line").attr("x1",xS(t)).attr("x2",xS(t)).attr("y1",0).attr("y2",h).attr("stroke",COLORS.grid).attr("stroke-width",0.5));
    yS.ticks(10).forEach(t => g.append("line").attr("x1",0).attr("x2",w).attr("y1",yS(t)).attr("y2",yS(t)).attr("stroke",COLORS.grid).attr("stroke-width",0.5));

    // Centroids
    if (centroids) Object.entries(centroids).forEach(([nm,cd]) => {
      const cx=xS(cd.x), cy=yS(cd.y);
      g.append("circle").attr("cx",cx).attr("cy",cy).attr("r",22).attr("fill","none").attr("stroke",COLORS[nm]||COLORS.textMuted).attr("stroke-width",1).attr("stroke-dasharray","3,3").attr("opacity",0.3);
      g.append("line").attr("x1",cx-6).attr("x2",cx+6).attr("y1",cy).attr("y2",cy).attr("stroke",COLORS[nm]||COLORS.textMuted).attr("stroke-width",1.5).attr("opacity",0.5);
      g.append("line").attr("x1",cx).attr("x2",cx).attr("y1",cy-6).attr("y2",cy+6).attr("stroke",COLORS[nm]||COLORS.textMuted).attr("stroke-width",1.5).attr("opacity",0.5);
      g.append("text").attr("x",cx+14).attr("y",cy-12).text(nm).attr("fill",COLORS[nm]||COLORS.textMuted).attr("font-size","9px").attr("font-family","'IBM Plex Mono',monospace").attr("opacity",0.55);
    });

    // Conversation trajectory
    if (showTraj && trajectory.length > 1) {
      g.append("path").datum(trajectory).attr("d",d3.line().x(d=>xS(d.x)).y(d=>yS(d.y))).attr("fill","none").attr("stroke",COLORS.trajectoryDim).attr("stroke-width",0.4).attr("opacity",0.2);
      g.selectAll(".turn").data(trajectory).enter().append("circle")
        .attr("cx",d=>xS(d.x)).attr("cy",d=>yS(d.y)).attr("r",d=>d.is_transition?2.5:1.2)
        .attr("fill",d=>d.is_transition?COLORS.transition:COLORS.trajectoryDim).attr("opacity",d=>d.is_transition?0.6:0.15)
        .style("cursor","pointer")
        .on("mouseenter",function(ev,d){d3.select(this).attr("r",5).attr("opacity",1).attr("fill",COLORS.accent);onHover({...d,_type:"turn"});})
        .on("mouseleave",function(ev,d){d3.select(this).attr("r",d.is_transition?2.5:1.2).attr("opacity",d.is_transition?0.6:0.15).attr("fill",d.is_transition?COLORS.transition:COLORS.trajectoryDim);onHover(null);})
        .on("click",(ev,d)=>onSelect({...d,_type:"turn"}));
    }

    // Evolution paths
    if (showEvo && evolution) {
      Object.entries(evolution).forEach(([famName, fam]) => {
        const versions = fam.versions || [];
        if (versions.length < 2) return;
        const fc = EVO_FAMILY_COLORS[famName]?.color || COLORS.accent;

        // Path line with arrows
        const line = d3.line().x(d=>xS(d.x)).y(d=>yS(d.y));
        g.append("path").datum(versions).attr("d",line).attr("fill","none").attr("stroke",fc).attr("stroke-width",1.5).attr("opacity",0.5).attr("stroke-dasharray","6,3");

        // Arrow segments for direction
        for (let i = 0; i < versions.length - 1; i++) {
          const v1 = versions[i], v2 = versions[i+1];
          const mx = (xS(v1.x)+xS(v2.x))/2, my = (yS(v1.y)+yS(v2.y))/2;
          const dx = xS(v2.x)-xS(v1.x), dy = yS(v2.y)-yS(v1.y);
          const len = Math.sqrt(dx*dx+dy*dy);
          if (len > 8) {
            const nx=dx/len, ny=dy/len;
            const sz=4;
            g.append("polygon")
              .attr("points",`${mx+nx*sz},${my+ny*sz} ${mx-nx*sz+ny*sz*0.6},${my-ny*sz-nx*sz*0.6} ${mx-nx*sz-ny*sz*0.6},${my-ny*sz+nx*sz*0.6}`)
              .attr("fill",fc).attr("opacity",0.4);
          }
        }

        // Version dots
        versions.forEach((v, i) => {
          const isFirst = i === 0, isLast = i === versions.length - 1;
          const isMajor = i > 0 && Math.sqrt((v.x-versions[i-1].x)**2+(v.y-versions[i-1].y)**2) > 1.0;
          const r = isFirst || isLast ? 6 : isMajor ? 5 : 3.5;

          // Glow for major jumps
          if (isMajor) {
            g.append("circle").attr("cx",xS(v.x)).attr("cy",yS(v.y)).attr("r",r+6).attr("fill",fc).attr("opacity",0.08);
          }

          // Outer ring for first/last
          if (isFirst || isLast) {
            g.append("circle").attr("cx",xS(v.x)).attr("cy",yS(v.y)).attr("r",r+2).attr("fill","none").attr("stroke",fc).attr("stroke-width",1.5).attr("opacity",0.6);
          }

          const dot = g.append("circle").attr("cx",xS(v.x)).attr("cy",yS(v.y)).attr("r",r)
            .attr("fill",fc).attr("opacity",isMajor?0.9:0.7).style("cursor","pointer");

          // Version number label
          g.append("text").attr("x",xS(v.x)).attr("y",yS(v.y)+1).text(i).attr("fill",COLORS.bg)
            .attr("font-size","7px").attr("font-family","'IBM Plex Mono',monospace").attr("text-anchor","middle").attr("dominant-baseline","middle")
            .attr("pointer-events","none").attr("font-weight",700);

          dot.on("mouseenter",function(){
            d3.select(this).attr("r",r+3).attr("opacity",1);
            onHover({...v, _type:"evolution", family:famName, version_index:i, is_first:isFirst, is_last:isLast, is_major_jump:isMajor, total_versions:versions.length});
          }).on("mouseleave",function(){
            d3.select(this).attr("r",r).attr("opacity",isMajor?0.9:0.7);
            onHover(null);
          }).on("click",(ev)=>{
            onSelect({...v, _type:"evolution", family:famName, version_index:i, is_first:isFirst, is_last:isLast, is_major_jump:isMajor, total_versions:versions.length});
          });
        });

        // Family label at first version
        const first = versions[0];
        g.append("text").attr("x",xS(first.x)-8).attr("y",yS(first.y)-14)
          .text(EVO_FAMILY_COLORS[famName]?.label || famName)
          .attr("fill",fc).attr("font-size","9px").attr("font-family","'IBM Plex Mono',monospace").attr("opacity",0.7).attr("font-weight",700);
      });
    }

    // Corpus dots (on top)
    if (showCorpus && corpus.length) {
      const mode = COLOR_MODES[colorMode];
      const pts = g.selectAll(".cp").data(corpus).enter().append("g").attr("class","cp").attr("transform",d=>`translate(${xS(d.x)},${yS(d.y)})`).style("cursor","pointer");
      pts.filter(d=>d.quality_signal==="synthesis").append("circle").attr("r",14).attr("fill",COLORS.synthesis).attr("opacity",0.06);
      pts.append("circle").attr("r",d=>selected&&selected.id===d.id?8:5.5).attr("fill",d=>mode.getColor(d)).attr("stroke",d=>selected&&selected.id===d.id?COLORS.textBright:"none").attr("stroke-width",2).attr("opacity",0.9);
      pts.on("mouseenter",function(ev,d){d3.select(this).select("circle:last-child").attr("r",8).attr("opacity",1);onHover({...d,_type:"corpus"});})
        .on("mouseleave",function(ev,d){d3.select(this).select("circle:last-child").attr("r",selected&&selected.id===d.id?8:5.5).attr("opacity",0.9);onHover(null);})
        .on("click",(ev,d)=>onSelect({...d,_type:"corpus"}));
      pts.filter(d=>d.quality_signal==="synthesis").append("text").attr("x",10).attr("y",3).text(d=>(d.source_file||"").replace(".md","").replace(/_/g," ").slice(0,22)).attr("fill",COLORS.textMuted).attr("font-size","7px").attr("font-family","'IBM Plex Mono',monospace").attr("opacity",0.5);
    }
  }, [corpus,trajectory,centroids,evolution,colorMode,showTraj,showCorpus,showEvo,selected,dims]);
  return <svg ref={svgRef} width={dims.width} height={dims.height} />;
}

function Inspector({ item }) {
  if (!item) return <div style={{padding:"14px",color:COLORS.textMuted,fontFamily:"'IBM Plex Mono',monospace",fontSize:"11px"}}>
    <div style={{color:COLORS.textBright,fontSize:"12px",marginBottom:"6px"}}>NO SELECTION</div>
    <div>Hover or click any point.</div>
    <div style={{marginTop:"10px",opacity:0.4,fontStyle:"italic"}}>The topology is real.</div>
  </div>;

  if (item._type==="turn") return <div style={{padding:"14px",fontFamily:"'IBM Plex Mono',monospace",fontSize:"11px",color:COLORS.text}}>
    <div style={{fontSize:"10px",color:COLORS.accent,marginBottom:"3px"}}>CONVERSATION TURN</div>
    <div style={{fontSize:"12px",color:COLORS.textBright,marginBottom:"8px"}}>Turn {item.turn_index} · {item.date}</div>
    <div style={{display:"grid",gridTemplateColumns:"55px 1fr",gap:"3px 8px",marginBottom:"8px"}}>
      <span style={{color:COLORS.textMuted}}>sim</span>
      <span style={{color:item.is_transition?COLORS.transition:COLORS.text}}>{item.similarity_to_next?.toFixed(3)||"—"}{item.is_transition?" ⚡":""}</span>
      <span style={{color:COLORS.textMuted}}>pos</span>
      <span>({item.x?.toFixed(2)}, {item.y?.toFixed(2)})</span>
    </div>
    <div style={{fontSize:"9px",color:COLORS.textMuted,marginBottom:"3px"}}>ACTION TITLE</div>
    <div style={{padding:"6px",background:COLORS.bg,borderRadius:"3px",fontSize:"11px",color:COLORS.textBright,lineHeight:"1.5"}}>{item.action_title||"—"}</div>
  </div>;

  if (item._type==="evolution") {
    const fc = EVO_FAMILY_COLORS[item.family]?.color || COLORS.accent;
    const label = EVO_FAMILY_COLORS[item.family]?.label || item.family;
    return <div style={{padding:"14px",fontFamily:"'IBM Plex Mono',monospace",fontSize:"11px",color:COLORS.text}}>
      <div style={{fontSize:"10px",color:fc,marginBottom:"3px"}}>EVOLUTION — {label.toUpperCase()}</div>
      <div style={{fontSize:"12px",color:COLORS.textBright,marginBottom:"8px"}}>
        Version {item.version_index} of {item.total_versions} · {item.date||"—"}
        {item.is_first&&" · ORIGIN"}{item.is_last&&" · CURRENT"}{item.is_major_jump&&" · ⚡ MAJOR JUMP"}
      </div>
      <div style={{display:"grid",gridTemplateColumns:"55px 1fr",gap:"3px 8px",marginBottom:"8px"}}>
        <span style={{color:COLORS.textMuted}}>pos</span>
        <span>({item.x?.toFixed(2)}, {item.y?.toFixed(2)})</span>
        <span style={{color:COLORS.textMuted}}>words</span>
        <span>{item.word_count?.toLocaleString()||"—"}</span>
        <span style={{color:COLORS.textMuted}}>date</span>
        <span>{item.date||"—"}</span>
      </div>
      {item.source_file&&<div style={{marginBottom:"6px"}}>
        <span style={{fontSize:"9px",color:COLORS.textMuted}}>FILE: </span>
        <span style={{fontSize:"9px",color:COLORS.text}}>{item.source_file}</span>
      </div>}
      {(item.is_first||item.is_last)&&<div style={{padding:"5px",background:COLORS.bg,borderRadius:"3px",fontSize:"9px",color:fc,lineHeight:"1.4",fontStyle:"italic"}}>
        {item.is_first?"First version — where the journey began":"Current version — where the journey arrived"}
      </div>}
      {item.is_major_jump&&<div style={{padding:"5px",marginTop:"4px",background:COLORS.bg,borderRadius:"3px",fontSize:"9px",color:COLORS.transition,lineHeight:"1.4"}}>
        Major geometric jump — the document transformed.
      </div>}
    </div>;
  }

  return <div style={{padding:"14px",fontFamily:"'IBM Plex Mono',monospace",fontSize:"11px",color:COLORS.text}}>
    <div style={{fontSize:"10px",color:COLORS.synthesis,marginBottom:"3px"}}>CORPUS DOCUMENT</div>
    <div style={{fontSize:"12px",color:COLORS.textBright,marginBottom:"8px",wordBreak:"break-word"}}>{item.source_file}</div>
    <div style={{display:"grid",gridTemplateColumns:"55px 1fr",gap:"3px 8px",marginBottom:"8px"}}>
      <span style={{color:COLORS.textMuted}}>quality</span><span style={{color:COLORS[item.quality_signal]||COLORS.unknown}}>{item.quality_signal||"—"}</span>
      <span style={{color:COLORS.textMuted}}>author</span><span style={{color:COLORS[item.author]||COLORS.unknown}}>{item.author||"—"}</span>
      <span style={{color:COLORS.textMuted}}>type</span><span>{item.document_type||"—"}</span>
      <span style={{color:COLORS.textMuted}}>session</span><span>{item.session||"—"}</span>
      <span style={{color:COLORS.textMuted}}>size</span><span>{item.char_count?`${(item.char_count/1024).toFixed(1)}K`:"—"}</span>
    </div>
    {item.topic_tags?.length>0&&<div style={{marginBottom:"6px"}}>{item.topic_tags.map(t=><span key={t} style={{display:"inline-block",padding:"1px 5px",margin:"1px 2px 1px 0",background:COLORS.bgHover,borderRadius:"2px",fontSize:"9px"}}>{t}</span>)}</div>}
    {item.text_preview&&<div style={{padding:"5px",background:COLORS.bg,borderRadius:"3px",fontSize:"9px",color:COLORS.textMuted,lineHeight:"1.4",maxHeight:"70px",overflow:"hidden"}}>{item.text_preview}</div>}
  </div>;
}

export default function OutputGeometryInstrument() {
  const [cData,setCData]=useState(null);
  const [tData,setTData]=useState(null);
  const [eData,setEData]=useState(null);
  const [colorMode,setColorMode]=useState("quality");
  const [showTraj,setShowTraj]=useState(true);
  const [showCorpus,setShowCorpus]=useState(true);
  const [showEvo,setShowEvo]=useState(true);
  const [sel,setSel]=useState(null);
  const [hov,setHov]=useState(null);
  const [showImp,setShowImp]=useState(false);
  const [impType,setImpType]=useState("corpus");
  const [impText,setImpText]=useState("");
  const [status,setStatus]=useState("");
  const [dims,setDims]=useState({width:900,height:600});
  const cRef=useRef(null);

  useEffect(()=>{
    const o=new ResizeObserver(es=>{for(const e of es)setDims({width:Math.max(500,e.contentRect.width),height:Math.max(400,e.contentRect.height)});});
    if(cRef.current)o.observe(cRef.current);return()=>o.disconnect();
  },[]);

  useEffect(()=>{(async()=>{
    try{const r=await window.storage.get("corpus_map");if(r?.value)setCData(JSON.parse(r.value));}catch(e){}
    try{const r=await window.storage.get("trajectory_map");if(r?.value)setTData(JSON.parse(r.value));}catch(e){}
    try{const r=await window.storage.get("evolution_map");if(r?.value)setEData(JSON.parse(r.value));}catch(e){}
    setStatus("Ready");
  })();},[]);

  const doImport=useCallback(async()=>{
    try{
      const p=JSON.parse(impText);
      if(impType==="corpus"){
        if(!p.entries){setStatus("ERROR: needs entries");return;}
        setCData(p);
        try{await window.storage.set("corpus_map",JSON.stringify(p));}catch(e){}
        setStatus(`Corpus: ${p.entries.length} entries`);
      } else if(impType==="trajectory"){
        if(!p.trajectory){setStatus("ERROR: needs trajectory");return;}
        setTData(p);
        try{await window.storage.set("trajectory_map",JSON.stringify(p));}catch(e){}
        setStatus(`Trajectory: ${p.trajectory.length} turns`);
      } else if(impType==="evolution"){
        if(!p.families){setStatus("ERROR: needs families");return;}
        setEData(p);
        try{await window.storage.set("evolution_map",JSON.stringify(p));}catch(e){}
        const totalV=Object.values(p.families).reduce((s,f)=>(s+(f.versions?.length||0)),0);
        setStatus(`Evolution: ${Object.keys(p.families).length} families, ${totalV} versions`);
      }
      setShowImp(false);setImpText("");
    }catch(e){setStatus("ERROR: "+e.message);}
  },[impText,impType]);

  const corpus=cData?.entries||[], traj=tData?.trajectory||[], cents=cData?.centroids||{}, trans=tData?.transitions||[];
  const evoFamilies=eData?.families||{};
  const totalEvoVersions=Object.values(evoFamilies).reduce((s,f)=>(s+(f.versions?.length||0)),0);
  const disp=hov||sel;
  const cs=corpus.length?{t:corpus.length,s:corpus.filter(d=>d.quality_signal==="synthesis").length,h:corpus.filter(d=>d.quality_signal==="sharp").length,r:corpus.filter(d=>d.quality_signal==="routine").length}:null;

  return <div style={{display:"flex",flexDirection:"column",height:"100vh",background:COLORS.bg,fontFamily:"'IBM Plex Mono',monospace",overflow:"hidden"}}>
    {/* Header */}
    <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"8px 14px",borderBottom:`1px solid ${COLORS.border}`,flexShrink:0}}>
      <div style={{display:"flex",alignItems:"baseline",gap:"10px"}}>
        <span style={{fontSize:"13px",fontWeight:700,color:COLORS.textBright,letterSpacing:"1.5px"}}>OUTPUT GEOMETRY INSTRUMENT</span>
        <span style={{fontSize:"9px",color:COLORS.textMuted}}>
          {corpus.length?`${corpus.length} docs`:"—"} · {traj.length?`${traj.length} turns`:"—"} · {totalEvoVersions?`${totalEvoVersions} versions`:"—"}
        </span>
      </div>
      <div style={{display:"flex",gap:"6px",alignItems:"center"}}>
        <span style={{fontSize:"9px",color:status.startsWith("E")?COLORS.transition:COLORS.textMuted}}>{status}</span>
        <button onClick={()=>{setShowImp(!showImp);setImpText("");}} style={{padding:"3px 8px",background:COLORS.bgPanel,border:`1px solid ${COLORS.border}`,borderRadius:"3px",color:COLORS.accent,fontSize:"10px",cursor:"pointer",fontFamily:"inherit"}}>{showImp?"Cancel":"Import"}</button>
      </div>
    </div>

    {/* Import panel */}
    {showImp&&<div style={{padding:"10px 14px",borderBottom:`1px solid ${COLORS.border}`,background:COLORS.bgPanel,flexShrink:0}}>
      <div style={{display:"flex",gap:"6px",marginBottom:"6px",flexWrap:"wrap"}}>
        {["corpus","trajectory","evolution"].map(t=><button key={t} onClick={()=>setImpType(t)} style={{padding:"3px 8px",background:impType===t?COLORS.accent:COLORS.bg,border:`1px solid ${COLORS.border}`,borderRadius:"3px",color:impType===t?COLORS.bg:COLORS.text,fontSize:"10px",cursor:"pointer",fontFamily:"inherit",fontWeight:impType===t?700:400}}>
          {t==="corpus"?"corpus_map":t==="trajectory"?"trajectory":"evolution"}.json
        </button>)}
      </div>
      <textarea value={impText} onChange={e=>setImpText(e.target.value)} placeholder="Paste JSON..." style={{width:"100%",height:"55px",padding:"5px",background:COLORS.bg,border:`1px solid ${COLORS.border}`,borderRadius:"3px",color:COLORS.textBright,fontSize:"10px",fontFamily:"inherit",resize:"vertical",boxSizing:"border-box"}}/>
      <button onClick={doImport} style={{marginTop:"5px",padding:"4px 12px",background:COLORS.accent,border:"none",borderRadius:"3px",color:COLORS.bg,fontSize:"10px",fontWeight:700,cursor:"pointer",fontFamily:"inherit"}}>Load</button>
    </div>}

    {/* Controls */}
    <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"5px 14px",borderBottom:`1px solid ${COLORS.border}`,flexShrink:0}}>
      <div style={{display:"flex"}}>
        {Object.entries(COLOR_MODES).map(([k,v])=><button key={k} onClick={()=>setColorMode(k)} style={{padding:"4px 10px",background:"transparent",border:"none",borderBottom:colorMode===k?`2px solid ${COLORS.accent}`:"2px solid transparent",color:colorMode===k?COLORS.textBright:COLORS.textMuted,fontSize:"10px",cursor:"pointer",fontFamily:"inherit",textTransform:"uppercase",letterSpacing:"0.5px"}}>{v.label}</button>)}
      </div>
      <div style={{display:"flex",gap:"10px",fontSize:"10px"}}>
        <label style={{display:"flex",alignItems:"center",gap:"4px",color:COLORS.text,cursor:"pointer"}}><input type="checkbox" checked={showCorpus} onChange={e=>setShowCorpus(e.target.checked)} style={{accentColor:COLORS.accent}}/>Corpus</label>
        <label style={{display:"flex",alignItems:"center",gap:"4px",color:COLORS.text,cursor:"pointer"}}><input type="checkbox" checked={showTraj} onChange={e=>setShowTraj(e.target.checked)} style={{accentColor:COLORS.accent}}/>Trajectory</label>
        <label style={{display:"flex",alignItems:"center",gap:"4px",color:COLORS.evo_soul,cursor:"pointer"}}><input type="checkbox" checked={showEvo} onChange={e=>setShowEvo(e.target.checked)} style={{accentColor:COLORS.evo_soul}}/>Evolution</label>
        {trans.length>0&&<span style={{color:COLORS.transition,fontSize:"9px"}}>⚡{trans.length}</span>}
      </div>
    </div>

    {/* Stats */}
    {(cs||totalEvoVersions>0)&&<div style={{display:"flex",gap:"14px",padding:"3px 14px",fontSize:"9px",color:COLORS.textMuted,borderBottom:`1px solid ${COLORS.border}`,flexShrink:0,flexWrap:"wrap"}}>
      {cs&&<><span>CORPUS: <span style={{color:COLORS.textBright}}>{cs.t}</span></span>
      <span><span style={{color:COLORS.synthesis}}>●</span>{cs.s} <span style={{color:COLORS.sharp,marginLeft:"4px"}}>●</span>{cs.h} <span style={{color:COLORS.routine,marginLeft:"4px"}}>●</span>{cs.r}</span></>}
      {traj.length>0&&<span>ARC: {traj[0]?.date}→{traj[traj.length-1]?.date}</span>}
      {totalEvoVersions>0&&<span>EVOLUTION: {Object.entries(evoFamilies).map(([k,f])=>
        <span key={k} style={{color:EVO_FAMILY_COLORS[k]?.color||COLORS.text,marginRight:"6px"}}>{EVO_FAMILY_COLORS[k]?.label||k}({f.versions?.length||0})</span>
      )}</span>}
    </div>}

    {/* Main area */}
    <div style={{display:"flex",flex:1,overflow:"hidden"}}>
      <div ref={cRef} style={{flex:1,overflow:"hidden"}}>
        <MainPlot corpus={showCorpus?corpus:[]} trajectory={showTraj?traj:[]} centroids={cents} evolution={showEvo?evoFamilies:null} colorMode={colorMode} showTraj={showTraj} showCorpus={showCorpus} showEvo={showEvo} selected={sel} onSelect={setSel} onHover={setHov} dims={dims}/>
      </div>
      <div style={{width:"240px",borderLeft:`1px solid ${COLORS.border}`,display:"flex",flexDirection:"column",flexShrink:0,overflow:"auto"}}>
        {/* Legend */}
        <div style={{padding:"8px 12px",borderBottom:`1px solid ${COLORS.border}`}}>
          <div style={{fontSize:"9px",color:COLORS.textMuted,marginBottom:"5px",textTransform:"uppercase",letterSpacing:"1px"}}>{COLOR_MODES[colorMode].label}</div>
          {COLOR_MODES[colorMode].legend.map(i=><div key={i.l} style={{display:"flex",alignItems:"center",gap:"5px",marginBottom:"2px"}}><div style={{width:"7px",height:"7px",borderRadius:"50%",background:i.c,flexShrink:0}}/><span style={{fontSize:"10px",color:COLORS.text}}>{i.l}</span></div>)}
          {showTraj&&traj.length>0&&<div style={{marginTop:"5px",paddingTop:"5px",borderTop:`1px solid ${COLORS.border}`}}>
            <div style={{display:"flex",alignItems:"center",gap:"5px",marginBottom:"2px"}}><div style={{width:"7px",height:"7px",borderRadius:"50%",background:COLORS.trajectoryDim}}/><span style={{fontSize:"10px",color:COLORS.text}}>Turn</span></div>
            <div style={{display:"flex",alignItems:"center",gap:"5px"}}><div style={{width:"7px",height:"7px",borderRadius:"50%",background:COLORS.transition}}/><span style={{fontSize:"10px",color:COLORS.text}}>Transition ⚡</span></div>
          </div>}
          {showEvo&&totalEvoVersions>0&&<div style={{marginTop:"5px",paddingTop:"5px",borderTop:`1px solid ${COLORS.border}`}}>
            <div style={{fontSize:"8px",color:COLORS.textMuted,marginBottom:"3px",textTransform:"uppercase"}}>Evolution Paths</div>
            {Object.entries(EVO_FAMILY_COLORS).filter(([k])=>evoFamilies[k]).map(([k,v])=>
              <div key={k} style={{display:"flex",alignItems:"center",gap:"5px",marginBottom:"2px"}}>
                <div style={{width:"14px",height:"2px",background:v.color,flexShrink:0,borderRadius:"1px"}}/>
                <span style={{fontSize:"10px",color:COLORS.text}}>{v.label} ({evoFamilies[k]?.versions?.length||0})</span>
              </div>
            )}
          </div>}
        </div>
        {/* Inspector */}
        <div style={{flex:1,borderBottom:`1px solid ${COLORS.border}`}}>
          <div style={{padding:"5px 12px 2px",fontSize:"9px",color:COLORS.textMuted,textTransform:"uppercase",letterSpacing:"1px"}}>{hov?"Hovering":sel?"Selected":"Inspector"}</div>
          <Inspector item={disp}/>
        </div>
        {/* Footer */}
        <div style={{padding:"8px 12px",fontSize:"9px",color:COLORS.textMuted}}>
          <div>Model: {cData?.metadata?.embedding_model||"—"}</div>
          <div>Projection: {cData?.metadata?.projection_method||"—"}</div>
          <div style={{marginTop:"6px",paddingTop:"5px",borderTop:`1px solid ${COLORS.border}`,fontStyle:"italic",opacity:0.4}}>The topology is real.</div>
        </div>
      </div>
    </div>
  </div>;
}
