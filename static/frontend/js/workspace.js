/* School workspace: shared readers, overview cards, and administrator forms. */
const modules = {
  timetable: {label:'Timetable', noun:'lesson', icon:'fa-calendar-days', empty:'No lessons scheduled.'},
  library: {label:'Library', noun:'resource', icon:'fa-book-open', empty:'No library resources yet.'},
  notices: {label:'Notices', noun:'notice', icon:'fa-bullhorn', empty:'No notices published.'},
};
const weekdays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];

function element(tag, className, text) {
  const item = document.createElement(tag);
  if (className) item.className = className;
  if (text != null) item.textContent = text;
  return item;
}
function actionButton(label, callback, className = 'btn btn-sm btn-outline-primary') {
  const button = element('button', className, label);
  button.type = 'button';
  button.onclick = callback;
  return button;
}
async function workspaceData(route, params) {
  const response = await API.workspace('GET', route, null, params);
  if (!response?.ok) throw new Error('Could not load records. Please try again.');
  return response.json();
}
function workspaceRow(key, record, compact) {
  const row = element('article','workspace-row');
  const symbol = element('span','workspace-symbol');
  symbol.append(element('i','fas ' + modules[key].icon));
  const content = element('div','workspace-copy');
  const title = key === 'timetable' ? record.subject_name : record.title;
  if (key === 'library') {
    const link = element('a','workspace-title',title);
    link.href = record.url; link.target = '_blank'; link.rel = 'noopener noreferrer';
    content.append(link);
  } else {
    content.append(element('strong','workspace-title',title));
  }
  const subtitle = key === 'timetable'
    ? [record.day, record.starts.slice(0,5) + '–' + record.ends.slice(0,5), record.class_name, record.academic_year, record.room].filter(Boolean).join(' · ')
    : key === 'library' ? record.subject_name : new Date(record.published).toLocaleDateString();
  content.append(element('small','workspace-meta',subtitle));
  if (key === 'notices') content.append(element('p',compact ? 'notice-preview' : 'notice-body',record.message));
  row.append(symbol,content);
  return row;
}
function workspaceCard(title, key) {
  const panel = element('section','workspace-card');
  const header = element('div','workspace-heading');
  header.append(element('h3','',title),actionButton('View all',()=>navigate(key),'text-action'));
  panel.append(header);
  return panel;
}
async function fillWorkspaceOverview(container) {
  for (const key of Object.keys(modules)) {
    const panel = workspaceCard(modules[key].label,key);
    container.append(panel);
    const body = element('div','workspace-list','Loading…');
    panel.append(body);
    workspaceData(key + '/').then(data=>{
      body.replaceChildren();
      data.results.slice(0,3).forEach(record=>body.append(workspaceRow(key,record,true)));
      if (!data.count) body.append(element('p','workspace-empty',modules[key].empty));
    }).catch(error=>{body.textContent=error.message;});
  }
  const chart = workspaceCard('Weekly lessons','timetable');
  container.append(chart);
  fillDashboardActivity(container);
  try {
    const distribution = await workspaceData('timetable/distribution/');
    const total = distribution.reduce((n,r)=>n+r.total,0);
    const colors = ['#554287','#9c89be','#657f86','#87a997','#caa765','#a67f84','#8794bc'];
    const ring = element('div','lesson-ring');
    let start = 0;
    const stops = distribution.map(r=>{
      const end = start + 100*r.total/total;
      const stop = colors[r.weekday-1] + ' ' + start + '% ' + end + '%';
      start=end; return stop;
    });
    if (total) ring.style.background='conic-gradient('+stops.join(',')+')';
    const center = element('div','ring-center');
    center.append(element('strong','',total),element('small','','lessons'));
    ring.append(center); chart.append(ring);
    const legend = element('div','week-legend');
    for (const r of distribution) {
      const entry = element('span','',weekdays[r.weekday-1].slice(0,3)+' '+r.total);
      entry.style.setProperty('--dot',colors[r.weekday-1]); legend.append(entry);
    }
    chart.append(legend);
  } catch (error) { chart.append(element('p','workspace-empty',error.message)); }
}
async function fillDashboardActivity(container) {
  const scores = workspaceCard('Recent scores','scores');
  const attendance = workspaceCard('Attendance today','attendance');
  container.append(scores,attendance);
  try {
    const data = await workspaceData('dashboard-activity/');
    for (const record of data.scores) {
      const row = element('div','workspace-row');
      const copy = element('div','workspace-copy');
      copy.append(element('strong','workspace-title',record.student),element('small','workspace-meta',record.subject));
      row.append(copy,element('span','score-mark',record.percentage == null ? '—' : Number(record.percentage)+'%'));
      scores.append(row);
    }
    if (!data.scores.length) scores.append(element('p','workspace-empty','No scores recorded yet.'));
    for (const record of data.attendance) {
      const row = element('div','workspace-row');
      row.append(element('span','workspace-copy text-capitalize',record.status),element('strong','',record.total));
      attendance.append(row);
    }
    if (!data.attendance.length) attendance.append(element('p','workspace-empty','No attendance marked today.'));
  } catch(error) {
    for (const panel of [scores,attendance]) panel.append(element('p','workspace-empty',error.message));
  }
}
async function renderWorkspace(key, page=1, filter='') {
  const config=modules[key];
  setTitle(config.label);
  const section=element('section','workspace-section');
  const head=element('div','section-header');
  head.append(element('h2','',config.label));
  if (user.role === 'admin') head.append(actionButton('Add '+config.noun,()=>editWorkspace(key,null,()=>renderWorkspace(key,1,filter)),'btn btn-primary'));
  section.append(head);
  const form=element('form','workspace-filter');
  let input;
  if (key==='timetable') {
    input=element('select','form-select'); input.add(new Option('All days',''));
    weekdays.forEach((day,i)=>input.add(new Option(day,i+1)));
    input.onchange=()=>renderWorkspace(key,1,input.value);
  } else {
    input=element('input','form-control'); input.type='search'; input.placeholder='Search '+config.label.toLowerCase();
  }
  input.setAttribute('aria-label',key==='timetable'?'Filter by day':'Search '+config.label);
  input.value=filter; form.append(input);
  if (key!=='timetable') form.append(element('button','btn btn-outline-primary','Search'));
  form.onsubmit=e=>{e.preventDefault();renderWorkspace(key,1,input.value);};
  section.append(form);
  const list=element('div','workspace-card','Loading…');section.append(list);pc().replaceChildren(section);
  try {
    const data=await workspaceData(key+'/',{page,[key==='timetable'?'weekday':'search']:filter||null});
    list.replaceChildren();
    data.results.forEach(record=>{
      const row=workspaceRow(key,record,false);
      if (user.role==='admin') {
        const actions=element('div','workspace-actions');
        actions.append(actionButton('Edit',()=>editWorkspace(key,record,()=>renderWorkspace(key,page,filter))),
          actionButton('Delete',()=>removeWorkspace(key,record,()=>renderWorkspace(key,1,filter)),'btn btn-sm btn-outline-danger'));
        row.append(actions);
      }
      list.append(row);
    });
    if (!data.count) list.append(element('p','workspace-empty',filter ? 'No matching records.' : config.empty));
    if (data.next || data.previous) {
      const nav=element('div','workspace-actions mt-3');
      if(data.previous) nav.append(actionButton('Previous',()=>renderWorkspace(key,page-1,filter)));
      nav.append(element('span','','Page '+page));
      if(data.next) nav.append(actionButton('Next',()=>renderWorkspace(key,page+1,filter)));
      list.append(nav);
    }
  } catch(error) { list.textContent=error.message; }
}
async function editWorkspace(key,record,onSaved) {
  const form=element('form','workspace-editor');
  const feedback=element('p','text-danger mb-0'); feedback.setAttribute('role','alert');
  const addField=(name,label,type,options)=>{
    const wrap=element('label','form-label',label);
    const field=element(type==='select'?'select':type==='textarea'?'textarea':'input',type==='select'?'form-select':'form-control');
    if(field.tagName==='INPUT') field.type=type;
    if (options) {
      field.add(new Option('Select…',''));
      options.forEach(([id,text])=>field.add(new Option(text,id)));
    }
    field.name=name; field.required=name!=='room';
    field.value=record?.[name]??'';
    wrap.append(field);form.append(wrap);
  };
  const save=async()=>{
    const button=$('modalSave');
    if (button.disabled || !form.reportValidity()) return;
    button.disabled=true; feedback.textContent='';
    try {
      const response=await API.workspace(record?'PUT':'POST',key+'/'+(record?record.id+'/':''),Object.fromEntries(new FormData(form)));
      if(!response?.ok) {
        const errors=await response?.json();
        feedback.textContent=Object.entries(errors||{}).map(([k,v])=>k+' — '+v).join(' ') || 'Could not save.';
        return;
      }
      bsModal.hide(); onSaved();
    } catch {feedback.textContent='Could not save. Please try again.';} finally {button.disabled=false;}
  };
  form.onsubmit=e=>{e.preventDefault();save();};
  openModal((record?'Edit ':'Add ')+modules[key].noun,'',save);
  $('modalBody').append(form); const button=$('modalSave');button.disabled=true;
  try {
    if(key==='timetable') {
      const choices=await workspaceData('timetable/assignments/');
      addField('assignment','Class and subject','select',choices.map(v=>[v.id,v.label]));
      addField('weekday','Day','select',weekdays.map((v,i)=>[i+1,v]));
      addField('starts','Starts at','time');addField('ends','Ends at','time');addField('room','Room (optional)','text');
      if (!choices.length) feedback.textContent='Assign a subject to a class first in Django admin.';
    } else {
      addField('title','Title','text');
      if(key==='library') {
        const subjects=[]; let page=1, data;
        do {data=await workspaceData('subjects/',{page:page++});subjects.push(...data.results);} while(data.next);
        addField('subject','Subject','select',subjects.map(v=>[v.id,v.name]));
        addField('url','Resource link','url');
      } else addField('message','Message','textarea');
    }
    if(form.isConnected) button.disabled=false;
  } catch(error) {feedback.textContent=error.message;}
  form.append(feedback);
}
function removeWorkspace(key,record,onSaved) {
  const name=record.title || record.subject_name+' · '+record.day;
  openModal('Delete '+modules[key].noun,'',async()=>{
    try {
      const response=await API.workspace('DELETE',key+'/'+record.id+'/');
      if(!response?.ok) throw new Error();
      bsModal.hide();onSaved();
    } catch {toast('Could not delete this record.','danger');}
  });
  $('modalSave').textContent='Delete';
  $('modalBody').textContent='Delete “'+name+'”?';
}
