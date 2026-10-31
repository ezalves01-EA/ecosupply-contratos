const assert=require('node:assert/strict');const {summarize}=require('./web/driver_metrics.js');
const r=(id,date,driver=1)=>({id,date:'2026-10-01',collectionDate:date,actualDriverId:driver,actualDriver:'Motorista '+driver,actualDriverSource:'atendimento',type:'COLETA',status:'EFETIVADO',measures:{KG:10,L:0},measureUnits:['KG']});
let list=summarize([r(1,'2026-10-28'),r(1,'2026-10-28'),r(2,'2026-10-28'),r(3,'2026-10-29'),r(4,null)],'2026-10-28','2026-10-28');
assert.equal(list[0].done,2);assert.equal(list[0].kg,20);assert.equal(list[0].days,1);assert.equal(list[0].unknownDate,1);
list=summarize(Array.from({length:17},(_,i)=>r(i,'2026-10-28',i)),'2026-10-28','2026-10-28');assert.equal(list.length,17);
assert.equal(summarize([r(1,'2026-10-29')],'2026-10-29','2026-10-29')[0].done,1);
console.log('Motoristas: data realizada, dias distintos, IDs únicos e todos os nomes validados.');

const {statusSummary}=require('./web/driver_metrics.js');
const operational=[{id:1,driverId:10,driver:'Programado',type:'COLETA',status:'EFETIVADO',date:'2026-10-28',collectionDate:'2026-10-29',truckType:'BAÚ'},{id:2,driverId:10,driver:'Programado',type:'COLETA',status:'ROTA',date:'2026-10-28',truckType:'BAÚ'},{id:3,driverId:10,driver:'Programado',type:'COLETA',status:'ROTA',date:'2026-10-30',truckType:'BAÚ'},{id:4,driver:'Outro',type:'ENTREGA',status:'ROTA',date:'2026-10-28'}];
let status=statusSummary([...operational,operational[0]],'2026-10-28','2026-10-30','2026-10-30');
assert.deepEqual(status.total,{done:1,late:1,other:1});assert.equal(status.drivers[0].name,'Programado');assert.equal(status.types[0].done,1);
status=statusSummary(operational,'2026-10-30','2026-10-30','2026-10-30');assert.equal(status.total.late,0);assert.equal(status.total.other,1);
console.log('Comparação operacional: mesma coorte de agendamento, atraso até ontem e exclusão de entregas validados.');
