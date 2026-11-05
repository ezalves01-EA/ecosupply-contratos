(function(root){
 const status=r=>String(r.status||'').trim().toUpperCase();
 function summarize(rows){const all=[...new Map(rows.map(r=>[String(r.id),r])).values()],canceled=all.filter(r=>r.canceled||status(r)==='CANCELADO').length,active=all.filter(r=>!r.canceled&&status(r)!=='CANCELADO'),total=active.length,done=active.filter(r=>['EFETIVADO','REALIZADO'].includes(status(r))).length,pending=active.filter(r=>status(r)==='ROTA').length,other=total-done-pending;return {total,done,pending,other,canceled,pct:total?100*done/total:null,complete:total>0&&done===total}}

 function by(rows,key){const m=new Map();for(const r of rows){const k=r[key]||'Não informado';if(!m.has(k))m.set(k,[]);m.get(k).push(r)}return [...m].map(([name,rs])=>({name,...summarize(rs)})).sort((a,b)=>b.pending-a.pending||b.other-a.other||a.name.localeCompare(b.name,'pt-BR'))}
 const api={summarize,by};if(typeof module!=='undefined')module.exports=api;else root.Completion=api;
})(typeof window!=='undefined'?window:globalThis);
