'use strict';
// Self-contained: executed in the authenticated SISGR tab, no cookies exported.
async function recurrenceInSisgr(item,mode){
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),25000);let posted=false,http=0;
 const bad=note=>({id:item.id,http,accepted:false,posted,note});
 try{
  if(location.origin!=='https://ecosupply.sisgr.com'||!/^[1-9][0-9]{0,14}$/.test(item.id)||!['preview','send'].includes(mode))return bad('Origem, ID ou modo inválido.');
  const edit='/recorrentes/editar/'+item.id,save='/recorrentes/salvar/'+item.id;
  const hash=async entries=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(entries))))).map(b=>b.toString(16).padStart(2,'0')).join('');
  async function load(){
   const r=await fetch(edit,{credentials:'same-origin',redirect:'error',cache:'no-store',signal:controller.signal});http=r.status;if(!r.ok)throw Error('Leitura não autorizada ou indisponível (HTTP '+http+').');
   const text=await r.text();if(text.length>2_000_000)throw Error('Formulário excedeu o limite.');
   const doc=new DOMParser().parseFromString(text,'text/html');if(doc.querySelector('input[type=password]'))throw Error('Sessão encerrada. Faça login no SISGR.');
   const inputs=[...doc.querySelectorAll('[name="identificadorRota"]')];if(inputs.length!==1||!inputs[0].form)throw Error('Formulário não reconhecido; leitura bloqueada sem salvar.');
   const form=inputs[0].form,action=form.getAttribute('action');
   if(action){const target=new URL(action,'https://ecosupply.sisgr.com'+edit);if(target.origin!==location.origin||![edit,save].includes(target.pathname))throw Error('Destino do formulário não corresponde à recorrência.');}
   const entries=[...new FormData(form).entries()];if(entries.some(e=>typeof e[1]!=='string'))throw Error('Formulário contém arquivos; salvar em lote foi bloqueado.');
   const one=name=>{const vals=entries.filter(e=>e[0]===name);if(vals.length!==1)throw Error('Campo ausente ou repetido: '+name);return vals[0][1]};
   for(const key of ['proximaData','clienteId','geradoraId','turno','tipoVeiculo','identificadorRota'])one(key);
   if(!one('clienteId')||!one('geradoraId')||!one('turno')||!one('tipoVeiculo'))throw Error('Formulário incompleto; nenhuma alteração enviada.');
   if(!entries.some(e=>/^coleta\[\d+\]\[id\]$/.test(e[0]))||!entries.some(e=>/^rota\[\d+\]\[veiculo\]$/.test(e[0])))throw Error('Produtos ou rotas não carregados no formulário.');
   if(entries.some(e=>/\[remover\]$/.test(e[0])&&!['','0'].includes(e[1])))throw Error('Há produtos marcados para remoção; bloqueado.');
   const date=one('proximaData'),parts=/^(\d{2})\/(\d{2})\/(\d{4})$/.exec(date);if(!parts)throw Error('Próxima data ausente ou inválida.');
   const day=+parts[1],month=+parts[2],year=+parts[3],d=new Date(Date.UTC(year,month-1,day));if(year<1900||d.getUTCFullYear()!==year||d.getUTCMonth()!==month-1||d.getUTCDate()!==day)throw Error('Próxima data inválida.');
   const week=Math.min(4,Math.floor((day-1)/7)+1),plates=new Set();
   for(const input of [...form.elements].filter(e=>/^rota\[\d+\]\[veiculo\]$/.test(e.name)&&!e.disabled)){
    const label=input.tagName==='SELECT'?[...input.selectedOptions].map(o=>o.textContent).join(' '):'';
    const matches=label.toUpperCase().match(/\b[A-Z]{3}[-_ ]?\d[A-Z0-9]\d{2}\b/g)||[];
    for(const match of matches){const raw=match.replace(/[-_ ]/g,'');plates.add(raw.slice(0,3)+'-'+raw.slice(3));}
   }
   const plate=plates.size===1?[...plates][0]:null;
   const requested=item.requestedRoute==null?'':item.requestedRoute;
   if(typeof requested!=='string'||requested.length>150||/[\x00-\x1f]/.test(requested))throw Error('Identificador importado inválido.');
   if(!requested.trim()&&!plate)throw Error('B vazia: placa não disponível ou múltiplas placas no cadastro. Informe B ou confira o formulário.');
   const newRoute=requested.trim()||plate+'_'+week,currentRoute=one('identificadorRota');
   return {entries,meta:{currentRoute,newRoute,plate,nextDate:date,week,source:requested.trim()?'Coluna B':'Placa + próxima data',fingerprint:await hash(entries),stableFingerprint:await hash(entries.filter(e=>e[0]!=='identificadorRota'))}};
  }
  const before=await load(),m=before.meta;
  if(mode==='preview')return {id:item.id,http,ok:true,...m};
  if(!item.fingerprint||m.fingerprint!==item.fingerprint||m.newRoute!==item.newRoute)return bad('Cadastro mudou desde a leitura. Gere nova conferência; nada salvo.');
  if(m.currentRoute===m.newRoute)return {id:item.id,http,accepted:true,posted:false,note:'Já está igual; sem envio.'};
  const body=new URLSearchParams(before.entries.map(([k,v])=>[k,k==='identificadorRota'?m.newRoute:v]));
  posted=true;
  const r=await fetch(save,{method:'POST',credentials:'same-origin',redirect:'error',signal:controller.signal,headers:{'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8','Accept':'application/json','X-Requested-With':'XMLHttpRequest'},body:body.toString()});http=r.status;
  let data;try{data=await r.json()}catch{return bad('Resposta de salvamento não reconhecida. Confira no SISGR antes de repetir.');}
  if(!r.ok||data?.erro!==false||data?.mensagem!=='Solicitação realizada.')return bad('Salvamento não confirmado. Confira no SISGR.');
  const after=await load();
  if(after.meta.currentRoute!==m.newRoute||after.meta.stableFingerprint!==m.stableFingerprint)return bad('Resposta aceita, mas conferência final divergiu. Verifique identificador e demais campos no SISGR.');
  return {id:item.id,http,accepted:true,posted:true,note:'Identificador conferido após salvar; demais campos enviados preservados.'};
 }catch(e){return bad(e?.name==='AbortError'?'Tempo limite. Confira no SISGR antes de repetir.':String(e.message||'Leitura ou envio interrompido.').slice(0,200));}finally{clearTimeout(timer)}
}
if(typeof module!=='undefined')module.exports={recurrenceInSisgr};
