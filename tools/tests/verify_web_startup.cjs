const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const html = fs.readFileSync('build/web/play.html','utf8');
const config=JSON.parse(html.match(/const GODOT_CONFIG = (\{[^\n]+\});/)[1]);
const revision=JSON.parse(fs.readFileSync('build/web/preview-version.json','utf8')).revision;
assert.equal(config.executable,'index-'+revision);
assert(html.includes('src="'+config.executable+'.js"'));
assert(fs.existsSync('build/web/'+config.executable+'.wasm'));
const source = html.match(/<script>\s*(const GODOT_CONFIG[\s\S]*?)<\/script>/)[1];
async function check(missing) {
 const nodes = new Map();
 function element(id) {
  const node = {id,style:{},textContent:'',children:[],remove(){},appendChild(child){this.children.push(child);},removeChild(){this.children.shift();},removeAttribute(){}};
  Object.defineProperty(node,'lastChild',{get(){return this.children.at(-1);}});
  return node;
 }
 ['status','status-progress','status-notice'].forEach(id=>nodes.set(id,element(id)));
 const document = {getElementById:id=>nodes.get(id),createElement:()=>element(''),createTextNode:text=>({textContent:text}),body:{appendChild(node){nodes.set(node.id,node);}}};
 let options;
 function Engine() {this.startGame = input=>{options=input;return Promise.resolve();};}
 Engine.getMissingFeatures = ()=>missing;
 vm.runInNewContext(source,{Engine,document,console:{error(){}},navigator:{serviceWorker:{getRegistration:()=>Promise.resolve({update:()=>Promise.resolve()})}},window:{location:{reload(){throw Error('Unexpected reload');}}},setTimeout(){},Promise,Error});
 await new Promise(resolve=>setImmediate(resolve));
 if(missing.length) {
  const text=nodes.get('status-notice').children.map(n=>n.textContent).join('');
  assert(text.includes('WebGL2'), 'Missing graphics support must produce a visible notice');
 } else {
  assert(options && typeof options.onPrintError==='function');
  options.onPrintError('SCRIPT ERROR: Failed loading image environment');
  assert(nodes.get('runtime-error').textContent.includes('Failed loading image environment'));
 }
}
(async()=>{await check([]);await check(['WebGL2']);console.log('WEB_STARTUP_VALIDATED resource_errors=visible missing_features=visible');})().catch(error=>{console.error(error);process.exit(1);});
