const assert=require('node:assert/strict'),m=require('./web/route_metrics.js');
const rows=[{id:1,status:'REALIZADO',routeWeek:1},{id:1,status:'REALIZADO',routeWeek:1},{id:2,status:'EFETIVADO',routeWeek:1},{id:3,status:'ROTA',routeWeek:1},{id:4,status:'CANCELADO',routeWeek:1},{id:5,status:'ROTA',routeWeek:null}];
assert.deepEqual(m.summary(rows),{canceled:1,total:4,done:2,pending:2,pct:50});assert.equal(m.weeks(rows)[0].pct,100*2/3);assert.equal(m.weeks(rows)[0].total,3);assert.equal(m.weeks(rows)[1].pct,null);console.log('Route metrics OK');
