const vm=require('node:vm'), fs=require('node:fs'), assert=require('node:assert/strict');
const handlers={}, stores=new Map(), origin='https://eneft.github.io', base=origin+'/Lembah-sari/';
const oldName='Lembah Sari-sw-cache-old';stores.set(oldName,new Map([[base+'index.pck',new Response('OLD')]]));
let skip=0,claim=0,network=0;
const caches={open:async key=>{if(!stores.has(key))stores.set(key,new Map());const cache=stores.get(key);return {addAll:async names=>names.forEach(n=>cache.set(base+n,new Response('HTML'))),match:async req=>cache.get(typeof req==='string'?base+req:req.url),put:(req,response)=>cache.set(req.url,response)}},keys:async()=>[...stores.keys()],delete:async key=>stores.delete(key),match:async()=>undefined};
const self={origin,addEventListener:(type,fn)=>handlers[type]=fn,skipWaiting:async()=>{skip++},clients:{claim:async()=>{claim++}},registration:{navigationPreload:{enable:async()=>{}}},fetch:async()=>{network++;return new Response('NEW')}};
vm.runInNewContext(fs.readFileSync('build/web/index.service.worker.js','utf8'),{self,caches,Response,Headers,Promise,console});
(async()=>{
 for(const type of ['install','activate']){let pending;handlers[type]({waitUntil:p=>pending=p});await pending;}
 assert.equal(skip,1);assert.equal(claim,1);assert(!stores.has(oldName));
 const version=JSON.parse(fs.readFileSync('build/web/preview-version.json')).revision;
 const req={url:base+'index.pck?v='+version,referrer:base+'play.html?v='+version,mode:'cors'};
 let pending;handlers.fetch({request:req,preloadResponse:Promise.resolve(undefined),respondWith:p=>pending=p});
 const first=await pending;assert.equal(await first.text(),'NEW');assert.equal(network,1);
 handlers.fetch({request:req,preloadResponse:Promise.resolve(undefined),respondWith:p=>pending=p});
 assert.equal(await (await pending).text(),'NEW');assert.equal(network,1);
 console.log('WORKER_UPDATE_VALIDATED immediate_activation=true fresh_versioned_pack=true second_load_cached=true');
})().catch(err=>{console.error(err);process.exit(1)});
