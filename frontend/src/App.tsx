import { FormEvent, useEffect, useState } from 'react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
type Profile = { user_id:number; first_name:string; last_name:string; city:string|null; description:string; goal:number; date_of_birth:string; sex:boolean; climbing:{leading:number;bouldering:number;speed:boolean;alpinism:boolean;belay:number} }
const levels = ['—','5','6a/a+','6b/b+','6c/c+','7a/a+','7b/b','7c/c+','8a/a+','8b/b','8c/c+','9+']
function App() {
  const [token,setToken] = useState(localStorage.getItem('token') || '')
  const [email,setEmail] = useState('')
  const [password,setPassword] = useState('')
  const [profiles,setProfiles] = useState<Profile[]>([])
  const [city,setCity] = useState('')
  const [lookingFor,setLookingFor] = useState('')
  const [error,setError] = useState('')
  const [busy,setBusy] = useState(false)
  const [tab,setTab] = useState<'search'|'profile'>('search')
  const headers = { 'Content-Type':'application/json', Authorization:`Bearer ${token}` }
  async function request(path:string, init:RequestInit = {}) {
    const response = await fetch(API+path,{...init,headers:{...headers,...init.headers}})
    if(!response.ok) { const body=await response.json().catch(()=>({})); throw new Error(body.detail || 'Ошибка запроса') }
    return response.json()
  }
  async function loadProfiles() {
    try { const q=new URLSearchParams(); if(city) q.set('city',city); if(lookingFor) q.set('looking_for',lookingFor); setProfiles(await request('/profiles?'+q.toString())) }
    catch(e) { setError(e instanceof Error?e.message:'Не удалось загрузить анкеты') }
  }
  useEffect(()=>{ if(token) void loadProfiles() },[token])
  async function login(e:FormEvent) {
    e.preventDefault(); setBusy(true); setError('')
    try {
      const body=new URLSearchParams({username:email,password})
      const response=await fetch(API+'/auth/login',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body})
      const data=await response.json(); if(!response.ok) throw new Error(data.detail || 'Не удалось войти')
      localStorage.setItem('token',data.access_token); setToken(data.access_token)
    } catch(e) {setError(e instanceof Error?e.message:'Ошибка входа')} finally {setBusy(false)}
  }
  function logout(){localStorage.removeItem('token');setToken('');setProfiles([])}
  if(!token) return <main className="auth-shell"><div className="auth-card"><div className="logo">C<span>M</span></div><p className="eyebrow">CLIMB TOGETHER</p><h1>Напарник для<br/><em>больших высот.</em></h1><p className="muted">Находи людей, с которыми хочется исследовать новые маршруты.</p><form onSubmit={login}><label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required placeholder="you@example.com"/></label><label>Пароль<input type="password" value={password} onChange={e=>setPassword(e.target.value)} required placeholder="••••••••"/></label><button disabled={busy}>{busy?'Входим…':'Войти в CatchMe'}</button></form>{error&&<p className="error">{error}</p>}<small>Новый пользователь? Регистрация доступна через API: <code>/docs</code>.</small></div><div className="auth-art"><div className="sun"/><div className="art-copy"><span>FIND YOUR</span><strong>CLIMBING<br/>TRIBE.</strong><p>Less scrolling. More sending.</p></div><div className="mountain m1"/><div className="mountain m2"/></div></main>
  return <div className="app"><aside className="sidebar"><div className="brand">C<span>M</span></div><p className="eyebrow">CATCHME</p><nav><button className={tab==='search'?'active':''} onClick={()=>setTab('search')}>⌕ <span>Поиск напарника</span></button><button className={tab==='profile'?'active':''} onClick={()=>setTab('profile')}>◉ <span>Моя анкета</span></button></nav><div className="side-bottom"><div className="avatar">CM</div><div><b>Climber</b><small>На связи</small></div><button className="logout" onClick={logout}>↗</button></div></aside><main className="content"><header><div><p className="eyebrow">ТВОЁ СЛЕДУЮЩЕЕ ПРИКЛЮЧЕНИЕ</p><h1>{tab==='search'?'Найди своего человека.':'Твоя анкета.'}</h1></div><div className="status"><i/> Сообщество растёт</div></header>{tab==='search'?<><section className="intro"><div><span className="pill">01 / DISCOVER</span><h2>Сильнее вместе<span>.</span></h2><p>Ищи тех, кто разделяет твою любовь к высоте.</p></div><div className="climb-mark">↗</div></section><section className="filters"><label>Город<input value={city} onChange={e=>setCity(e.target.value)} placeholder="Любой город"/></label><label>Ищу<select value={lookingFor} onChange={e=>setLookingFor(e.target.value)}><option value="">Всех</option><option value="male">Мужчин</option><option value="female">Женщин</option></select></label><button onClick={()=>void loadProfiles()}>Показать анкеты ↗</button></section><div className="section-heading"><div><p className="eyebrow">COMMUNITY / CLIMBERS</p><h3>Люди рядом <span>({profiles.length})</span></h3></div><span className="muted">Первые 8 анкет</span></div>{error&&<p className="error">{error}</p>}<div className="cards">{profiles.map(p=><article className="profile-card" key={p.user_id}><div className="card-top"><div className="person-avatar">{p.first_name.slice(0,1)}{p.last_name.slice(0,1)}</div><span className="pill">CLIMBER</span></div><h4>{p.first_name} {p.last_name}</h4><p className="location">⌖ {p.city||'Город не указан'}</p><p className="description">{p.description||'Пока ничего не рассказал о себе.'}</p><div className="stats"><div><small>ТРУДНОСТЬ</small><b>{levels[p.climbing.leading]||'—'}</b></div><div><small>БОЛДЕРИНГ</small><b>{levels[p.climbing.bouldering]||'—'}</b></div><div><small>СТРАХОВКА</small><b>{p.climbing.belay===2?'Нижняя + верхняя':p.climbing.belay===1?'Верхняя':'—'}</b></div></div><button className="outline" onClick={()=>setError('Чаты доступны через API; создание чата требует ID пользователя '+p.user_id)}>Познакомиться ↗</button></article>)}</div>{profiles.length===0&&!error&&<div className="empty">Пока никого не нашли. Попробуй изменить фильтры.</div>}</>:<ProfileEditor request={request}/>}</main></div>
}
function ProfileEditor({request}:{request:(path:string,init?:RequestInit)=>Promise<any>}) {
  const [data,setData]=useState<any>(null); const [message,setMessage]=useState('')
  useEffect(()=>{request('/me').then(setData).catch(e=>setMessage(e.message))},[])
  async function save(e:FormEvent){e.preventDefault();try{await request('/me/profile',{method:'PUT',body:JSON.stringify(data.profile)});setMessage('Анкета сохранена')}catch(e){setMessage(e instanceof Error?e.message:'Ошибка')}}
  if(!data) return <p>{message||'Загружаем профиль…'}</p>
  return <form className="editor" onSubmit={save}><h2>Расскажи о себе</h2>{(['first_name','last_name','city','description'] as const).map(k=><label key={k}>{({first_name:'Имя',last_name:'Фамилия',city:'Город',description:'О себе'} as any)[k]}<input value={data.profile[k]||''} onChange={e=>setData({...data,profile:{...data.profile,[k]:e.target.value}})}/></label>)}<label>Цель знакомства<select value={data.profile.goal} onChange={e=>setData({...data,profile:{...data.profile,goal:Number(e.target.value)}})}><option value="0">Не в поиске</option><option value="1">Вместе полазать</option><option value="2">Больше, чем полазать</option><option value="3">За любой кипиш</option></select></label><button>Сохранить анкету</button>{message&&<p>{message}</p>}</form>
}
export default App
