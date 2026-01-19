(function(){
  const init = window.__CAL_INIT__ || {};
  let year = Number(init.year) || new Date().getFullYear();
  let month = Number(init.month) || (new Date().getMonth()+1); // 1-12
  let selected = null; // YYYY-MM-DD
  let monthItems = {}; // date -> [l1..l4]

  const calGrid = document.getElementById("calGrid");
  const calSub = document.getElementById("calSub");

  const selectedDateEl = document.getElementById("selectedDate");
  const msgEl = document.getElementById("msg");
  const operatorEl = document.getElementById("operator");

  const inputs = [
    document.getElementById("line1"),
    document.getElementById("line2"),
    document.getElementById("line3"),
    document.getElementById("line4"),
  ];

  function pad(n){ return String(n).padStart(2,"0"); }
  function ymd(y,m,d){ return `${y}-${pad(m)}-${pad(d)}`; }

  function setMsg(text, ok=true){
    msgEl.textContent = text || "";
    msgEl.style.opacity = text ? "1" : "0.7";
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

  function monthLabel(y,m){
    return `${y}년 ${m}월`;
  }

  function render(){
    calSub.textContent = monthLabel(year, month);

    const first = new Date(year, month-1, 1);
    const firstDow = first.getDay(); // 0 Sun
    const daysInMonth = new Date(year, month, 0).getDate();

    // grid start: previous month days fill
    const prevDays = new Date(year, month-1, 0).getDate();
    const startPrev = prevDays - firstDow + 1;

    const dows = ["일","월","화","수","목","금","토"];
    calGrid.innerHTML = "";
    for(const d of dows){
      const el = document.createElement("div");
      el.className = "cal-dow";
      el.textContent = d;
      calGrid.appendChild(el);
    }

    const cells = [];
    // 6 weeks (42) to keep stable
    for(let i=0;i<42;i++){
      const cell = document.createElement("div");
      cell.className = "cal-cell";
      let cellY=year, cellM=month, cellD=0;
      let isOut=false;

      if(i < firstDow){
        // prev month
        isOut=true;
        cellM = month-1; cellY = year;
        if(cellM<=0){ cellM=12; cellY=year-1; }
        cellD = startPrev + i;
      } else if(i >= firstDow + daysInMonth){
        // next month
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
      head.className = "cal-day";
      head.innerHTML = `<div class="cal-day-num">${cellD}</div><div class="small">${dateStr}</div>`;
      cell.appendChild(head);

      const linesWrap = document.createElement("div");
      linesWrap.className = "cal-lines";

      const lines = monthItems[dateStr] || ["","","",""];
      for(let k=0;k<4;k++){
        const line = document.createElement("div");
        line.className = "cal-line" + ((lines[k]||"").trim()? "" : " empty");
        line.textContent = (lines[k]||"").trim() || "·";
        linesWrap.appendChild(line);
      }
      cell.appendChild(linesWrap);

      cell.addEventListener("click", async ()=>{
        selected = dateStr;
        selectedDateEl.textContent = dateStr;
        setMsg("");
        // load day lines
        try{
          const dayLines = await apiGetDay(dateStr);
          for(let k=0;k<4;k++) inputs[k].value = dayLines[k] || "";
        }catch(e){
          for(let k=0;k<4;k++) inputs[k].value = "";
          setMsg(String(e.message||e), false);
        }
        render();
      });

      cells.push(cell);
      calGrid.appendChild(cell);
    }
  }

  async function loadMonth(){
    setMsg("불러오는 중...");
    try{
      monthItems = await apiGetMonth(year, month);
      setMsg("");
      render();

      // default select today if same month
      const t = new Date();
      const todayStr = ymd(t.getFullYear(), t.getMonth()+1, t.getDate());
      if(!selected){
        selected = todayStr;
      }
      // if selected is not in current 6w grid, keep but editor will still work
      selectedDateEl.textContent = selected || "-";
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

  document.getElementById("prevBtn").addEventListener("click", ()=>{
    month -= 1;
    if(month<=0){ month=12; year-=1; }
    loadMonth();
  });
  document.getElementById("nextBtn").addEventListener("click", ()=>{
    month += 1;
    if(month>=13){ month=1; year+=1; }
    loadMonth();
  });
  document.getElementById("todayBtn").addEventListener("click", ()=>{
    const t = new Date();
    year = t.getFullYear();
    month = t.getMonth()+1;
    selected = ymd(year, month, t.getDate());
    loadMonth();
  });

  document.getElementById("saveBtn").addEventListener("click", async ()=>{
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

  document.getElementById("deleteBtn").addEventListener("click", async ()=>{
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