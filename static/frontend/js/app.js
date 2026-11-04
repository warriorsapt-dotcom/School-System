/* ── State ── */
let user = null;
let schoolAccountSuffix = JSON.parse(document.getElementById('schoolAccountSuffix').textContent);
let activeSection = 'overview';
let bsModal = null;

/* ── Nav config by role ── */
const NAV = {
  admin: [
    { section:'overview',  icon:'fa-gauge-high',      label:'Dashboard' },
    { section:'students',  icon:'fa-user-graduate',   label:'Students' },
    { section:'teachers',  icon:'fa-chalkboard-user', label:'Teachers' },
    { section:'classes',   icon:'fa-building-columns',label:'Classes' },
    { section:'subjects',  icon:'fa-book',             label:'Subjects' },
    { section:'attendance',icon:'fa-calendar-check',   label:'Attendance' },
    { section:'scores',    icon:'fa-star-half-stroke', label:'Scores' },
    { section:'results',   icon:'fa-trophy',           label:'Results' },
    { section:'school_settings', icon:'fa-school', label:'School Settings' },
    { section:'images',    icon:'fa-images',           label:'School Images' },
    { section:'profile',   icon:'fa-circle-user',      label:'Profile' },
  ],
  teacher: [
    { section:'overview',         icon:'fa-gauge-high',      label:'Dashboard' },
    { section:'class_performance',icon:'fa-chart-bar',       label:'Class Performance' },
    { section:'students',         icon:'fa-user-graduate',   label:'My Students' },
    { section:'classes',          icon:'fa-building-columns',label:'My Classes' },
    { section:'attendance',       icon:'fa-calendar-check',   label:'Attendance' },
    { section:'scores',           icon:'fa-star-half-stroke', label:'Scores' },
    { section:'profile',          icon:'fa-circle-user',      label:'Profile' },
  ],
  student: [
    { section:'overview',  icon:'fa-gauge-high',      label:'Dashboard' },
    { section:'attendance',icon:'fa-calendar-check',   label:'My Attendance' },
    { section:'scores',    icon:'fa-star-half-stroke', label:'My Scores' },
    { section:'results',   icon:'fa-trophy',           label:'My Results' },
    { section:'profile',   icon:'fa-circle-user',      label:'Profile' },
  ],
};

/* ── Helpers ── */
const $  = id => document.getElementById(id);
const pc = () => $('pageContent');

function setTitle(t) { $('pageTitle').textContent = t; }

function loading() {
  pc().innerHTML = `<div class="spinner-wrap"><div class="spinner-border text-primary"></div><span>Loading…</span></div>`;
}

function empty(msg = 'No records found.') {
  return `<div class="empty-state"><i class="fas fa-inbox"></i><p>${msg}</p></div>`;
}

function toast(msg, type = 'success') {
  const el = $('toast');
  el.className = `toast align-items-center text-bg-${type} border-0`;
  $('toastMsg').textContent = msg;
  new bootstrap.Toast(el, { delay: 3500 }).show();
}

function badge(val, trueLabel='Active', falseLabel='Inactive') {
  return val
    ? `<span class="badge rounded-pill status-active">${trueLabel}</span>`
    : `<span class="badge rounded-pill status-inactive">${falseLabel}</span>`;
}

function table(cols, rows) {
  if (!rows.length) return empty();
  const head = cols.map(c => `<th>${c}</th>`).join('');
  const body = rows.map(r => `<tr>${r.map(c => `<td>${c ?? '—'}</td>`).join('')}</tr>`).join('');
  return `<div class="table-responsive"><table class="table table-hover">
    <thead class="table-light"><tr>${head}</tr></thead>
    <tbody>${body}</tbody>
  </table></div>`;
}

function openModal(title, body, onSave) {
  $('modalTitle').textContent = title;
  $('modalBody').innerHTML = body;
  const saveBtn = $('modalSave');
  if (onSave) {
    saveBtn.classList.remove('d-none');
    saveBtn.onclick = onSave;
  } else {
    saveBtn.classList.add('d-none');
  }
  bsModal.show();
}

/* Render paginator controls for server-side pagination */
function paginatorControls(count, page, pageSize, onPage) {
  const totalPages = Math.ceil(count / pageSize);
  if (totalPages <= 1) return '';
  const prev = page > 1 ? `<li class="page-item"><a class="page-link" href="#" data-p="${page-1}">‹</a></li>` : `<li class="page-item disabled"><span class="page-link">‹</span></li>`;
  const next = page < totalPages ? `<li class="page-item"><a class="page-link" href="#" data-p="${page+1}">›</a></li>` : `<li class="page-item disabled"><span class="page-link">›</span></li>`;
  const pages = [];
  const start = Math.max(1, page - 2);
  const end   = Math.min(totalPages, page + 2);
  for (let i = start; i <= end; i++) {
    pages.push(`<li class="page-item ${i===page?'active':''}"><a class="page-link" href="#" data-p="${i}">${i}</a></li>`);
  }
  const html = `<nav><ul class="pagination pagination-sm justify-content-center mb-0">${prev}${pages.join('')}${next}</ul></nav>`;
  setTimeout(() => {
    document.querySelectorAll('.page-link[data-p]').forEach(a => {
      a.addEventListener('click', e => { e.preventDefault(); onPage(+a.dataset.p); });
    });
  }, 0);
  return html;
}

/* Destroy a Chart.js instance on a canvas before re-creating it */
function destroyChart(id) {
  const existing = Chart.getChart(id);
  if (existing) existing.destroy();
}

/* Stat card HTML helper */
function statCard(icon, label, value, bg, color) {
  return `<div class="stat-card">
    <div class="stat-icon" style="background:${bg};color:${color}"><i class="fas ${icon}"></i></div>
    <div class="stat-info"><div class="stat-value">${value}</div><div class="stat-label">${label}</div></div>
  </div>`;
}

/* ── Sections ── */

async function renderOverview() {
  setTitle('Dashboard');
  loading();
  const role = user.role;

  const [stuRes, tchRes, clsRes, trmRes, attRes] = await Promise.all([
    role !== 'student' ? API.json(await API.getStudents({page_size:1})) : null,
    role === 'admin'   ? API.json(await API.getTeachers({page_size:1})) : null,
    API.json(await API.getClasses({page_size:1})),
    API.json(await API.getTerms({is_current:true})),
    role === 'student' ? API.json(await API.getAttendance({page_size:500, ordering:'-date'})) : null,
  ]);

  if (activeSection !== 'overview') return;

  const termName = trmRes?.results?.[0]
    ? `${trmRes.results[0].name.replace('_',' ')} ${trmRes.results[0].academic_year}`
    : 'N/A';

  const cards = [];
  if (role !== 'student') cards.push({ icon:'fa-user-graduate', label:'Total Students', value: stuRes?.count ?? '—', bg:'#e9d8fd', color:'#6b21a8' });
  if (role === 'admin')   cards.push({ icon:'fa-chalkboard-user',label:'Total Teachers', value: tchRes?.count ?? '—', bg:'#bee3f8', color:'#1a56db' });
  cards.push({ icon:'fa-building-columns', label:'Classes', value: clsRes?.count ?? '—', bg:'#c6f6d5', color:'#276749' });
  cards.push({ icon:'fa-calendar-days', label:'Current Term', value: termName, bg:'#feebc8', color:'#c05621' });

  const cardHtml = cards.map(c => `
    <div class="col-md-3 col-sm-6 mb-4">
      <div class="stat-card">
        <div class="stat-icon" style="background:${c.bg};color:${c.color}"><i class="fas ${c.icon}"></i></div>
        <div class="stat-info">
          <div class="stat-value">${c.value}</div>
          <div class="stat-label">${c.label}</div>
        </div>
      </div>
    </div>`).join('');

  // Compute student attendance counts for overview chart
  const attRecords = attRes?.results ?? [];
  const attCounts = { present:0, absent:0, late:0, excused:0, medical:0 };
  attRecords.forEach(r => { if (r.status in attCounts) attCounts[r.status]++; });
  const attTotal = attRecords.length;
  const attRate  = attTotal ? ((attCounts.present / attTotal) * 100).toFixed(1) : null;

  const attChartCard = (role === 'student' && attTotal > 0) ? `
    <div class="col-md-6 mb-4">
      <div class="card h-100">
        <div class="card-header"><i class="fas fa-chart-pie me-2"></i>My Attendance — ${attRate}% rate</div>
        <div class="card-body"><div style="position:relative;height:200px"><canvas id="overviewAttChart"></canvas></div></div>
      </div>
    </div>` : `
    <div class="col-md-6 mb-4">
      <div class="card h-100">
        <div class="card-header"><i class="fas fa-circle-info me-2"></i>Welcome</div>
        <div class="card-body">
          <p class="mb-1">Hello, <strong>${user.first_name} ${user.last_name}</strong>!</p>
          <p class="text-muted small mb-0">Role: <span class="role-pill role-${role}">${role}</span></p>
          <p class="text-muted small mb-0 mt-1">Active term: <strong>${termName}</strong></p>
        </div>
      </div>
    </div>`;

  pc().innerHTML = `
    <div class="row">${cardHtml}</div>
    <div class="row mt-2">
      <div class="col-md-6 mb-4">
        <div class="card">
          <div class="card-header"><i class="fas fa-clock-rotate-left me-2"></i>Quick Links</div>
          <div class="card-body">
            <div class="d-flex flex-wrap gap-2">
              ${NAV[role].filter(n=>n.section!=='overview').map(n=>`
                <button class="btn btn-outline-primary btn-sm" onclick="navigate('${n.section}')">
                  <i class="fas ${n.icon} me-1"></i>${n.label}
                </button>`).join('')}
            </div>
          </div>
        </div>
      </div>
      ${attChartCard}
    </div>`;

  // Render attendance donut chart for students
  if (role === 'student' && attTotal > 0) {
    const COLOR_MAP = { present:'#06d6a0', absent:'#ef476f', late:'#ffd166', excused:'#4361ee', medical:'#adb5bd' };
    const nonZero = Object.entries(attCounts).filter(([,v]) => v > 0);
    destroyChart('overviewAttChart');
    new Chart($('overviewAttChart'), {
      type: 'doughnut',
      data: {
        labels: nonZero.map(([k]) => k.charAt(0).toUpperCase() + k.slice(1)),
        datasets: [{
          data: nonZero.map(([,v]) => v),
          backgroundColor: nonZero.map(([k]) => COLOR_MAP[k]),
          borderWidth: 2,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } },
          tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed} days` } }
        }
      }
    });
  }
}

async function renderStudents(page = 1) {
  if (user.role === 'teacher') { await renderTeacherStudents(); return; }

  setTitle('Students');
  loading();
  const pageSize = 20;
  const data = await API.json(await API.getStudents({ page, page_size: pageSize }));
  const students = data?.results ?? [];
  const count    = data?.count ?? 0;

  const addBtn = `<button class="btn btn-primary btn-sm" onclick="openAddStudent()"><i class="fas fa-plus me-1"></i>Add Student</button>`;

  pc().innerHTML = `
    <div class="section-header">
      <h4><i class="fas fa-user-graduate me-2 text-primary"></i>Students</h4>
      ${addBtn}
    </div>
    <div class="card">
      <div class="card-header d-flex gap-3 align-items-center flex-wrap">
        <span class="text-muted small">${count} total</span>
      </div>
      <div class="card-body p-0">
        ${table(
          ['Name','Admission #','Class','Parent Contact','Status',''],
          students.map(s => [
            `<strong>${s.user?.first_name} ${s.user?.last_name}</strong><br><small class="text-muted">${s.user?.email}</small>`,
            s.admission_number,
            s.class_assigned_name || '—',
            s.parent_contact || '—',
            badge(s.is_active),
            `<button class="btn btn-outline-secondary btn-sm" onclick="openStudentProgress('${s.id}','${s.user?.first_name} ${s.user?.last_name}')"><i class="fas fa-chart-line"></i></button>`,
          ])
        )}
      </div>
      <div class="card-footer">${paginatorControls(count, page, pageSize, p => renderStudents(p))}</div>
    </div>`;
}

async function renderTeacherStudents() {
  setTitle('My Students');
  loading();

  const data = await API.json(await API.getStudents({ page_size: 200, ordering: 'user__last_name' }));
  const students = data?.results ?? [];

  if (!students.length) {
    pc().innerHTML = `
      <div class="section-header"><h4><i class="fas fa-user-graduate me-2 text-primary"></i>My Students</h4></div>
      ${empty('No students found in your classes.')}`;
    return;
  }

  // Group by class
  const byClass = {};
  students.forEach(s => {
    const cls = s.class_assigned_name || 'Unassigned';
    if (!byClass[cls]) byClass[cls] = [];
    byClass[cls].push(s);
  });

  const classSections = Object.entries(byClass).map(([className, list]) => `
    <div class="card mb-4">
      <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
        <strong><i class="fas fa-building-columns me-2"></i>${className}</strong>
        <span class="badge bg-light text-dark">${list.length} student${list.length !== 1 ? 's' : ''}</span>
      </div>
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover mb-0">
            <thead class="table-light"><tr>
              <th>Name</th><th>Admission #</th><th>Parent Contact</th><th>Status</th><th></th>
            </tr></thead>
            <tbody>
              ${list.map(s => `
                <tr>
                  <td>
                    <strong>${s.user?.first_name} ${s.user?.last_name}</strong>
                    <br><small class="text-muted">${s.user?.email}</small>
                  </td>
                  <td>${s.admission_number}</td>
                  <td>${s.parent_contact || '—'}</td>
                  <td>${badge(s.is_active)}</td>
                  <td>
                    <button class="btn btn-primary btn-sm"
                      onclick="openStudentDetail('${s.id}','${(s.user?.first_name + ' ' + s.user?.last_name).replace(/'/g,"\\'")}')">
                      <i class="fas fa-eye me-1"></i>View Details
                    </button>
                    <button class="btn btn-outline-primary btn-sm" onclick="openAttendanceHistory('${s.id}')">Attendance History</button>
                  </td>
                </tr>`).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>`).join('');

  pc().innerHTML = `
    <div class="section-header">
      <h4><i class="fas fa-user-graduate me-2 text-primary"></i>My Students</h4>
      <span class="text-muted small">${students.length} student${students.length !== 1 ? 's' : ''} across ${Object.keys(byClass).length} class${Object.keys(byClass).length !== 1 ? 'es' : ''}</span>
    </div>
    ${classSections}`;
}

async function renderTeachers(page = 1) {
  setTitle('Teachers');
  loading();
  const pageSize = 20;
  const data = await API.json(await API.getTeachers({ page, page_size: pageSize }));
  const teachers = data?.results ?? [];
  const count    = data?.count ?? 0;

  const addBtn = user.role === 'admin'
    ? `<button class="btn btn-primary btn-sm" onclick="openAddTeacher()"><i class="fas fa-plus me-1"></i>Add Teacher</button>`
    : '';

  pc().innerHTML = `
    <div class="section-header">
      <h4><i class="fas fa-chalkboard-user me-2 text-primary"></i>Teachers</h4>
      ${addBtn}
    </div>
    <div class="card">
      <div class="card-header"><span class="text-muted small">${count} total</span></div>
      <div class="card-body p-0">
        ${table(
          ['Name','Employee ID','Specialization','Qualification','Class Teacher','Status'],
          teachers.map(t => [
            `<strong>${t.user?.first_name} ${t.user?.last_name}</strong><br><small class="text-muted">${t.user?.email}</small>`,
            t.employee_id,
            t.subject_specialization || '—',
            t.qualification || '—',
            t.is_class_teacher ? '<i class="fas fa-check text-success"></i>' : '—',
            badge(t.is_active),
          ])
        )}
      </div>
      <div class="card-footer">${paginatorControls(count, page, 20, p => renderTeachers(p))}</div>
    </div>`;
}

async function renderClasses() {
  setTitle('Classes');
  loading();
  const data = await API.json(await API.getClasses({ page_size: 100 }));
  const classes = data?.results ?? [];

  const cards = classes.map(c => `
    <div class="col-md-4 col-sm-6 mb-4">
      <div class="card h-100">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-start mb-2">
            <h5 class="card-title mb-0">${c.name}</h5>
            ${badge(c.is_active)}
          </div>
          <p class="text-muted small mb-1"><i class="fas fa-layer-group me-1"></i>Form ${c.form_level}${c.section} ${c.stream||''}</p>
          <p class="text-muted small mb-1"><i class="fas fa-user-tie me-1"></i>${c.class_teacher_name||'No class teacher'}</p>
          <p class="text-muted small mb-1"><i class="fas fa-users me-1"></i>${c.student_count} students</p>
          <p class="text-muted small mb-0"><i class="fas fa-calendar me-1"></i>${c.year}</p>
        </div>
      </div>
    </div>`).join('');

  pc().innerHTML = `
    <div class="section-header">
      <h4><i class="fas fa-building-columns me-2 text-primary"></i>Classes</h4>
      <span class="text-muted small">${classes.length} total</span>
    </div>
    <div class="row">${cards || `<div class="col"><div class="empty-state"><i class="fas fa-inbox"></i><p>No classes found.</p></div></div>`}</div>`;
}

async function renderSubjects() {
  setTitle('Subjects');
  loading();
  const data = await API.json(await API.getSubjects({ page_size: 100 }));
  const subjects = data?.results ?? [];

  pc().innerHTML = `
    <div class="section-header">
      <h4><i class="fas fa-book me-2 text-primary"></i>Subjects</h4>
    </div>
    <div class="card">
      <div class="card-body p-0">
        ${table(
          ['Name','Code','Compulsory','Status'],
          subjects.map(s => [
            `<strong>${s.name}</strong>`,
            s.code || '—',
            s.is_compulsory ? '<i class="fas fa-check text-success"></i>' : '<i class="fas fa-minus text-muted"></i>',
            badge(s.is_active),
          ])
        )}
      </div>
    </div>`;
}

async function renderAttendance() {
  setTitle('Attendance');
  loading();
  const role = user.role;

  /* ── Student: raw attendance records + chart ── */
  if (role === 'student') {
    const data = await API.json(await API.getAttendance({ page_size: 500, ordering: '-date' }));
    const records = data?.results ?? [];

    if (!records.length) {
      pc().innerHTML = `
        <div class="section-header">
          <h4><i class="fas fa-calendar-check me-2 text-primary"></i>My Attendance</h4>
        </div>
        ${empty('No attendance records found.')}`;
      return;
    }

    const C = { present:0, absent:0, late:0, excused:0, medical:0 };
    records.forEach(r => { if (r.status in C) C[r.status]++; });
    const total   = records.length;
    const attRate = ((C.present / total) * 100).toFixed(1);
    const COLOR_MAP = { present:'#06d6a0', absent:'#ef476f', late:'#ffd166', excused:'#4361ee', medical:'#adb5bd' };
    const STATUS_BG = { present:'success', absent:'danger', late:'warning', excused:'info', medical:'secondary' };

    pc().innerHTML = `
      <div class="section-header">
        <h4><i class="fas fa-calendar-check me-2 text-primary"></i>My Attendance</h4>
      </div>

      <div class="row g-3 mb-4">
        <div class="col-6 col-md-3">
          ${statCard('fa-check-circle', 'Present', C.present, '#c6f6d5', '#276749')}
        </div>
        <div class="col-6 col-md-3">
          ${statCard('fa-times-circle', 'Absent', C.absent, '#fed7d7', '#9b2c2c')}
        </div>
        <div class="col-6 col-md-3">
          ${statCard('fa-clock', 'Late', C.late, '#feebc8', '#c05621')}
        </div>
        <div class="col-6 col-md-3">
          ${statCard('fa-percent', 'Attendance Rate', attRate + '%', '#bee3f8', '#1a56db')}
        </div>
      </div>

      <div class="row g-3 mb-4">
        <div class="col-md-4">
          <div class="card h-100">
            <div class="card-header"><i class="fas fa-chart-pie me-2"></i>Breakdown</div>
            <div class="card-body"><div style="position:relative;height:230px"><canvas id="attDonut"></canvas></div></div>
          </div>
        </div>
        <div class="col-md-8">
          <div class="card h-100">
            <div class="card-header"><i class="fas fa-list me-2"></i>Recent Attendance</div>
            <div class="card-body p-0" style="max-height:320px;overflow-y:auto">
              ${table(
                ['Date', 'Term', 'Status'],
                records.slice(0, 50).map(r => [
                  r.date,
                  r.term_name || '—',
                  `<span class="badge bg-${STATUS_BG[r.status]||'secondary'}">${r.status}</span>`,
                ])
              )}
            </div>
          </div>
        </div>
      </div>`;

    const nonZero = Object.entries(C).filter(([,v]) => v > 0);
    destroyChart('attDonut');
    new Chart($('attDonut'), {
      type: 'doughnut',
      data: {
        labels: nonZero.map(([k]) => k.charAt(0).toUpperCase() + k.slice(1)),
        datasets: [{
          data: nonZero.map(([,v]) => v),
          backgroundColor: nonZero.map(([k]) => COLOR_MAP[k]),
          borderWidth: 2,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } },
          tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed} days` } }
        }
      }
    });
    return;
  }

  /* ── Teacher / Admin: mark attendance form ── */
  const [clsData, trmData] = await Promise.all([
    API.json(await API.getClasses({ page_size: 100 })),
    API.json(await API.getTerms({ is_current: true })),
  ]);
  const classes = clsData?.results ?? [];
  const currentTerm = trmData?.results?.[0];

  pc().innerHTML = `
    <div class="section-header">
      <h4><i class="fas fa-calendar-check me-2 text-primary"></i>Mark Attendance</h4>
    </div>
    <div class="card mb-4">
      <div class="card-header">Select Class & Date</div>
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-4">
            <label class="form-label small fw-semibold">Class</label>
            <select class="form-select" id="attClass">
              <option value="">— Select class —</option>
              ${classes.map(c=>`<option value="${c.id}">${c.name}</option>`).join('')}
            </select>
          </div>
          <div class="col-md-3">
            <label class="form-label small fw-semibold">Date</label>
            <input type="date" class="form-control" id="attDate" value="${new Date().toISOString().split('T')[0]}">
          </div>
          <div class="col-md-3 d-flex align-items-end">
            <button class="btn btn-primary w-100" id="loadStudentsBtn">
              <i class="fas fa-users me-2"></i>Load Students
            </button>
          </div>
        </div>
      </div>
    </div>
    <div id="attendanceForm"></div>`;

  $('loadStudentsBtn').addEventListener('click', async () => {
    const classId = $('attClass').value;
    const attDate = $('attDate').value;
    if (!classId || !attDate) { toast('Select a class and date first.', 'warning'); return; }

    const cls = await API.json(await API.getClass(classId));
    const students = cls?.students ?? [];

    const existing = await API.json(await API.getAttendance({ class_obj: classId, date: attDate, page_size: 200 }));
    const existingMap = {};
    (existing?.results ?? []).forEach(a => { existingMap[a.student] = a.status; });

    const statuses = ['present','absent','late','excused','medical'];
    const statusColor = { present:'success', absent:'danger', late:'warning', excused:'info', medical:'secondary' };

    const rows = students.map(s => `
      <div class="attendance-card">
        <div>
          <div class="att-student-name">${s.user?.first_name} ${s.user?.last_name}</div>
          <div class="att-id">${s.admission_number}</div>
          <button type="button" class="btn btn-link btn-sm px-0" onclick="openAttendanceHistory('${s.id}')">Attendance History</button>
        </div>
        <div class="d-flex gap-1 flex-wrap justify-content-end">
          ${statuses.map(st => `
            <input type="radio" class="btn-check" name="att_${s.id}" id="att_${s.id}_${st}" value="${st}"
              ${(existingMap[s.id]||'present')===st ? 'checked' : ''}>
            <label class="btn btn-outline-${statusColor[st]} btn-sm" for="att_${s.id}_${st}">${st}</label>
          `).join('')}
        </div>
      </div>`).join('');

    $('attendanceForm').innerHTML = students.length ? `
      <div class="card">
        <div class="card-header d-flex justify-content-between align-items-center">
          <span>${cls.name} — ${attDate}</span>
          <button class="btn btn-success btn-sm" id="saveAttBtn">
            <i class="fas fa-save me-1"></i>Save Attendance
          </button>
        </div>
        <div class="card-body">
          <div class="d-flex gap-2 mb-3">
            <button class="btn btn-outline-success btn-sm" onclick="markAll('present')">All Present</button>
            <button class="btn btn-outline-danger btn-sm" onclick="markAll('absent')">All Absent</button>
          </div>
          ${rows}
        </div>
      </div>` : empty('No students in this class.');

    window._attStudents = students;
    window._attClassId = classId;
    window._attDate = attDate;
    window._attTermId = currentTerm?.id;

    $('saveAttBtn')?.addEventListener('click', saveAttendance);
  });
}

window.openAttendanceHistory = (studentId) => {
  openModal('Student Attendance History', `
    <form id="historyFilters" class="row g-2 mb-3">
      <div class="col-sm-4"><label for="historyStart" class="form-label">From</label><input id="historyStart" type="date" class="form-control"></div>
      <div class="col-sm-4"><label for="historyEnd" class="form-label">To</label><input id="historyEnd" type="date" class="form-control"></div>
      <div class="col-sm-4"><label for="historyStatus" class="form-label">Status</label><select id="historyStatus" class="form-select">
        <option value="">All statuses</option><option value="present">Present</option><option value="absent">Absent</option><option value="late">Late</option><option value="excused">Excused</option><option value="medical">Medical leave</option>
      </select></div>
      <div class="col-12"><button class="btn btn-primary btn-sm" type="submit">Apply filters</button> <button class="btn btn-outline-secondary btn-sm" type="reset">Reset</button></div>
    </form>
    <div id="historyRecords" aria-live="polite"></div>
    <div class="d-flex justify-content-between align-items-center mt-3">
      <button id="historyPrev" class="btn btn-outline-primary btn-sm">Previous</button>
      <span id="historyCount"></span>
      <button id="historyNext" class="btn btn-outline-primary btn-sm">Next</button>
    </div>`, null);
  const form = $('historyFilters'), records = $('historyRecords');
  const prev = $('historyPrev'), next = $('historyNext'), count = $('historyCount');
  let page = 1, requestId = 0, filters = {};
  const escape = value => { const el = document.createElement('span'); el.textContent = value ?? '—'; return el.innerHTML; };
  async function load(targetPage) {
    const currentRequest = ++requestId;
    records.textContent = 'Loading attendance history…';
    prev.disabled = next.disabled = true;
    count.textContent = '';
    try {
      const response = await API.studentAttendance(studentId, { ...filters, page: targetPage });
      if (!response?.ok) throw new Error('Unable to load attendance history. Check your class access and try again.');
      const data = await API.json(response);
      if (currentRequest !== requestId || !records.isConnected) return;
      page = targetPage;
      records.innerHTML = data.results.length ? table(
        ['Date', 'Class', 'Status', 'Term', 'Marked by', 'Remarks'],
        data.results.map(r => [r.date, r.class_name, r.status, r.term_name, r.teacher_name || '—', r.remarks || '—'].map(escape))
      ) : empty('No attendance records match these filters.');
      if (data.results.length) $('modalTitle').textContent = `Attendance History — ${data.results[0].student_name}`;
      count.textContent = `${data.count} records · Page ${page}`;
      prev.disabled = !data.previous;
      next.disabled = !data.next;
    } catch (error) {
      if (currentRequest === requestId && records.isConnected) records.textContent = error.message;
    }
  }
  form.addEventListener('submit', e => {
    e.preventDefault();
    const start = $('historyStart').value, end = $('historyEnd').value;
    if (start && end && start > end) { toast('From date must be on or before To date.', 'warning'); return; }
    filters = {};
    if (start) filters.start_date = start;
    if (end) filters.end_date = end;
    if ($('historyStatus').value) filters.status = $('historyStatus').value;
    load(1);
  });
  form.addEventListener('reset', () => { filters = {}; load(1); });
  prev.onclick = () => load(page - 1);
  next.onclick = () => load(page + 1);
  load(1);
};

window.markAll = (status) => {
  (window._attStudents||[]).forEach(s => {
    const radio = document.getElementById(`att_${s.id}_${status}`);
    if (radio) radio.checked = true;
  });
};

async function saveAttendance() {
  const students = window._attStudents || [];
  const attendances = students.map(s => {
    const checked = document.querySelector(`input[name="att_${s.id}"]:checked`);
    return {
      student: s.id,
      class_obj: window._attClassId,
      date: window._attDate,
      status: checked?.value || 'absent',
      term: window._attTermId,
    };
  });

  const res = await API.bulkMark(attendances);
  if (res?.ok) {
    toast(`Attendance saved for ${students.length} students.`);
  } else {
    toast('Failed to save attendance.', 'danger');
  }
}

async function renderScores(page = 1) {
  setTitle('Scores');
  loading();
  const role = user.role;
  const pageSize = 20;

  const [pageData, allData] = await Promise.all([
    API.json(await API.getScores({ page, page_size: pageSize })),
    role === 'student' ? API.json(await API.getScores({ page_size: 300 })) : null,
  ]);

  const scores = pageData?.results ?? [];
  const count  = pageData?.count ?? 0;
  const all    = allData?.results ?? [];

  const addBtn = (role === 'teacher' || role === 'admin')
    ? `<button class="btn btn-primary btn-sm" onclick="openRecordScore()"><i class="fas fa-plus me-1"></i>Record Score</button>`
    : '';

  /* Student-only summary cards + subject chart */
  let topSection = '';
  if (role === 'student' && all.length) {
    const subjMap = {};
    all.forEach(s => {
      const k = s.subject_name || 'Unknown';
      if (!subjMap[k]) subjMap[k] = { sum: 0, n: 0 };
      subjMap[k].sum += parseFloat(s.percentage || 0);
      subjMap[k].n++;
    });
    const overallAvg = (all.reduce((t, s) => t + parseFloat(s.percentage || 0), 0) / all.length).toFixed(1);
    const gradeCounts = { A:0, B:0, C:0, D:0, E:0, F:0 };
    all.forEach(s => { if (s.grade in gradeCounts) gradeCounts[s.grade]++; });
    const topGrade = Object.entries(gradeCounts).find(([,v]) => v > 0)?.[0] || '—';

    topSection = `
      <div class="row g-3 mb-4">
        <div class="col-6 col-md-3">
          ${statCard('fa-chart-line', 'Overall Average', overallAvg + '%', '#bee3f8', '#1a56db')}
        </div>
        <div class="col-6 col-md-3">
          ${statCard('fa-file-alt', 'Assessments', all.length, '#c6f6d5', '#276749')}
        </div>
        <div class="col-6 col-md-3">
          ${statCard('fa-star', 'Top Grade', topGrade, '#feebc8', '#c05621')}
        </div>
        <div class="col-6 col-md-3">
          ${statCard('fa-book', 'Subjects', Object.keys(subjMap).length, '#e9d8fd', '#6b21a8')}
        </div>
      </div>
      <div class="card mb-4">
        <div class="card-header"><i class="fas fa-chart-bar me-2"></i>Average Score by Subject</div>
        <div class="card-body"><div style="position:relative;height:220px"><canvas id="subjectChart"></canvas></div></div>
      </div>`;
  }

  /* Table columns differ by role */
  const cols = role === 'student'
    ? ['Subject', 'Type', 'Marks', 'Max', '%', 'Grade', 'Term']
    : ['Student', 'Subject', 'Type', 'Marks', 'Max', '%', 'Grade', 'Term'];

  const rows = scores.map(s => {
    const r = [];
    if (role !== 'student') r.push(`<strong>${s.student_name || '—'}</strong>`);
    r.push(s.subject_name || '—');
    r.push(s.assessment_type?.replace('_', ' ') || '—');
    r.push(s.marks_obtained ?? '—');
    r.push(s.max_marks ?? '—');
    r.push(`<strong>${parseFloat(s.percentage || 0).toFixed(1)}%</strong>`);
    r.push(`<span class="badge bg-primary">${s.grade || '—'}</span>`);
    r.push(s.term_name || '—');
    return r;
  });

  pc().innerHTML = `
    <div class="section-header">
      <h4><i class="fas fa-star-half-stroke me-2 text-primary"></i>Scores</h4>
      ${addBtn}
    </div>
    ${topSection}
    <div class="card">
      <div class="card-body p-0">${table(cols, rows)}</div>
      <div class="card-footer">${paginatorControls(count, page, pageSize, p => renderScores(p))}</div>
    </div>`;

  /* Render subject chart for students */
  if (role === 'student' && all.length) {
    const subjMap = {};
    all.forEach(s => {
      const k = s.subject_name || 'Unknown';
      if (!subjMap[k]) subjMap[k] = { sum: 0, n: 0 };
      subjMap[k].sum += parseFloat(s.percentage || 0);
      subjMap[k].n++;
    });
    const labels = Object.keys(subjMap).sort();
    const avgs   = labels.map(k => (subjMap[k].sum / subjMap[k].n).toFixed(1));
    const PALETTE = ['#4361ee','#3a86ff','#06d6a0','#ffd166','#ef476f','#073b4c','#f72585','#7209b7'];
    destroyChart('subjectChart');
    new Chart($('subjectChart'), {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Average %',
          data: avgs,
          backgroundColor: labels.map((_, i) => PALETTE[i % PALETTE.length] + 'bb'),
          borderColor:     labels.map((_, i) => PALETTE[i % PALETTE.length]),
          borderWidth: 1,
          borderRadius: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { min: 0, max: 100, ticks: { callback: v => v + '%' } }
        }
      }
    });
  }
}

window.openRecordScore = async () => {
  const [stuData, clsData, trmData] = await Promise.all([
    API.json(await API.getStudents({ page_size: 200 })),
    API.json(await API.getClasses({ page_size: 100 })),
    API.json(await API.getTerms({ is_current: true })),
  ]);

  const students = stuData?.results ?? [];
  const classes  = clsData?.results ?? [];
  const terms    = trmData?.results ?? [];
  const types = ['test','exam','assignment','project','class_work','homework'];

  openModal('Record Score', `
    <form id="scoreForm">
      <div class="row g-3">
        <div class="col-md-6">
          <label class="form-label small fw-semibold">Student</label>
          <select class="form-select" name="student" required>
            <option value="">Select student…</option>
            ${students.map(s=>`<option value="${s.id}">${s.user?.first_name} ${s.user?.last_name} (${s.admission_number})</option>`).join('')}
          </select>
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-semibold">Class</label>
          <select class="form-select" id="scoreClass" required>
            <option value="">Select class…</option>
            ${classes.map(c=>`<option value="${c.id}">${c.name}</option>`).join('')}
          </select>
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-semibold">Subject (via class)</label>
          <select class="form-select" id="scoreClassSubject" name="class_subject" required disabled>
            <option value="">Select class first…</option>
          </select>
          <input type="hidden" name="subject" id="scoreSubjectHidden">
          <div id="scoreSubjectHelp" class="form-text" role="status" aria-live="polite"></div>
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-semibold">Assessment Type</label>
          <select class="form-select" name="assessment_type" required>
            ${types.map(t=>`<option value="${t}">${t.replace('_',' ')}</option>`).join('')}
          </select>
        </div>
        <div class="col-md-4">
          <label class="form-label small fw-semibold">Marks Obtained</label>
          <input type="number" class="form-control" name="marks_obtained" min="0" step="0.01" required>
        </div>
        <div class="col-md-4">
          <label class="form-label small fw-semibold">Max Marks</label>
          <input type="number" class="form-control" name="max_marks" value="100" min="0.01" step="0.01" required>
        </div>
        <div class="col-md-4">
          <label class="form-label small fw-semibold">Term</label>
          <select class="form-select" name="term">
            <option value="">Select term…</option>
            ${terms.map(t=>`<option value="${t.id}">${t.name} ${t.academic_year}</option>`).join('')}
          </select>
        </div>
        <div class="col-12">
          <label class="form-label small fw-semibold">Remarks (optional)</label>
          <textarea class="form-control" name="remarks" rows="2"></textarea>
        </div>
      </div>
    </form>`, async () => {
      const form = document.getElementById('scoreForm');
      if (!form.reportValidity()) return;
      const fd = new FormData(form);
      const payload = Object.fromEntries(fd.entries());
      payload.subject = $('scoreSubjectHidden').value;
      if (!payload.term) payload.term = null;
      if (!payload.class_subject || !payload.subject) {
        toast('Please select a class and subject.', 'warning'); return;
      }
      const res = await API.recordScore(payload);
      if (res?.ok) {
        toast('Score recorded!');
        bsModal.hide();
        renderScores();
      } else {
        const err = await API.json(res);
        toast(JSON.stringify(err), 'danger');
      }
    });

  let subjectRequest = 0;
  $('scoreClass').addEventListener('change', async function() {
    const requestId = ++subjectRequest;
    const classId = this.value;
    const sel = $('scoreClassSubject');
    const hidden = $('scoreSubjectHidden');
    const help = $('scoreSubjectHelp');
    hidden.value = '';
    help.textContent = '';
    sel.replaceChildren(new Option(classId ? 'Loading…' : 'Select class first…', ''));
    sel.disabled = true;
    if (!classId) return;
    try {
      const response = await API.getClass(classId);
      if (!response?.ok) throw new Error('Could not load subjects. Select the class again to retry.');
      const detail = await API.json(response);
      if (!Array.isArray(detail?.class_subjects)) throw new Error('The server returned an invalid subject list. Please contact the administrator.');
      if (requestId !== subjectRequest || !sel.isConnected) return;
      const classSubjects = detail.class_subjects;
      sel.replaceChildren(new Option(classSubjects.length ? 'Select subject…' : 'No subjects assigned', ''));
      for (const cs of classSubjects) {
        const option = new Option(`${cs.subject_name} (${cs.academic_year})`, cs.id);
        option.dataset.subject = cs.subject;
        sel.add(option);
      }
      sel.disabled = !classSubjects.length;
      if (!classSubjects.length) {
        help.textContent = 'An administrator needs to assign subjects to this class under Django admin → Class Subjects.';
      }
    } catch (error) {
      if (requestId !== subjectRequest || !sel.isConnected) return;
      sel.replaceChildren(new Option('Unable to load subjects', ''));
      help.textContent = error.message;
    }
  });

  $('scoreClassSubject').addEventListener('change', function() {
    const opt = this.options[this.selectedIndex];
    $('scoreSubjectHidden').value = opt?.dataset?.subject ?? '';
  });
};

async function renderResults(page = 1) {
  setTitle('Results');
  loading();
  const pageSize = 20;

  const [pageData, allData] = await Promise.all([
    API.json(await API.getResults({ page, page_size: pageSize })),
    API.json(await API.getResults({ page_size: 500 })),
  ]);

  const results = pageData?.results ?? [];
  const count   = pageData?.count ?? 0;
  const all     = allData?.results ?? [];

  if (!all.length) {
    pc().innerHTML = `
      <div class="section-header">
        <h4><i class="fas fa-trophy me-2 text-primary"></i>Term Results</h4>
      </div>
      ${empty('No results yet. Run: python manage.py generate_term_results --term first --class "Form 1A"')}`;
    return;
  }

  /* Aggregate for charts */
  const gradeCounts   = { A:0, B:0, C:0, D:0, E:0, F:0 };
  const statusCounts  = { promoted:0, conditional:0, retained:0, pending:0 };
  const classAverages = {};
  const classN        = {};

  all.forEach(r => {
    if (r.overall_grade in gradeCounts) gradeCounts[r.overall_grade]++;
    if (r.status in statusCounts) statusCounts[r.status]++;
    if (r.class_name) {
      classAverages[r.class_name] = (classAverages[r.class_name] || 0) + parseFloat(r.average_percentage || 0);
      classN[r.class_name]        = (classN[r.class_name] || 0) + 1;
    }
  });

  const classLabels = Object.keys(classAverages).sort();
  const classAvgs   = classLabels.map(c => (classAverages[c] / classN[c]).toFixed(1));

  const totalStudents = all.length;
  const overallAvg    = (all.reduce((s, r) => s + parseFloat(r.average_percentage || 0), 0) / totalStudents).toFixed(1);
  const passRate      = ((statusCounts.promoted + statusCounts.conditional) / totalStudents * 100).toFixed(1);
  const topGrade      = ['A','B','C','D','E','F'].find(g => gradeCounts[g] > 0) || '—';

  const exportBtn = user.role === 'admin'
    ? `<button class="btn btn-outline-success btn-sm" onclick="exportResultsCsv()"><i class="fas fa-file-csv me-1"></i>Export CSV</button>`
    : '';

  pc().innerHTML = `
    <div class="section-header mb-3">
      <h4><i class="fas fa-trophy me-2 text-primary"></i>Term Results</h4>
      ${exportBtn}
    </div>

    <!-- Stat cards -->
    <div class="row g-3 mb-4">
      <div class="col-6 col-md-3">
        ${statCard('fa-users', 'Students', totalStudents, '#e9d8fd', '#6b21a8')}
      </div>
      <div class="col-6 col-md-3">
        ${statCard('fa-percent', 'Overall Avg', overallAvg + '%', '#bee3f8', '#1a56db')}
      </div>
      <div class="col-6 col-md-3">
        ${statCard('fa-arrow-up', 'Pass Rate', passRate + '%', '#c6f6d5', '#276749')}
      </div>
      <div class="col-6 col-md-3">
        ${statCard('fa-star', 'Top Grade', topGrade, '#feebc8', '#c05621')}
      </div>
    </div>

    <!-- Charts row -->
    <div class="row g-3 mb-4">
      <div class="col-md-4">
        <div class="card h-100">
          <div class="card-header"><i class="fas fa-chart-pie me-2"></i>Grade Distribution</div>
          <div class="card-body"><div style="position:relative;height:220px"><canvas id="gradeChart"></canvas></div></div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card h-100">
          <div class="card-header"><i class="fas fa-chart-bar me-2"></i>Class Averages</div>
          <div class="card-body"><div style="position:relative;height:220px"><canvas id="classChart"></canvas></div></div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card h-100">
          <div class="card-header"><i class="fas fa-chart-pie me-2"></i>Promotion Status</div>
          <div class="card-body"><div style="position:relative;height:220px"><canvas id="statusChart"></canvas></div></div>
        </div>
      </div>
    </div>

    <!-- Score distribution histogram -->
    <div class="card mb-4">
      <div class="card-header"><i class="fas fa-chart-area me-2"></i>Average % Distribution</div>
      <div class="card-body"><div style="position:relative;height:200px"><canvas id="distChart"></canvas></div></div>
    </div>

    <!-- Results table -->
    <div class="card">
      <div class="card-header fw-semibold"><i class="fas fa-table me-2"></i>All Results</div>
      <div class="card-body p-0">
        ${table(
          ['Student','Class','Avg %','Grade','Position','Passed','Failed','Status',''],
          results.map(r => [
            `<strong>${r.student_name}</strong>`,
            r.class_name,
            `<strong>${parseFloat(r.average_percentage||0).toFixed(1)}%</strong>`,
            `<span class="badge bg-primary">${r.overall_grade||'—'}</span>`,
            r.position_in_class ? `<span class="badge bg-secondary">#${r.position_in_class}</span>` : '—',
            `<span class="text-success fw-semibold">${r.subjects_passed}</span>`,
            `<span class="text-danger fw-semibold">${r.subjects_failed}</span>`,
            `<span class="badge bg-${r.status==='promoted'?'success':r.status==='retained'?'danger':r.status==='conditional'?'warning':'secondary'}">${r.status||'—'}</span>`,
            `<button class="btn btn-outline-secondary btn-sm" title="Progress chart"
               onclick="openStudentProgress('${r.student}','${r.student_name}')">
               <i class="fas fa-chart-line"></i></button>`,
          ])
        )}
      </div>
      <div class="card-footer">${paginatorControls(count, page, pageSize, p => renderResults(p))}</div>
    </div>`;

  /* ── Render charts (destroy existing first) ── */
  const GRADE_COLOR_MAP = { A:'#4361ee', B:'#3a86ff', C:'#06d6a0', D:'#ffd166', E:'#ef476f', F:'#073b4c' };
  const STATUS_COLORS   = { promoted:'#06d6a0', conditional:'#ffd166', retained:'#ef476f', pending:'#adb5bd' };

  /* Grade distribution doughnut — skip zero-count grades */
  const gradeNonZero = Object.entries(gradeCounts).filter(([,v]) => v > 0);
  destroyChart('gradeChart');
  new Chart($('gradeChart'), {
    type: 'doughnut',
    data: {
      labels: gradeNonZero.map(([k]) => `Grade ${k}`),
      datasets: [{
        data: gradeNonZero.map(([,v]) => v),
        backgroundColor: gradeNonZero.map(([k]) => GRADE_COLOR_MAP[k]),
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } },
        tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed} students` } }
      }
    }
  });

  /* Class averages horizontal bar */
  destroyChart('classChart');
  new Chart($('classChart'), {
    type: 'bar',
    data: {
      labels: classLabels,
      datasets: [{
        label: 'Average %',
        data: classAvgs,
        backgroundColor: classLabels.map((_, i) => ['#4361ee','#3a86ff','#06d6a0','#ffd166','#ef476f','#073b4c'][i % 6] + 'cc'),
        borderRadius: 6,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { min: 0, max: 100, ticks: { callback: v => v + '%' } } }
    }
  });

  /* Promotion status doughnut — skip zero-count statuses */
  const statusNonZero = Object.entries(statusCounts).filter(([,v]) => v > 0);
  destroyChart('statusChart');
  new Chart($('statusChart'), {
    type: 'doughnut',
    data: {
      labels: statusNonZero.map(([k]) => k.charAt(0).toUpperCase() + k.slice(1)),
      datasets: [{
        data: statusNonZero.map(([,v]) => v),
        backgroundColor: statusNonZero.map(([k]) => STATUS_COLORS[k]),
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } },
        tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed} students` } }
      }
    }
  });

  /* Average % distribution histogram */
  const buckets = Array(10).fill(0);
  all.forEach(r => {
    const pct = parseFloat(r.average_percentage || 0);
    buckets[Math.min(9, Math.floor(pct / 10))]++;
  });
  const bucketLabels = ['0–9','10–19','20–29','30–39','40–49','50–59','60–69','70–79','80–89','90–100'];
  destroyChart('distChart');
  new Chart($('distChart'), {
    type: 'bar',
    data: {
      labels: bucketLabels,
      datasets: [{
        label: 'Students',
        data: buckets,
        backgroundColor: bucketLabels.map((_, i) => i < 5 ? '#ef476fcc' : i < 7 ? '#ffd166cc' : '#06d6a0cc'),
        borderRadius: 4,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 } },
        x: { title: { display: true, text: 'Score Range (%)' } }
      }
    }
  });
}

window.exportResultsCsv = async () => {
  const res = await API.exportResultsCsv({});
  if (res?.ok) {
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = 'term_results.csv'; a.click();
    URL.revokeObjectURL(url);
  } else {
    toast('Export failed.', 'danger');
  }
};

window.openStudentProgress = async (studentId, studentName) => {
  openModal(`Progress Chart — ${studentName}`,
    `<div style="position:relative;height:300px"><canvas id="progressChart"></canvas></div>
     <div id="progressEmpty" class="d-none text-center text-muted mt-3">No progress data available yet.</div>`,
    null
  );

  const data = await API.json(await API.studentProgress(studentId));
  if (!data?.length) {
    $('progressEmpty').classList.remove('d-none');
    return;
  }

  const labels   = data.map(d => `${d.term_name || ''} ${d.academic_year}`.trim());
  const percents = data.map(d => parseFloat(d.average_percentage));

  destroyChart('progressChart');
  new Chart($('progressChart'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Average %',
        data: percents,
        borderColor: '#4361ee',
        backgroundColor: 'rgba(67,97,238,.15)',
        fill: true,
        tension: 0.3,
        pointRadius: 5,
        pointBackgroundColor: '#4361ee',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { min: 0, max: 100, ticks: { callback: v => v + '%' } }
      },
      plugins: { legend: { display: false } }
    }
  });
};

window.openStudentDetail = async (studentId, studentName) => {
  openModal(`Student: ${studentName}`,
    `<div class="text-center py-4"><div class="spinner-border text-primary"></div><span class="ms-2">Loading…</span></div>`,
    null
  );

  const [scoresRes, attRes, progressRes] = await Promise.all([
    API.json(await API.getScores({ student: studentId, page_size: 200 })),
    API.json(await API.getAttendance({ student: studentId, page_size: 500 })),
    API.json(await API.studentProgress(studentId)),
  ]);

  const scores   = scoresRes?.results ?? [];
  const attRecs  = attRes?.results ?? [];
  const progress = progressRes ?? [];

  // Attendance stats
  const attTotal   = attRecs.length;
  const attPresent = attRecs.filter(a => a.status === 'present').length;
  const attLate    = attRecs.filter(a => a.status === 'late').length;
  const attAbsent  = attRecs.filter(a => a.status === 'absent').length;
  const attRate    = attTotal ? Math.round((attPresent + attLate) / attTotal * 100) : 0;

  // Subject average scores
  const subjectMap = {};
  scores.forEach(s => {
    const subj = s.subject_name || s.subject;
    if (!subjectMap[subj]) subjectMap[subj] = { sum: 0, count: 0 };
    subjectMap[subj].sum += parseFloat(s.percentage || 0);
    subjectMap[subj].count++;
  });
  const subjectLabels = Object.keys(subjectMap);
  const subjectAvgs   = subjectLabels.map(k => +(subjectMap[k].sum / subjectMap[k].count).toFixed(1));
  const overallAvg    = subjectAvgs.length ? +(subjectAvgs.reduce((a, b) => a + b, 0) / subjectAvgs.length).toFixed(1) : 0;

  // Recent scores (last 10)
  const recentScores = [...scores].reverse().slice(0, 10);

  // Progress data
  const progLabels   = progress.map(d => `${d.term_name || ''} ${d.academic_year}`.trim());
  const progPercents = progress.map(d => parseFloat(d.average_percentage));

  const modalEl = $('modalBody');
  if (!modalEl) return;

  modalEl.innerHTML = `
    <div class="row g-3 mb-4">
      <div class="col-6">
        <div class="card text-center h-100 border-0 bg-light">
          <div class="card-body py-3">
            <div class="fs-2 fw-bold text-primary">${overallAvg}%</div>
            <small class="text-muted">Overall Average</small>
          </div>
        </div>
      </div>
      <div class="col-6">
        <div class="card text-center h-100 border-0 bg-light">
          <div class="card-body py-3">
            <div class="fs-2 fw-bold ${attRate >= 80 ? 'text-success' : attRate >= 60 ? 'text-warning' : 'text-danger'}">${attRate}%</div>
            <small class="text-muted">Attendance Rate</small>
          </div>
        </div>
      </div>
    </div>

    ${subjectLabels.length ? `
    <h6 class="fw-semibold mb-2"><i class="fas fa-book me-1 text-primary"></i>Subject Averages</h6>
    <div style="position:relative;height:220px" class="mb-4"><canvas id="sdSubjectChart"></canvas></div>` : ''}

    <div class="row g-3 mb-4">
      <div class="col-md-7">
        <h6 class="fw-semibold mb-2"><i class="fas fa-calendar-check me-1 text-primary"></i>Attendance Breakdown</h6>
        <div class="d-flex gap-3 mb-2">
          <span class="badge bg-success">Present: ${attPresent}</span>
          <span class="badge bg-warning text-dark">Late: ${attLate}</span>
          <span class="badge bg-danger">Absent: ${attAbsent}</span>
        </div>
        ${attTotal ? `<div style="position:relative;height:180px"><canvas id="sdAttChart"></canvas></div>` : '<p class="text-muted small">No attendance records.</p>'}
      </div>
      <div class="col-md-5">
        <h6 class="fw-semibold mb-2"><i class="fas fa-chart-line me-1 text-primary"></i>Progress</h6>
        ${progLabels.length ? `<div style="position:relative;height:180px"><canvas id="sdProgressChart"></canvas></div>`
          : '<p class="text-muted small">No progress data yet.</p>'}
      </div>
    </div>

    ${recentScores.length ? `
    <h6 class="fw-semibold mb-2"><i class="fas fa-star-half-stroke me-1 text-primary"></i>Recent Scores</h6>
    <div class="table-responsive">
      <table class="table table-sm table-hover">
        <thead class="table-light"><tr><th>Subject</th><th>Type</th><th>Marks</th><th>%</th><th>Grade</th><th>Term</th></tr></thead>
        <tbody>
          ${recentScores.map(s => `
            <tr>
              <td>${s.subject_name || '—'}</td>
              <td class="text-capitalize">${s.assessment_type}</td>
              <td>${s.marks_obtained}/${s.max_marks}</td>
              <td>${parseFloat(s.percentage || 0).toFixed(1)}%</td>
              <td><span class="badge bg-secondary">${s.grade || '—'}</span></td>
              <td><small class="text-muted">${s.term_name || '—'}</small></td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>` : '<p class="text-muted small">No scores recorded yet.</p>'}`;

  // Subject chart
  if (subjectLabels.length && $('sdSubjectChart')) {
    destroyChart('sdSubjectChart');
    new Chart($('sdSubjectChart'), {
      type: 'bar',
      data: {
        labels: subjectLabels,
        datasets: [{ label: 'Average %', data: subjectAvgs,
          backgroundColor: subjectAvgs.map(v => v >= 80 ? 'rgba(76,175,80,.7)' : v >= 60 ? 'rgba(255,193,7,.7)' : 'rgba(244,67,54,.7)'),
          borderRadius: 5 }],
      },
      options: { responsive: true, maintainAspectRatio: false,
        scales: { y: { min: 0, max: 100, ticks: { callback: v => v + '%' } } },
        plugins: { legend: { display: false } } }
    });
  }

  // Attendance donut
  if (attTotal && $('sdAttChart')) {
    destroyChart('sdAttChart');
    new Chart($('sdAttChart'), {
      type: 'doughnut',
      data: {
        labels: ['Present', 'Late', 'Absent'],
        datasets: [{ data: [attPresent, attLate, attAbsent],
          backgroundColor: ['#4caf50', '#ffc107', '#f44336'] }],
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
    });
  }

  // Progress line
  if (progLabels.length && $('sdProgressChart')) {
    destroyChart('sdProgressChart');
    new Chart($('sdProgressChart'), {
      type: 'line',
      data: {
        labels: progLabels,
        datasets: [{ label: 'Average %', data: progPercents,
          borderColor: '#4361ee', backgroundColor: 'rgba(67,97,238,.15)',
          fill: true, tension: 0.3, pointRadius: 4, pointBackgroundColor: '#4361ee' }],
      },
      options: { responsive: true, maintainAspectRatio: false,
        scales: { y: { min: 0, max: 100, ticks: { callback: v => v + '%' } } },
        plugins: { legend: { display: false } } }
    });
  }
};

async function renderImages() {
  setTitle('School Images');
  loading();
  const data = await API.json(await API.getImages({ page_size: 50 }));
  const images = data?.results ?? [];

  if (!images.length) {
    pc().innerHTML = `<div class="section-header"><h4><i class="fas fa-images me-2 text-primary"></i>School Images</h4></div>${empty('No images published yet.')}`;
    return;
  }

  const cards = images.map(img => `
    <div class="col-md-4 col-sm-6 mb-4">
      <div class="card h-100">
        <img src="${img.image}" class="card-img-top" style="height:200px;object-fit:cover" alt="${img.title}"
             onerror="this.src='/static/frontend/img/placeholder.png'">
        <div class="card-body">
          <h6 class="card-title mb-1">${img.title}</h6>
          ${img.description ? `<p class="card-text small text-muted mb-2">${img.description}</p>` : ''}
          <span class="badge bg-secondary">${img.category || 'General'}</span>
          <small class="text-muted ms-2">${img.uploaded_by_name || ''}</small>
        </div>
      </div>
    </div>`).join('');

  pc().innerHTML = `
    <div class="section-header">
      <h4><i class="fas fa-images me-2 text-primary"></i>School Images</h4>
      <span class="text-muted small">${images.length} published</span>
    </div>
    <div class="row">${cards}</div>`;
}

async function renderProfile() {
  setTitle('Profile');
  loading();
  const res = await API.json(await API.profile());
  if (!res) { pc().innerHTML = empty('Failed to load profile.'); return; }

  pc().innerHTML = `
    <div class="row justify-content-center">
      <div class="col-md-7">
        <div class="card">
          <div class="card-header"><i class="fas fa-circle-user me-2"></i>My Profile</div>
          <div class="card-body">
            <div id="profileAlert" class="d-none alert"></div>
            <form id="profileForm">
              <div class="row g-3">
                <div class="col-md-6">
                  <label class="form-label small fw-semibold">First Name</label>
                  <input class="form-control" name="first_name" value="${res.first_name||''}">
                </div>
                <div class="col-md-6">
                  <label class="form-label small fw-semibold">Last Name</label>
                  <input class="form-control" name="last_name" value="${res.last_name||''}">
                </div>
                <div class="col-md-6">
                  <label class="form-label small fw-semibold">Email or school login ID</label>
                  <input class="form-control" type="email" value="${res.email||''}" disabled>
                </div>
                <div class="col-md-6">
                  <label class="form-label small fw-semibold">Phone</label>
                  <input class="form-control" name="phone_number" value="${res.phone_number||''}">
                </div>
                <div class="col-12">
                  <label class="form-label small fw-semibold">Role</label>
                  <input class="form-control" value="${res.role}" disabled>
                </div>
              </div>
              <button type="submit" class="btn btn-primary mt-4">
                <i class="fas fa-save me-2"></i>Save Changes
              </button>
            </form>
          </div>
        </div>

        <div class="card mt-4">
          <div class="card-header"><i class="fas fa-lock me-2"></i>Change Password</div>
          <div class="card-body">
            <div id="pwdAlert" class="d-none alert"></div>
            <form id="pwdForm">
              <div class="mb-3">
                <label class="form-label small fw-semibold">Current Password</label>
                <input type="password" class="form-control" name="old_password" required>
              </div>
              <div class="mb-3">
                <label class="form-label small fw-semibold">New Password</label>
                <input type="password" class="form-control" name="new_password" required minlength="8">
              </div>
              <div class="mb-3">
                <label class="form-label small fw-semibold">Confirm New Password</label>
                <input type="password" class="form-control" name="new_password_confirm" required minlength="8">
              </div>
              <button type="submit" class="btn btn-warning">
                <i class="fas fa-key me-2"></i>Change Password
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>`;

  $('profileForm').addEventListener('submit', async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const payload = Object.fromEntries(fd.entries());
    const res = await API.json(await API.updateProfile(payload));
    const al = $('profileAlert');
    if (res?.id) {
      al.className = 'alert alert-success'; al.textContent = 'Profile updated!';
      const u = API.getUser(); Object.assign(u, payload); localStorage.setItem('sp_user', JSON.stringify(u));
      updateTopbar(u);
    } else {
      al.className = 'alert alert-danger'; al.textContent = JSON.stringify(res);
    }
    al.classList.remove('d-none');
  });

  $('pwdForm').addEventListener('submit', async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const payload = Object.fromEntries(fd.entries());
    const r = await API.changePassword(payload);
    const al = $('pwdAlert');
    if (r?.ok) {
      al.className = 'alert alert-success'; al.textContent = 'Password changed successfully!';
      e.target.reset();
    } else {
      const err = await API.json(r);
      al.className = 'alert alert-danger'; al.textContent = err?.detail || JSON.stringify(err);
    }
    al.classList.remove('d-none');
  });
}

/* ── Add Student modal ── */
window.openAddStudent = async () => {
  const clsData = await API.json(await API.getClasses({ page_size: 100 }));
  const classes = clsData?.results ?? [];

  openModal('Add New Student', `
    <form id="addStudentForm">
      <div class="row g-3">
        <div class="col-md-6">
          <label class="form-label small fw-semibold">First Name</label>
          <input class="form-control" name="first_name" required>
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-semibold">Last Name</label>
          <input class="form-control" name="last_name" required>
        </div>
        <div class="col-12">
          <label class="form-label small fw-semibold">Email or school login ID</label>
          <input class="form-control" type="text" name="email" required placeholder="mary or mary@${schoolAccountSuffix}">
          <small class="text-muted">A name without @ uses @${schoolAccountSuffix}. Full existing email addresses also work.</small>
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-semibold">Password</label>
          <input class="form-control" type="password" name="password" minlength="8" placeholder="Min 8 characters">
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-semibold">Admission Number</label>
          <input class="form-control" name="admission_number" required>
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-semibold">Class</label>
          <select class="form-select" name="class_assigned">
            <option value="">— No class —</option>
            ${classes.map(c=>`<option value="${c.id}">${c.name}</option>`).join('')}
          </select>
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-semibold">Date of Birth</label>
          <input class="form-control" type="date" name="date_of_birth">
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-semibold">Parent Name</label>
          <input class="form-control" name="parent_name">
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-semibold">Parent Contact</label>
          <input class="form-control" name="parent_contact">
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-semibold">Parent Email</label>
          <input class="form-control" type="email" name="parent_email">
        </div>
      </div>
    </form>`, async () => {
    const fd = new FormData($('addStudentForm'));
    const payload = Object.fromEntries([...fd.entries()].filter(([,v]) => v !== ''));
    const res = await API.createStudent(payload);
    if (res?.ok) {
      toast('Student added successfully!');
      bsModal.hide();
      renderStudents();
    } else {
      const err = await API.json(res);
      toast(JSON.stringify(err), 'danger');
    }
  });
};

/* ── Add Teacher modal ── */
window.openAddTeacher = async () => {
  openModal('Add New Teacher', `
    <form id="addTeacherForm">
      <div class="row g-3">
        <div class="col-md-6">
          <label class="form-label small fw-semibold">First Name</label>
          <input class="form-control" name="first_name" required>
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-semibold">Last Name</label>
          <input class="form-control" name="last_name" required>
        </div>
        <div class="col-12">
          <label class="form-label small fw-semibold">Email or school login ID</label>
          <input class="form-control" type="text" name="email" required placeholder="mary or mary@${schoolAccountSuffix}">
          <small class="text-muted">A name without @ uses @${schoolAccountSuffix}. Full existing email addresses also work.</small>
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-semibold">Password</label>
          <input class="form-control" type="password" name="password" minlength="8" placeholder="Min 8 characters">
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-semibold">Employee ID</label>
          <input class="form-control" name="employee_id" required>
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-semibold">Qualification</label>
          <input class="form-control" name="qualification">
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-semibold">Subject Specialization</label>
          <input class="form-control" name="subject_specialization">
        </div>
        <div class="col-12">
          <label class="form-label small fw-semibold">Bio</label>
          <textarea class="form-control" name="bio" rows="2"></textarea>
        </div>
      </div>
    </form>`, async () => {
    const fd = new FormData($('addTeacherForm'));
    const payload = Object.fromEntries([...fd.entries()].filter(([,v]) => v !== ''));
    const res = await API.createTeacher(payload);
    if (res?.ok) {
      toast('Teacher added successfully!');
      bsModal.hide();
      renderTeachers();
    } else {
      const err = await API.json(res);
      toast(JSON.stringify(err), 'danger');
    }
  });
};

/* ── Class Teacher Performance Dashboard ── */
async function renderClassPerformance() {
  setTitle('Class Performance');
  loading();

  // 1. Get this teacher's profile + assigned class
  const meRes = await API.json(await API.teacherMe());
  if (!meRes || meRes.error) {
    pc().innerHTML = empty('Could not load your teacher profile.');
    return;
  }

  const myClass = meRes.my_class;
  if (!myClass) {
    pc().innerHTML = `
      <div class="section-header">
        <h4><i class="fas fa-chart-bar me-2 text-primary"></i>Class Performance</h4>
      </div>
      <div class="empty-state">
        <i class="fas fa-chalkboard-user"></i>
        <p>You are not assigned as a class teacher.<br>
           Ask an admin to assign you to a class.</p>
      </div>`;
    return;
  }

  // 2. Fetch student performance data for that class
  const perfRes = await API.json(await API.classStudentPerformance(myClass.id));
  if (!perfRes) {
    pc().innerHTML = empty('Failed to load class performance data.');
    return;
  }

  const { class_name, total_students, current_term, all_subjects, students } = perfRes;

  if (!students.length) {
    pc().innerHTML = `
      <div class="section-header">
        <h4><i class="fas fa-chart-bar me-2 text-primary"></i>${class_name} — Performance</h4>
      </div>
      ${empty('No students in this class yet.')}`;
    return;
  }

  // 3. Aggregate class-level stats
  const withPct   = students.filter(s => s.average_percentage > 0);
  const classAvg  = withPct.length
    ? (withPct.reduce((t, s) => t + s.average_percentage, 0) / withPct.length).toFixed(1)
    : '—';
  const passRate  = total_students
    ? ((students.filter(s => ['promoted','conditional'].includes(s.status)).length / total_students) * 100).toFixed(1)
    : '—';
  const gradeCounts = { A:0, B:0, C:0, D:0, E:0, F:0 };
  students.forEach(s => { if (s.overall_grade in gradeCounts) gradeCounts[s.overall_grade]++; });

  // Subject averages across the whole class
  const subjClassMap = {};
  students.forEach(s => {
    Object.entries(s.subjects).forEach(([subj, avg]) => {
      subjClassMap[subj] = subjClassMap[subj] || { sum: 0, count: 0 };
      subjClassMap[subj].sum += avg;
      subjClassMap[subj].count++;
    });
  });
  const subjLabels = all_subjects;
  const subjAvgs   = subjLabels.map(k =>
    subjClassMap[k] ? (subjClassMap[k].sum / subjClassMap[k].count).toFixed(1) : 0
  );

  const GRADE_COLOR_MAP = { A:'#4361ee', B:'#3a86ff', C:'#06d6a0', D:'#ffd166', E:'#ef476f', F:'#073b4c' };
  const PALETTE = ['#4361ee','#3a86ff','#06d6a0','#ffd166','#ef476f','#073b4c','#f72585','#7209b7'];

  // 4. Render HTML
  pc().innerHTML = `
    <div class="section-header mb-3">
      <h4><i class="fas fa-chart-bar me-2 text-primary"></i>${class_name} — Performance</h4>
      <span class="badge bg-secondary fs-6">${current_term || 'No active term'}</span>
    </div>

    <!-- Stat cards -->
    <div class="row g-3 mb-4">
      <div class="col-6 col-md-3">
        ${statCard('fa-users', 'Students', total_students, '#e9d8fd', '#6b21a8')}
      </div>
      <div class="col-6 col-md-3">
        ${statCard('fa-percent', 'Class Average', classAvg + '%', '#bee3f8', '#1a56db')}
      </div>
      <div class="col-6 col-md-3">
        ${statCard('fa-arrow-up', 'Pass Rate', passRate + '%', '#c6f6d5', '#276749')}
      </div>
      <div class="col-6 col-md-3">
        ${statCard('fa-chalkboard-user', 'Subjects', subjLabels.length, '#feebc8', '#c05621')}
      </div>
    </div>

    <!-- Charts row -->
    <div class="row g-3 mb-4">
      <div class="col-md-4">
        <div class="card h-100">
          <div class="card-header"><i class="fas fa-chart-pie me-2"></i>Grade Distribution</div>
          <div class="card-body"><div style="position:relative;height:220px"><canvas id="cpGradeChart"></canvas></div></div>
        </div>
      </div>
      <div class="col-md-8">
        <div class="card h-100">
          <div class="card-header"><i class="fas fa-chart-bar me-2"></i>Class Average by Subject</div>
          <div class="card-body"><div style="position:relative;height:220px"><canvas id="cpSubjChart"></canvas></div></div>
        </div>
      </div>
    </div>

    <!-- Student performance table -->
    <div class="card">
      <div class="card-header fw-semibold"><i class="fas fa-table me-2"></i>Student Performance</div>
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover mb-0">
            <thead class="table-light">
              <tr>
                <th>#</th>
                <th>Student</th>
                <th>Avg %</th>
                <th>Grade</th>
                <th>Position</th>
                ${subjLabels.map(s => `<th class="text-center" title="${s}">${s.split(' ')[0]}</th>`).join('')}
                <th>Attendance</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              ${students.map((s, i) => `
                <tr>
                  <td class="text-muted small">${i + 1}</td>
                  <td>
                    <strong>${s.student_name}</strong><br>
                    <small class="text-muted">${s.admission_number}</small>
                  </td>
                  <td><strong>${s.average_percentage > 0 ? s.average_percentage.toFixed(1) + '%' : '—'}</strong></td>
                  <td><span class="badge bg-primary">${s.overall_grade || '—'}</span></td>
                  <td>${s.position_in_class ? `<span class="badge bg-secondary">#${s.position_in_class}</span>` : '—'}</td>
                  ${subjLabels.map(subj => {
                    const val = s.subjects[subj];
                    const color = val === undefined ? 'text-muted' : val >= 70 ? 'text-success' : val >= 50 ? 'text-warning' : 'text-danger';
                    return `<td class="text-center ${color}">${val !== undefined ? val.toFixed(1) + '%' : '—'}</td>`;
                  }).join('')}
                  <td>
                    <span class="${s.attendance_rate >= 80 ? 'text-success' : s.attendance_rate >= 60 ? 'text-warning' : 'text-danger'} fw-semibold">
                      ${s.attendance_rate}%
                    </span>
                    <small class="text-muted d-block">${s.attendance_present}/${s.attendance_total} days</small>
                  </td>
                  <td>
                    <span class="badge bg-${s.status==='promoted'?'success':s.status==='retained'?'danger':s.status==='conditional'?'warning':'secondary'}">
                      ${s.status}
                    </span>
                  </td>
                  <td>
                    <button class="btn btn-outline-secondary btn-sm" title="Progress chart"
                      onclick="openStudentProgress('${s.student_id}','${s.student_name}')">
                      <i class="fas fa-chart-line"></i>
                    </button>
                  </td>
                </tr>`).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>`;

  // 5. Render charts
  const gradeNonZero = Object.entries(gradeCounts).filter(([,v]) => v > 0);
  destroyChart('cpGradeChart');
  new Chart($('cpGradeChart'), {
    type: 'doughnut',
    data: {
      labels: gradeNonZero.map(([k]) => `Grade ${k}`),
      datasets: [{
        data: gradeNonZero.map(([,v]) => v),
        backgroundColor: gradeNonZero.map(([k]) => GRADE_COLOR_MAP[k]),
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } },
        tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed} students` } }
      }
    }
  });

  destroyChart('cpSubjChart');
  new Chart($('cpSubjChart'), {
    type: 'bar',
    data: {
      labels: subjLabels,
      datasets: [{
        label: 'Class Average %',
        data: subjAvgs,
        backgroundColor: subjLabels.map((_, i) => PALETTE[i % PALETTE.length] + 'bb'),
        borderColor:     subjLabels.map((_, i) => PALETTE[i % PALETTE.length]),
        borderWidth: 1,
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { min: 0, max: 100, ticks: { callback: v => v + '%' } }
      }
    }
  });
}

/* ── Router ── */
const SECTIONS = {
  school_settings:   renderSchoolSettings,
  overview:          renderOverview,
  class_performance: renderClassPerformance,
  students:          renderStudents,
  teachers:          renderTeachers,
  classes:           renderClasses,
  subjects:          renderSubjects,
  attendance:        renderAttendance,
  scores:            renderScores,
  results:           renderResults,
  images:            renderImages,
  profile:           renderProfile,
};

function navigate(section) {
  if (!SECTIONS[section]) return;
  activeSection = section;
  window.location.hash = section;

  document.querySelectorAll('.nav-item a').forEach(a => {
    a.classList.toggle('active', a.dataset.section === section);
  });

  SECTIONS[section]();

  if (window.innerWidth < 768) {
    $('sidebar').classList.remove('open');
  }
}

/* ── Sidebar nav ── */
function buildNav(role) {
  const items = NAV[role] || NAV.student;
  $('navMenu').innerHTML = items.map(n => `
    <li class="nav-item">
      <a href="#" data-section="${n.section}" onclick="navigate('${n.section}');return false;">
        <i class="fas ${n.icon}"></i>${n.label}
      </a>
    </li>`).join('');
}

/* ── Topbar ── */
function updateTopbar(u) {
  const initials = `${u.first_name?.[0]||''}${u.last_name?.[0]||''}`.toUpperCase() || '?';
  $('userAvatar').textContent = initials;
  $('userName').textContent   = `${u.first_name} ${u.last_name}`;
  const pill = $('rolePill');
  pill.textContent  = u.role;
  pill.className    = `role-pill role-${u.role}`;
}

/* ── Sidebar toggle ── */
function setupToggle() {
  $('sidebarToggle').addEventListener('click', () => {
    if (window.innerWidth < 768) {
      $('sidebar').classList.toggle('open');
    } else {
      $('sidebar').classList.toggle('collapsed');
      $('mainContent').classList.toggle('expanded');
    }
  });
}

/* ── Boot ── */
window.addEventListener('sessionExpired', () => {
  toast('Your session expired. Redirecting to login…', 'warning');
});

document.addEventListener('DOMContentLoaded', async () => {
  bsModal = new bootstrap.Modal($('mainModal'));
  setupToggle();

  const storedUser = API.getUser();
  const token      = localStorage.getItem('sp_token');

  if (!storedUser || !token) {
    window.location.href = '/';
    return;
  }

  user = storedUser;
  buildNav(user.role);
  updateTopbar(user);

  $('logoutBtn').addEventListener('click', async () => {
    await API.logout();
    window.location.href = '/';
  });

  const hash = window.location.hash.replace('#', '');
  const start = SECTIONS[hash] ? hash : 'overview';
  navigate(start);
});


async function renderSchoolSettings() {
  setTitle('School Settings');
  if (user.role !== 'admin') { pc().textContent = 'Only administrators can change school settings.'; return; }
  loading();
  try {
    const response = await API.schoolSettings();
    if (!response?.ok) throw new Error('Could not load school settings.');
    const settings = await API.json(response);
    if (activeSection !== 'school_settings') return;
    pc().innerHTML = `
      <div class="card" style="max-width:720px">
        <div class="card-header">Set up your school</div>
        <div class="card-body">
          <p>Choose the school name displayed on the login page and dashboard, and the suffix used for new accounts.</p>
          <form id="schoolSettingsForm">
            <div class="mb-3">
              <label for="schoolName" class="form-label">School name</label>
              <input id="schoolName" name="school_name" class="form-control" required maxlength="150">
            </div>
            <div class="mb-3">
              <label for="accountSuffix" class="form-label">Account suffix</label>
              <div class="input-group"><span class="input-group-text">@</span>
                <input id="accountSuffix" name="account_suffix" class="form-control" required maxlength="100" aria-describedby="suffixHelp">
              </div>
              <div id="suffixHelp" class="form-text">Use ksc for Kahuho Secondary School or ktp for Kiambogo Township Primary. Enter the suffix without @.</div>
            </div>
            <p>New account example: <strong id="accountPreview"></strong></p>
            <p class="text-muted">These are school login IDs. A short suffix does not create an email inbox. Changing it leaves existing accounts and passwords unchanged. Each school needs its own installation and database.</p>
            <div id="schoolSettingsMessage" role="status" aria-live="polite"></div>
            <button type="submit" id="saveSchoolSettings" class="btn btn-primary">Save School Settings</button>
          </form>
        </div>
      </div>`;
    $('schoolName').value = settings.school_name;
    $('accountSuffix').value = settings.account_suffix;
    const preview = () => { $('accountPreview').textContent = 'example@' + $('accountSuffix').value.trim().toLowerCase(); };
    $('accountSuffix').addEventListener('input', preview);
    preview();
    $('schoolSettingsForm').addEventListener('submit', async event => {
      event.preventDefault();
      const button = $('saveSchoolSettings');
      const message = $('schoolSettingsMessage');
      button.disabled = true;
      message.textContent = '';
      try {
        const response = await API.updateSchoolSettings({school_name: $('schoolName').value.trim(), account_suffix: $('accountSuffix').value.trim().toLowerCase()});
        const data = await API.json(response);
        if (!response?.ok) throw new Error(data ? Object.values(data).flat().join(' ') : 'Could not save school settings.');
        schoolAccountSuffix = data.account_suffix;
        $('schoolBrand').textContent = data.school_name;
        document.title = data.school_name;
        message.className = 'alert alert-success';
        message.textContent = 'School settings saved. Existing accounts keep their login IDs.';
      } catch (error) {
        message.className = 'alert alert-danger';
        message.textContent = error.message;
      } finally { button.disabled = false; }
    });
  } catch (error) { pc().textContent = error.message; }
}
