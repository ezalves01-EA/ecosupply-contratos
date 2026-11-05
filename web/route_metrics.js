(function(root){
 const norm=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase().replace(/[^A-Z0-9]/g,'');
 function unique(rows){return [...new Map(rows.map(r=>[String(r.id),r])).values()]}
 function summary(rows){const list=unique(rows).filter(r=>!r.canceled&&r.status!=='CANCELADO'),done=list.filter(r=>['REALIZADO','EFETIVADO'].includes(r.status)).length;return {canceled:unique(rows).filter(r=>r.canceled||r.status==='CANCELADO').length,total:list.length,done,pending:list.filter(r=>r.status==='ROTA').length,pct:list.length?100*done/list.length:null}}
 function weeks(rows){const list=unique(rows);return [1,2,3,4].map(week=>({week,...summary(list.filter(r=>r.routeWeek===week))}))}
 const api={norm,unique,summary,weeks};if(typeof module!=='undefined')module.exports=api;else root.RouteMetrics=api;
})(typeof window!=='undefined'?window:globalThis);
