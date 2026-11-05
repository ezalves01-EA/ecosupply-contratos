'use strict';
importScripts('core.js','recurrence.js');
let queue=Promise.resolve();
const serial=fn=>{const p=queue.then(fn);queue=p.catch(()=>{});return p};
const read=async key=>(await chrome.storage.local.get(key))[key];
const write=async(key,value)=>chrome.storage.local.set({[key]:value});
const jobKey=id=>'job:'+id;
function panelSender(s){try{return s.id===chrome.runtime.id&&s.frameId===0&&new URL(s.url).origin===PANEL_ORIGIN&&Number.isInteger(s.tab?.id)}catch{return false}}
function reviewSender(s){try{const url=new URL(s.url);return s.id===chrome.runtime.id&&url.protocol==='chrome-extension:'&&url.hostname===chrome.runtime.id&&url.pathname==='/review.html'}catch{return false}}
async function getJob(id){if(typeof id!=='string'||!/^[0-9a-f-]{36}$/.test(id))throw Error('Lote inválido.');const j=await read(jobKey(id));if(!j)throw Error('Lote não encontrado.');return j}
async function openReview(id){await chrome.tabs.create({url:chrome.runtime.getURL('review.html')+(id?'?job='+id:'')})}
async function finish(j){await write(jobKey(j.id),j);if((await read('activeJob'))===j.id)await chrome.storage.local.remove('activeJob')}
// Runs in the existing SISGR tab. Fixed route and fields; no cookies are read or exported.
async function sendInSisgr(payload){
 if(location.origin!=='https://ecosupply.sisgr.com')return {http:0,accepted:false};
 if(document.querySelector('input[type=password]')||/\/(login|entrar)(\/|$)/i.test(location.pathname))return {http:401,accepted:false};
 const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),20000);
 try{
  const r=await fetch('/agendamentos/reagendar',{method:'POST',credentials:'same-origin',redirect:'error',signal:ctrl.signal,headers:{'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8','Accept':'application/json, text/javascript, */*; q=0.01','X-Requested-With':'XMLHttpRequest'},body:new URLSearchParams(payload).toString()});
  let data;try{data=await r.json()}catch{return {http:r.status,accepted:false}};
  return {http:r.status,id:payload.agendamentoIds,accepted:r.ok&&data?.erro===false&&data?.agendamentos?.[payload.agendamentoIds]?.erro===false};
 }catch{return {http:0,accepted:false}}finally{clearTimeout(timer)}
}
async function handle(m,s){
 const fromPanel=panelSender(s),fromReview=reviewSender(s);
 if(!fromPanel&&!fromReview)throw Error('Origem não autorizada.');
 if(m.command==='ping'&&fromPanel)return {version:'1.2.0'};
 if(m.command==='prepare'&&fromPanel){
  const active=await read('activeJob');if(active){await openReview(active);throw Error('Já existe um lote para conferir ou em andamento. Finalize/cancele esse lote na extensão.')}
  const p=normalizePlan(m.plan);const id=crypto.randomUUID();
  const j={id,plan:p,panelTab:s.tab.id,panelOrigin:PANEL_ORIGIN,state:p.format==='ecosupply-recurrence-plan'?'leitura':'revisao',createdAt:new Date().toISOString(),items:p.items.map(i=>({...i,state:p.format==='ecosupply-recurrence-plan'?'aguardando':'pendente'}))};
  await write(jobKey(id),j);await write('activeJob',id);await write('latestJob',id);await openReview(id);return {jobId:id};
 }
 if(m.command==='latest'&&fromReview){return {jobId:await read('latestJob')||null}}
 const j=await getJob(m.jobId);
 if(fromPanel){if(m.command!=='status'||j.panelTab!==s.tab.id||j.panelOrigin!==new URL(s.url).origin)throw Error('Acesso ao lote negado.');return {job:j}}
 if(m.command==='review'){
  if(j.items.some(i=>i.state==='enviando')){j.state='conferir';j.note='Envio interrompido: confira no SISGR; não haverá repetição automática.';await finish(j)}
  return {job:j};
 }
 if(m.command==='cancel'){
  j.state='cancelado';await finish(j);return {job:j};
 }
 if(m.command==='inspectNext'&&j.plan.format==='ecosupply-recurrence-plan'){
  if(j.state!=='leitura')return {job:j};
  if(Date.now()<(j.nextAt||0))return {job:j};
  const item=j.items.find(i=>i.state==='aguardando');
  if(!item){j.state=j.items.some(i=>i.state==='pendente')?'revisao':j.items.some(i=>i.state==='bloqueado')?'conferir':'concluido';if(j.state==='revisao')await write(jobKey(j.id),j);else await finish(j);return {job:j};}
  const tabs=await chrome.tabs.query({url:'https://ecosupply.sisgr.com/*'});if(!tabs.length)throw Error('Abra o SISGR e faça login neste perfil.');
  j.sisgrTab=(tabs.find(t=>t.active)||tabs[0]).id;
  let result;try{const entries=await chrome.scripting.executeScript({target:{tabId:j.sisgrTab},world:'ISOLATED',func:recurrenceInSisgr,args:[item,'preview']});result=entries[0]?.result}catch{result={note:'Não foi possível ler o formulário.'}}
  if(result?.ok){Object.assign(item,{currentRoute:result.currentRoute,newRoute:result.newRoute,plate:result.plate,nextDate:result.nextDate,week:result.week,source:result.source,fingerprint:result.fingerprint});item.state=item.currentRoute===item.newRoute?'ignorado':'pendente';item.note=item.state==='ignorado'?'Já está igual; não será enviado.':'Pronto para conferência.';}
  else{item.state='bloqueado';item.note=result?.note||'Leitura bloqueada.';}
  j.nextAt=Date.now()+3000;await write(jobKey(j.id),j);return {job:j};
 }
 if(m.command==='confirm'){
  if(j.plan.format==='ecosupply-recurrence-plan'&&(!j.items.some(i=>i.state==='pendente')||j.items.filter(i=>i.state==='pendente').some(i=>!i.fingerprint||!i.newRoute)))throw Error('Conclua a leitura das recorrências.');
  if(j.state!=='revisao')throw Error('Lote já confirmado ou encerrado.');
  const tabs=await chrome.tabs.query({url:'https://ecosupply.sisgr.com/*'});
  if(!tabs.length)throw Error('Abra o SISGR e faça login no mesmo perfil do navegador. Depois confirme novamente.');
  // Pin the chosen existing tab for this job; login is checked again before each fetch.
  j.sisgrTab=(tabs.find(t=>t.active)||tabs[0]).id;j.state='executando';j.nextAt=0;await write(jobKey(j.id),j);return {job:j};
 }
 if(m.command==='next'){
  if(j.state!=='executando')return {job:j};
  if(j.items.some(i=>i.state==='enviando')){j.state='conferir';await finish(j);return {job:j}}
  if(Date.now()<(j.nextAt||0))return {job:j,wait:true};
  const item=j.items.find(i=>i.state==='pendente');if(!item){j.state=j.items.some(i=>i.state==='bloqueado')?'concluido_com_bloqueios':'concluido';await finish(j);return {job:j}}
  const key='attempt:'+attemptKey(item.id,j.plan.format==='ecosupply-recurrence-plan'?'recorrencia:'+item.newRoute:j.plan.format==='ecosupply-route-plan'?'rota:'+j.plan.newRoute:j.plan.newDate),past=await read(key);
  if(past){item.state='ignorado';item.note='Tentativa anterior neste perfil para o mesmo valor de destino. Confira o histórico/SISGR.';await write(jobKey(j.id),j);return {job:j}}
  let tab;try{tab=await chrome.tabs.get(j.sisgrTab)}catch{throw Error('A aba SISGR foi fechada. O lote permanece sem reenvio. Cancele e gere outro lote para os itens não enviados.')}
  if(!tab.url||new URL(tab.url).origin!==SISGR_ORIGIN)throw Error('A aba selecionada não está no SISGR.');
  item.state='enviando';item.sentAt=new Date().toISOString();
  await write(key,{state:'indeterminado',jobId:j.id,at:item.sentAt});await write(jobKey(j.id),j);
  let result;try{const entries=await chrome.scripting.executeScript({target:{tabId:j.sisgrTab},world:'ISOLATED',func:j.plan.format==='ecosupply-recurrence-plan'?recurrenceInSisgr:j.plan.format==='ecosupply-route-plan'?sendRouteInSisgr:sendInSisgr,args:j.plan.format==='ecosupply-recurrence-plan'?[item,'send']:[j.plan.format==='ecosupply-route-plan'?routePayload(j.plan,item.id):payloadFor(j.plan,item.id)]});result=entries[0]?.result}catch{result={http:0,accepted:false}}
  item.state=resultState(result,item.id);item.http=Number.isInteger(result?.http)?result.http:0;
  item.note=result?.note||(item.state==='aceita'?'Solicitação aceita. Confira a data no SISGR.':'Resultado não confirmado. Confira o cadastro antes de tentar novamente.');
  await write(key,{state:item.state,jobId:j.id,at:item.sentAt});j.nextAt=Date.now()+3000;
  if(item.state!=='aceita'){j.state='conferir';await finish(j)}else if(!j.items.some(i=>i.state==='pendente')){j.state=j.items.some(i=>i.state==='bloqueado')?'concluido_com_bloqueios':'concluido';await finish(j)}else await write(jobKey(j.id),j);
  return {job:j};
 }
 throw Error('Comando não permitido.');
}
chrome.runtime.onMessage.addListener((m,s,respond)=>{serial(()=>handle(m||{},s)).then(data=>respond({ok:true,...data}),err=>respond({ok:false,error:String(err?.message||'Operação interrompida. Confira o lote antes de repetir.').slice(0,250)}));return true});
chrome.action.onClicked.addListener(()=>read('latestJob').then(openReview));

chrome.runtime.onInstalled.addListener(()=>chrome.storage.local.setAccessLevel({accessLevel:'TRUSTED_CONTEXTS'}));

async function sendRouteInSisgr(payload){
 if(location.origin!=='https://ecosupply.sisgr.com'||document.querySelector('input[type=password]')||/\/(login|entrar)(\/|$)/i.test(location.pathname))return {http:401,accepted:false};
 const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),20000);
 try{const r=await fetch('/rotas/trocarMotoristaVeiculoAction',{method:'POST',credentials:'same-origin',redirect:'error',signal:ctrl.signal,headers:{'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8','Accept':'application/json','X-Requested-With':'XMLHttpRequest'},body:new URLSearchParams(payload).toString()});let d;try{d=await r.json()}catch{return {http:r.status,accepted:false}};return {http:r.status,id:payload['agendamentos[]'],accepted:r.ok&&d?.erro===false&&d?.confirmarTrocaVeiculoDistinto===false&&d?.mensagem==='Alteração realizada.'};}catch{return {http:0,accepted:false}}finally{clearTimeout(timer)}
}
