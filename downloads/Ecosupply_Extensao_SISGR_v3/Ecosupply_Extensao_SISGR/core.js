'use strict';
const SISGR_ORIGIN='https://ecosupply.sisgr.com';
const PANEL_ORIGIN='https://ecosupply-logistica-api.onrender.com';
function validISO(s){if(typeof s!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(s))return false;const d=new Date(s+'T12:00:00Z');return !isNaN(d)&&d.toISOString().slice(0,10)===s}
function normalizePlan(p){
 if(p?.format==='ecosupply-recurrence-plan')return normalizeRecurrencePlan(p);
 if(p?.format==='ecosupply-route-plan')return normalizeRoutePlan(p);
 if(!p||p.format!=='ecosupply-reschedule-plan'||p.version!==1)throw Error('Lote não reconhecido.');
 if(typeof p.newDate!=='string'||!/^\d{2}\/\d{2}\/\d{4}$/.test(p.newDate)||!validISO(p.newDate.split('/').reverse().join('-')))throw Error('Nova data inválida.');
 if(p.turn!=='qualquerturno'||!['s','n'].includes(p.left)||typeof p.reason!=='string'||!p.reason.trim()||p.reason.length>1000)throw Error('Turno, motivo ou saída inválidos.');
 if(!Array.isArray(p.items)||p.items.length<1||p.items.length>100)throw Error('Selecione de 1 a 100 IDs.');
 const seen=new Set();const items=p.items.map(i=>{if(!i||typeof i.id!=='string'||! /^[1-9][0-9]*$/.test(i.id)||seen.has(i.id)||i.status!=='ROTA'||!validISO(i.sourceDate)||i.sourceDate.slice(0,7)!==p.sourceMonth)throw Error('ID, status ou data de origem inválidos.');seen.add(i.id);return {id:i.id,sourceDate:i.sourceDate,status:'ROTA'}});
 return {format:p.format,version:1,newDate:p.newDate,turn:p.turn,left:p.left,reason:p.reason.trim(),sourceMonth:p.sourceMonth,sourceUpdatedAt:typeof p.sourceUpdatedAt==='string'?p.sourceUpdatedAt:null,items};
}
function payloadFor(p,id){const x={agendamentoIds:id,novaData:p.newDate,novoTurno:p.turn,motivo:p.reason};if(p.left==='s')x.caminhaoSaiu='1';return x}
function resultState(r,id){if(r?.http>=200&&r.http<300&&r.accepted===true&&r.id===id)return 'aceita';return 'conferir'}
function attemptKey(id,date){return id+'|'+date}
if(typeof module!=='undefined')module.exports={normalizePlan,payloadFor,resultState,attemptKey,validISO};

function normalizeRoutePlan(p){
 if(p.version!==1||typeof p.newRoute!=='string'||!p.newRoute.trim()||p.newRoute.length>150||/[\x00-\x1f]/.test(p.newRoute))throw Error('Identificador de rota inválido.');
 if(!Array.isArray(p.items)||!p.items.length||p.items.length>100)throw Error('Selecione 1 a 100 IDs.');
 const seen=new Set();const items=p.items.map(i=>{if(!i||typeof i.id!=='string'||!/^[1-9][0-9]*$/.test(i.id)||seen.has(i.id)||i.status!=='ROTA'||!validISO(i.sourceDate)||i.sourceDate.slice(0,7)!==p.sourceMonth||!['transporterId','vehicleId','driverId'].every(k=>/^[1-9][0-9]*$/.test(String(i[k]||''))))throw Error('ID, data, status ou alocação incompleta.');seen.add(i.id);return {id:i.id,sourceDate:i.sourceDate,status:i.status,transporterId:String(i.transporterId),vehicleId:String(i.vehicleId),driverId:String(i.driverId),currentRoute:typeof i.currentRoute==='string'?i.currentRoute.slice(0,200):null};});
 return {format:p.format,version:1,newRoute:p.newRoute.trim(),sourceMonth:p.sourceMonth,sourceUpdatedAt:typeof p.sourceUpdatedAt==='string'?p.sourceUpdatedAt:null,items};
}
function routePayload(p,id){const i=p.items.find(i=>i.id===id);if(!i)throw Error('ID fora do lote.');return {tipoColeta:'coleta',data_de:i.sourceDate.split('-').reverse().join('/'),data_ate:i.sourceDate.split('-').reverse().join('/'),identificadorFilter:'',transportadoraId:i.transporterId,caminhaoId:'',motoristaId:'',identificadorRota:p.newRoute,'agendamentos[]':i.id,nTransportadoraId:i.transporterId,nCaminhaoId:i.vehicleId,nMotoristaId:i.driverId};}
if(typeof module!=='undefined'){module.exports.normalizeRoutePlan=normalizeRoutePlan;module.exports.routePayload=routePayload;}

function normalizeRecurrencePlan(p){
 if(p.version!==1||!Array.isArray(p.items)||!p.items.length||p.items.length>100)throw Error('Planilha: use 1 a 100 IDs.');
 const seen=new Set();const items=p.items.map(i=>{if(!i||typeof i.id!=='string'||!/^[1-9][0-9]{0,14}$/.test(i.id)||seen.has(i.id))throw Error('ID de recorrência inválido ou repetido.');seen.add(i.id);const value=i.requestedRoute==null?'':i.requestedRoute;if(typeof value!=='string'||value.length>150||/[\x00-\x1f]/.test(value))throw Error('Identificador inválido.');return {id:i.id,requestedRoute:value.trim()||null,sourceRow:Number.isInteger(i.sourceRow)?i.sourceRow:null};});return {format:p.format,version:1,items};
}
if(typeof module!=='undefined')module.exports.normalizeRecurrencePlan=normalizeRecurrencePlan;
