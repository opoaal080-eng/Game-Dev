/* ASHFALL · Public player site. Every public fact is editorially approved in Nightwell Dev. */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const API = "https://nightwell-dev-web-production.up.railway.app/api/public/ashfall/";
  const DEFAULT = {
    title:"ASHFALL",eyebrow:"NIGHTWELL · ИГРОВОЙ ПРОЕКТ",
    tagline:"Официальный сайт проекта",published:false,
    introduction:"Подробности игрового проекта ASHFALL появятся здесь по мере публикации командой разработчиков.",
    story_teaser:"",world_description:"",feature_lines:[],genre:"",platforms:"",
    development_status:"",release_window:"",hero_image_url:"",trailer_url:"",
    screenshots:[],community_url:"",telegram_url:"",wishlist_url:"",
    news:[],updated_at:null
  };
  let current = DEFAULT;

  function elem(tag,className,text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = String(text);
    return el;
  }
  function link(url) {
    try {
      const parsed = new URL(url);
      if (parsed.protocol !== "https:" || parsed.username || parsed.password) return "";
      return parsed.href;
    } catch (_) { return ""; }
  }
  function plain(value, fallback="") {
    return typeof value === "string" && value.trim() ? value.trim() : fallback;
  }
  function lines(value, max=12) {
    if (Array.isArray(value)) return value.filter(x=>typeof x==="string"&&x.trim()).slice(0,max);
    return typeof value==="string" ? value.split("\n").map(x=>x.trim()).filter(Boolean).slice(0,max) : [];
  }
  function date(value) {
    try {
      const d = new Date(value);
      if (Number.isNaN(d.valueOf())) return "";
      return d.toLocaleDateString("ru-RU",{year:"numeric",month:"long",day:"numeric"});
    } catch (_) { return ""; }
  }
  function update(data) {
    if (!data || typeof data !== "object") return;
    const page = data.published === true ? {...DEFAULT,...data} : DEFAULT;
    current = page;
    const set = (id,value) => { if ($(id)) $(id).textContent=value; };
    set("eyebrow",plain(page.eyebrow,"NIGHTWELL · ИГРОВОЙ ПРОЕКТ"));
    set("hero-title",plain(page.title,"ASHFALL").toUpperCase());
    // Retain brand typography and colored dot independently of dynamic title.
    const dot=elem("span","hero-period",".");
    $("hero-title").append(dot);
    set("hero-tagline",plain(page.tagline,"Официальный сайт проекта"));
    set("game-genre",plain(page.genre,"БУДЕТ ОБЪЯВЛЕН").toUpperCase());
    set("game-platforms",plain(page.platforms,"БУДУТ ОБЪЯВЛЕНЫ").toUpperCase());
    set("game-status",plain(page.development_status,"В РАЗРАБОТКЕ").toUpperCase());
    set("game-intro",plain(page.introduction,DEFAULT.introduction));
    const teaser=$("game-story");
    teaser.hidden=!plain(page.story_teaser);
    teaser.textContent=plain(page.story_teaser);
    set("game-release",plain(page.release_window,"ИНФОРМАЦИЯ О РЕЛИЗЕ ПОЗЖЕ").toUpperCase());
    const hero=$("hero-image"),heroUrl=link(page.hero_image_url);
    if (heroUrl) {
      hero.src=heroUrl;hero.hidden=false;hero.referrerPolicy="no-referrer";
      hero.onerror=()=>{hero.hidden=true};
    } else {hero.hidden=true;hero.removeAttribute("src");}
    const world = $("world"), worldText = plain(page.world_description);
    world.hidden=!worldText;
    set("world-description",worldText);
    const features=$("features"), featureGrid=$("features-grid");
    featureGrid.replaceChildren();
    const featureItems=lines(page.feature_lines);
    features.hidden=featureItems.length===0;
    featureItems.forEach((value,idx)=>{
      const card=elem("article","feature");
      card.append(elem("span","feature-number",String(idx+1).padStart(2,"0")+" / ASHFALL"),
        elem("p","",value));
      featureGrid.append(card);
    });
    const gallery=$("gallery"),media=$("media");
    gallery.replaceChildren();
    const imageUrls=lines(page.screenshots,16).map(link).filter(Boolean);
    imageUrls.forEach((url,idx)=>{
      const wrap=elem("a","");wrap.href=url;wrap.target="_blank";wrap.rel="noopener noreferrer";
      wrap.setAttribute("aria-label","Открыть скриншот "+(idx+1));
      const image=elem("img","");image.src=url;image.loading="lazy";image.alt="ASHFALL, скриншот "+(idx+1);
      image.referrerPolicy="no-referrer";
      wrap.append(image);gallery.append(wrap);
    });
    const trailerUrl=link(page.trailer_url),trailer=$("trailer-link");
    trailer.hidden=!trailerUrl;
    if (trailerUrl) trailer.href=trailerUrl;
    media.hidden=!imageUrls.length&&!trailerUrl;
    const newsGrid=$("news-grid");
    newsGrid.replaceChildren();
    const news=Array.isArray(page.news) ? page.news.slice(0,12) : [];
    if (!news.length) {
      const empty=elem("div","news-empty");
      empty.append(elem("span","","/// 001"),elem("p","","Здесь скоро появятся новости проекта."));
      newsGrid.append(empty);
    }
    news.forEach((item)=>{
      if (!item||typeof item!=="object")return;
      const card=elem("details","news-item");
      const head=elem("summary","");
      head.append(elem("span","news-date",date(item.date)||"ОБНОВЛЕНИЕ"),
        elem("h3","",plain(item.title,"Новости ASHFALL")),
        elem("p","",plain(item.summary)),
        elem("span","news-more","ПОДРОБНЕЕ ↗"));
      card.append(head);
      if (plain(item.content)) {
        const description=elem("p","news-description",item.content);
        description.style.whiteSpace="pre-line";
        card.append(description);
      }
      newsGrid.append(card);
    });
    const socials=$("social-links");socials.replaceChildren();
    const choices=[
      ["СООБЩЕСТВО",page.community_url],["TELEGRAM",page.telegram_url],
      ["ДОБАВИТЬ В ЖЕЛАЕМОЕ",page.wishlist_url],
    ];
    let socialCount=0;
    choices.forEach(([label,raw])=>{
      const url=link(raw);
      if(!url)return;
      const a=elem("a","",label+" ↗");a.href=url;a.target="_blank";a.rel="noopener noreferrer";
      socials.append(a);socialCount++;
    });
    if(!socialCount)socials.append(elem("span","awaiting","Официальные ссылки появятся позже."));
    set("update-time",page.updated_at?"ОБНОВЛЕНО "+date(page.updated_at).toUpperCase():"IN DEVELOPMENT");
  }
  async function getJSON(url,timeoutMs) {
    const controller=new AbortController(),handle=setTimeout(()=>controller.abort(),timeoutMs);
    try{
      const res=await fetch(url,{signal:controller.signal,cache:"no-store",credentials:"omit"});
      if(!res.ok)throw new Error("HTTP "+res.status);
      const json=await res.json();
      return json&&typeof json==="object"?json:null;
    }finally{clearTimeout(handle)}
  }
  async function load() {
    // Static JSON is always hosted alongside the website on GitHub Pages.
    // An optional live request upgrades content for players with Railway access.
    let snapshot=null;
    try {snapshot=await getJSON("./data/public.json",5500)} catch (_) {}
    if (snapshot)update(snapshot);
    try{
      const live=await getJSON(API,3500);
      if (live)update(live);
    }catch (_) {
      // A blocked backend must never prevent players seeing the cached public site.
    }
  }
  const trigger=$("menu-trigger"),menu=$("mobile-nav");
  function closeMenu(){menu.hidden=true;trigger.setAttribute("aria-expanded","false")}
  trigger?.addEventListener("click",()=>{
    const open=menu.hidden;menu.hidden=!open;trigger.setAttribute("aria-expanded",String(open));
  });
  menu?.querySelectorAll("a").forEach(a=>a.addEventListener("click",closeMenu));
  window.addEventListener("keydown",ev=>{if(ev.key==="Escape")closeMenu()});
  document.querySelectorAll(".desktop-nav a").forEach(a=>a.addEventListener("click",closeMenu));
  update(DEFAULT);
  load();
})();
