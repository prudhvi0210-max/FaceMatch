'use strict';
const $ = id => document.getElementById(id);
const names = {overview:'Overview', recognize:'Check a photo', register:'Register a person', directory:'People directory', about:'About & validation'};
let state = {people:[], token:''};
let busy = false;
const files = {recognize:null, register:null};
const urls = {};
function message(id, text) { $(id).textContent = text; $(id).hidden = !text; }
function page(name, focus = true) {
  if (!names[name]) name = 'overview';
  document.querySelectorAll('.page').forEach(el => el.hidden = el.id !== name);
  document.querySelectorAll('.nav').forEach(el => { el.classList.toggle('active', el.dataset.page === name); if (el.dataset.page === name) el.setAttribute('aria-current','page'); else el.removeAttribute('aria-current'); });
  $('breadcrumb').textContent = names[name];
  document.title = `${names[name]} · FaceMatch`;
  if (location.hash !== '#'+name) history.replaceState(null,'','#'+name);
  if (focus) { $('content').focus(); window.scrollTo(0,0); }
}
document.querySelectorAll('[data-page]').forEach(el => el.addEventListener('click',()=>page(el.dataset.page)));
document.querySelectorAll('[data-go]').forEach(el => el.addEventListener('click',()=>page(el.dataset.go)));
window.addEventListener('hashchange',()=>page(location.hash.slice(1)));
function updateButtons() {
  $('recognize-submit').disabled = busy || !files.recognize || !state.token;
  $('register-submit').disabled = busy || !files.register || !state.token;
  document.querySelectorAll('input, [data-clear]').forEach(el => el.disabled = busy);
}
function selectFile(kind, file) {
  if (busy) return;
  message(kind+'-error','');
  if (kind === 'register') message('register-success','');
  if (file && (!/\.(jpe?g|png)$/i.test(file.name) || file.size > 20*1024*1024 || !file.size)) {
    message(kind+'-error','Choose a nonempty JPG or PNG photograph smaller than 20 MB.');
    return;
  }
  files[kind] = file || null;
  if (urls[kind]) URL.revokeObjectURL(urls[kind]);
  const preview = $(kind+'-preview');
  preview.hidden = !file;
  $(kind+'-drop').hidden = !!file;
  if (file) {
    urls[kind] = URL.createObjectURL(file);
    preview.querySelector('img').src = urls[kind];
    preview.querySelector('strong').textContent = file.name;
  } else { preview.querySelector('img').removeAttribute('src'); $(kind+'-file').value = ''; }
  if (kind === 'recognize') emptyResult();
  updateButtons();
}
for (const kind of ['recognize','register']) {
  $(kind+'-file').addEventListener('change', e => selectFile(kind,e.target.files[0]));
  const drop = $(kind+'-drop');
  ['dragenter','dragover'].forEach(event=>drop.addEventListener(event,e=>{e.preventDefault();if(!busy)drop.classList.add('drag');}));
  ['dragleave','drop'].forEach(event=>drop.addEventListener(event,e=>{e.preventDefault();drop.classList.remove('drag');}));
  drop.addEventListener('drop',e=>selectFile(kind,e.dataTransfer.files[0]));
}
document.querySelectorAll('[data-clear]').forEach(el=>el.addEventListener('click',()=>selectFile(el.dataset.clear,null)));
function renderPeople() {
  const query = $('people-search').value.toLowerCase().trim();
  const filtered = state.people.filter(p=>(p.id+' '+p.name).toLowerCase().includes(query));
  $('people-rows').replaceChildren();
  for (const person of filtered) {
    const tr=document.createElement('tr');
    const name=document.createElement('td');
    const avatar=document.createElement('span');avatar.className='avatar';avatar.setAttribute('aria-hidden','true');avatar.textContent=person.name.slice(0,2).toUpperCase();
    name.append(avatar, document.createTextNode(person.name));
    const id=document.createElement('td');id.textContent=person.id;
    const status=document.createElement('td');const badge=document.createElement('span');badge.textContent=person.status;
    badge.className='status'+(person.status==='Duplicate reference'?' issue':person.status!=='Ready'?' missing':'');status.append(badge);
    tr.append(name,id,status);$('people-rows').append(tr);
  }
  $('people-empty').hidden=!!filtered.length;
  $('people-empty').textContent=state.people.length?'No people match your search.':'No people registered yet. Add a person to get started.';
  $('people-count').textContent=`Showing ${filtered.length} of ${state.people.length} registered people`;
  $('stat-people').textContent=state.people.length;
  $('stat-photos').textContent=state.people.filter(p=>['Ready','Duplicate reference'].includes(p.status)).length;
  $('stat-issues').textContent=state.people.filter(p=>p.status!=='Ready').length;
}
$('people-search').addEventListener('input',renderPeople);
async function refresh() {
  const response=await fetch('/api/state',{cache:'no-store'});
  const data=await response.json();
  if(!response.ok) throw new Error(data.error || 'Could not load your workspace.');
  state=data;renderPeople();updateButtons();
}
function readBase64(file) { return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=()=>reject(new Error('The photograph could not be read.'));reader.readAsDataURL(file);}); }
function emptyResult() {
  $('recognize-output').innerHTML='<div class="result-empty"><div class="empty-icon">⌕</div><h2>A result with context</h2><p>Your comparison will appear here, including a decision and similarity scores.</p><div class="chips"><span>Possible match</span><span>Unknown</span><span>Ambiguous</span></div></div>';
}
function showResult(data) {
  const output=$('recognize-output');output.replaceChildren();
  const descriptions={possible:['Possible match',`${data.best?.name || ''} (ID: ${data.best?.person_id || ''})`,'The best score meets the experimental threshold. Review the result carefully; it is not proof of identity.'],unknown:['Unknown person','No reference meets the threshold','The photograph did not reach the fixed 0.50 similarity threshold for any usable registered reference.'],ambiguous:['Ambiguous result','More than one identity is possible','Duplicate reference photographs or tied best scores prevent choosing one identity. No records were changed.'],unavailable:['Comparison unavailable','No usable references','Register a person with a valid reference photograph before trying again.']};
  const [tag,title,description]=descriptions[data.decision]||descriptions.unavailable;
  const badge=document.createElement('span');badge.className='result-tag'+(data.decision==='ambiguous'?' warning':'');badge.textContent=tag;
  const heading=document.createElement('h2');heading.className='result-title';heading.textContent=title;
  const text=document.createElement('p');text.className='result-description';text.textContent=description;
  output.append(badge,heading,text);
  if(data.results.length){const label=document.createElement('p');label.className='score-label';label.textContent='COSINE SIMILARITY · EXPERIMENTAL THRESHOLD 0.50';output.append(label);}
  for(const row of data.results){
    const item=document.createElement('div');item.className='score-row';
    const heading=document.createElement('div');heading.className='score-heading';
    const person=document.createElement('span');person.textContent=row.name+' ';const id=document.createElement('small');id.textContent='ID '+row.person_id;person.append(id);
    const score=document.createElement('strong');score.textContent=Number(row.similarity).toFixed(4);heading.append(person,score);
    item.append(heading);
    if(row.ambiguous){const note=document.createElement('small');note.className='result-description';note.textContent='Reference shared by multiple registered IDs';item.append(note);}
    output.append(item);
  }
  const note=document.createElement('p');note.className='micro';note.textContent='Scores measure similarity, not probability. Unusable references are skipped.';output.append(note);
}
for (const kind of ['recognize','register']) $(kind+'-form').addEventListener('submit',async event=>{
  event.preventDefault();if(busy||!files[kind])return;
  const file=files[kind];busy=true;updateButtons();message(kind+'-error','');
  if(kind==='register') message('register-success','');
  const button=$(kind+'-submit');const old=button.textContent;button.textContent=kind==='recognize'?'Comparing…':'Registering…';
  if(kind==='recognize') $('recognize-output').innerHTML='<div class="processing" role="status"><div class="spinner"></div><h2>Looking for possible matches</h2><p class="result-description">Detecting, aligning, and comparing your photograph.<br>The first run may take longer while the model loads.</p></div>';
  try {
    const payload={filename:file.name,image:await readBase64(file)};
    if(kind==='register')Object.assign(payload,{person_id:$('person-id').value,name:$('person-name').value,consent:$('consent').checked});
    const response=await fetch('/api/'+kind,{method:'POST',headers:{'Content-Type':'application/json','X-FaceMatch-Token':state.token},body:JSON.stringify(payload)});
    const data=await response.json();if(!response.ok)throw new Error(data.error||'The operation failed.');
    if(kind==='recognize') showResult(data);
    else {
      // The successful response is authoritative even if refreshing the directory fails.
      busy=false;selectFile('register',null);$('register-form').reset();message('register-success',data.message);
      try{await refresh();}catch(error){message('global-error','Registration succeeded, but the directory could not refresh. Reload this page.');}
    }
  } catch(error){
    if(kind==='recognize')emptyResult();
    message(kind+'-error',error.message==='Failed to fetch'?'Connection lost. Check the FaceMatch terminal. If registering, check the directory before retrying.':error.message);
  } finally {busy=false;button.textContent=old;updateButtons();}
});
page(location.hash.slice(1)||'overview',false);
refresh().catch(error=>message('global-error',error.message+' Refresh the page to retry.'));
