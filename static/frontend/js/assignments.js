async function renderAssignments(page=1) {
  setTitle('Assignments');
  const section = element('section','workspace-section');
  const header = element('div','section-header');
  header.append(element('h2','','Assignments'));
  if (user.role === 'teacher') {
    header.append(actionButton('Post assignment',openAssignmentForm,'btn btn-primary'));
  }
  const list = element('div','workspace-card','Loading…');
  section.append(header,list);
  pc().replaceChildren(section);
  try {
    const data = await workspaceData('assignments/',{page});
    list.replaceChildren();
    for (const item of data.results) {
      const row = element('article','workspace-row');
      const content = element('div','workspace-copy');
      content.append(element('strong','workspace-title',item.title),
        element('small','workspace-meta',[item.class_name,item.teacher_name,new Date(item.published).toLocaleDateString()].join(' · ')));
      if (item.instructions) content.append(element('p','notice-body',item.instructions));
      if (item.filename) content.append(actionButton('Download '+item.filename,()=>downloadAssignment(item)));
      row.append(content); list.append(row);
    }
    if (!data.count) list.append(element('p','workspace-empty','No assignments posted yet.'));
    const nav = element('div','workspace-actions mt-3');
    if (data.previous) nav.append(actionButton('Previous',()=>renderAssignments(page-1)));
    if (data.next) nav.append(actionButton('Next',()=>renderAssignments(page+1)));
    if (nav.childElementCount) list.append(nav);
  } catch { list.textContent=workspaceLoadMessage; }
}

async function downloadAssignment(item) {
  try {
    const response=await API.workspace('GET','assignments/'+item.id+'/download/');
    if (!response?.ok) throw new Error();
    const url=URL.createObjectURL(await response.blob());
    const link=document.createElement('a');
    link.href=url; link.download=item.filename; document.body.append(link);
    link.click(); link.remove(); setTimeout(()=>URL.revokeObjectURL(url),60000);
  } catch { toast('Could not download the attachment. Please try again.','danger'); }
}

async function openAssignmentForm() {
  openModal('Post assignment',`
    <form id="assignmentForm" class="workspace-editor">
      <label>Class<select class="form-select" name="class_obj" required><option value="">Choose a class…</option></select></label>
      <label>Title<input class="form-control" name="title" maxlength="180" required></label>
      <label>Instructions<textarea class="form-control" rows="5" name="instructions"></textarea></label>
      <label>Attachment<input class="form-control" type="file" name="file" accept=".doc,.docx,.pdf,.jpg,.jpeg,.png,.webp"></label>
      <small class="workspace-meta">Type instructions, attach a file, or do both. Word, PDF, JPEG, PNG or WebP, up to 10 MB.</small>
      <p class="text-danger mb-0" role="alert"></p>
    </form>`,publish);
  const form=$('assignmentForm'), save=$('modalSave'), feedback=form.querySelector('[role=alert]');
  save.textContent='Publish'; save.disabled=true;
  form.onsubmit=e=>{ e.preventDefault(); publish(); };
  try {
    const choices=await workspaceData('assignments/choices/');
    if (!form.isConnected) return;
    choices.forEach(c=>form.elements.class_obj.add(new Option(c.name,c.id)));
    if (choices.length===1) form.elements.class_obj.selectedIndex=1;
    save.disabled=!choices.length;
    if (!choices.length) feedback.textContent='Ask your administrator to assign you a class or subject first.';
  } catch {feedback.textContent=workspaceLoadMessage;}
  async function publish() {
    if (save.disabled || !form.reportValidity()) return;
    const file=form.elements.file.files[0];
    if (!file && !form.elements.instructions.value.trim()) {feedback.textContent='Type instructions or choose a file.';return;}
    if (file && file.size>10*1024*1024) {feedback.textContent='Choose a file of 10 MB or less.';return;}
    const data=new FormData(form);
    if (!file) data.delete('file');
    save.disabled=true; feedback.textContent='Publishing…';
    try {
      const response=await API.workspace('POST','assignments/',data);
      if (!response?.ok) {
        const details=await response?.json();
        feedback.textContent=Object.values(details||{}).flat().join(' ') || 'Could not publish this assignment.';
        return;
      }
      if (form.isConnected && activeSection==='assignments') {
        bsModal.hide(); renderAssignments(); toast('Assignment published.');
      }
    } catch {feedback.textContent='Could not publish this assignment. Please try again.';}
    finally {if (form.isConnected) save.disabled=false;}
  }
}
