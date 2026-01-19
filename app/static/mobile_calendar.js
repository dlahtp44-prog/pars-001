(function(){
  const init = window.__CAL_INIT__ || {};
  let year = Number(init.year) || new Date().getFullYear();
  let month = Number(init.month) || (new Date().getMonth()+1);
  let selected = null;
  let monthItems = {};

  const grid = document.getElementById("mcalGrid");
  const sub = document.getElementById("mcalSub");

  const selectedEl = document.getElementById("mSelectedDate");
  const msgEl = document.getElementById("mMsg");
  const operatorEl = document.getElementById("mOperator");
  const inputs = [
    document.getElementById("mLine1"),
    document.getElementById("mLine2"),
    document.getElementById("mLine3"),
    document.getElementById("mLine4"),
  ];

  function pad(n){ return String(n).padStart(2,"0"); }
  function ymd(y,m,d){ return `${y}-${pad(m)}-${pad(d)}`; }

  function setMsg(text, ok=true){
    msgEl.textContent = text || "";
    msgEl.style.color = ok ? "" : "var(--danger, #ff6b6b)";
  }

  async function apiGetMonth(y,m){
    const r = await fetch(`/api/calendar/month?year=${y}&month=${m}`);
    const j = await r.json();
    if(!j.ok) throw new Error(j.detail || "month load failed");
    return j.items || {};
  }

  async function apiGetDay(dateStr){
    const r = await fetch(`/api/calendar/day?date=${encodeURIComponent(dateStr)}`);
    const j = await r.json();
    if(!j.ok) throw new Error(j.detail || "day load failed");
    return j.lines || ["","","",""];
  }

  async function apiSave(dateStr, lines, operator){
    const fd = new FormData();
    fd.append("date", dateStr);
    fd.append("line1", lines[0] || "");
    fd.append("line2", lines[1] || "");
    fd.append("line3", lines[2] || "");
    fd.append("line4", lines[3] || "");
    fd.append("operator", operator || "");
    const r = await fetch(`/api/calendar/save`, { method:"POST", body: fd });
    const j = await r.json();
    if(!j.ok) throw new Error(j.detail || "save failed");
    return j.lines || lines;
  }

  async function apiDelete(dateStr){
    const fd = new FormData();
    fd.append("date", dateStr);
    const r = await fetch(`/api/calendar/delete`, { method:"POST", body: fd });
    const j = await r.json();
    if(!j.ok) throw new Error(j.detail || "delete failed");
    return true;
  }

  function monthLabel(y,m){ return `${y}년 ${m}월`; }

  function render(){
    sub.textContent = monthLabel(year, month);

    const first = new Date(year, month-1, 1);
    const firstDow = first.getDay();
    const daysInMonth = new Date(year, month, 0).getDate();
    const prevDays = new Date(year, month-1, 0).getDate();
    const startPrev = prevDays - firstDow + 1;

    const dows = ["일","월","화","수","목","금","토"];
    grid.innerHTML = "";
    for(const d of dows){
      const el = document.createElement("div");
      el.className = "mcal-dow";
      el.textContent = d;
      grid.appendChild(el);
    }

    for(let i=0;i<42;i++){
      const cell = document.createElement("div");
      cell.className = "mcal-cell";

      let cellY=year, cellM=month, cellD=0;
      let isOut=false;

      if(i < firstDow){
        isOut=true;
        cellM = month-1; cellY = year;
        if(cellM<=0){ cellM=12; cellY=year-1; }
        cellD = startPrev + i;
      } else if(i >= firstDow + daysInMonth){
        isOut=true;
        cellM = month+1; cellY = year;
        if(cellM>=13){ cellM=1; cellY=year+1; }
        cellD = (i - (firstDow + daysInMonth)) + 1;
      } else {
        cellD = (i - firstDow) + 1;
      }

      const dateStr = ymd(cellY, cellM, cellD);
      if(isOut) cell.classList.add("is-out");
      if(selected === dateStr) cell.classList.add("is-selected");

      const head = document.createElement("div");
      head.className = "mcal-day";
      head.innerHTML = `<div class="mcal-day-num">${cellD}</div>`;
      cell.appendChild(head);

      const linesWrap = document.createElement("div");
      linesWrap.className = "mcal-lines";
      const lines = monthItems[dateStr] || ["","","",""];
      for(let k=0;k<4;k++){
        const line = document.createElement("div");
        line.className = "mcal-line" + ((lines[k]||"").trim()? "" : " empty");
        line.textContent = (lines[k]||"").trim() || "·";
        linesWrap.appendChild(line);
      }
      cell.appendChild(linesWrap);

      cell.addEventListener("click", async ()=>{
        selected = dateStr;
        selectedEl.textContent = dateStr;
        setMsg("");
        try{
          const dayLines = await apiGetDay(dateStr);
          for(let k=0;k<4;k++) inputs[k].value = dayLines[k] || "";
        }catch(e){
          inputs.forEach(i=> i.value="");
          setMsg(String(e.message||e), false);
        }
        render();
      });

      grid.appendChild(cell);
    }
  }

  async function loadMonth(){
    setMsg("불러오는 중...");
    try{
      monthItems = await apiGetMonth(year, month);
      setMsg("");
      render();

      if(!selected){
        const t = new Date();
        selected = ymd(t.getFullYear(), t.getMonth()+1, t.getDate());
      }
      selectedEl.textContent = selected || "-";
      if(selected){
        try{
          const dayLines = await apiGetDay(selected);
          for(let k=0;k<4;k++) inputs[k].value = dayLines[k] || "";
        }catch{}
      }
      render();
    }catch(e){
      setMsg(String(e.message||e), false);
      render();
    }
  }

  document.getElementById("mPrevBtn").addEventListener("click", ()=>{
    month -= 1;
    if(month<=0){ month=12; year-=1; }
    loadMonth();
  });
  document.getElementById("mNextBtn").addEventListener("click", ()=>{
    month += 1;
    if(month>=13){ month=1; year+=1; }
    loadMonth();
  });
  document.getElementById("mTodayBtn").addEventListener("click", ()=>{
    const t = new Date();
    year = t.getFullYear();
    month = t.getMonth()+1;
    selected = ymd(year, month, t.getDate());
    loadMonth();
  });

  document.getElementById("mSaveBtn").addEventListener("click", async ()=>{
    if(!selected){ setMsg("날짜를 선택하세요.", false); return; }
    const lines = inputs.map(i=> (i.value||"").trim());
    try{
      const saved = await apiSave(selected, lines, operatorEl.value || "");
      monthItems[selected] = saved;
      setMsg("저장 완료");
      render();
    }catch(e){
      setMsg(String(e.message||e), false);
    }
  });

  document.getElementById("mDeleteBtn").addEventListener("click", async ()=>{
    if(!selected){ setMsg("날짜를 선택하세요.", false); return; }
    try{
      await apiDelete(selected);
      delete monthItems[selected];
      inputs.forEach(i=> i.value="");
      setMsg("삭제 완료");
      render();
    }catch(e){
      setMsg(String(e.message||e), false);
    }
  });

  loadMonth();
})();