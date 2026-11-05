'use strict';
let reSelected=new Set();
function pendingReschedules(){const q=document.getElementById('reSearch').value.trim().toLocaleLowerCase('pt-BR');return filtered.filter(r=>r.status==='ROTA'&&!r.canceled&&(!q||[r.id,r.point,r.city,r.driver].join(' ').toLocaleLowerCase('pt-BR').includes(q))).sort((a,b)=>a.date.localeCompare(b.date)||String(a.id).localeCompare(String(b.id)))}
function clearRescheduleSelection(){reSelected.clear();const el=document.getElementById('reMessage');if(el)el.textContent=''}
function renderReschedule(){
 const panel=document.getElementById('reschedulePanel');panel.hidden=currentView!=='reagendar';if(panel.hidden)return;
 const eligible=new Map(rows.filter(r=>r.status==='ROTA'&&!r.canceled).map(r=>[String(r.id),r]));reSelected=new Set([...reSelected].filter(id=>eligible.has(id)));
 const list=pendingReschedules();document.getElementById('reCount').textContent=`${list.length} pendentes nos filtros · ${reSelected.size} selecionados no mês (inclusive fora dos filtros)`;
 document.getElementById('reRows').innerHTML=list.length?'<table><thead><tr><th>Selecionar</th><th>ID</th><th>Data atual na base</th><th>Cidade / ponto</th><th>Motorista</th><th>Status</th></tr></thead><tbody>'+list.map(r=>`<tr><td><input type="checkbox" data-re-id="${esc(r.id)}" aria-label="Selecionar ${esc(r.id)}" ${reSelected.has(String(r.id))?'checked':''}></td><td>#${esc(r.id)}</td><td>${esc(r.date.split('-').reverse().join('/'))}</td><td>${esc(r.city)}<small>${esc(r.point)}</small></td><td>${esc(r.driver)}</td><td>ROTA</td></tr>`).join('')+'</tbody></table>':'<p class="empty">Nenhum agendamento em ROTA nos filtros.</p>';
 document.querySelectorAll('[data-re-id]').forEach(el=>el.onchange=()=>{if(el.checked&&reSelected.size>=100){el.checked=false;document.getElementById('reMessage').textContent='Máximo de 100 IDs por lote.';return}if(el.checked)reSelected.add(el.dataset.reId);else reSelected.delete(el.dataset.reId);renderReschedule()});
 const chosen=[...reSelected].map(id=>eligible.get(id));document.getElementById('reReview').textContent=chosen.length?'IDs selecionados: '+chosen.map(r=>`#${r.id} (${r.city}, ${r.date.split('-').reverse().join('/')})`).join(' · '):'Nenhum ID selecionado.';
}
function rescheduleEvents(){
 extensionEvents();
 document.getElementById('reSearch').oninput=renderReschedule;
 document.getElementById('reSelectAll').onclick=()=>{const list=pendingReschedules();const union=new Set([...reSelected,...list.map(r=>String(r.id))]);if(union.size>100){document.getElementById('reMessage').textContent='O resultado excede 100 IDs. Refine os filtros ou selecione individualmente.';return}reSelected=union;renderReschedule()};
 document.getElementById('reClear').onclick=()=>{clearRescheduleSelection();renderReschedule()};
 document.getElementById('rePaste').onclick=()=>{const ids=document.getElementById('reIds').value.split(/[\s,;]+/).filter(Boolean);const eligible=new Set(pendingReschedules().map(r=>String(r.id)));const invalid=ids.filter(id=>!eligible.has(id));if(invalid.length){document.getElementById('reMessage').textContent='IDs fora dos pendentes filtrados: '+invalid.join(', ');return}const union=new Set([...reSelected,...ids]);if(union.size>100){document.getElementById('reMessage').textContent='Máximo de 100 IDs.';return}reSelected=union;renderReschedule()};
 document.getElementById('reExport').onclick=()=>{
  const plan=buildReschedulePlan();if(!plan)return;
  const url=URL.createObjectURL(new Blob([JSON.stringify(plan,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='lote_reagendamento_'+Date.now()+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  document.getElementById('reMessage').textContent='Lote baixado. Abra INICIAR_LOTE_DO_PAINEL no executor local e escolha o arquivo. Nenhuma alteração foi enviada pelo painel.';document.getElementById('reConfirm').checked=false;
 };
}

function buildReschedulePlan(){
  const date=document.getElementById('reDate').value,reason=document.getElementById('reReason').value.trim(),left=document.getElementById('reLeft').value;
  if(!reSelected.size||!date||!reason||!['s','n'].includes(left)){document.getElementById('reMessage').textContent='Selecione IDs, nova data, motivo e se o veículo saiu.';return null}
  if(!document.getElementById('reConfirm').checked){document.getElementById('reMessage').textContent='Confira os IDs e marque a confirmação para preparar o lote.';return null}
  const byId=new Map(rows.filter(r=>r.status==='ROTA'&&!r.canceled).map(r=>[String(r.id),r]));const items=[...reSelected].map(id=>({id,sourceDate:byId.get(id).date,status:'ROTA'}));
  const plan={format:'ecosupply-reschedule-plan',version:1,createdAt:new Date().toISOString(),sourceMonth:DATA.meta.selectedMonth||DATA.meta.periodStart.slice(0,7),sourceUpdatedAt:DATA.meta.importedAt||null,newDate:date.split('-').reverse().join('/'),turn:'qualquerturno',reason,left,items};

 return plan;
}
