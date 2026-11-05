const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const ids=['transporter','plate','region','city','truckType','driver','route','sisgrRouteFilter','scheduleWeekFilter','status'];const nodes={};
for(const id of [...ids,'search','start','end'])nodes[id]={value:'',selectedOptions:[],parentElement:{querySelector:()=>null}};
const labels={};
for(const id of ids){labels[id]=[];nodes[id].parentElement.querySelector=()=>({querySelectorAll:()=>labels[id]})}
const ctx={document:{getElementById:id=>nodes[id]},console,Intl};vm.createContext(ctx);
let src=fs.readFileSync(__dirname+'/web/app.js','utf8').replace(/\binit\(\);/,'').replace(/rescheduleEvents\(\);/,'');vm.runInContext(src,ctx);
vm.runInContext(`rows=[{id:1,date:'2026-11-01',driver:'Ana',plate:'AAA',city:'Cuiabá',status:'ROTA',route:'A',routeCandidates:['A']},{id:2,date:'2026-11-02',driver:'Bia',plate:'BBB',city:'Sinop',status:'ROTA',route:'B',routeCandidates:['B']},{id:3,date:'2026-11-03',driver:'Ana',plate:'CCC',city:'Rondonópolis',status:'ROTA',route:'Rota a confirmar',routeCandidates:['C','D']}];`,ctx);
function select(id,values){nodes[id].selectedOptions=values.map(value=>({value}));}
function label(value){return{value,checked:false,parentElement:{hidden:false,title:''}}}
labels.route=[label('A'),label('B'),label('C'),label('D')];labels.plate=[label('AAA'),label('BBB'),label('CCC')];
select('driver',['Ana']);vm.runInContext('cascadeFilters()',ctx);assert.equal(labels.route[0].parentElement.hidden,false);assert.equal(labels.route[1].parentElement.hidden,true);assert.equal(labels.plate[1].parentElement.hidden,true);assert.equal(labels.route[2].parentElement.hidden,false);
select('route',['C','D']);assert.equal(vm.runInContext('getRows().length',ctx),1);assert.equal(vm.runInContext('getRows()[0].id',ctx),3);
select('driver',[]);select('route',[]);vm.runInContext('cascadeFilters()',ctx);assert.equal(labels.route[1].parentElement.hidden,false);
console.log('Filtros: cascata por motorista, placa e rota; múltiplos candidatos sem duplicar IDs; restauração ao limpar OK');
vm.runInContext("rows[0].sisgrRouteFilter='SISGR A';rows[1].sisgrRouteFilter='SISGR B';rows[2].sisgrRouteFilter='Sem identificador de rota'",ctx);
select('sisgrRouteFilter',['SISGR A']);assert.equal(vm.runInContext('getRows().length',ctx),1);select('sisgrRouteFilter',['SISGR A','SISGR B']);assert.equal(vm.runInContext('getRows().length',ctx),2);select('sisgrRouteFilter',['Sem identificador de rota']);assert.equal(vm.runInContext('getRows()[0].id',ctx),3);console.log('Identificador SISGR: seleção única, múltipla e sem identificador OK');
