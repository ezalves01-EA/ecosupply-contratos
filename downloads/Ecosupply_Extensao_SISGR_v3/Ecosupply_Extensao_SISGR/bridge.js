'use strict';
const ORIGIN='https://ecosupply-logistica-api.onrender.com';
if(window.top===window&&location.origin===ORIGIN){
 window.addEventListener('message',async e=>{
  if(e.source!==window||e.origin!==ORIGIN||e.data?.type!=='ECOSUPPLY_EXTENSION_REQUEST')return;
  const {requestId,command,plan,jobId}=e.data;
  if(typeof requestId!=='string'||requestId.length>100||!['ping','prepare','status'].includes(command))return;
  try{const response=await chrome.runtime.sendMessage({command,plan,jobId});window.postMessage({type:'ECOSUPPLY_EXTENSION_RESPONSE',requestId,response},ORIGIN)}
  catch{window.postMessage({type:'ECOSUPPLY_EXTENSION_RESPONSE',requestId,response:{ok:false,error:'Extensão indisponível. Recarregue o painel.'}},ORIGIN)}
 });
}
