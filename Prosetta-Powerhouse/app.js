(() => {
  "use strict";
  const DATA = window.RITU_DEMO_DATA;
  const views = [["command","Command Center","◉"],["boardroom","Boardroom","◇"],["projects","Projects","▦"],["agents","Agents","◌"],["tasks","Tasks","▤"],["memory","Memory","◈"],["activity","Activity","≋"],["system","System","⚙"]];
  views.splice(1,0,["company","Company","CEO"]);
  views.splice(2,0,["training","Training Room","TRN"]);
  const $ = (s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const safe = value => String(value ?? "").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  class StorageController {
    static load(){try{return JSON.parse(localStorage.getItem("ritu-command-state"))||{}}catch{return {}}}
    static save(){try{localStorage.setItem("ritu-command-state",JSON.stringify({activeView:state.activeView,activeProjectId:state.activeProjectId,selectedAgentId:state.selectedAgentId,chats:state.chats,roomChats:state.roomChats,agentChats:state.agentChats}))}catch(e){toast("Local persistence is unavailable.")}}
  }
  const saved=StorageController.load();
  const state={activeView:saved.activeView||"command",activeProjectId:saved.activeProjectId||null,selectedAgentId:saved.selectedAgentId||null,rituState:"idle",isListening:false,isGenerating:false,notifications:[...DATA.notifications],projects:[],agents:[],tasks:[],memories:[],activities:[],chats:saved.chats||{},roomChats:saved.roomChats||{},agentChats:saved.agentChats||{},visible:true,sessionId:sessionStorage.getItem("ritu-session-id")||crypto.randomUUID(),backend:{online:false,ready:false,baseUrl:"",revision:null,health:null},ollama:{online:false,fastModel:"Unknown",deepModel:"Unknown",model:"Unknown",models:[]},ocr:{online:false,busy:false,lastResult:null,lastImage:null}};
  state.company={online:false,busy:false,data:null};state.training={online:false,busy:false,data:null,lastResult:null};
  sessionStorage.setItem("ritu-session-id",state.sessionId);
  const EMPTY_PROJECT={id:"",name:"No active project",objective:"Ritu backend is connecting.",phase:"Offline",milestone:"Await live state",blocker:"None",owner:"Ritu",priority:"Medium",progress:0,health:"Blocked",agents:[],files:[],risks:[]};
  const project=id=>state.projects.find(p=>p.id===id)||state.projects[0]||EMPTY_PROJECT, agent=id=>state.agents.find(a=>a.id===id);
  const routedModel=room=>(room==="training"||room==="boardroom")?state.ollama.deepModel:state.ollama.fastModel;
  const chatViews=new Set(["command","company","training","boardroom","agents","project-room","agent-room"]);
  const internalViews=new Set(["project-room","agent-room"]);
  const roomStarters={
    command:{sender:"Ritu",time:"Ready",text:"Command Center is ready for company-wide questions, overall priorities, new missions, and cross-project direction.",kind:"Overall command"},
    company:{sender:"Ritu",time:"Ready",text:"Ask me for the live status of projects, agents, tasks, programs, blockers, or company execution.",kind:"CEO status room"},
    training:{sender:"Ritu",time:"Ready",text:"Tell me what capability I should develop. I will discuss the proposed intelligence, memory, and guardrails with you before asking permission to apply it.",kind:"Permission-gated training"},
    boardroom:{sender:"Ritu",time:"Ready",text:"The Boardroom is open for consequential company, project, agent, and intelligence decisions. I will present options, risks, and the decision required.",kind:"Decision room"},
    agents:{sender:"Ritu",time:"Ready",text:"This is the overall agent organization room. Ask about staffing, workload, blockers, performance, learning, or which specialist should handle new work.",kind:"Agent organization"}
  };
  for(const [key,message] of Object.entries(roomStarters))if(!state.roomChats[key])state.roomChats[key]=[message];
  if(!state.selectedAgentId)state.selectedAgentId=state.agents[0]?.id||null;
  function roomHistory(key){
    if(key.startsWith("project:")){const id=key.split(":")[1];return state.chats[id]??=([])}
    if(key.startsWith("agent:")){const id=key.split(":")[1];return state.agentChats[id]??=([{sender:agent(id)?.name||"Agent",time:"Ready",text:"I am available to discuss my current assignment, blockers, status, and learning.",kind:"Direct agent channel"}])}
    return state.roomChats[key]??=([])
  }
  function activeRoom(){
    const p=project(state.activeProjectId),a=agent(state.selectedAgentId);
    if(state.activeView==="project-room")return {key:`project:${p.id}`,room:"project",title:`Project · ${p.name}`,placeholder:`Ask Ritu about ${p.name}…`,project:p,participant:"Ritu",selected_context:{project_id:p.id,project_name:p.name,objective:p.objective,phase:p.phase,milestone:p.milestone}};
    if(state.activeView==="agent-room")return {key:`agent:${a?.id||"unknown"}`,room:"agent",title:`Agent · ${a?.name||"Unknown"}`,placeholder:`Discuss status, issues, or learning with ${a?.name||"this agent"}…`,project:project(a?.project),participant:a?.name||"Agent",selected_context:{agent_id:a?.id,agent_name:a?.name,agent_role:a?.role,agent_status:a?.status,agent_task:a?.task,project_id:a?.project,project_name:project(a?.project).name}};
    const definitions={
      command:{title:"Command Center · Overall",placeholder:"Ask an overall question, set direction, or create a new mission…"},
      company:{title:"CEO Company · Live Status",placeholder:"Ask Ritu about project, agent, task, program, or blocker status…"},
      training:{title:"Training Room · Ritu Development",placeholder:"Discuss what Ritu should learn, then approve the training when ready…"},
      boardroom:{title:"Boardroom · Decisions",placeholder:"Discuss a consequential decision, options, risks, or approval…"},
      agents:{title:"Agents · Organization Room",placeholder:"Ask about overall agents, staffing, workload, issues, or learning…"}
    };
    const definition=definitions[state.activeView]||definitions.command;
    return {key:state.activeView,room:state.activeView,title:definition.title,placeholder:definition.placeholder,project:p,participant:"Ritu",selected_context:{project_id:p.id,project_name:p.name,objective:p.objective,phase:p.phase,milestone:p.milestone}}
  }
  function isChatView(){return chatViews.has(state.activeView)}
  function toast(text){const el=document.createElement("div");el.className="toast";el.textContent=text;$("#toast-region").append(el);setTimeout(()=>el.remove(),3200)}
  class NavigationController {
    init(){this.renderNav();this.navigate(state.activeView)}
    renderNav(){const active=state.activeView==="project-room"?"projects":state.activeView==="agent-room"?"agents":state.activeView;$("#primary-nav").innerHTML=views.map(([id,label,icon])=>`<button class="nav-item ${active===id?"active":""}" data-view="${id}" aria-label="${label}"><span class="nav-icon">${icon}</span><span>${label}</span></button>`).join("")}
    navigate(view){if(!views.some(v=>v[0]===view)&&!internalViews.has(view))return;state.activeView=view;this.renderNav();configureComposer();renderView();renderContext();StorageController.save();rituBridge.syncScreen();$("#workspace").focus({preventScroll:true})}
  }
  class RituCoreController {
    set(value){const allowed=["idle","listening","thinking","executing","success","warning","offline"];state.rituState=allowed.includes(value)?value:"idle";const stage=$(".core-stage");if(stage){stage.className=`core-stage glass state-${state.rituState}`;const label=$("#ritu-state-label");if(label)label.textContent=`RITU IS ${state.rituState==="idle"?"MONITORING":state.rituState.toUpperCase()}`}}
  }
  class OllamaController {
    init(){this.syncFromHealth(state.backend.health)}
    syncFromHealth(health){
      const ollamaHealth=health?.ollama||{};
      const rawModels=Array.isArray(ollamaHealth.models)?ollamaHealth.models:[];
      state.ollama.models=rawModels.map(item=>typeof item==="string"?item:item?.name).filter(Boolean);
      state.ollama.fastModel=ollamaHealth.fast_model||"Unknown";
      state.ollama.deepModel=ollamaHealth.deep_model||"Unknown";
      state.ollama.online=ollamaHealth.online===true;
      this.updateRoute()
    }
    updateRoute(){
      const room=activeRoom().room,model=routedModel(room),selector=$("#model-selector"),status=$("#local-ai-status");
      state.ollama.model=model;
      if(!selector||!status)return;
      if(!state.ollama.online){
        selector.innerHTML=`<option value="">Ollama unavailable through Ritu Core</option>`;
        selector.disabled=true;
        status.innerHTML=`<i class="dot offline"></i>OLLAMA OFFLINE`;
        return
      }
      selector.innerHTML=`<option value="${safe(model)}">${safe(model)} · ${room==="training"||room==="boardroom"?"deep reasoning":"fast response"}</option>`;
      selector.disabled=true;
      const installed=state.ollama.models.length===0||state.ollama.models.includes(model);
      status.innerHTML=`<i class="dot ${installed?"online":"offline"}"></i>${room==="training"||room==="boardroom"?"DEEP":"FAST"} · ${safe(model)}`
    }
  }
  class RituBridgeController {
    constructor(){this.syncTimer=null}
    setOnline(online,ready=online){
      state.backend.online=Boolean(online);
      state.backend.ready=Boolean(online&&ready);
      const status=$("#api-status");
      if(status){
        const label=!state.backend.online?"RITU API OFFLINE":state.backend.ready?"RITU CORE CONNECTED":"RITU CORE DEGRADED";
        const dot=state.backend.ready?"online":"offline";
        status.innerHTML=`<i class="dot ${dot}"></i>${label}`
      }
      configureComposer()
    }
    applyHealth(health){
      const validBackend=health?.ok===true&&health?.service==="Ritu eCEO";
      const ready=validBackend&&health?.ollama?.online===true;
      state.backend.health=health||null;
      this.setOnline(validBackend,ready);
      ollama.syncFromHealth(health);
      if(state.activeView==="system"){renderView();renderContext()}
      return {validBackend,ready}
    }
    async refreshHealth({showToast=false}={}){
      try{
        const response=await fetch(`${state.backend.baseUrl}/api/health`,{signal:AbortSignal.timeout(2500)});
        if(!response.ok)throw new Error("Ritu backend unavailable");
        const health=await response.json();
        const result=this.applyHealth(health);
        if(!result.validBackend)throw new Error("Unexpected service responded on the Ritu port");
        if(showToast){
          toast(result.ready?"Ritu Core and Ollama are connected.":"Ritu backend is online, but Ollama is unavailable.")
        }
        return result
      }catch(error){
        state.backend.health=null;
        this.setOnline(false,false);
        ollama.syncFromHealth(null);
        if(showToast)toast(`Ritu Core is offline: ${error.message}`);
        return {validBackend:false,ready:false,error}
      }
    }
    async init(){
      const health=await this.refreshHealth();
      if(health.validBackend){
        await company.refresh();
        await training.refresh();
        await this.syncScreen(true);
        toast(health.ready?"Ritu Core, Ollama, and workspace API connected.":"Ritu backend connected in degraded mode. Ollama is offline.")
      }
    }
    snapshot(){
      const p=project(state.activeProjectId),room=activeRoom();
      return {session_id:`${state.sessionId}:${room.key}`,active_screen:state.activeView,conversation_room:room.room,selected_memory:null,selected_project_id:p?.id||null,selected_agent_id:state.selectedAgentId,visible_project_ids:state.projects.map(item=>item.id),visible_agent_ids:state.agents.map(item=>item.id),page_title:document.title,metadata:{room_title:room.title,project_name:p?.name||null,project_phase:p?.phase||null,project_objective:p?.objective||null,visible:state.visible,source:"ritu-command-center-8080",agents:state.agents.map(item=>({id:item.id,name:item.name,status:item.status,project:item.project,task:item.task})),projects:state.projects.map(item=>({id:item.id,name:item.name,phase:item.phase,progress:item.progress,health:item.health})),tasks:state.tasks.map(item=>({id:item.id,title:item.title,status:item.status,agent:item.agent,project:item.project}))}}
    }
    syncScreen(immediate=false){
      clearTimeout(this.syncTimer);
      const run=async()=>{
        if(!state.backend.online)return;
        try{
          const response=await fetch(`${state.backend.baseUrl}/api/state/screen`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(this.snapshot())});
          if(!response.ok)throw new Error("Screen sync failed")
        }catch{
          await this.refreshHealth()
        }
      };
      if(immediate)return run();this.syncTimer=setTimeout(run,120)
    }
    async chat(text,room,signal){
      if(!state.backend.ready)throw new Error("Ritu Core is not ready. Start the backend and Ollama before sending a message.");
      const response=await fetch(`${state.backend.baseUrl}/api/ritu/chat`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:text,room:room.room,session_id:`${state.sessionId}:${room.key}`,selected_context:room.selected_context}),signal});
      const result=await response.json().catch(()=>({}));
      if(!response.ok)throw new Error(result.error||`Ritu backend returned ${response.status}`);
      if(result.company)company.apply(result.company);
      for(const action of result.actions||[]){
        if(action.type==="navigate"&&action.target&&views.some(v=>v[0]===action.target))navigation.navigate(action.target);
      }
      if(result.model){
        state.ollama.model=result.model;
        const pending=roomHistory(room.key).at(-1);
        if(pending)pending.kind=`Verified Ritu Core · ${result.model}`
      }
      return result.response||result.reply||"I received the request and updated the operational state."
    }
  }
  class ChatController {
    constructor(){this.controller=null}
    async send(text=$("#command-input")?.value.trim()||""){
      if(!isChatView()||!text||state.isGenerating)return;
      if(!state.backend.ready){
        rituCore.set("offline");
        toast("Ritu Core is not ready. Start Ritu and confirm Ollama is online.");
        return
      }
      const input=$("#command-input");input.value="";autoSize(input);
      const room=activeRoom(),p=room.project||project(state.activeProjectId),history=roomHistory(room.key);
      history.push({sender:"You",time:nowTime(),text});
      addActivity({type:`${room.title} message`,text,project:p.id,agent:"You",priority:"Medium",time:"Now"});
      state.isGenerating=true;rituCore.set("thinking");renderView();updateStop();
      const msg={sender:room.participant,time:nowTime(),text:"",kind:`Verified Ritu Core · ${routedModel(room.room)}`};
      history.push(msg);this.controller=new AbortController();
      try{
        rituCore.set("executing");
        const full=await rituBridge.chat(text,room,this.controller.signal);
        msg.text=full;
        if(isChatView())renderView();
        if(!full)throw new Error("Ritu Core returned an empty response");
        this.finish(full,p.id)
      }catch(error){
        if(error.name==="AbortError"){
          state.isGenerating=false;this.controller=null;rituCore.set("idle");updateStop();return
        }
        this.fail(msg,p.id,error)
      }
      StorageController.save()
    }
    finish(full,pid){state.isGenerating=false;this.controller=null;rituCore.set("success");addActivity({type:"Ritu response",text:full,project:pid,agent:"Ritu",priority:"Medium",time:"Now"});if(isChatView())renderView();updateStop();setTimeout(()=>rituCore.set("idle"),1200)}
    fail(msg,pid,error){
      const failure=`Ritu Core could not complete this request: ${error.message}`;
      msg.kind="Verified backend error";msg.text=failure;
      state.isGenerating=false;this.controller=null;rituCore.set("warning");
      addActivity({type:"Ritu response failed",text:failure,project:pid,agent:"Ritu",priority:"High",time:"Now"});
      if(isChatView())renderView();updateStop();toast("Ritu Core is unavailable or degraded.")
    }
    stop(){this.controller?.abort();state.isGenerating=false;this.controller=null;rituCore.set("idle");if(isChatView())renderView();updateStop();toast("Response stopped.")}
  }
  class VoiceController {
    constructor(){this.recognition=null}
    start(){const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SpeechRecognition){toast("Voice recognition is not supported in this browser.");return}try{this.recognition=new SpeechRecognition();this.recognition.continuous=true;this.recognition.interimResults=true;this.recognition.lang="en-IN";this.recognition.onstart=()=>this.ui(true);this.recognition.onresult=e=>{let text="";for(let i=e.resultIndex;i<e.results.length;i++)text+=e.results[i][0].transcript;$("#command-input").value=text;autoSize($("#command-input"))};this.recognition.onerror=e=>{toast(`Voice input: ${e.error}`);this.ui(false)};this.recognition.onend=()=>this.ui(false);this.recognition.start()}catch{toast("Microphone could not be started.");this.ui(false)}}
    stop(){try{this.recognition?.stop()}catch{}this.ui(false)}
    ui(on){state.isListening=on;$("#mic-button").classList.toggle("listening",on);$("#voice-wave").classList.toggle("active",on);rituCore.set(on?"listening":"idle")}
  }
  class RapidOCRController {
    async init(){
      try{
        const response=await fetch("/api/ocr/health",{signal:AbortSignal.timeout(3500)});
        if(!response.ok)throw new Error("RapidOCR service unavailable");
        const data=await response.json();state.ocr.online=Boolean(data.ok);this.updateUi()
      }catch{state.ocr.online=false;this.updateUi()}
    }
    updateUi(){
      const status=$("#ocr-status"),button=$("#screen-read-button");
      if(status)status.innerHTML=state.ocr.online?`<i class="dot online"></i>RAPIDOCR LOCAL`:`<i class="dot offline"></i>OCR OFFLINE`;
      if(button){button.disabled=state.ocr.busy||!state.ocr.online;button.classList.toggle("scanning",state.ocr.busy);button.textContent=state.ocr.busy?"SCAN":"OCR"}
    }
    async readScreen(){
      if(state.ocr.busy)return;
      if(!navigator.mediaDevices?.getDisplayMedia){toast("Screen capture is not supported in this browser.");return}
      if(!state.ocr.online){toast("RapidOCR is offline. Start Ritu with start-ritu.cmd.");return}
      let stream;
      try{
        state.ocr.busy=true;this.updateUi();rituCore.set("executing");
        stream=await navigator.mediaDevices.getDisplayMedia({video:{frameRate:{ideal:1,max:5}},audio:false});
        const video=document.createElement("video");video.muted=true;video.playsInline=true;video.srcObject=stream;
        await video.play();
        if(!video.videoWidth)await new Promise(resolve=>video.addEventListener("loadedmetadata",resolve,{once:true}));
        await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
        const scale=Math.min(1,2560/Math.max(video.videoWidth,video.videoHeight));
        const canvas=document.createElement("canvas");canvas.width=Math.max(1,Math.round(video.videoWidth*scale));canvas.height=Math.max(1,Math.round(video.videoHeight*scale));
        canvas.getContext("2d",{alpha:false}).drawImage(video,0,0,canvas.width,canvas.height);
        const image=canvas.toDataURL("image/jpeg",.92);
        const response=await fetch("/api/ocr",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({image})});
        const result=await response.json();
        if(!response.ok||!result.ok)throw new Error(result.error||"RapidOCR could not read the screen");
        state.ocr.lastResult=result;state.ocr.lastImage=image;this.openResult(result,image);
        addActivity({type:"Screen read",text:`RapidOCR extracted ${result.line_count} text lines locally.`,project:state.activeProjectId,agent:"Ritu",priority:"Low",time:"Now"});
        rituCore.set("success")
      }catch(error){
        rituCore.set("warning");
        if(error.name==="NotAllowedError")toast("Screen reading was cancelled.");else toast(`Screen reading failed: ${error.message}`)
      }finally{
        stream?.getTracks().forEach(track=>track.stop());state.ocr.busy=false;this.updateUi();setTimeout(()=>rituCore.set("idle"),1400)
      }
    }
    openResult(result,image){
      document.body.classList.add("modal-open");
      const confidence=result.confidence==null?"—":`${Math.round(result.confidence*100)}%`;
      const text=result.text||"No readable text was detected.";
      $("#modal-root").innerHTML=`<div class="modal-backdrop"><article class="modal ocr-modal glass" role="dialog" aria-modal="true" aria-labelledby="ocr-modal-title"><button class="modal-close" data-action="close-modal" aria-label="Close">×</button><header class="modal-hero"><span class="eyebrow">Private local screen reading</span><h2 id="ocr-modal-title">RapidOCR Scan</h2><p>The screenshot stayed on this device. Review the extracted text before sending it to Qwen.</p></header><div class="ocr-grid"><section class="ocr-preview glass"><img src="${image}" alt="Captured screen preview"></section><section class="ocr-output glass"><div class="ocr-metrics"><span><b>${result.line_count}</b> lines</span><span><b>${confidence}</b> confidence</span><span><b>${result.duration_ms} ms</b> local scan</span></div><textarea id="ocr-result-text" aria-label="Recognized screen text">${safe(text)}</textarea><div class="button-row"><button class="button primary" data-action="analyze-screen">Ask Ritu about screen</button><button class="button" data-action="use-ocr">Use as context</button><button class="button" data-action="copy-ocr">Copy text</button><button class="button" data-action="read-screen">Scan again</button></div></section></div></article></div>`;
      $(".modal-close").focus()
    }
    useAsContext(){
      const text=$("#ocr-result-text")?.value.trim()||state.ocr.lastResult?.text?.trim();
      if(!text)return;
      closeProjectModal();navigation.navigate("command");
      const input=$("#command-input");input.value=`Screen text:\n${text}`;autoSize(input);input.focus();toast("Screen text added as local context.")
    }
    analyze(){
      const text=$("#ocr-result-text")?.value.trim()||state.ocr.lastResult?.text?.trim();
      if(!text){toast("No screen text is available.");return}
      closeProjectModal();navigation.navigate("command");
      chat.send(`Analyze the following text captured locally from my screen. Explain what is visible, identify anything important or actionable, and answer as my private AI companion.\n\nSCREEN TEXT:\n${text.slice(0,16000)}`)
    }
    async copy(){
      const text=$("#ocr-result-text")?.value||state.ocr.lastResult?.text||"";
      if(!text)return;
      try{await navigator.clipboard.writeText(text);toast("OCR text copied.")}catch{toast("Clipboard access was unavailable.")}
    }
  }
  class CompanyController {
    apply(data,{render=true}={}){
      if(!data?.ok)return false;
      const changed=state.backend.revision!==data.revision;
      state.company.data=data;state.company.online=true;rituBridge.setOnline(true,state.backend.ready);state.backend.revision=data.revision;
      state.projects=Array.isArray(data.projects)?data.projects:[];
      state.agents=Array.isArray(data.agents)?data.agents:[];
      state.tasks=Array.isArray(data.tasks)?data.tasks:[];
      state.memories=Array.isArray(data.memories)?data.memories:[];
      state.activities=Array.isArray(data.activities)?data.activities:[];
      if(!state.projects.some(p=>p.id===state.activeProjectId))state.activeProjectId=state.projects[0]?.id||null;
      if(!state.agents.some(a=>a.id===state.selectedAgentId))state.selectedAgentId=state.agents[0]?.id||null;
      const selector=$("#project-selector");
      if(selector){selector.innerHTML=state.projects.map(p=>`<option value="${safe(p.id)}">${safe(p.name)}</option>`).join("");selector.value=state.activeProjectId||""}
      if(render&&changed&&!state.isGenerating){renderView();renderContext()}
      StorageController.save();return changed
    }
    async refresh(render=true){
      try{
        const response=await fetch("/api/portal/state",{signal:AbortSignal.timeout(5000)});
        if(!response.ok)throw new Error("Company state unavailable");
        this.apply(await response.json(),{render})
      }catch{state.company.online=false;await rituBridge.refreshHealth()}
    }
    async runTask(taskId){
      if(state.company.busy)return;
      try{
        state.company.busy=true;rituCore.set("executing");toast("Ritu delegated the task. The assigned agent is working.");
        const response=await fetch("/api/company/run-task",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({task_id:taskId,sleep_after:true})});
        const result=await response.json();if(!response.ok||!result.ok)throw new Error(result.error||"Task execution failed");
        company.apply(result.company);toast(result.result?.summary||"Agent task completed.")
      }catch(error){rituCore.set("warning");toast(`Agent execution: ${error.message}`)}
      finally{state.company.busy=false;setTimeout(()=>rituCore.set("idle"),1200)}
    }
  }
  class TrainingController {
    async refresh(){
      try{
        const response=await fetch("/api/training/status",{signal:AbortSignal.timeout(5000)});
        if(!response.ok)throw new Error("Training state unavailable");
        state.training.data=await response.json();state.training.online=true;
        if(state.activeView==="training")renderView()
      }catch{state.training.online=false}
    }
    async start(){
      if(state.training.busy)return;
      const topic=$("#training-topic")?.value.trim(),objective=$("#training-objective")?.value.trim();
      if(!topic||!objective){toast("Add a training topic and the behavior Ritu should learn.");return}
      const payload={topic,objective,category:$("#training-category")?.value||"Operations",scope:$("#training-scope")?.value||"global",source_notes:$("#training-notes")?.value.trim()||""};
      try{
        state.training.busy=true;rituCore.set("executing");renderView();toast("Ritu is studying this lesson with local Qwen.");
        const response=await fetch("/api/training/session",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
        const result=await response.json();if(!response.ok||!result.ok)throw new Error(result.error||"Training failed");
        state.training.lastResult=result;state.training.data=result.training_status||state.training.data;
        await company.refresh();await this.refresh();renderView();
        if(result.needs_input)toast(`Ritu needs clarification: ${result.question}`);else toast(result.summary||"Ritu added new operational intelligence.")
      }catch(error){rituCore.set("warning");toast(`Training Room: ${error.message}`)}
      finally{state.training.busy=false;setTimeout(()=>rituCore.set("idle"),1200);if(state.activeView==="training")renderView()}
    }
  }
  class ReferenceController {
    choose(){$("#reference-upload").click()}
    read(file){return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(file)})}
    async upload(files){
      for(const file of files){
        try{
          toast(`Uploading ${file.name} locally…`);
          const data=await this.read(file);
          const response=await fetch("/api/company/upload",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({filename:file.name,media_type:file.type||"application/octet-stream",data})});
          const result=await response.json();if(!response.ok||!result.ok)throw new Error(result.error||"Upload failed");
          toast(`${file.name} saved to Ritu's project references.`)
        }catch(error){toast(`Reference upload: ${error.message}`)}
      }
      await company.refresh();$("#reference-upload").value=""
    }
  }
  class FileController {
    query(scope,projectId,path=""){
      const params=new URLSearchParams({scope});
      if(projectId)params.set("project",projectId);
      if(path)params.set("path",path);
      return params.toString()
    }
    async browse(scope="project",projectId=state.activeProjectId){
      try{
        const response=await fetch(`/api/portal/files?${this.query(scope,projectId)}`,{signal:AbortSignal.timeout(8000)});
        const result=await response.json();if(!response.ok||!result.ok||!result.verified)throw new Error(result.error||"File inventory unavailable");
        document.body.classList.add("modal-open");
        $("#modal-root").innerHTML=`<div class="modal-backdrop"><article class="modal file-modal glass" role="dialog" aria-modal="true"><button class="modal-close" data-action="close-modal">×</button><header class="modal-hero"><span class="eyebrow">Verified localhost workspace API</span><h2>${scope==="portal"?"Portal source files":safe(result.project?.name||"Project files")}</h2><p>${result.count} files are available inside the protected ${scope} scope. Internal history, secrets, and Git data remain inaccessible.</p><div class="button-row"><button class="button primary" data-action="new-file" data-file-scope="${safe(scope)}" data-file-project="${safe(projectId||"")}">New text file</button><span class="chip">RITU API CONNECTED</span></div></header><div class="file-browser-list">${result.files.map(file=>`<button class="file-browser-row" data-file-path="${safe(file.path)}" data-file-scope="${safe(scope)}" data-file-project="${safe(projectId||"")}" ${file.editable?"":"disabled"}><span>${safe(file.path)}</span><small>${Math.max(1,Math.round(file.size/1024))} KB · ${file.editable?"read / edit":"stored file"}</small></button>`).join("")||"<p>No files are available yet.</p>"}</div></article></div>`
      }catch(error){toast(`Workspace files: ${error.message}`)}
    }
    async open(scope,projectId,path){
      try{
        const response=await fetch(`/api/portal/file?${this.query(scope,projectId,path)}`,{signal:AbortSignal.timeout(8000)});
        const result=await response.json();if(!response.ok||!result.ok||!result.verified)throw new Error(result.error||"File unavailable");
        this.editor(scope,projectId,result.path,result.content,result.sha256,false)
      }catch(error){toast(`Open file: ${error.message}`)}
    }
    editor(scope,projectId,path="",content="",sha256="",isNew=false){
      document.body.classList.add("modal-open");
      $("#modal-root").innerHTML=`<div class="modal-backdrop"><article class="modal file-editor-modal glass" role="dialog" aria-modal="true"><button class="modal-close" data-action="close-modal">×</button><header class="modal-hero"><span class="eyebrow">${scope==="portal"?"Portal source · Boardroom changes recommended":"Project workspace"} · localhost only</span><h2>${isNew?"Create file":"Edit verified file"}</h2><p>Saving creates a recoverable backup when replacing an existing file, writes atomically, and verifies the exact content and SHA-256 from disk.</p></header><label class="file-path-field"><span>Relative path</span><input id="file-editor-path" value="${safe(path)}" ${isNew?"":"readonly"} placeholder="docs/notes.md"></label><textarea id="file-editor-content" class="file-editor-content" spellcheck="false">${safe(content)}</textarea><div class="file-editor-footer"><span class="chip">${sha256?safe(sha256.slice(0,16))+"…":"NEW FILE"}</span><div class="button-row"><button class="button primary" data-action="save-file" data-file-scope="${safe(scope)}" data-file-project="${safe(projectId||"")}">Save and verify</button><button class="button" data-action="close-modal">Cancel</button></div></div></article></div>`;
      $("#file-editor-content").focus()
    }
    newFile(scope,projectId){this.editor(scope,projectId)}
    async save(scope,projectId){
      const path=$("#file-editor-path")?.value.trim(),content=$("#file-editor-content")?.value??"";
      if(!path){toast("Enter a relative file path.");return}
      try{
        rituCore.set("executing");
        const response=await fetch("/api/portal/file",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({scope,project:projectId||null,path,content,summary:"Edited and verified from localhost portal"})});
        const result=await response.json();if(!response.ok||!result.ok||!result.verified||!result.file?.verified)throw new Error(result.error||"File write was not verified");
        company.apply(result.company);closeProjectModal();toast(`${result.file.path} saved and verified from disk.`);
        if(scope==="portal")toast("Portal source changed. Refresh when you are ready to load it.")
      }catch(error){toast(`Save file: ${error.message}`)}
      finally{setTimeout(()=>rituCore.set("idle"),900)}
    }
  }
  class TaskController {
    async move(id,status){
      const t=state.tasks.find(x=>x.id===id);if(!t)return;
      try{
        const response=await fetch("/api/portal/task",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({task:id,status})});
        const result=await response.json();if(!response.ok||!result.ok||!result.verified)throw new Error(result.error||"Task update was not verified");
        company.apply(result.company);toast(`${t.title} moved to ${status} and verified.`)
      }catch(error){toast(`Task update: ${error.message}`)}
    }
  }
  class SystemMonitor {
    constructor(){this.running=true}
    command(){toast("System controls are read-only here. Ritu reports only verified backend state.")}
  }
  function nowTime(){return new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})}
  function viewHead(title,sub,eyebrow="Ritu operations"){return `<div class="view-head"><div><span class="eyebrow">${eyebrow}</span><h1>${title}</h1><p>${sub}</p></div></div>`}
  function messages(roomKey){return roomHistory(roomKey).map(m=>`<article class="message ${m.sender==="You"?"user":""}"><div class="message-meta">${safe(m.sender)} · ${safe(m.time)}</div><p>${safe(m.text)}</p>${m.kind?`<span class="message-tag">${safe(m.kind)}</span>`:""}</article>`).join("")}
  function roomConversation(key,title,tag){return `<section class="conversation room-conversation glass"><div class="panel-head"><h2>${safe(title)}</h2><span class="chip">${safe(tag)}</span></div><div class="conversation-list">${messages(key)}${state.isGenerating&&activeRoom().key===key?`<div class="typing"><i></i><i></i><i></i></div>`:""}</div></section>`}
  function coreMarkup(){const c=state.company.data?.counts||{},inProgress=state.tasks.filter(t=>t.status==="In Progress").length,blocked=state.tasks.filter(t=>t.status==="Blocked").length,completed=state.tasks.filter(t=>t.status==="Completed").length;return `<section class="core-stage glass state-${state.rituState}"><div class="core-wrap"><i class="orbit one"></i><i class="orbit two"></i><i class="orbit three"></i><i class="core"></i></div><div class="core-copy"><strong id="ritu-state-label">RITU IS ${state.rituState==="idle"?"MONITORING":state.rituState.toUpperCase()}</strong><span>Live backend · verified ${safe(state.company.data?.verified_at||"connecting")}</span></div><div class="pulse-strip">${[[c.projects||0,"Projects"],[c.active_agents||0,"Agents working"],[inProgress,"In progress"],[c.open_tasks||0,"Open tasks"],[blocked,"Blocked"],[completed,"Completed"]].map(x=>`<div class="pulse-signal"><b>${x[0]}</b><span>${x[1]}</span></div>`).join("")}</div></section>`}
  function renderCommand(){return `${viewHead("Good evening, Prashant.","Overall direction, cross-project questions, and new missions belong here.","Cognitive command center")}<div class="command-grid">${coreMarkup()}${roomConversation("command","COMMAND CONVERSATION","Company-wide context")}</div>`}
  function renderProjects(){return `${viewHead("Projects","Choose a project to inspect its status and enter its dedicated Project Room.")}<div class="view-guidance glass"><b>Project-specific conversation</b><span>Open a project, then enter its room. Use Command Center for overall questions across projects.</span></div><div class="card-grid">${state.projects.map(p=>`<article class="project-card glass"><button class="card-hit" data-project-modal="${p.id}" aria-label="Open ${safe(p.name)}"></button><div class="card-top"><span class="chip">${p.type}</span><span class="status-${p.health}">${p.health}</span></div><h3>${p.name}</h3><p>${p.objective}</p><div class="card-metrics"><div class="metric"><small>Phase</small><b>${p.phase}</b></div><div class="metric"><small>Priority</small><b>${p.priority}</b></div></div><div class="progress"><i style="width:${p.progress}%"></i></div><div class="card-foot"><span>${p.progress}% complete</span><span>Open project room →</span></div></article>`).join("")}</div>`}
  function renderAgents(){return `${viewHead("Agent Organization","Discuss the workforce with Ritu here, or open one specialist for a direct conversation.")}<div class="agents-room-layout">${roomConversation("agents","AGENT ORGANIZATION DISCUSSION","All agents")}<div class="card-grid">${state.agents.map(a=>`<article class="agent-card glass"><button class="card-hit" data-agent="${a.id}" aria-label="Inspect ${a.name}"></button><div class="card-top"><span class="chip">${a.role}</span><span class="status-${a.status}">${a.status}</span></div><h3>${a.name}</h3><p>${a.task}</p><div class="card-metrics"><div class="metric"><small>Project</small><b>${project(a.project).name}</b></div><div class="metric"><small>Signal</small><b>${a.signal}</b></div></div><div class="progress"><i style="width:${a.progress}%"></i></div><div class="card-foot"><span>${a.capabilities.join(" · ")}</span><span>Open agent room →</span></div></article>`).join("")}</div></div>`}
  function renderBoardroom(){const p=project(state.activeProjectId);return `${viewHead("Executive Boardroom","Consequential company, project, agent, and intelligence decisions are discussed and approved here.","Decision authority")}<div class="boardroom-layout"><div><section class="objective-card glass"><span class="eyebrow">Decision context · ${p.name}</span><h2>${p.objective}</h2><div class="button-row"><span class="chip">${p.health} health</span><span class="chip">${p.progress}% complete</span><span class="chip">${p.phase}</span></div></section>${roomConversation("boardroom","BOARDROOM DELIBERATION","Explicit approval required")}</div><aside><section class="decision glass"><span class="eyebrow">Decision requested</span><h3>${p.blocker==="None"?"Review next strategic commitment":p.blocker}</h3><p>Ritu will present alternatives, risks, evidence, and a recommendation. Nothing consequential is executed without your explicit approval.</p><div class="button-row"><button class="button primary" data-action="approve-boardroom">Approve recommendation</button><button class="button" data-action="ask">Discuss first</button></div></section><section class="modal-section glass"><h3>Decision scope</h3><div class="data-row"><span>Company</span><b>Strategy & resources</b></div><div class="data-row"><span>Projects</span><b>Priorities & risk</b></div><div class="data-row"><span>Agents</span><b>Hiring & intelligence</b></div><h3>Current milestone</h3><div class="data-row"><span>${p.phase}</span><b>${p.milestone}</b></div></section></aside></div>`}
  function renderProjectRoom(){const p=project(state.activeProjectId),projectTasks=state.tasks.filter(t=>t.project===p.id),projectAgents=p.agents.map(id=>agent(id)).filter(Boolean),projectFiles=p.files||[];return `${viewHead(p.name,"Dedicated project status, requirements, live files, agents, and execution conversation.","Project Room")}<button class="room-back" data-view="projects">← All projects</button><div class="room-detail-layout"><section class="room-brief glass"><span class="eyebrow">${p.type} · ${p.health} health</span><h2>${p.objective}</h2><div class="room-stat-grid">${[["Phase",p.phase],["Progress",`${p.progress}%`],["Priority",p.priority],["Milestone",p.milestone],["Blocker",p.blocker],["Owner",p.owner]].map(([label,value])=>`<div><span>${safe(label)}</span><b>${safe(value)}</b></div>`).join("")}</div><div class="progress"><i style="width:${p.progress}%"></i></div><h3>Assigned agents</h3><div class="room-people">${projectAgents.map(a=>`<button data-open-agent-room="${a.id}"><i></i><span>${safe(a.name)}<small>${safe(a.role)}</small></span></button>`).join("")}</div><h3>Current tasks</h3>${projectTasks.map(t=>`<div class="data-row"><span>${safe(t.status)}</span><b>${safe(t.title)} · ${safe(agent(t.agent)?.name||"Ritu")}</b></div>`).join("")||"<p>No tasks assigned.</p>"}<h3>Live workspace files</h3><div class="project-file-list">${projectFiles.slice(0,8).map(path=>`<button data-file-path="${safe(path)}" data-file-scope="project" data-file-project="${safe(p.id)}"><span>${safe(path)}</span><small>Open through Ritu API</small></button>`).join("")||"<p>No workspace files yet.</p>"}</div><button class="button file-browse-button" data-browse-files data-file-scope="project" data-file-project="${safe(p.id)}">Browse all ${projectFiles.length} files</button></section>${roomConversation(`project:${p.id}`,"PROJECT CONVERSATION",p.name)}</div>`}
  function renderAgentRoom(){const a=agent(state.selectedAgentId)||state.agents[0],p=project(a.project),assigned=state.tasks.filter(t=>t.agent===a.id);return `${viewHead(a.name,`Direct discussion with ${a.role} about status, issues, work, and learning.`,"Agent Room")}<button class="room-back" data-view="agents">← Agent organization</button><div class="room-detail-layout"><section class="room-brief agent-brief glass"><div class="agent-room-identity"><i class="agent-orb status-${safe(a.status)}"></i><div><span class="eyebrow">${safe(a.status)} · ${safe(a.role)}</span><h2>${safe(a.name)}</h2><p>${safe(a.task)}</p></div></div><div class="room-stat-grid">${[["Project",p.name],["Progress",`${a.progress}%`],["Signal",a.signal],["Dependencies",a.dependencies],["Last update",a.last],["Capabilities",a.capabilities.join(" · ")]].map(([label,value])=>`<div><span>${safe(label)}</span><b>${safe(value)}</b></div>`).join("")}</div><h3>Assigned work</h3>${assigned.map(t=>`<div class="data-row"><span>${safe(t.status)}</span><b>${safe(t.title)}</b></div>`).join("")||"<p>No current task.</p>"}<div class="training-authority"><b>Agent learning report</b><p>Ask what issue was faced, what changed, how it was validated, and what Ritu should preserve for future agents.</p></div></section>${roomConversation(`agent:${a.id}`,"DIRECT AGENT CONVERSATION",a.name)}</div>`}
  const columns=["Proposed","Planned","In Progress","Review","Blocked","Completed"];
  function renderTasks(){return `${viewHead("Jira Task Board","A no-chat execution board showing task state, project, priority, and assigned agent.","Delivery workflow")}<div class="view-guidance glass"><b>Execution tracking only</b><span>Discuss a task inside its Project Room or with the assigned agent.</span></div><div class="task-board">${columns.map((c,ci)=>`<section class="task-column glass"><h3>${c}<span>${state.tasks.filter(t=>t.status===c).length}</span></h3>${state.tasks.filter(t=>t.status===c).map(t=>`<article class="task-card"><span class="task-key">${safe(t.id.toUpperCase())}</span><b>${t.title}</b><p>${project(t.project).name}</p><div class="task-assignee"><i></i><span>${agent(t.agent)?.name||"Ritu"}<small>${t.priority} priority</small></span></div><div class="progress"><i style="width:${t.progress}%"></i></div><div class="task-actions"><button ${ci===0?"disabled":""} data-move-task="${t.id}" data-status="${columns[ci-1]||c}" aria-label="Move task left">←</button><button ${ci===columns.length-1?"disabled":""} data-move-task="${t.id}" data-status="${columns[ci+1]||c}" aria-label="Move task right">→</button></div></article>`).join("")}</section>`).join("")}</div>`}
  function renderMemory(){return `${viewHead("Memory","Usable context and decisions—never private chain-of-thought.")}<div class="filters"><input id="memory-search" placeholder="Search memory…" aria-label="Search memory"><select id="memory-filter"><option>All categories</option>${[...new Set(state.memories.map(m=>m.category))].map(c=>`<option>${c}</option>`).join("")}</select></div><div id="memory-grid" class="card-grid">${memoryCards(state.memories)}</div>`}
  function memoryCards(items){return items.map(m=>`<article class="memory-card glass"><div class="card-top"><span class="chip">${m.category}</span><span>${m.confidence}% confidence</span></div><h3>${m.title}</h3><p>${m.summary}</p><div class="data-row"><span>Source</span><b>${m.source}</b></div><div class="card-foot"><span>Created ${m.created}</span><span>Used ${m.used}</span></div></article>`).join("")}
  function activityProjectName(item){return item.project?project(item.project).name:"Global"}
  function activityRows(items){return items.map(a=>`<article class="activity-item"><time>${safe(a.time)}</time><i class="activity-node"></i><div><b>${safe(a.type)}</b><p>${safe(a.text)}</p><small>${safe(activityProjectName(a))} · ${safe(agent(a.agent)?.name||a.agent||"Ritu")}</small></div><span class="chip">${safe(a.priority)}</span></article>`).join("")||"<p class='training-empty'>No matching activity or event.</p>"}
  function filterActivity(){const q=$("#activity-search")?.value.toLowerCase()||"",projectId=$("#activity-project-filter")?.value||"all",type=$("#activity-type-filter")?.value||"all";const items=state.activities.filter(a=>(projectId==="all"||a.project===projectId)&&(type==="all"||a.type===type)&&(`${a.type} ${a.text} ${a.agent} ${activityProjectName(a)}`).toLowerCase().includes(q));const stream=$("#activity-results");if(stream)stream.innerHTML=activityRows(items)}
  function renderActivity(){const types=[...new Set(state.activities.map(a=>a.type))];return `${viewHead("Activity & Event Log","Search the chronological audit trail by text, project, event type, or agent.","Operational history")}<div class="filters activity-filters"><input id="activity-search" placeholder="Search logs, events, agents, or details…" aria-label="Search activity logs"><select id="activity-project-filter" aria-label="Filter activity by project"><option value="all">All projects</option>${state.projects.map(p=>`<option value="${p.id}">${safe(p.name)}</option>`)}</select><select id="activity-type-filter" aria-label="Filter activity by event type"><option value="all">All event types</option>${types.map(type=>`<option value="${safe(type)}">${safe(type)}</option>`)}</select></div><section id="activity-results" class="activity-stream">${activityRows(state.activities)}</section>`}
  function renderSystem(){const health=state.backend.health||{},models=health.ollama||{},c=state.company.data?.counts||{};const services=[["Ritu API",state.backend.online],["Ollama",Boolean(models.online||state.ollama.online)],["RapidOCR",state.ocr.online],["Database",Boolean(state.company.data)],["Live state sync",state.company.online],["Workspace file API",state.backend.online],["Training service",state.training.online]];return `${viewHead("System","Verified local services, workspace access, and model routing from Ritu's backend.","Live system state")}<div class="view-guidance glass"><div><b>Ritu localhost API</b><span>Company records and protected Powerhouse files are connected, audited, and verified from disk.</span></div><button class="button primary" data-browse-files data-file-scope="portal">Open portal source files</button></div><div class="system-grid">${services.map(([label,online])=>`<section class="service glass"><div class="service-head"><b>${safe(label)}</b><span class="${online?"status-Strong":"status-Blocked"}">${online?"Operational":"Offline"}</span></div></section>`).join("")}<section class="telemetry glass"><span class="eyebrow">Fast route</span><h2>${safe(models.fast_model||state.ollama.fastModel)}</h2><small>All rooms except Training and Boardroom</small></section><section class="telemetry glass"><span class="eyebrow">Deep route</span><h2>${safe(models.deep_model||state.ollama.deepModel)}</h2><small>Training and Boardroom only</small></section><section class="telemetry glass"><span class="eyebrow">Workspace files</span><h2>${safe(c.files||0)}</h2><small>Visible to Ritu through the project API</small></section><section class="telemetry glass"><span class="eyebrow">Backend revision</span><h2>${safe(state.backend.revision??"—")}</h2><small>${safe(state.company.data?.verified_at||"Awaiting sync")}</small></section><section class="telemetry glass"><span class="eyebrow">Authoritative records</span><h2>${(c.projects||0)+(c.agents||0)+(state.tasks.length||0)}</h2><small>Projects · agents · tasks</small></section></div>`}
  function parseCapabilities(value){if(Array.isArray(value))return value;try{return JSON.parse(value||"[]")}catch{return []}}
  function renderCompany(){
    const data=state.company.data;
    if(!data)return `${viewHead("Agentic Company","Connecting Ritu's durable operating core…","Personal eCEO")}<section class="company-empty glass"><h2>${state.company.online?"Loading company state":"Ritu core is offline"}</h2><p>Start the OCR-enabled Ritu server to connect projects, agents, tasks, memory, and artifacts.</p></section>`;
    const c=data.counts||{},companyTasks=data.tasks||[],companyAgents=data.agents||[],companyProjects=data.projects||[],events=data.events||[];
    return `${viewHead("CEO Company","Ask Ritu for live project, program, agent, task, blocker, and execution status.","Personal eCEO")}<div class="company-metrics">${[["Projects",c.projects||0],["Active agents",c.active_agents||0],["Sleeping",c.sleeping_agents||0],["Open tasks",c.open_tasks||0],["Memories",c.memories||0],["Artifacts",c.artifacts||0],["References",c.references||0]].map(([label,value])=>`<section class="company-metric glass"><span>${label}</span><b>${value}</b></section>`).join("")}</div>${roomConversation("company","CEO STATUS CONVERSATION","Live company state")}<div class="company-layout"><section class="company-panel glass"><div class="panel-head"><h2>LIVE PROJECTS</h2><span class="chip">${safe(data.workspace||"P:\\RituAI\\Powerhouse")}</span></div><div class="company-list">${companyProjects.map(p=>`<article class="company-project"><div><span class="eyebrow">${safe(p.phase)} · ${safe(p.status)}</span><h3>${safe(p.name)}</h3><p>${safe(p.objective)}</p></div><span class="chip">${companyTasks.filter(t=>t.project_id===p.id&&t.status!=="Completed").length} open</span></article>`).join("")||"<p>No live projects yet.</p>"}</div></section><section class="company-panel glass"><div class="panel-head"><h2>AGENT ORGANIZATION</h2><span class="chip">${companyAgents.length} agents</span></div><div class="company-agent-grid">${companyAgents.map(a=>`<article class="company-agent"><div class="agent-orb status-${safe(a.status)}"></div><div><span class="eyebrow">${safe(a.status)}</span><h3>${safe(a.name)}</h3><p>${safe(a.role)}</p><small>${parseCapabilities(a.capabilities).map(safe).join(" · ")}</small></div><button class="button" data-agent-command="${safe(a.name)}" data-agent-next="${a.status==="Active"?"sleep":"wake"}">${a.status==="Active"?"Sleep":"Wake"}</button></article>`).join("")}</div></section></div><section class="company-panel company-tasks glass"><div class="panel-head"><h2>DELEGATION QUEUE</h2><span class="chip">${c.open_tasks||0} open</span></div><div class="company-task-list">${companyTasks.map(t=>`<article class="company-task"><span class="task-state">${safe(t.status)}</span><div><h3>${safe(t.title)}</h3><p>${safe(t.description)}</p></div><span class="chip">${safe(t.priority)}</span>${["Planned","Review","Blocked"].includes(t.status)?`<button class="button primary" data-run-company-task="${t.id}" ${state.company.busy?"disabled":""}>Delegate now</button>`:""}</article>`).join("")}</div></section><section class="company-panel glass"><div class="panel-head"><h2>RITU AUDIT STREAM</h2><span class="chip">Local · persistent</span></div><div class="company-events">${events.slice(0,12).map(e=>`<article><time>${safe(new Date(e.created_at).toLocaleString())}</time><b>${safe(e.summary)}</b></article>`).join("")}</div></section>`
  }
  function renderTraining(){
    const data=state.training.data,last=state.training.lastResult,c=data?.counts||{},sessions=data?.sessions||[],modules=data?.modules||[];
    if(!data)return `${viewHead("eCEO Training Room","Connecting Ritu's private learning workspace…","Self-development console")}<section class="company-empty glass"><h2>${state.training.online?"Loading training state":"Training service is offline"}</h2><p>Start the local Ritu server to create durable intelligence and memory.</p></section>`;
    return `${viewHead("eCEO Training Room","Discuss capabilities with Ritu, review her proposal, then grant permission to equip her.","Permission-gated self-development")}${roomConversation("training","TRAINING DIALOGUE","Discuss → review → approve")}<div class="training-permission glass"><span class="eyebrow">Permission protocol</span><div><b>1. Discuss the capability</b><b>2. Ritu proposes intelligence and memory</b><b>3. You approve or revise</b><b>4. Ritu creates a versioned module</b></div></div><div class="training-metrics">${[["Training sessions",c.sessions||0],["Completed",c.completed||0],["Needs input",c.needs_input||0],["Intelligence modules",c.modules||0],["Total memories",c.memories||0]].map(([label,value])=>`<section class="training-metric glass"><span>${label}</span><b>${value}</b></section>`).join("")}</div><div class="training-layout"><section class="training-console glass"><div class="panel-head"><h2>DIRECT TRAINING BRIEF</h2><span class="chip">Explicit begin button</span></div><div class="training-form"><label><span>Lesson topic</span><input id="training-topic" placeholder="Example: Issue-to-intelligence learning loop"></label><label><span>What should Ritu learn or improve?</span><textarea id="training-objective" placeholder="Describe the behavior, knowledge, procedure, or decision standard Ritu should adopt."></textarea></label><div class="training-options"><label><span>Intelligence category</span><select id="training-category"><option>Strategy</option><option>Leadership</option><option selected>Operations</option><option>Research</option><option>Memory</option><option>Technical</option></select></label><label><span>Memory scope</span><select id="training-scope"><option value="global">Global — Ritu and all agents</option><option value="project">Ritu self-development project</option><option value="agent">Ritu only</option></select></label></div><label><span>Source notes or examples</span><textarea id="training-notes" placeholder="Optional examples, facts, existing process, or constraints to preserve."></textarea></label><div class="training-authority"><b>Bounded operational training</b><p>Clicking Begin is explicit permission to create versioned declarative intelligence and scoped memory. It does not change Qwen model weights or execute generated code.</p></div><button class="button primary training-submit" data-action="start-training" ${state.training.busy?"disabled":""}>${state.training.busy?"Ritu is learning…":"Begin approved training"}</button></div>${last?`<div class="training-result ${last.needs_input?"needs-input":"complete"}"><span class="eyebrow">${last.needs_input?"Clarification required":"Latest training result"}</span><h3>${safe(last.summary||last.question||"Training recorded")}</h3>${last.question?`<p>${safe(last.question)}</p>`:""}${last.module?`<small>${safe(last.module.name)} · v${safe(last.module.version)} · ${safe(last.module.path)}</small>`:""}</div>`:""}</section><aside class="training-side"><section class="training-panel glass"><div class="panel-head"><h2>ACTIVE INTELLIGENCE</h2><span class="chip">${modules.length} modules</span></div><div class="training-module-list">${modules.slice(0,8).map(m=>`<article><div><span class="eyebrow">${safe(m.category)} · VERSION ${safe(m.version)}</span><h3>${safe(m.name)}</h3><p>${safe(m.description)}</p><small>${safe(m.path)}</small></div><span class="module-state">${safe(m.status)}</span></article>`).join("")||"<p class='training-empty'>No trained modules yet. Give Ritu her first lesson.</p>"}</div></section><section class="training-panel glass"><div class="panel-head"><h2>TRAINING HISTORY</h2><span class="chip">Audited</span></div><div class="training-session-list">${sessions.slice(0,10).map(s=>`<article><i class="session-indicator status-${safe(s.status).replaceAll(" ","-")}"></i><div><span class="eyebrow">${safe(s.category)} · ${safe(s.scope_type)}</span><h3>${safe(s.topic)}</h3><p>${safe(s.summary||s.objective)}</p>${s.question?`<small>${safe(s.question)}</small>`:""}</div><b>${safe(s.status)}</b></article>`).join("")||"<p class='training-empty'>Training history will appear here.</p>"}</div></section></aside></div>`
  }
  function configureComposer(){
    const chatView=isChatView(),enabled=chatView&&state.backend.ready,shell=$(".app-shell"),composer=$(".composer"),input=$("#command-input"),room=activeRoom();
    shell.classList.toggle("no-composer",!chatView);composer.classList.toggle("composer-disabled",!enabled);composer.setAttribute("aria-hidden",String(!chatView));
    input.disabled=!enabled;
    input.placeholder=!chatView?"This operational view has no chat.":state.backend.ready?room.placeholder:"Ritu Core is offline or degraded. Start the backend and Ollama.";
    $("#project-selector").style.display=["command","boardroom","project-room"].includes(state.activeView)?"":"none";
    $("#top-project-name").textContent=chatView?room.title:views.find(v=>v[0]===state.activeView)?.[1]||"Ritu Operations";
    ollama.updateRoute()
  }
  function renderView(){const w=$("#workspace");const map={command:renderCommand,company:renderCompany,training:renderTraining,boardroom:renderBoardroom,projects:renderProjects,"project-room":renderProjectRoom,agents:renderAgents,"agent-room":renderAgentRoom,tasks:renderTasks,memory:renderMemory,activity:renderActivity,system:renderSystem};w.innerHTML=(map[state.activeView]||renderCommand)();requestAnimationFrame(()=>{$$(".conversation-list").forEach(c=>c.scrollTop=c.scrollHeight)})}
  function renderContext(){
    const p=project(state.activeProjectId),a=agent(state.selectedAgentId),companyCounts=state.company.data?.counts||{};
    let focus=[["Room",activeRoom().title],["Active project",p.name],["Objective",p.objective],["Next milestone",p.milestone]];
    let awareness=[["Pending approval",p.blocker],["Important memory","Keep sensitive context local"],["Suggested action","Review the current decision"]];
    if(state.activeView==="agent-room"&&a){focus=[["Direct agent",a.name],["Role",a.role],["Status",a.status],["Current work",a.task]];awareness=[["Project",project(a.project).name],["Progress",`${a.progress}%`],["Learning prompt","Issue · change · validation · reuse"]]}
    if(state.activeView==="training"){focus=[["Room","Ritu self-development"],["Protocol","Discuss → propose → approve"],["Modules",state.training.data?.counts?.modules||0],["Memories",state.training.data?.counts?.memories||0]];awareness=[["Authority","Explicit permission required"],["Output","Versioned intelligence"],["Execution","Modules are not auto-executed"]]}
    if(state.activeView==="company"){focus=[["Room","CEO live status"],["Projects",companyCounts.projects||0],["Active agents",companyCounts.active_agents||0],["Open tasks",companyCounts.open_tasks||0]]}
    $("#context-content").innerHTML=`<h2>OPERATIONAL CONTEXT</h2><div class="section-label">Current focus</div><section class="focus-card glass">${focus.map(x=>`<div class="data-row"><span>${safe(x[0])}</span><b>${safe(x[1])}</b></div>`).join("")}</section><div class="section-label">Room awareness</div><div class="awareness-list">${awareness.map(x=>`<div class="awareness-item"><b>${safe(x[0])}</b><span>${safe(x[1])}</span></div>`).join("")}</div><div class="section-label">Agent activity</div><div class="agent-mini-list">${state.agents.slice(0,5).map(agentItem=>`<div class="agent-mini"><i class="agent-state"></i><div><b>${safe(agentItem.name)}</b><span>${safe(agentItem.task)}</span></div><small>${agentItem.progress}%</small></div>`).join("")}</div>`
  }
  function openProjectModal(id){const p=project(id);document.body.classList.add("modal-open");$("#modal-root").innerHTML=`<div class="modal-backdrop"><article class="modal glass" role="dialog" aria-modal="true" aria-labelledby="modal-title"><button class="modal-close" data-action="close-modal" aria-label="Close">×</button><header class="modal-hero"><span class="eyebrow">${p.type} · ${p.health} health</span><h2 id="modal-title">${p.name}</h2><p>${p.objective}</p><div class="button-row"><button class="button primary" data-project-room="${p.id}">Open Project Room</button><button class="button" data-boardroom="${p.id}">Take decision to Boardroom</button><button class="button" data-view="tasks">Review Tasks</button><button class="button" data-action="close-modal">Close</button></div></header><div class="modal-grid"><section class="modal-section glass"><h3>Mission status</h3>${[["Phase",p.phase],["Progress",p.progress+"%"],["Owner",p.owner],["Next milestone",p.milestone],["Agents assigned",p.agents.map(id=>agent(id).name).join(", ")]].map(x=>`<div class="data-row"><span>${x[0]}</span><b>${x[1]}</b></div>`).join("")}<h3>Tasks</h3>${state.tasks.filter(t=>t.project===p.id).map(t=>`<div class="data-row"><span>${t.status}</span><b>${t.title}</b></div>`).join("")}</section><section class="modal-section glass"><h3>Decisions & risks</h3><div class="data-row"><span>Decision</span><b>${p.blocker}</b></div>${p.risks.map(r=>`<div class="data-row"><span>Risk</span><b>${r}</b></div>`).join("")}<h3>Files</h3>${p.files.map(f=>`<div class="data-row"><span>File</span><b>${f}</b></div>`).join("")}</section><section class="modal-section glass"><h3>Recent activity</h3>${state.activities.filter(a=>a.project===p.id).map(a=>`<div class="data-row"><span>${a.time}</span><b>${a.text}</b></div>`).join("")||"<p>No recent activity.</p>"}</section><section class="modal-section glass"><h3>Conversation boundary</h3><p>Project questions stay inside this project's room. Cross-project and overall company questions belong in Command Center.</p></section></div></article></div>`;$(".modal-close").focus()}
  function closeProjectModal(){document.body.classList.remove("modal-open");$("#modal-root").innerHTML=""}
  function openProjectBoardroom(id){selectProject(id);closeProjectModal();navigation.navigate("boardroom")}
  function openProjectRoom(id){selectProject(id);closeProjectModal();navigation.navigate("project-room")}
  function openAgentRoom(id){if(!agent(id))return;state.selectedAgentId=id;closeProjectModal();navigation.navigate("agent-room")}
  function selectProject(id){if(!state.projects.some(p=>p.id===id))return;state.activeProjectId=id;$("#top-project-name").textContent=project(id).name;$("#project-selector").value=id;StorageController.save();renderContext();rituBridge.syncScreen()}
  function addActivity(a){state.activities.unshift(a);state.activities=state.activities.slice(0,60)}
  function autoSize(el){el.style.height="auto";el.style.height=Math.min(el.scrollHeight,85)+"px"}
  function updateStop(){$("#stop-button").classList.toggle("hidden",!state.isGenerating)}
  function openMission(){ $("#modal-root").innerHTML=`<div class="modal-backdrop"><section class="modal mission-panel glass" role="dialog" aria-modal="true"><button class="modal-close" data-action="close-modal">×</button><span class="eyebrow">New mission</span><h2>What would you like Ritu to build, solve, improve, or investigate?</h2><textarea id="mission-input" placeholder="Describe the outcome, context, and any constraints…"></textarea><div class="button-row"><button class="button primary" data-action="submit-mission">Brief Ritu</button><button class="button" data-action="close-modal">Cancel</button></div></section></div>`;$("#mission-input").focus()}
  function openAgent(id){const a=agent(id);state.selectedAgentId=id;document.body.classList.add("modal-open");$("#modal-root").innerHTML=`<div class="modal-backdrop"><article class="modal glass" role="dialog" aria-modal="true"><button class="modal-close" data-action="close-modal">×</button><span class="eyebrow">Coordinated by Ritu</span><h2>${a.name}</h2><p>${a.role}</p><div class="button-row"><button class="button primary" data-agent-room="${a.id}">Open direct agent chat</button><button class="button" data-project-room="${a.project}">Open assigned project</button><button class="button" data-action="close-modal">Close</button></div><div class="modal-grid"><section class="modal-section glass"><h3>Current mission</h3><p>${a.task}</p>${[["Status",a.status],["Active project",project(a.project).name],["Progress",a.progress+"%"],["Dependencies",a.dependencies],["Performance",a.signal]].map(x=>`<div class="data-row"><span>${x[0]}</span><b>${x[1]}</b></div>`).join("")}</section><section class="modal-section glass"><h3>Recent work & handoffs</h3><p>Ask this agent directly about issues, status, changes made, validation, and learning.</p><div class="data-row"><span>Last communication</span><b>${a.last}</b></div><div class="data-row"><span>Files generated</span><b>${Math.max(1,Math.round(a.progress/30))}</b></div><div class="data-row"><span>Completed tasks</span><b>${state.tasks.filter(t=>t.agent===a.id&&t.status==="Completed").length}</b></div></section></div></article></div>`}
  const navigation=new NavigationController(),rituCore=new RituCoreController(),ollama=new OllamaController(),rituBridge=new RituBridgeController(),chat=new ChatController(),voice=new VoiceController(),ocr=new RapidOCRController(),company=new CompanyController(),training=new TrainingController(),references=new ReferenceController(),files=new FileController(),tasks=new TaskController(),systemMonitor=new SystemMonitor();
  function bind(){
    document.addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;
    
      if(b.dataset.view){closeProjectModal();navigation.navigate(b.dataset.view)}
      if(b.dataset.projectModal)openProjectModal(b.dataset.projectModal);
      if(b.dataset.projectRoom)openProjectRoom(b.dataset.projectRoom);
      if(b.dataset.boardroom)openProjectBoardroom(b.dataset.boardroom);
      if(b.dataset.agent)openAgent(b.dataset.agent);
      if(b.dataset.agentRoom)openAgentRoom(b.dataset.agentRoom);
      if(b.dataset.openAgentRoom)openAgentRoom(b.dataset.openAgentRoom);
      if(b.dataset.filePath){files.open(b.dataset.fileScope||"project",b.dataset.fileProject||null,b.dataset.filePath);return}
      if(b.hasAttribute("data-browse-files")){files.browse(b.dataset.fileScope||"project",b.dataset.fileProject||state.activeProjectId);return}
      if(b.dataset.moveTask)tasks.move(b.dataset.moveTask,b.dataset.status);
      if(b.dataset.system)systemMonitor.command(b.dataset.system);
      if(b.dataset.runCompanyTask)company.runTask(b.dataset.runCompanyTask);
      if(b.dataset.agentCommand)chat.send(`${b.dataset.agentNext==="sleep"?"Put":"Wake"} agent ${b.dataset.agentCommand}${b.dataset.agentNext==="sleep"?" to sleep because it is not needed right now.":"."}`);
      if(b.dataset.action==="start-training"){training.start();return}
      if(b.dataset.action==="read-screen")ocr.readScreen();
      if(b.dataset.action==="analyze-screen")ocr.analyze();
      if(b.dataset.action==="use-ocr")ocr.useAsContext();
      if(b.dataset.action==="copy-ocr")ocr.copy();
      if(b.dataset.action==="attach"){references.choose();return}
      if(b.dataset.action==="new-file"){files.newFile(b.dataset.fileScope||"project",b.dataset.fileProject||null);return}
      if(b.dataset.action==="save-file"){files.save(b.dataset.fileScope||"project",b.dataset.fileProject||null);return}
      const actions={send:()=>chat.send(),voice:()=>state.isListening?voice.stop():voice.start(),stop:()=>chat.stop(),fullscreen:toggleFullscreen,"toggle-context":()=>$("#context-panel").classList.toggle("collapsed"),"close-modal":closeProjectModal,"new-mission":openMission,"submit-mission":()=>{const text=$("#mission-input")?.value.trim();if(text){closeProjectModal();navigation.navigate("command");chat.send(text)}},"ask":()=>$("#command-input").focus(),"approve-boardroom":()=>chat.send("I explicitly approve the current Boardroom recommendation. Proceed with the approved action and report exactly what was executed."),notifications:()=>toast(state.notifications.join(" · ")),shortcuts:()=>toast("Command, Company, Training, Boardroom, Project, and Agent rooms keep separate conversations.")};actions[b.dataset.action]?.();
    });
    $("#command-input").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();chat.send()}});$("#command-input").addEventListener("input",e=>autoSize(e.target));
    $("#project-selector").addEventListener("change",e=>{selectProject(e.target.value);configureComposer();renderView()});
    $("#reference-upload").addEventListener("change",e=>references.upload([...e.target.files]));
    document.addEventListener("keydown",e=>{if(e.key==="Escape")closeProjectModal()});
    document.addEventListener("input",e=>{if(e.target.id==="memory-search"){const q=e.target.value.toLowerCase();$("#memory-grid").innerHTML=memoryCards(state.memories.filter(m=>(m.title+m.summary+m.category).toLowerCase().includes(q)))}if(e.target.id==="activity-search")filterActivity()});
    document.addEventListener("change",e=>{if(["activity-project-filter","activity-type-filter"].includes(e.target.id))filterActivity()});
    document.addEventListener("visibilitychange",()=>{state.visible=!document.hidden;rituBridge.syncScreen()});window.addEventListener("resize",resizeCanvas);
  }
  function toggleFullscreen(){if(!document.fullscreenElement)document.documentElement.requestFullscreen?.().catch(()=>toast("Fullscreen is unavailable."));else document.exitFullscreen?.()}
  const canvas=$("#particle-canvas"),ctx=canvas.getContext("2d"),particles=Array.from({length:42},()=>({x:Math.random(),y:Math.random(),r:Math.random()*1.2+.3,v:Math.random()*.00015+.00004}));
  function resizeCanvas(){canvas.width=innerWidth*devicePixelRatio;canvas.height=innerHeight*devicePixelRatio;ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0)}
  function animate(){if(state.visible&&!matchMedia("(prefers-reduced-motion: reduce)").matches){ctx.clearRect(0,0,innerWidth,innerHeight);ctx.fillStyle="rgba(117,217,232,.45)";particles.forEach(p=>{p.y-=p.v;if(p.y<0)p.y=1;ctx.beginPath();ctx.arc(p.x*innerWidth,p.y*innerHeight,p.r,0,Math.PI*2);ctx.fill()})}requestAnimationFrame(animate)}
  function clock(){const d=new Date();$("#clock").innerHTML=`<b>${d.toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})}</b><small>${d.toLocaleDateString([],{weekday:"short",day:"2-digit",month:"short"}).toUpperCase()}</small>`}
  async function init(){bind();await rituBridge.init();await company.refresh(false);$("#project-selector").innerHTML=state.projects.map(p=>`<option value="${safe(p.id)}">${safe(p.name)}</option>`).join("");if(state.activeProjectId)selectProject(state.activeProjectId);navigation.init();ollama.init();ocr.init();resizeCanvas();animate();clock();setInterval(clock,1000);setInterval(()=>rituBridge.syncScreen(),15000);setInterval(()=>{if(state.visible)rituBridge.refreshHealth()},5000);setInterval(()=>{if(state.visible&&state.backend.online)company.refresh()},2000)}
  window.setRituState=s=>rituCore.set(s);window.navigateTo=v=>navigation.navigate(v);window.sendMessage=()=>chat.send();window.startVoiceInput=()=>voice.start();window.stopVoiceInput=()=>voice.stop();window.readScreen=()=>ocr.readScreen();window.openProjectModal=openProjectModal;window.closeProjectModal=closeProjectModal;window.openProjectBoardroom=openProjectBoardroom;window.selectProject=selectProject;window.updateAgentStatus=(id,s)=>{const a=agent(id);if(a){a.status=s;renderView()}};window.moveTask=(id,s)=>tasks.move(id,s);window.addActivity=addActivity;window.saveApplicationState=()=>StorageController.save();window.loadApplicationState=()=>StorageController.load();window.toggleContextPanel=()=>$("#context-panel").classList.toggle("collapsed");window.toggleFullscreen=toggleFullscreen;
  init();
})();