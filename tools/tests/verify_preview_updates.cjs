const vm=require('node:vm'), fs=require('node:fs'), assert=require('node:assert/strict');
const handlers={}, stores=new Map(), origin='https://eneft.github.io', base=origin+'/Lembah-sari/';
const oldName='Lembah Sari-sw-cache-old';stores.set(oldName,new Map([[base+'index.pck',new Response('OLD')]]));
let skip=0,claim=0,network=0,precacheReload=false;
const caches={open:async key=>{if(!stores.has(key))stores.set(key,new Map());const cache=stores.get(key);return {addAll:async requests=>{precacheReload=requests.every(r=>r.cache==='reload');requests.forEach(r=>cache.set(r.url,new Response('HTML')))},match:async req=>cache.get(typeof req==='string'?base+req:req.url),put:(req,response)=>cache.set(req.url,response)}},keys:async()=>[...stores.keys()],delete:async key=>stores.delete(key),match:async()=>undefined};
const self={origin,location:{href:base+'index.service.worker.js'},addEventListener:(type,fn)=>handlers[type]=fn,skipWaiting:async()=>{skip++},clients:{claim:async()=>{claim++}},registration:{navigationPreload:{enable:async()=>{}}},fetch:async()=>{network++;return new Response('NEW')}};
vm.runInNewContext(fs.readFileSync('build/web/index.service.worker.js','utf8'),{self,caches,Response,Headers,Request,URL,Promise,console});
(async()=>{
 for(const type of ['install','activate']){let pending;handlers[type]({waitUntil:p=>pending=p});await pending;}
 assert.equal(precacheReload,true);assert.equal(skip,1);assert.equal(claim,1);assert(!stores.has(oldName));
 const metadata=JSON.parse(fs.readFileSync('build/web/preview-version.json'));
 const version=metadata.revision;
 const req={url:base+metadata.pack,referrer:base+'play.html?v='+version,mode:'cors'};
 let pending;handlers.fetch({request:req,preloadResponse:Promise.resolve(undefined),respondWith:p=>pending=p});
 const first=await pending;assert.equal(await first.text(),'NEW');assert.equal(network,1);
 handlers.fetch({request:req,preloadResponse:Promise.resolve(undefined),respondWith:p=>pending=p});
 assert.equal(await (await pending).text(),'NEW');assert.equal(network,1);
 const html=fs.readFileSync('build/web/play.html','utf8');
 const config=JSON.parse(html.match(/const GODOT_CONFIG = (\{[^\n]+\});/)[1]);
 const engineReq={...req,url:base+config.executable+'.wasm'};
 handlers.fetch({request:engineReq,preloadResponse:Promise.resolve(undefined),respondWith:p=>pending=p});
 await pending;
 const before=network;
 // Activating the next game release must not erase the unchanged engine cache.
 const nextSource=fs.readFileSync('build/web/index.service.worker.js','utf8').replace(version,'next-game-version');
 vm.runInNewContext(nextSource,{self,caches,Response,Headers,Request,URL,Promise,console});
 let activation;handlers.activate({waitUntil:p=>activation=p});await activation;
 handlers.fetch({request:engineReq,preloadResponse:Promise.resolve(undefined),respondWith:p=>pending=p});
 assert.equal(await (await pending).text(),'NEW');assert.equal(network,before);
 console.log('ENGINE_CACHE_VALIDATED survives_game_update=true no_repeat_download=true');
 console.log('WORKER_UPDATE_VALIDATED immediate_activation=true fresh_versioned_pack=true second_load_cached=true');
})().catch(err=>{console.error(err);process.exit(1)});
