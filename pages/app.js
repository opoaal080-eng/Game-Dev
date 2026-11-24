/* Nightwell Dev · GitHub Pages client · all private content comes from authenticated API. */
"use strict";
(() => {
  const API = "https://nightwell-dev-web-production.up.railway.app/api/v1/";
  const LABELS = {home:"Главная",info:"Информация",journal:"Дневник",docs:"Документация",tasks:"Задачи",files:"Файлы",team:"Команда",player:"Сайт ASHFALL"};
  const STATUSES = {todo:"К выполнению",progress:"В работе",review:"На проверке",done:"Готово"};
  const PRIORITIES = {low:"Низкий",normal:"Обычный",high:"Высокий",critical:"Критический"};
  const KINDS = {devlog:"Дневник",doc:"Документация",note:"Заметка",meeting:"Встреча",decision:"Решение"};
  const state = { token:sessionStorage.getItem("nwdev_token")||"",
    user:null,projects:[],currentProject:0,posts:[],tasks:[],files:[],team:[],home:null,
    info:null,events:[],characters:[],playerSite:null,playerLoading:false,playerError:"",view:"home",query:"" };
  const $ = (id) => document.getElementById(id);
  const node = (tag,cls,text) => {
    const item=document.createElement(tag);
    if(cls)item.className=cls;
    if(text!==undefined && text!==null)item.textContent=String(text);
    return item;
  };
  const add = (parent,...children) => {
    for(const child of children){if(child===null||child===undefined)continue;
      if(Array.isArray(child))add(parent,...child);else if(typeof child==="string")parent.append(document.createTextNode(child));else parent.append(child);}
    return parent;
  };
  const title = (text,tag="h3") => node(tag,"",text);
  const sub = (text) => node("p","muted",text);
  const line = (text) => node("span","overline",text);
  const box = (...children) => add(node("div","card"),...children);
  const small = (text) => node("small","",text);
  const action = (text,click,kind="secondary") => {
    const b=node("button","btn btn-"+kind,text);b.type="button";b.addEventListener("click",click);return b;
  };
  const errorText = (e) => e instanceof Error ? e.message : String(e);
  let toastTimer;
  function toast(msg) {
    const t=$("toast");t.textContent=msg;t.hidden=false;clearTimeout(toastTimer);
    toastTimer=setTimeout(()=>{t.hidden=true},4500);
  }
  function errorOnLogin(message){
    const target=$("login-error");
    target.textContent=message;target.hidden=false;
  }
  function apiOfflineError(){
    return "Интерфейс GitHub Pages доступен, но не получается связаться с API Railway. Если у тебя заблокирован Railway, вход и данные пока не заработают. Нужен другой доступный сервер API.";
  }
  async function api(path,options={}) {
    const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),16000);
    const headers={Accept:"application/json"};
    if(state.token)headers.Authorization="Bearer "+state.token;
    const init={method:options.method||"GET",headers,signal:ctrl.signal,cache:"no-store",mode:"cors"};
    if(options.data instanceof FormData)init.body=options.data;
    else if(options.data!==undefined){headers["Content-Type"]="application/json";init.body=JSON.stringify(options.data);}
    let response;
    try {response=await fetch(API+path.replace(/^\//,""),init)}
    catch(e){throw new Error(apiOfflineError())}
    finally{clearTimeout(timer)}
    if(options.binary){
      if(!response.ok)throw new Error("Не удалось скачать файл: HTTP "+response.status);
      return await response.blob();
    }
    const raw=await response.text();
    let parsed={};try{parsed=raw?JSON.parse(raw):{}}catch(e){throw new Error("Сервер прислал неожиданный ответ (HTTP "+response.status+")")}
    if(!response.ok){
      if(response.status===401 && path!=="auth/login/"){state.token="";sessionStorage.removeItem("nwdev_token");showLogin();}
      let detail=parsed.error||("Ошибка HTTP "+response.status);
      if(parsed.fields)detail+=" · "+Object.entries(parsed.fields).map(([k,v])=>k+": "+JSON.stringify(v)).join("; ").slice(0,350);
      throw new Error(detail);
    }
    return parsed;
  }
  const canEdit = () => !!state.user?.can_write;
  const ownProject = () => state.projects.find(p=>p.id===state.currentProject);
  const inProject = (items) => items.filter(x=>Number(x.project_id)===Number(state.currentProject));
  const datestr = (iso)=>{try{return new Date(iso).toLocaleDateString("ru-RU",{day:"numeric",month:"short",year:"numeric"})}catch(e){return iso||""}};
  const fileSize = (n)=>n>1048576?(n/1048576).toFixed(1)+" МБ":n>1024?(n/1024).toFixed(1)+" КБ":(n||0)+" Б";
  function showLogin(){
    $("login-screen").hidden=false;$("workspace").hidden=true;
    closeModal();closeSheet();
  }
  function showWorkspace(){
    $("login-screen").hidden=true;$("workspace").hidden=false;
    $("user-avatar").textContent=(state.user?.username||"N").slice(0,1).toUpperCase();
    $("top-avatar").textContent=(state.user?.username||"N").slice(0,1).toUpperCase();
    $("sidebar-username").textContent=state.user?.name||state.user?.username||"Разработчик";
    $("sidebar-role").textContent={admin:"Администратор",developer:"Разработчик",viewer:"Наблюдатель"}[state.user?.role]||"Участник";
    document.querySelectorAll("[data-writer-only]").forEach(x=>{x.hidden=!canEdit()});
    const picker=$("project-picker");picker.replaceChildren();
    state.projects.forEach(p=>{const opt=node("option","",p.name);opt.value=String(p.id);picker.add(opt)});
    picker.value=String(state.currentProject);
    render();
  }
  async function loadAll(){
    const [me,projects,home,posts,tasks,files,team] = await Promise.all([
      api("me/"),api("projects/"),api("dashboard/"),api("posts/"),api("tasks/"),api("files/"),api("team/")
    ]);
    state.user=me.user;
    state.projects=projects.items||[];
    state.home=home;
    state.posts=posts.items||[];
    state.tasks=tasks.items||[];
    state.files=files.items||[];
    state.team=team.items||[];
    if(!state.projects.some(x=>x.id===state.currentProject))state.currentProject=state.projects[0]?.id||0;
    if(state.currentProject)await loadInfo();
    showWorkspace();
  }
  async function loadInfo(){
    if(!state.currentProject){state.info=null;state.events=[];state.characters=[];return}
    const b=await api("information/"+state.currentProject+"/");
    state.info=b.info;state.events=b.events||[];state.characters=b.characters||[];
  }
  async function refresh(){
    try{await loadAll();toast("Данные обновлены")}catch(e){toast(errorText(e))}
  }
  async function logout(){
    try{if(state.token)await api("auth/logout/",{method:"POST"})}catch(e){}
    state.token="";state.user=null;
    sessionStorage.removeItem("nwdev_token");
    showLogin();
    $("login-form").reset();
    $("login-error").hidden=true;
  }
  function buildHead(caption,heading,description,buttons=[]){
    const head=node("div","page-head"),left=node("div","");
    add(left,line(caption),title(heading,"h1"),sub(description));
    add(head,left,...buttons);return head;
  }
  function listRow(icon,heading,meta,callback){
    const row=node("div","list-row");
    const left=node("div","row-main");
    add(left,title(heading,"b"),small(meta));
    add(row,node("span","list-icon",icon),left);
    if(callback)add(row,action("Открыть ↗",callback));
    return row;
  }
  function view(name){
    state.view=name;state.query="";closeSheet();
    const active=name in LABELS?name:"home";
    document.querySelectorAll("[data-view]").forEach(b=>b.classList.toggle("active",b.dataset.view===active));
    $("top-label").textContent=LABELS[active];
    render();window.scrollTo({top:0,behavior:"smooth"});
  }
  function render(){
    const c=$("content");c.replaceChildren();
    const page=state.view in LABELS?state.view:"home";
    ({home:renderHome,info:renderInfo,journal:()=>renderPosts(false),docs:()=>renderPosts(true),
      tasks:renderTasks,files:renderFiles,team:renderTeam,player:renderPlayer})[page](c);
  }
  function renderHome(c){
    add(c,buildHead("NIGHTWELL STUDIO / РАБОЧЕЕ ПРОСТРАНСТВО","Твоя команда.","Здесь собираются идеи, события и задачи команды Nightwell Studio."));
    const hero=node("section","hero");
    add(hero,line("РАБОЧЕЕ ПРОСТРАНСТВО КОМАНДЫ"),title("Все идеи.\nОдна история.","h2"),
      sub("От первых заметок до проработанного мира игры."),
      action("Информация об игре ↗",()=>view("info"),"primary"));
    c.append(hero);
    const counts=state.home?.counts||{};
    const stats=node("div","stat-grid");
    [["Записи",counts.posts||0,"▤"],["Активные задачи",counts.tasks||0,"☷"],["Файлы",counts.files||0,"▣"],["Участники",counts.members||0,"♧"]].forEach(([label,n,icon])=>{
      const item=box(node("span","stat-icon",icon),node("span","",label),title(n,"strong"));item.classList.add("stat");stats.append(item)});
    c.append(stats);
    const columns=node("div","two-col"),recent=box(title("Последние публикации","h2")),tasks=box(title("Актуальные задачи","h2"));
    const ps=inProject(state.posts).slice(0,6),ts=inProject(state.tasks).filter(t=>t.status!=="done").slice(0,6);
    if(!ps.length)add(recent,node("div","empty","Публикаций пока нет"));
    ps.forEach(p=>add(recent,listRow("▤",p.title,p.author+" · "+(KINDS[p.kind]||p.kind),()=>viewPost(p))));
    if(!ts.length)add(tasks,node("div","empty","Активных задач пока нет"));
    ts.forEach(t=>add(tasks,listRow("☷",t.title,(STATUSES[t.status]||t.status)+" · "+(PRIORITIES[t.priority]||t.priority),()=>view("tasks"))));
    add(columns,recent,tasks);c.append(columns);
  }
  function renderInfo(c){
    const p=ownProject(),i=state.info||{};
    add(c,buildHead("GAME BIBLE / ИСТОРИЯ И КОНЦЕПЦИЯ","Информация.","Жанр, сюжет, мир, персонажи и события проекта.",
      canEdit()?[action("Редактировать",()=>editInfo(),"primary")]:[]));
    const hero=node("section","hero");
    add(hero,line("ИНФОРМАЦИЯ О ПРОЕКТЕ"),title(i.title||p?.name||"Игра","h2"),sub(i.tagline||p?.description||"Опишите идею игры и её особенности."));
    const chips=node("div","filter-row");
    [i.genre||"Жанр не указан",i.engine||"Движок не указан",i.development_status||"В разработке"].forEach(s=>chips.append(node("span","pill",s)));
    hero.append(chips);c.append(hero);
    const grid=node("div","bible-grid");
    [["Сюжет","story"],["Мир и сеттинг","setting"],["Геймплей","gameplay"],["Лор и предыстория","universe"],["Темы и атмосфера","themes"],["Прочее","notes"]].forEach(([label,key],ix)=>{
      const b=box(line("0"+(ix+1)+" / GAME BIBLE"),title(label,"h2"),sub(i[key]||"Информация пока не заполнена."));
      if(ix===0)b.classList.add("wide");grid.append(b);
    });
    c.append(grid);
    const evHead=node("div","section-head");add(evHead,title("События и хронология","h2"),
      canEdit()?action("＋ Событие",()=>editEvent(null)):null);
    c.append(evHead);
    const timeline=node("div","timeline");
    const events=[...state.events].sort((a,b)=>a.order-b.order);
    if(!events.length)timeline.append(node("div","empty","Добавьте первое событие или главу сюжета."));
    events.forEach(event=>{
      const meta=node("div","filter-row");
      add(meta,node("span","pill",event.chapter||"Событие "+event.order),node("span","pill",event.kind==="main"?"Основная линия":event.kind==="side"?"Побочная линия":"Предыстория"));
      if(event.spoiler)meta.append(node("span","pill","Спойлер"));
      const details=node("details",""),summary=node("summary","muted","Полное описание");
      add(details,summary,sub(event.description||event.summary||"Описание ещё не добавлено"),
        sub(event.location?"Место: "+event.location:""),sub(event.participants?"Участники: "+event.participants:""),
        sub(event.consequences?"Последствия: "+event.consequences:""));
      const b=box(meta,title(event.title,"h3"),sub(event.summary),details);
      if(canEdit())b.append(action("Редактировать",()=>editEvent(event)));
      timeline.append(b);
    });
    c.append(timeline);
    const peopleHead=node("div","section-head");add(peopleHead,title("Персонажи","h2"),
      canEdit()?action("＋ Персонаж",()=>editCharacter(null)):null);c.append(peopleHead);
    const people=node("div","character-grid");
    if(!state.characters.length)people.append(node("div","empty","Персонажи ещё не добавлены"));
    state.characters.forEach(p=>{
      const b=box(node("div","char-avatar",(p.name||"?").slice(0,1).toUpperCase()),title(p.name,"h3"),
        line(p.role||"Персонаж"),sub(p.bio||"Биография не заполнена."),p.faction?small("Фракция: "+p.faction):null);
      if(canEdit())b.append(action("Редактировать",()=>editCharacter(p)));people.append(b);
    });
    c.append(people);
  }
  function renderPosts(docs){
    const c=$("content"),name=docs?"Документация.":"Дневник.";
    add(c,buildHead(docs?"БАЗА ЗНАНИЙ / МАТЕРИАЛЫ":"РАЗРАБОТКА / ЗАМЕТКИ",name,"Публикации и решения команды, синхронизированные с сервером.",
      canEdit()?[action("＋ Новая запись",()=>editPost(null,docs),"primary")]:[]));
    const filtered=inProject(state.posts).filter(p=>docs?p.kind==="doc":p.kind!=="doc");
    const cards=node("div","stack");
    if(!filtered.length)cards.append(node("div","empty","В этом разделе пока нет публикаций."));
    filtered.forEach(p=>{
      const b=box(line((KINDS[p.kind]||p.kind).toUpperCase()),title(p.title,"h2"),sub((p.body||"").slice(0,320)),
        node("div","card-meta",(p.author||"")+" · "+datestr(p.updated_at)+(p.pinned?" · Закреплено":"")));
      const commands=node("div","filter-row");
      add(commands,action("Читать",()=>viewPost(p)),canEdit()&&(state.user.role==="admin"||state.user.id===p.author_id)?action("Изменить",()=>editPost(p,docs)):null);
      b.append(commands);cards.append(b);
    });c.append(cards);
  }
  function viewPost(p){
    const c=$("content");c.replaceChildren();
    const pre=node("div","filter-row");pre.append(action("← Назад",()=>view(p.kind==="doc"?"docs":"journal")));c.append(pre);
    add(c,buildHead((KINDS[p.kind]||p.kind).toUpperCase(),p.title,p.author+" · "+datestr(p.updated_at)));
    const body=box(line("СОДЕРЖАНИЕ"));
    body.append(renderDocBody(p));c.append(body);
  }

  function addScriptPanel(root, code, language) {
    const panel=node("section","script-panel");
    const head=node("div","script-panel-head");
    const label=node("span","",language||"Исходный код");
    const button=action("Копировать",async()=>{
      try{await navigator.clipboard.writeText(code);toast("Скрипт скопирован целиком")}
      catch(e){toast("Не удалось скопировать код")}
    });
    add(head,label,button);
    const pre=node("pre","script-panel-pre");
    pre.append(node("code","",code));
    add(panel,head,pre);root.append(panel);
  }
  function renderDocBody(post) {
    const root=node("div","doc-body");
    const text=String(post.body||"");
    if(post.content_mode==="code"){
      addScriptPanel(root,text,post.code_language||"Скрипт");
      return root;
    }
    const lines=text.replace(/\r\n?/g,"\n").split("\n");
    const tick=String.fromCharCode(96);
    const open=new RegExp("^ {0,3}(("+tick+"{3,}|~{3,}))(.*)$");
    let paragraph=[],index=0;
    const flush=()=>{
      if(!paragraph.length)return;
      const prose=node("div","doc-prose",paragraph.join("\n"));
      prose.style.whiteSpace="pre-wrap";root.append(prose);paragraph=[];
    };
    while(index<lines.length){
      const match=lines[index].match(open);
      if(!match){paragraph.push(lines[index++]);continue}
      flush();index++;
      const fence=match[1],lang=match[2].trim().slice(0,48);
      const chunk=[];
      const close=new RegExp("^ {0,3}"+fence[0]+"{"+fence.length+",}[ \\t]*$");
      while(index<lines.length && !close.test(lines[index])){
        chunk.push(lines[index++]);
      }
      if(index<lines.length)index++;
      addScriptPanel(root,chunk.join("\n"),lang||"Код");
    }
    flush();return root;
  }
  function renderTasks(c){
    add(c,buildHead("WORKFLOW / РАЗРАБОТКА","Задачи.","Канбан-доска с приоритетами и исполнителями.",
      canEdit()?[action("＋ Новая задача",()=>editTask(null),"primary")]:[]));
    const cols=node("div","task-columns");
    Object.entries(STATUSES).forEach(([key,label])=>{
      const col=node("div","task-column"),tasks=inProject(state.tasks).filter(t=>t.status===key);
      col.append(title(label+" · "+tasks.length,"h3"));
      tasks.forEach(t=>{
        const b=box(title(t.title,"b"),sub((t.description||"").slice(0,220)),
          node("span","pill",PRIORITIES[t.priority]||t.priority),node("div","card-meta",(t.assignee||"Не назначен")+(t.due_date?" · до "+t.due_date:"")));
        const mayEdit=canEdit()&&(state.user.role==="admin"||state.user.id===t.created_by_id||state.user.id===t.assignee_id);
        if(mayEdit)b.append(action("Изменить",()=>editTask(t)));
        col.append(b);
      });
      cols.append(col);
    });c.append(cols);
  }
  function renderFiles(c){
    add(c,buildHead("PRIVATE STORAGE / ФАЙЛЫ","Файлы.","Материалы проекта, доступные только после входа.",
      canEdit()?[action("＋ Загрузить",()=>uploadFile(),"primary")]:[]));
    const list=box();
    const files=inProject(state.files);
    if(!files.length)list.append(node("div","empty","Файлов пока нет"));
    files.forEach(f=>list.append(listRow("▣",f.title||f.original_name,
      fileSize(f.size)+" · "+f.original_name+" · "+f.uploader,()=>downloadFile(f))));
    c.append(list);
  }
  function renderTeam(c){
    add(c,buildHead("NIGHTWELL STUDIO / УЧАСТНИКИ","Команда.","Разработчики и роли проекта."));
    const grid=node("div","character-grid");
    state.team.forEach(m=>{
      const b=box(node("div","char-avatar",(m.username||"?").slice(0,1).toUpperCase()),
        title(m.name||m.username,"h3"),sub({admin:"Администратор",developer:"Разработчик",viewer:"Наблюдатель"}[m.role]||m.role),
        m.job_title?node("p","muted",m.job_title):null);
      grid.append(b);
    });c.append(grid);
  }

  function renderPlayer(c) {
    if (!canEdit()) {
      add(c,buildHead("ASHFALL","Доступ ограничен.","Редактирование публичного сайта доступно разработчикам."));
      return;
    }
    add(c,buildHead("ASHFALL / ПУБЛИКАЦИЯ ДЛЯ ИГРОКОВ","Сайт ASHFALL.",
      "Меняй контент, новости и ссылки публичного сайта. Закрытая информация Nightwell Dev не раскрывается.",
      [action("Редактировать сайт",editPlayerPage,"primary")]));
    const intro=box(title("Публичный сайт игры","h2"),
      sub("Основной адрес: https://afl.nightwell.fun/"),
      sub("Резервная публикация: GitHub Pages, обновляется по расписанию."),
      action("Открыть afl.nightwell.fun ↗",()=>window.open("https://afl.nightwell.fun/","_blank","noopener,noreferrer")),
      action("Открыть GitHub Pages ↗",()=>window.open("https://opoaal080-eng.github.io/Game-Dev/ashfall/","_blank","noopener,noreferrer")));
    c.append(intro);
    if(!state.playerSite) {
      c.append(node("div","empty",state.playerError||"Загружаем настройки публикации..."));
      if(!state.playerLoading&&!state.playerError) {
        state.playerLoading=true;
        api("player-site/").then(data=>{
          state.playerSite=data;
          if(state.view==="player")render();
        }).catch(e=>{
          state.playerError=errorText(e);
          if(state.view==="player")render();
        }).finally(()=>state.playerLoading=false);
      }
      return;
    }
    const site=state.playerSite.page||{};
    const status=node("span","pill",site.is_published?"ОПУБЛИКОВАНО":"ЧЕРНОВИК");
    add(c,box(line("РЕЖИМ ПУБЛИКАЦИИ"),status,
      title(site.title||"ASHFALL","h2"),sub(site.tagline||"Слоган игры пока не заполнен."),
      sub("Жанр: "+(site.genre||"не указан")+" · Платформы: "+(site.platforms||"не объявлены")),
      action("Изменить описание и ссылки",editPlayerPage)));
    const section=node("div","section-head");
    add(section,title("Новости для игроков","h2"),action("＋ Создать новость",()=>editPlayerNews(null),"primary"));c.append(section);
    const news=state.playerSite.news||[],cards=node("div","stack");
    if(!news.length)cards.append(node("div","empty","Публичных новостей ещё нет"));
    news.forEach(item=>{
      const card=box(line((item.is_published?"ОПУБЛИКОВАНО":"ЧЕРНОВИК")+" · "+(item.date||"")),
        title(item.title,"h3"),sub(item.summary||item.content||""),action("Изменить",()=>editPlayerNews(item)));
      cards.append(card);
    });
    c.append(cards);
  }

  function editPlayerPage() {
    const p=state.playerSite?.page;
    if(!p) {toast("Настройки ещё загружаются");return}
    const fields=[
      field("is_published","Публиковать сайт для игроков",p.is_published,"checkbox"),
      field("title","Название игры",p.title||"ASHFALL","text",{required:true}),
      field("eyebrow","Надпись над названием",p.eyebrow),
      field("tagline","Слоган",p.tagline),
      field("introduction","Описание для игроков",p.introduction,"textarea"),
      field("story_teaser","Завязка истории без спойлеров",p.story_teaser,"textarea"),
      field("world_description","Мир игры (публично)",p.world_description,"textarea"),
      field("feature_lines","Особенности (по одной на строку)",p.feature_lines,"textarea"),
      field("genre","Жанр",p.genre),
      field("platforms","Платформы",p.platforms),
      field("development_status","Стадия разработки",p.development_status),
      field("release_window","Дата или период релиза",p.release_window),
      field("hero_image_url","Ссылка на обложку, HTTPS",p.hero_image_url),
      field("trailer_url","Ссылка на видео, HTTPS",p.trailer_url),
      field("screenshots","Скриншоты (HTTPS, по одной ссылке в строке)",p.screenshots,"textarea"),
      field("wishlist_url","Ссылка на страницу игры",p.wishlist_url),
      field("community_url","Ссылка на сообщество",p.community_url),
      field("telegram_url","Ссылка на Telegram",p.telegram_url),
      field("contact_email","Email для связи",p.contact_email)
    ];
    editModal("Публичный сайт ASHFALL",fields,async data=>{
      await api("player-site/",{method:"PUT",data});
      state.playerSite=null;state.playerError="";
    });
  }

  function editPlayerNews(item) {
    const p=item||{};
    editModal(item?"Изменить новость":"Новая новость для игроков",[
      field("title","Заголовок",p.title,"text",{required:true}),
      field("summary","Краткое описание",p.summary),
      field("content","Полный текст",p.content,"textarea"),
      field("is_published","Показывать игрокам",p.is_published||false,"checkbox")
    ],async data=>{
      if(item)await api("player-site/news/"+item.id+"/",{method:"PATCH",data});
      else await api("player-site/news/",{method:"POST",data});
      state.playerSite=null;state.playerError="";
    });
  }

  function closeModal(){
    $("modal-backdrop").hidden=true;$("modal-form").onsubmit=null;
    $("modal-fields").replaceChildren();$("modal-error").hidden=true;
  }
  function closeSheet(){$("mobile-sheet").hidden=true;$("mobile-shade").hidden=true}
  function editModal(name,fields,submit){
    $("modal-title").textContent=name;
    const root=$("modal-fields");root.replaceChildren();
    fields.forEach(f=>{
      const label=node("label","",f.label);label.htmlFor="form-"+f.name;root.append(label);
      let input;
      if(f.type==="textarea")input=node("textarea","");
      else if(f.type==="select"){
        input=node("select","");
        (f.options||[]).forEach(([value,name])=>{const opt=node("option","",name);opt.value=value;input.add(opt)});
      }else{input=node("input","");input.type=f.type||"text"}
      input.id="form-"+f.name;input.name=f.name;input.value=f.value??"";
      if(f.type==="checkbox"){input.type="checkbox";input.checked=Boolean(f.value);}
      if(f.required)input.required=true;
      if(f.maxLength)input.maxLength=f.maxLength;
      root.append(input);
    });
    $("modal-error").hidden=true;$("modal-backdrop").hidden=false;
    $("modal-form").onsubmit=async(ev)=>{
      ev.preventDefault();
      const data={};fields.forEach(f=>{const inp=$("form-"+f.name);data[f.name]=inp.type==="checkbox"?inp.checked:inp.type==="number"?Number(inp.value):inp.value});
      const button=$("save-modal");button.disabled=true;
      try {await submit(data);closeModal();await loadAll();toast("Сохранено")}
      catch(e){const err=$("modal-error");err.textContent=errorText(e);err.hidden=false}
      finally{button.disabled=false}
    };
  }
  const field=(name,label,value="",type="text",extra={})=>({name,label,value,type,...extra});
  function editInfo(){
    const i=state.info||{};
    const fields=[
      field("title","Название игры",i.title),field("genre","Жанр",i.genre),
      field("tagline","Короткое описание",i.tagline),
      field("story","Сюжет",i.story,"textarea"),field("setting","Мир и сеттинг",i.setting,"textarea"),
      field("gameplay","Геймплей и механики",i.gameplay,"textarea"),
      field("universe","Лор",i.universe,"textarea"),
      field("themes","Темы и атмосфера",i.themes,"textarea"),
      field("platforms","Платформы",i.platforms),field("engine","Движок",i.engine),
      field("development_status","Стадия разработки",i.development_status),
      field("audience","Аудитория",i.audience),
      field("notes","Прочее",i.notes,"textarea")
    ];
    editModal("Информация об игре",fields,async data=>{await api("information/"+state.currentProject+"/",{method:"PUT",data})});
  }
  function editEvent(event){
    const e=event||{};
    const fields=[
      field("chapter","Акт или глава",e.chapter),
      field("title","Название события",e.title,"text",{required:true}),
      field("kind","Тип события",e.kind||"main","select",{options:[["main","Основное"],["side","Побочное"],["backstory","Предыстория"],["optional","Необязательное"]]}),
      field("order","Порядок",e.order||state.events.length+1,"number"),
      field("timeline","Время в сюжете",e.timeline),
      field("location","Место",e.location),field("participants","Участники",e.participants),
      field("summary","Краткое содержание",e.summary,"textarea"),
      field("description","Полное описание",e.description,"textarea"),
      field("consequences","Последствия",e.consequences,"textarea"),
      field("spoiler","Содержит спойлеры",e.spoiler||false,"checkbox")
    ];
    editModal(event?"Редактирование события":"Новое событие",fields,async data=>{
      if(event)await api("information/events/"+event.id+"/",{method:"PATCH",data});
      else await api("information/"+state.currentProject+"/events/",{method:"POST",data});
    });
  }
  function editCharacter(person){
    const p=person||{};
    const fields=[
      field("name","Имя",p.name,"text",{required:true}),
      field("role","Роль",p.role),field("faction","Фракция",p.faction),
      field("bio","Биография",p.bio,"textarea"),
      field("motivation","Цели и мотивация",p.motivation,"textarea"),
      field("notes","Прочее",p.notes,"textarea"),
      field("order","Порядок",p.order||1,"number")
    ];
    editModal(person?"Редактирование персонажа":"Новый персонаж",fields,async data=>{
      if(person)await api("information/characters/"+person.id+"/",{method:"PATCH",data});
      else await api("information/"+state.currentProject+"/characters/",{method:"POST",data});
    });
  }
  function editPost(post,docs){
    const p=post||{};
    editModal(post?"Редактировать запись":"Новая запись",[
      field("title","Заголовок",p.title,"text",{required:true,maxLength:180}),
      field("kind","Тип",p.kind||(docs?"doc":"note"),"select",{options:Object.entries(KINDS)}),
      field("status","Публикация",p.status||"published","select",{options:[["published","Опубликовано"],["draft","Черновик"]]}),
      field("content_mode","Отображение содержимого",p.content_mode||"markdown","select",{options:[["markdown","Текст и Markdown"],["code","Скрипт целиком, одним окном"]]}),
      field("code_language","Язык скрипта, например csharp, python, js",p.code_language||""),
      field("body","Содержимое документа или весь скрипт",p.body,"textarea",{required:true}),
      field("pinned","Закрепить",p.pinned||false,"checkbox")
    ],async data=>{
      data.project=post?.project_id||state.currentProject;
      if(post)await api("posts/"+post.id+"/",{method:"PATCH",data});
      else await api("posts/",{method:"POST",data});
    });
  }
  function editTask(task){
    const t=task||{};
    editModal(task?"Изменить задачу":"Новая задача",[
      field("title","Название задачи",t.title,"text",{required:true}),
      field("description","Описание",t.description,"textarea"),
      field("status","Статус",t.status||"todo","select",{options:Object.entries(STATUSES)}),
      field("priority","Приоритет",t.priority||"normal","select",{options:Object.entries(PRIORITIES)}),
      field("assignee","Исполнитель",t.assignee_id||"","select",{options:[["","Не назначен"],...state.team.map(u=>[String(u.id),u.username])]}),
      field("due_date","Срок",t.due_date||"","date")
    ],async data=>{
      data.project=task?.project_id||state.currentProject;
      if(task)await api("tasks/"+task.id+"/",{method:"PATCH",data});
      else await api("tasks/",{method:"POST",data});
    });
  }
  function uploadFile(){
    $("modal-title").textContent="Загрузка файла";
    const root=$("modal-fields");root.replaceChildren();
    const name=node("input","");name.type="file";name.id="upload-selector";name.required=true;
    add(root,node("label","","Выбери файл проекта"),name);
    const description=node("textarea","");description.id="upload-description";description.placeholder="Описание (необязательно)";
    add(root,node("label","","Описание"),description);
    $("modal-error").hidden=true;$("modal-backdrop").hidden=false;
    $("modal-form").onsubmit=async ev=>{
      ev.preventDefault();
      const file=name.files?.[0];if(!file)return;
      if(file.size>100*1024*1024){$("modal-error").textContent="Максимум 100 МБ";$("modal-error").hidden=false;return}
      const data=new FormData();data.append("project",String(state.currentProject));data.append("title",file.name);data.append("description",description.value);data.append("file",file);
      const button=$("save-modal");button.disabled=true;
      try{await api("files/",{method:"POST",data});closeModal();await loadAll();toast("Файл загружен")}
      catch(e){$("modal-error").textContent=errorText(e);$("modal-error").hidden=false}
      finally{button.disabled=false}
    };
  }
  async function downloadFile(file){
    try{
      const blob=await api(file.download_path.replace("/api/v1/",""),{binary:true});
      const url=URL.createObjectURL(blob),a=node("a","");
      a.href=url;a.download=file.original_name||file.title||"file";document.body.append(a);a.click();a.remove();
      setTimeout(()=>URL.revokeObjectURL(url),60000);
    }catch(e){toast(errorText(e))}
  }
  function changePassword(){
    editModal("Сменить пароль",[
      field("old_password","Текущий пароль","","password",{required:true}),
      field("new_password","Новый пароль","","password",{required:true})
    ],async data=>{
      await api("auth/password/",{method:"POST",data});
      state.token="";sessionStorage.removeItem("nwdev_token");showLogin();
      toast("Пароль изменён. Войди с новым паролем.");
    });
  }
  document.querySelectorAll("[data-view]").forEach(b=>b.addEventListener("click",()=>view(b.dataset.view)));
  document.querySelectorAll("[data-action]").forEach(b=>b.addEventListener("click",()=>b.dataset.action==="logout"?logout():changePassword()));
  $("refresh").addEventListener("click",refresh);
  $("project-picker").addEventListener("change",async e=>{
    state.currentProject=Number(e.target.value);
    try{await loadInfo();render()}catch(err){toast(errorText(err))}
  });
  $("more-button").addEventListener("click",()=>{$("mobile-sheet").hidden=false;$("mobile-shade").hidden=false});
  $("close-sheet").addEventListener("click",closeSheet);
  $("mobile-shade").addEventListener("click",closeSheet);
  $("close-modal").addEventListener("click",closeModal);
  $("cancel-modal").addEventListener("click",closeModal);
  $("modal-backdrop").addEventListener("click",e=>{if(e.target===e.currentTarget)closeModal()});
  window.addEventListener("keydown",e=>{if(e.key==="Escape"){closeModal();closeSheet()}});
  $("login-form").addEventListener("submit",async ev=>{
    ev.preventDefault();
    const b=$("login-button");b.disabled=true;$("login-error").hidden=true;
    try{
      const auth=await api("auth/login/",{method:"POST",data:{
        username:$("username").value.trim(),password:$("password").value,
        device_name:"GitHub Pages web client"
      }});
      state.token=auth.token;
      sessionStorage.setItem("nwdev_token",state.token);
      $("password").value="";
      await loadAll();
    }catch(e){errorOnLogin(errorText(e));if(!state.user){state.token="";sessionStorage.removeItem("nwdev_token")}}
    finally{b.disabled=false}
  });
  if(state.token){
    loadAll().catch(e=>{showLogin();errorOnLogin(errorText(e))});
  }else showLogin();
})();
