'use strict';
let sisgrExtensionReady=false,extensionJobId=null,extensionTimer=null;
const extensionRequests=new Map();
window.addEventListener('message',event=>{
 if(event.source!==window||event.origin!==location.origin||event.data?.type!=='ECOSUPPLY_EXTENSION_RESPONSE')return;
 const pending=extensionRequests.get(event.data.requestId);if(!pending)return;clearTimeout(pending.timer);extensionRequests.delete(event.data.requestId);
 if(event.data.response?.ok)pending.resolve(event.data.response);else pending.reject(Error(event.data.response?.error||'Falha na extensão.'));
});
function extensionRequest(command,extra={}){return new Promise((resolve,reject)=>{const requestId=crypto.randomUUID();const timer=setTimeout(()=>{extensionRequests.delete(requestId);reject(Error('Extensão não encontrada. Instale no Chrome/Edge e recarregue o painel.'))},30000);extensionRequests.set(requestId,{resolve,reject,timer});window.postMessage({type:'ECOSUPPLY_EXTENSION_REQUEST',requestId,command,...extra},location.origin)})}
async function connectSisgrExtension(){const el=document.getElementById('reExtensionStatus');try{const r=await extensionRequest('ping');sisgrExtensionReady=true;el.textContent='Extensão conectada · '+r.version+' · Deixe uma aba SISGR aberta e logada neste perfil.';document.getElementById('reSendExtension').disabled=false;return true}catch(e){sisgrExtensionReady=false;el.textContent=e.message;document.getElementById('reSendExtension').disabled=true;return false}}
function showExtensionJob(job){
 const labels={pendente:'Ainda não enviado',enviando:'Em andamento',aceita:'Solicitação aceita',conferir:'Conferir no SISGR',ignorado:'Tentativa anterior — não reenviado'};
 const root=document.getElementById('reExtensionResults');root.replaceChildren();const status=document.createElement('p');status.textContent='Estado do lote: '+job.state;root.append(status);
 const table=document.createElement('table');for(const i of job.items){const tr=document.createElement('tr');for(const value of ['#'+i.id,job.plan.newDate,labels[i.state]||i.state,i.http||'—']){const td=document.createElement('td');td.textContent=value;tr.append(td)}table.append(tr)}root.append(table);
 document.getElementById('reMessage').textContent=job.state==='revisao'?'O lote está na aba da extensão. Confira e confirme lá para iniciar.':job.state==='executando'?'Acompanhe os envios na aba da extensão; mantenha-a aberta.':'Lote encerrado ou interrompido. Confira as novas datas no SISGR e sincronize os períodos envolvidos. Aceite não é confirmação independente da data final.';
}
async function pollExtensionJob(){if(!extensionJobId)return;try{const r=await extensionRequest('status',{jobId:extensionJobId});showExtensionJob(r.job);if(['revisao','executando'].includes(r.job.state))extensionTimer=setTimeout(pollExtensionJob,3500)}catch(e){document.getElementById('reMessage').textContent=e.message}}
function extensionEvents(){
 document.getElementById('reConnectExtension').onclick=connectSisgrExtension;
 document.getElementById('reSendExtension').disabled=true;
 document.getElementById('reSendExtension').onclick=async()=>{
  const plan=buildReschedulePlan();if(!plan)return;
  try{const r=await extensionRequest('prepare',{plan});extensionJobId=r.jobId;sessionStorage.setItem('ecosupplyExtensionJob',r.jobId);clearTimeout(extensionTimer);document.getElementById('reConfirm').checked=false;await pollExtensionJob()}catch(e){document.getElementById('reMessage').textContent=e.message}
 };
 extensionJobId=sessionStorage.getItem('ecosupplyExtensionJob');
 // Button also allows connecting after installation without an automatic send.
 setTimeout(async()=>{if(await connectSisgrExtension()&&extensionJobId)await pollExtensionJob()},800);
}
