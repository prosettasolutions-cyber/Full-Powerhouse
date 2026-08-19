window.RITU_DEMO_DATA = {
  projects: [
    {id:"p1",name:"PowerHouse Cognitive Organization",type:"AI Agent",objective:"Build an operating model where specialized AI agents coordinate execution.",health:"Strong",priority:"Critical",progress:74,phase:"Integration",milestone:"Executive review",last:"8 min ago",agents:["a1","a2","a4","a6"],owner:"Prashant",blocker:"Approval of agent autonomy policy",risks:["Cross-agent context drift","Approval latency"],files:["Organization Blueprint.md","Agent Charter.pdf"]},
    {id:"p2",name:"Ritu Desktop Companion",type:"Desktop Application",objective:"Create a private, always-available desktop companion with voice and memory.",health:"Watch",priority:"High",progress:58,phase:"Prototype",milestone:"Voice loop validation",last:"14 min ago",agents:["a2","a3","a4","a5"],owner:"Prashant",blocker:"Wake-word reliability",risks:["Microphone permissions","Background resource use"],files:["Desktop UX.fig","Voice Architecture.md"]},
    {id:"p3",name:"MSI Financier Intelligence",type:"SaaS Product",objective:"Turn finance operations into an auditable intelligence workspace.",health:"Strong",priority:"High",progress:43,phase:"Discovery",milestone:"Data model sign-off",last:"31 min ago",agents:["a1","a4","a6"],owner:"Finance Team",blocker:"Sample ledger access",risks:["Source data quality"],files:["Research Notes.md","Data Map.csv"]},
    {id:"p4",name:"Ritu Web Command Center",type:"Website",objective:"Deliver a cinematic, credible command interface for Ritu.",health:"Strong",priority:"Critical",progress:86,phase:"Quality Review",milestone:"Experience approval",last:"Now",agents:["a1","a2","a3","a5","a7"],owner:"Prashant",blocker:"None",risks:["Information density at tablet widths"],files:["Command Center.html","Interaction Spec.md"]}
  ],
  agents: [
    {id:"a1",name:"Product Strategist",role:"Frames objectives and decisions",status:"Working",project:"p1",task:"Preparing executive synthesis",progress:78,capabilities:["Strategy","Prioritization"],dependencies:"Research Analyst",last:"2 min ago",signal:"Excellent"},
    {id:"a2",name:"UI/UX Designer",role:"Designs interaction systems",status:"Reviewing",project:"p4",task:"Auditing command hierarchy",progress:91,capabilities:["UX","Visual systems"],dependencies:"Product Strategist",last:"Now",signal:"Strong"},
    {id:"a3",name:"Frontend Developer",role:"Builds responsive interfaces",status:"Working",project:"p4",task:"Completing live interface",progress:87,capabilities:["JavaScript","Accessibility"],dependencies:"UI/UX Designer",last:"Now",signal:"Excellent"},
    {id:"a4",name:"Backend Developer",role:"Builds services and data flows",status:"Waiting",project:"p2",task:"Awaiting API contract",progress:62,capabilities:["APIs","Databases"],dependencies:"Product Strategist",last:"12 min ago",signal:"Strong"},
    {id:"a5",name:"QA Engineer",role:"Validates behavior and resilience",status:"Working",project:"p4",task:"Testing state persistence",progress:68,capabilities:["Testing","Risk analysis"],dependencies:"Frontend Developer",last:"4 min ago",signal:"Strong"},
    {id:"a6",name:"Research Analyst",role:"Finds and synthesizes evidence",status:"Completed",project:"p3",task:"Market scan delivered",progress:100,capabilities:["Research","Synthesis"],dependencies:"None",last:"18 min ago",signal:"Excellent"},
    {id:"a7",name:"DevOps Engineer",role:"Coordinates delivery systems",status:"Reviewing",project:"p4",task:"Reviewing deployment readiness",progress:81,capabilities:["Delivery","Observability"],dependencies:"QA Engineer",last:"6 min ago",signal:"Strong"}
  ],
  tasks: [
    {id:"t1",title:"Approve autonomy policy",project:"p1",agent:"a1",priority:"Critical",due:"Today",progress:20,dependency:"Executive input",approval:true,status:"Proposed"},
    {id:"t2",title:"Finalize voice interaction loop",project:"p2",agent:"a3",priority:"High",due:"Tomorrow",progress:46,dependency:"Wake word test",approval:false,status:"In Progress"},
    {id:"t3",title:"Map finance source systems",project:"p3",agent:"a6",priority:"High",due:"Aug 01",progress:70,dependency:"Ledger sample",approval:true,status:"Blocked"},
    {id:"t4",title:"Responsive command workspace",project:"p4",agent:"a3",priority:"Critical",due:"Today",progress:88,dependency:"UX review",approval:false,status:"Review"},
    {id:"t5",title:"Accessibility verification",project:"p4",agent:"a5",priority:"High",due:"Today",progress:64,dependency:"Interface complete",approval:false,status:"In Progress"},
    {id:"t6",title:"Define memory retention rules",project:"p1",agent:"a4",priority:"Medium",due:"Aug 03",progress:0,dependency:"Policy approval",approval:true,status:"Planned"},
    {id:"t7",title:"Market research synthesis",project:"p3",agent:"a6",priority:"Medium",due:"Jul 25",progress:100,dependency:"None",approval:false,status:"Completed"}
  ],
  memories: [
    {title:"Ritu should be direct, calm, and proactive",summary:"Prefer concise recommendations with clear next actions.",category:"User preferences",source:"Boardroom",confidence:98,created:"Jul 12",used:"Today",projects:["p1","p4"]},
    {title:"Cinematic without imitation",summary:"Use original spatial, orbital, and glass motifs; avoid branded sci-fi references.",category:"Product principles",source:"Project brief",confidence:100,created:"Jul 20",used:"Today",projects:["p4"]},
    {title:"Local-first companion architecture",summary:"Sensitive memory stays local; cloud models are optional accelerators.",category:"Technical architecture",source:"Decision D-14",confidence:94,created:"Jul 15",used:"Yesterday",projects:["p2"]},
    {title:"Finance outputs require traceability",summary:"Every conclusion needs a source, timestamp, and confidence signal.",category:"Business knowledge",source:"MSI workshop",confidence:91,created:"Jul 18",used:"Jul 24",projects:["p3"]}
  ],
  activities: [
    {type:"Ritu response",text:"Command Center moved into quality review.",project:"p4",agent:"Ritu",priority:"High",time:"Now"},
    {type:"Agent started",text:"QA Engineer began persistence verification.",project:"p4",agent:"a5",priority:"Medium",time:"4 min ago"},
    {type:"Decision requested",text:"Autonomy policy requires executive approval.",project:"p1",agent:"a1",priority:"Critical",time:"8 min ago"},
    {type:"File generated",text:"Voice Architecture.md was updated.",project:"p2",agent:"a4",priority:"Medium",time:"14 min ago"},
    {type:"Task completed",text:"Market research synthesis delivered.",project:"p3",agent:"a6",priority:"Low",time:"18 min ago"}
  ],
  chats: {
    p4:[{sender:"Ritu",time:"09:42",text:"The command center is structurally complete. I am coordinating interaction review and accessibility verification.",kind:"Project update"},{sender:"You",time:"09:44",text:"Keep the interface alive, but disciplined. It should feel operational rather than decorative."}],
    p1:[{sender:"Ritu",time:"Yesterday",text:"The organization model is coherent. One decision remains: how much autonomy should agents have before approval?"}],
    p2:[{sender:"Ritu",time:"Yesterday",text:"Voice-loop testing found inconsistent wake-word behavior. I recommend push-to-talk for the first release."}],
    p3:[{sender:"Ritu",time:"Jul 24",text:"The data model is ready for review once a representative ledger sample is available."}]
  },
  notifications:["Autonomy policy needs approval","Command Center ready for review","Voice test requires a decision"]
};
