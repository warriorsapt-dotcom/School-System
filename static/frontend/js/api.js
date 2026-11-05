const API = (() => {
  const BASE = '/api/v1';

  const getToken   = () => localStorage.getItem('sp_token');
  const getRefresh = () => localStorage.getItem('sp_refresh');
  const getUser    = () => JSON.parse(localStorage.getItem('sp_user') || 'null');

  const setSession = (access, refresh, user) => {
    localStorage.setItem('sp_token', access);
    if (refresh) localStorage.setItem('sp_refresh', refresh);
    if (user)    localStorage.setItem('sp_user', JSON.stringify(user));
  };

  const clearSession = () => {
    ['sp_token','sp_refresh','sp_user'].forEach(k => localStorage.removeItem(k));
  };

  const authHeaders = () => ({
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${getToken()}`,
  });

  const doRefresh = async () => {
    const refresh = getRefresh();
    if (!refresh) return false;
    const res = await fetch(`${BASE}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return false;
    const d = await res.json();
    localStorage.setItem('sp_token', d.access);
    if (d.refresh) localStorage.setItem('sp_refresh', d.refresh);
    return true;
  };

  const req = async (method, endpoint, body = null, params = {}) => {
    const url = new URL(BASE + endpoint, window.location.origin);
    Object.entries(params).forEach(([k, v]) => v != null && url.searchParams.set(k, v));
    const opts = { method, headers: authHeaders() };
    if (body) opts.body = JSON.stringify(body);

    let res = await fetch(url.toString(), opts);
    if (res.status === 401) {
      const ok = await doRefresh();
      if (ok) {
        opts.headers = authHeaders();
        res = await fetch(url.toString(), opts);
      } else {
        clearSession();
        window.dispatchEvent(new CustomEvent('sessionExpired'));
        setTimeout(() => { window.location.href = '/'; }, 2000);
        return null;
      }
    }
    return res;
  };

  const json = async res => {
    if (!res || res.status === 204) return null;
    try { return await res.json(); } catch { return null; }
  };

  return {
    getUser, setSession, clearSession, json,
    workspace: (method, path, data, params) => req(method, '/' + path, data, params),

    schoolSettings: () => req('GET', '/school-settings/'),
    updateSchoolSettings: data => req('PATCH', '/school-settings/', data),

    /* auth */
    login:          (email, password) => fetch(`${BASE}/auth/login/`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email,password}) }),
    logout:         async () => { await req('POST','/auth/logout/',{refresh_token:getRefresh()}); clearSession(); },
    profile:        ()      => req('GET',  '/auth/profile/'),
    updateProfile:  data    => req('PUT',  '/auth/profile/', data),
    changePassword: data    => req('POST', '/auth/change-password/', data),

    /* students */
    getStudents:       p    => req('GET',  '/users/students/', null, p),
    studentAttendance: (id, p) => req('GET', `/users/students/${id}/attendance_history/`, null, p),
    getStudent:        id   => req('GET',  `/users/students/${id}/`),
    createStudent:     data => req('POST', '/users/students/', data),
    studentResults:    (id,p)=> req('GET', `/users/students/${id}/results/`, null, p),
    studentProgress:   id   => req('GET',  `/users/students/${id}/progress/`),

    /* teachers */
    getTeachers:       p    => req('GET',  '/users/teachers/', null, p),
    createTeacher:     data => req('POST', '/users/teachers/', data),
    teacherMe:         ()   => req('GET',  '/users/teachers/me/'),
    teacherClasses:    id   => req('GET',  `/users/teachers/${id}/classes/`),

    /* classes */
    getClasses:             p    => req('GET',  '/classes/', null, p),
    getClass:               id   => req('GET',  `/classes/${id}/`),
    createClass:            data => req('POST', '/classes/', data),
    classAttendance:        id   => req('GET',  `/classes/${id}/attendance/`),
    getClassSubjects:       id   => req('GET',  `/classes/${id}/`),
    classStudentPerformance:id   => req('GET',  `/classes/${id}/student_performance/`),

    /* subjects */
    getSubjects:       p    => req('GET',  '/subjects/', null, p),

    /* terms */
    getTerms:          p    => req('GET',  '/terms/', null, p),

    /* attendance */
    getAttendance:     p    => req('GET',  '/attendance/', null, p),
    markAttendance:    data => req('POST', '/attendance/', data),
    bulkMark:          list => req('POST', '/attendance/bulk_mark/', {attendances: list}),
    attendanceSummary: p    => req('GET',  '/attendance/summary/', null, p),

    /* scores */
    getScores:         p    => req('GET',  '/scores/', null, p),
    recordScore:       data => req('POST', '/scores/', data),
    addComment:        (id,data) => req('POST', `/scores/${id}/add_comment/`, data),

    /* results */
    getResults:        p    => req('GET',  '/results/', null, p),
    classRanking:      p    => req('GET',  '/results/class_ranking/', null, p),
    exportResultsCsv:  p    => req('GET',  '/results/export_csv/', null, p),
    progressChart:     p    => req('GET',  '/progress/chart/', null, p),

    /* images */
    getImages:         p    => req('GET',  '/images/', null, p),
  };
})();
