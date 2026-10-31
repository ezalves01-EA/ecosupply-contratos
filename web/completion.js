(function(root){
 const status=r=>String(r.status||'').trim().toUpperCase();
 function summarize(rows){const unique=[...new Map(rows.map(r=>[r.id,r])).values()],total=unique.length,done=unique.filter(r=>['EFETIVADO','REALIZADO'].includes(status(r))).length,pending=unique.filter(r=>status(r)==='ROTA').length,other=total-done-pending;return {total,done,pending,other,pct:total?100*done/total:null,complete:total>0&&done===total}}
 function by(rows,key){const m=new Map();for(const r of rows){const k=r[key]||'Não informado';if(!m.has(k))m.set(k,[]);m.get(k).push(r)}return [...m].map(([name,rs])=>({name,...summarize(rs)})).sort((a,b)=>b.pending-a.pending||b.other-a.other||a.name.localeCompare(b.name,'pt-BR'))}
 const api={summarize,by};if(typeof module!=='undefined')module.exports=api;else root.Completion=api;
})(typeof window!=='undefined'?window:globalThis);
