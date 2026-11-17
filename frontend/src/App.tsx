import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Preferences } from '@capacitor/preferences'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
type Climbing = { leading:number; where_leading:number; bouldering:number; where_bouldering:number; speed:boolean; alpinism:boolean; belay:number; belay_description:string }
type Profile = { user_id:number; first_name:string; last_name:string; city:string|null; description:string; goal:number; date_of_birth:string; sex:boolean; avatar:string|null; climbing:Climbing }
type Me = { id:number; email:string; profile:Omit<Profile,'climbing'|'date_of_birth'|'sex'|'avatar'> & {avatar:string|null}; climbing:Climbing }
type Chat = { id:number; members:number[]; online?:Record<string,boolean> }
type Message = { id:number; chat_id:number; sender_id:number; text:string; is_read?:boolean; created_at:string }
const emptyClimbing:Climbing = {leading:0,where_leading:0,bouldering:0,where_bouldering:0,speed:false,alpinism:false,belay:0,belay_description:''}
const grades=['—','5','6a/a+','6b/b+','6c/c+','7a/a+','7b/b','7c/c+','8a/a+','8b/b','8c/c+','9+']
type Tab='discover'|'chats'|'profile'

async function readToken(){ const {value}=await Preferences.get({key:'catchme_token'}); return value || localStorage.getItem('catchme_token') || '' }
async function saveToken(value:string){ await Preferences.set({key:'catchme_token',value}); localStorage.setItem('catchme_token',value) }
async function clearToken(){ await Preferences.remove({key:'catchme_token'}); localStorage.removeItem('catchme_token') }

function App(){
  const [token,setToken]=useState(''),[ready,setReady]=useState(false)
  const [tab,setTab]=useState<Tab>('discover'),[me,setMe]=useState<Me|null>(null)
  const [profiles,setProfiles]=useState<Profile[]>([]),[chats,setChats]=useState<Chat[]>([])
  const [activeChat,setActiveChat]=useState<number|null>(null),[messages,setMessages]=useState<Message[]>([])
  const [presence,setPresence]=useState<Record<string,boolean>>({}),[typingUser,setTypingUser]=useState<number|null>(null)
  const socketRef=useRef<WebSocket|null>(null)
  const [draft,setDraft]=useState(''),[city,setCity]=useState(''),[lookingFor,setLookingFor]=useState('')
  const [email,setEmail]=useState(''),[password,setPassword]=useState(''),[first,setFirst]=useState(''),[last,setLast]=useState('')
  const [birth,setBirth]=useState('1995-01-01'),[sex,setSex]=useState('false'),[register,setRegister]=useState(false)
  const [error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false)
  const request=useCallback(async(path:string,init:RequestInit={})=>{
    const mergedHeaders=new Headers(init.headers)
    if(!mergedHeaders.has('Content-Type') && !(init.body instanceof URLSearchParams)) mergedHeaders.set('Content-Type','application/json')
    if(token) mergedHeaders.set('Authorization','Bearer '+token)
    const response=await fetch(API+path,{...init,headers:mergedHeaders})
    const body=await response.json().catch(()=>({}))
    if(!response.ok) throw new Error(body.detail||'Ошибка запроса ('+response.status+')')
    return body
  },[token])
  const refreshMe=useCallback(async()=>{const data=await request('/me');setMe(data)},[request])
  const loadProfiles=useCallback(async()=>{
    const q=new URLSearchParams({limit:'24'}); if(city)q.set('city',city);if(lookingFor)q.set('looking_for',lookingFor)
    setProfiles(await request('/profiles?'+q.toString()))
  },[city,lookingFor,request])
  const loadChats=useCallback(async()=>{setChats(await request('/chats'))},[request])
  const loadMessages=useCallback(async(id:number)=>{setMessages(await request('/chats/'+id+'/messages'))},[request])
  useEffect(()=>{readToken().then(value=>{setToken(value);setReady(true)})},[])
  useEffect(()=>{if(!token)return;Promise.all([refreshMe(),loadProfiles(),loadChats()]).catch(e=>setError(e.message))},[token,refreshMe,loadProfiles,loadChats])
  useEffect(()=>{
    if(!token)return
    const wsBase=API.replace(/^http/,'ws').replace(/\\/api\\/v1$/,'/api/v1/ws')
    let disposed=false
    let retry:ReturnType<typeof setTimeout>|undefined
    const connect=()=>{
      if(disposed)return
      const socket=new WebSocket(wsBase+'?token='+encodeURIComponent(token))
      socketRef.current=socket
      socket.onmessage=(event)=>{
        try{
          const data=JSON.parse(event.data)
          if(data.type==='message' && data.message){
            const incoming=data.message as Message
            if(activeChat===incoming.chat_id)setMessages(old=>old.some(m=>m.id===incoming.id)?old:[...old,incoming])
            else loadChats().catch(()=>{})
          }else if(data.type==='presence')setPresence(old=>({...old,[String(data.user_id)]:!!data.online}))
          else if(data.type==='messages.read' && activeChat===data.chat_id)setMessages(old=>old.map(m=>m.sender_id===me?.id?{...m,is_read:true}:m))
          else if(data.type==='typing' && activeChat===data.chat_id)setTypingUser(data.active?data.user_id:null)
        }catch{/* Ignore malformed socket frames. */}
      }
      socket.onclose=()=>{
        if(socketRef.current===socket)socketRef.current=null
        if(!disposed)retry=setTimeout(connect,2000)
      }
    }
    connect()
    return ()=>{disposed=true;if(retry)clearTimeout(retry);socketRef.current?.close();socketRef.current=null}
  },[token,activeChat,me?.id,loadChats])

  useEffect(()=>{if(activeChat!==null){loadMessages(activeChat).catch(e=>setError(e.message));request('/chats/'+activeChat+'/presence').then(setPresence).catch(()=>{})}},[activeChat,loadMessages,request])
  async function authenticate(e:FormEvent){
    e.preventDefault();setBusy(true);setError('')
    try{
      let data
      if(register){data=await request('/auth/register',{method:'POST',body:JSON.stringify({email,password,first_name:first,last_name:last,date_of_birth:birth,sex:sex==='true'})})}
      else{const body=new URLSearchParams({username:email,password});const r=await fetch(API+'/auth/login',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body});data=await r.json();if(!r.ok)throw new Error(data.detail||'Не удалось войти')}
      await saveToken(data.access_token);setToken(data.access_token)
    }catch(e){setError(e instanceof Error?e.message:'Ошибка авторизации')}finally{setBusy(false)}
  }
  async function logout(){await clearToken();setToken('');setMe(null);setProfiles([]);setChats([]);setActiveChat(null)}
  async function startChat(userId:number){try{const chat=await request('/chats?other_user_id='+userId,{method:'POST'});await loadChats();setActiveChat(chat.id);setTab('chats');setError('')}catch(e){setError(e instanceof Error?e.message:'Не удалось создать чат')}}
  async function sendMessage(e:FormEvent){e.preventDefault();if(!activeChat||!draft.trim())return;try{const sent=await request('/chats/'+activeChat+'/messages',{method:'POST',body:JSON.stringify({text:draft.trim()})});setMessages(old=>old.some(m=>m.id===sent.id)?old:[...old,sent]);setDraft('');}catch(e){setError(e instanceof Error?e.message:'Не удалось отправить сообщение')}}
  function updateDraft(value:string){setDraft(value);if(activeChat!==null&&socketRef.current?.readyState===WebSocket.OPEN)socketRef.current.send(JSON.stringify({type:'typing',chat_id:activeChat,active:!!value}))}
  if(!ready)return <div className="splash">C<span>M</span></div>
  if(!token)return <main className="auth-page"><div className="auth-panel"><div className="brand large">C<span>M</span></div><p className="eyebrow">CLIMB TOGETHER</p><h1>Напарник для<br/><em>больших высот.</em></h1><p className="muted">Находи людей, с которыми хочется исследовать новые маршруты.</p><form onSubmit={authenticate} className="stack">
    {register&&<><label>Имя<input value={first} onChange={e=>setFirst(e.target.value)} required maxLength={32}/></label><label>Фамилия<input value={last} onChange={e=>setLast(e.target.value)} required maxLength={32}/></label><label>Дата рождения<input type="date" value={birth} onChange={e=>setBirth(e.target.value)} required/></label><label>Пол<select value={sex} onChange={e=>setSex(e.target.value)}><option value="false">Мужской</option><option value="true">Женский</option></select></label></>}
    <label>Email<input type="email" autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)} required placeholder="you@example.com"/></label><label>Пароль<input type="password" autoComplete={register?'new-password':'current-password'} minLength={register?8:1} value={password} onChange={e=>setPassword(e.target.value)} required placeholder="••••••••"/></label><button disabled={busy}>{busy?'Подождите…':register?'Создать аккаунт':'Войти в CatchMe'}</button>
  </form>{error&&<p className="error">{error}</p>}<button className="text-button" onClick={()=>{setRegister(!register);setError('')}}>{register?'Уже есть аккаунт? Войти':'Впервые здесь? Создать аккаунт'}</button></div><div className="auth-visual"><span>FIND YOUR</span><strong>CLIMBING<br/>TRIBE.</strong><p>Less scrolling. More sending.</p></div></main>
  return <div className="mobile-app"><header className="topbar"><div className="brand">C<span>M</span></div><div className="top-user">{me?.profile.first_name||'Climber'} <button onClick={logout} aria-label="Выйти">↗</button></div></header>
    <main className="screen">
      {error&&<div className="alert" role="alert">{error}<button onClick={()=>setError('')}>×</button></div>}
      {notice&&<div className="notice">{notice}<button onClick={()=>setNotice('')}>×</button></div>}
      {tab==='discover'&&<><p className="eyebrow">ТВОЁ СЛЕДУЮЩЕЕ ПРИКЛЮЧЕНИЕ</p><h1>Найди своего<br/><em>человека.</em></h1><p className="muted">Ищи тех, кто разделяет твою любовь к высоте.</p><section className="filter-panel"><label>Город<input value={city} onChange={e=>setCity(e.target.value)} placeholder="Любой город"/></label><label>Кого ищем<select value={lookingFor} onChange={e=>setLookingFor(e.target.value)}><option value="">Всех</option><option value="male">Мужчин</option><option value="female">Женщин</option></select></label><button onClick={()=>loadProfiles().catch(e=>setError(e.message))}>Найти напарника</button></section><div className="section-title"><div><p className="eyebrow">COMMUNITY</p><h2>Люди рядом <small>{profiles.length}</small></h2></div></div><div className="profile-list">{profiles.map(p=><article className="profile-card" key={p.user_id}><div className="person-head"><div className="person-avatar">{p.first_name?.[0]}{p.last_name?.[0]}</div><div><h3>{p.first_name} {p.last_name}</h3><p>{p.city||'Город не указан'} · {p.date_of_birth?.slice(0,4)||'—'}</p></div></div><p className="bio">{p.description||'Пока ничего не рассказал о себе.'}</p><div className="chips"><span>Трудность: {grades[p.climbing.leading]||'—'}</span><span>Боулдер: {grades[p.climbing.bouldering]||'—'}</span>{p.climbing.belay>0&&<span>Страховка: {p.climbing.belay===2?'Нижняя + верхняя':'Верхняя'}</span>}</div><button className="primary full" onClick={()=>startChat(p.user_id)}>Познакомиться <b>↗</b></button></article>)}</div>{profiles.length===0&&<div className="empty">Пока никого не нашли. Попробуй изменить фильтры.</div>}</>}
      {tab==='profile'&&<ProfileScreen me={me} request={request} onSaved={async()=>{await refreshMe();setNotice('Анкета сохранена')}}/>}
      {tab==='chats'&&<section className="chat-screen"><h1>{activeChat?'Переписка':'Сообщения'}</h1>{activeChat!==null?<><button className="text-button back" onClick={()=>setActiveChat(null)}>← Все диалоги</button><div className="messages">{messages.map(m=><div className={'bubble '+(m.sender_id===me?.id?'mine':'')} key={m.id}><p>{m.text}</p><small>{new Date(m.created_at).toLocaleString()} {m.sender_id===me?.id?(m.is_read?' · Прочитано':' · Доставлено'):''}</small></div>)}</div><form className="send-form" onSubmit={sendMessage}><input value={draft} onChange={e=>updateDraft(e.target.value)} placeholder="Сообщение…" maxLength={10000}/><button disabled={!draft.trim()}>➤</button></form></>:<div className="chat-list">{chats.map(c=><button className="chat-row" key={c.id} onClick={()=>setActiveChat(c.id)}><div className="person-avatar">CM</div><div><b>Диалог #{c.id}</b><small>Участники: {c.members.join(', ')} · {c.members.some(id=>presence[String(id)]??c.online?.[String(id)])?'В сети':'Не в сети'}</small></div><span>›</span></button>)}{!chats.length&&<div className="empty">Здесь появятся ваши диалоги. Найдите напарника и начните общение.</div>}</div>}</section>}
    </main>
    <nav className="bottom-nav"><button className={tab==='discover'?'selected':''} onClick={()=>{setTab('discover');setActiveChat(null)}}><span>⌕</span>Поиск</button><button className={tab==='chats'?'selected':''} onClick={()=>{setTab('chats');setActiveChat(null);loadChats().catch(e=>setError(e.message))}}><span>▤</span>Чаты</button><button className={tab==='profile'?'selected':''} onClick={()=>{setTab('profile');setActiveChat(null)}}><span>◉</span>Анкета</button></nav>
  </div>
}
function ProfileScreen({me,request,onSaved}:{me:Me|null;request:(path:string,init?:RequestInit)=>Promise<any>;onSaved:()=>Promise<void>}){
 const [data,setData]=useState<any>(null),[message,setMessage]=useState('')
 useEffect(()=>{if(me)setData({...me.profile,...me.climbing})},[me])
 if(!data)return <p className="muted">Загружаем анкету…</p>
 const set=(key:string,value:any)=>setData((old:any)=>({...old,[key]:value}))
 async function save(e:FormEvent){e.preventDefault();setMessage('');try{await request('/profiles/me',{method:'PUT',body:JSON.stringify(data)});await onSaved();setMessage('Изменения сохранены')}catch(e){setMessage(e instanceof Error?e.message:'Ошибка сохранения')}}
 return <form className="profile-editor" onSubmit={save}><p className="eyebrow">ТВОЙ ПРОФИЛЬ</p><h1>Расскажи<br/><em>о себе.</em></h1><label>Имя<input value={data.first_name||''} onChange={e=>set('first_name',e.target.value)} maxLength={32}/></label><label>Фамилия<input value={data.last_name||''} onChange={e=>set('last_name',e.target.value)} maxLength={32}/></label><label>Город<input value={data.city||''} onChange={e=>set('city',e.target.value)}/></label><label>О себе<textarea value={data.description||''} onChange={e=>set('description',e.target.value)} rows={4}/></label><label>Цель знакомства<select value={data.goal??0} onChange={e=>set('goal',Number(e.target.value))}><option value="0">Не в поиске</option><option value="1">Вместе полазать</option><option value="2">Больше, чем полазать</option><option value="3">За любой кипиш</option></select></label><div className="two-col"><label>Трудность<select value={data.leading??0} onChange={e=>set('leading',Number(e.target.value))}>{grades.map((g,i)=><option value={i} key={i}>{g}</option>)}</select></label><label>Боулдеринг<select value={data.bouldering??0} onChange={e=>set('bouldering',Number(e.target.value))}>{grades.map((g,i)=><option value={i} key={i}>{g}</option>)}</select></label></div><label>Страховка<select value={data.belay??0} onChange={e=>set('belay',Number(e.target.value))}><option value="0">Нет</option><option value="1">Верхняя</option><option value="2">Нижняя + верхняя</option></select></label><label className="toggle"><input type="checkbox" checked={!!data.speed} onChange={e=>set('speed',e.target.checked)}/> Скоростное лазание</label><label className="toggle"><input type="checkbox" checked={!!data.alpinism} onChange={e=>set('alpinism',e.target.checked)}/> Альпинизм</label><label>Комментарий о страховке<input value={data.belay_description||''} onChange={e=>set('belay_description',e.target.value)}/></label><button className="primary full">Сохранить анкету</button>{message&&<p className="success">{message}</p>}</form>
}
export default App
