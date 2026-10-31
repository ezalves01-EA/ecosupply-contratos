(function(root){
'use strict';
function summarize(rows,start,end){
 const groups=new Map(),ids=new Set();
 for(const r of rows){const id=String(r.id);if(ids.has(id))continue;ids.add(id);
 const driverId=r.actualDriverId??r.driverId??r.actualDriver??r.driver??'Sem motorista';
 if(!groups.has(String(driverId)))groups.set(String(driverId),{id:driverId,name:r.actualDriver||r.driver||'Sem motorista',done:0,kg:0,liters:0,kgKnown:0,dates:new Set(),unknownDate:0,assignedDriver:0});
 const g=groups.get(String(driverId));if(r.type!=='COLETA'||!['REALIZADO','EFETIVADO'].includes(r.status))continue;
 if(!r.collectionDate){g.unknownDate++;continue}
 if((start&&r.collectionDate<start)||(end&&r.collectionDate>end))continue;
 g.done++;g.dates.add(r.collectionDate);if(r.actualDriverSource!=='atendimento')g.assignedDriver++;
 if(r.measureUnits?.includes('KG')){g.kg+=r.measures.KG;g.kgKnown++}
 if(r.measureUnits?.includes('L'))g.liters+=r.measures.L;
 }
 return [...groups.values()].map(g=>({...g,days:g.dates.size,dates:[...g.dates].sort()})).sort((a,b)=>b.done-a.done||a.name.localeCompare(b.name,'pt-BR'));
}
function statusSummary(rows,start,end,today){
 const drivers=new Map(),types=new Map(),seen=new Set();const total={done:0,late:0,other:0};
 for(const r of rows){if(seen.has(String(r.id)))continue;seen.add(String(r.id));if(r.type!=='COLETA'||(start&&r.date<start)||(end&&r.date>end))continue;
 const key=String(r.driverId??r.driver??'Sem motorista');if(!drivers.has(key))drivers.set(key,{name:r.driver||'Sem motorista',id:key,done:0,late:0,other:0});
 const type=r.truckType||'Sem tipo';if(!types.has(type))types.set(type,{name:type,done:0,late:0,other:0});
 const metric=['REALIZADO','EFETIVADO'].includes(r.status)?'done':r.status==='ROTA'&&r.date<today?'late':'other';
 total[metric]++;drivers.get(key)[metric]++;types.get(type)[metric]++;
 }
 return {total,drivers:[...drivers.values()].sort((a,b)=>b.done+b.late-a.done-a.late||a.name.localeCompare(b.name)),types:[...types.values()].sort((a,b)=>b.done+b.late-a.done-a.late)};
}
const api={summarize,statusSummary};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.DriverMetrics=api;
})(typeof globalThis!=='undefined'?globalThis:this);
