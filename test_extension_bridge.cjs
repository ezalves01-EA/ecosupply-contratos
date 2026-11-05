const fs=require('fs'),vm=require('vm'),assert=require('assert');
const handlers=[],sent=[],nodes={};let timers=[];
const origin='https://ecosupply-logistica-api.onrender.com';
const window={addEventListener:(type,fn)=>handlers.push(fn),postMessage:m=>sent.push(m)};
const c={window,location:{origin},crypto:require('crypto'),sessionStorage:{getItem:()=>null,setItem(){}},document:{getElementById:id=>nodes[id]??={textContent:'',disabled:false,checked:true}},setTimeout:(fn,ms)=>(timers.push({fn,ms}),timers.length),clearTimeout(){},buildReschedulePlan:()=>({format:'test-plan'})};vm.createContext(c);vm.runInContext(fs.readFileSync(__dirname+'/web/extension.js','utf8'),c);
(async()=>{
 const promise=vm.runInContext("extensionRequest('ping')",c);const m=sent.at(-1);let resolved=false;promise.then(()=>resolved=true);
 handlers[0]({source:window,origin:'https://evil.invalid',data:{type:'ECOSUPPLY_EXTENSION_RESPONSE',requestId:m.requestId,response:{ok:true}}});await Promise.resolve();assert(!resolved);
 handlers[0]({source:window,origin,data:{type:'ECOSUPPLY_EXTENSION_RESPONSE',requestId:m.requestId,response:{ok:true,version:'1.0.0'}}});assert.equal((await promise).version,'1.0.0');
 assert.equal(m.command,'ping');assert(!('url' in m));assert(!('token' in m));
 vm.runInContext('extensionEvents()',c);assert.equal(nodes.reSendExtension.disabled,true);assert(nodes.reConnectExtension.onclick);
 console.log('Ponte do painel: origem, correlação da resposta e conexão sem envio automático validadas.');
})().catch(e=>{console.error(e);process.exitCode=1});
