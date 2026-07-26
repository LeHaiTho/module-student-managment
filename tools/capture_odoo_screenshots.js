const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const baseURL = process.env.ODOO_URL || 'http://localhost:8069';
const outDir = path.resolve(__dirname, '..', 'docs', 'screenshots');

const users = {
  student: {
    login: process.env.ODOO_STUDENT_LOGIN || 'sv.nguyenvanan',
    password: process.env.ODOO_STUDENT_PASSWORD || '123456',
  },
  admin: {
    login: process.env.ODOO_ADMIN_LOGIN || 'admin.sms',
    password: process.env.ODOO_ADMIN_PASSWORD || '123456',
  },
};

async function settle(page) {
  await page.waitForLoadState('domcontentloaded').catch(() => {});
  await page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(1200);
}

async function capture(page, fileName, url) {
  const target = `${baseURL}${url}`;
  console.log(`[capture] ${fileName} <= ${target}`);
  await page.goto(target, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await settle(page);
  await page.screenshot({
    path: path.join(outDir, fileName),
    fullPage: true,
    animations: 'disabled',
  });
}

async function login(page, account) {
  await page.goto(`${baseURL}/web/login`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await settle(page);
  await page.locator('input[name="login"]').fill(account.login);
  await page.locator('input[name="password"]').fill(account.password);
  await page.locator('button[type="submit"], input[type="submit"]').first().click();
  await settle(page);
}

async function logout(page) {
  await page.goto(`${baseURL}/web/session/logout`, { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(() => {});
  await settle(page);
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });

  const publicPages = [
    ['hinh-4-6-login.png', '/web/login'],
    ['hinh-4-7-landing.png', '/university'],
    ['hinh-4-9-student-register.png', '/student/register'],
  ];
  for (const item of publicPages) await capture(page, ...item);

  await login(page, users.student);
  const portalPages = [
    ['hinh-4-8-portal-home.png', '/my/academic'],
    ['hinh-4-47-portal-registration.png', '/my/academic/registration'],
    ['hinh-4-48-portal-timetable.png', '/my/academic/timetable'],
    ['hinh-4-49-portal-transcript.png', '/my/academic/transcript'],
    ['hinh-4-50-portal-attendance.png', '/my/academic/attendance'],
    ['hinh-4-51-portal-fees.png', '/my/academic/fees'],
    ['hinh-4-52-portal-certificates.png', '/my/academic/certificates'],
    ['hinh-4-53-portal-affairs.png', '/my/academic/student-affairs'],
    ['hinh-4-54-portal-conduct.png', '/my/academic/conduct'],
    ['hinh-4-55-portal-surveys.png', '/my/academic/surveys'],
    ['hinh-4-56-portal-feedback.png', '/my/academic/feedback'],
  ];
  for (const item of portalPages) await capture(page, ...item);

  await logout(page);
  await login(page, users.admin);
  const backendPages = [
    ['hinh-4-10-main-menu.png', '/web'],
    ['hinh-4-11-faculty-kanban.png', '/web#action=182&model=univ.sms.faculty&view_type=kanban'],
    ['hinh-4-12-faculty-form.png', '/web#action=182&model=univ.sms.faculty&view_type=form'],
    ['hinh-4-13-department.png', '/web#action=183&model=univ.sms.department&view_type=list'],
    ['hinh-4-14-program.png', '/web#action=184&model=univ.sms.program&view_type=list'],
    ['hinh-4-15-subject.png', '/web#action=185&model=univ.sms.subject&view_type=list'],
    ['hinh-4-16-academic-year.png', '/web#action=186&model=univ.sms.academic.year&view_type=list'],
    ['hinh-4-17-term.png', '/web#action=187&model=univ.sms.term&view_type=list'],
    ['hinh-4-18-student-list.png', '/web#action=207&model=univ.sms.student&view_type=list'],
    ['hinh-4-19-student-form.png', '/web#action=207&model=univ.sms.student&view_type=form'],
    ['hinh-4-20-student-lookup.png', '/web#action=333&model=univ.sms.student&view_type=list'],
    ['hinh-4-21-home-class.png', '/web#action=332&model=univ.sms.home.class&view_type=list'],
    ['hinh-4-22-enrollment.png', '/web#action=206&model=univ.sms.enrollment&view_type=list'],
    ['hinh-4-23-class.png', '/web#action=219&model=univ.sms.class&view_type=list'],
    ['hinh-4-24-timetable.png', '/web#action=220&model=univ.sms.timetable&view_type=list'],
    ['hinh-4-25-attendance-sheet.png', '/web#action=301&model=univ.sms.attendance.sheet&view_type=list'],
    ['hinh-4-26-exam.png', '/web#action=307&model=univ.sms.exam&view_type=list'],
    ['hinh-4-27-exam-result.png', '/web#action=308&model=univ.sms.exam.result&view_type=list'],
    ['hinh-4-28-transcript.png', '/web#action=309&model=univ.sms.transcript&view_type=list'],
    ['hinh-4-29-fee.png', '/web#action=310&model=univ.sms.fee&view_type=list'],
    ['hinh-4-30-fee-invoice.png', '/web#action=311&model=univ.sms.fee.invoice&view_type=list'],
    ['hinh-4-31-registration-period.png', '/web#action=312&model=univ.sms.registration.period&view_type=list'],
    ['hinh-4-32-course-offering.png', '/web#action=313&model=univ.sms.course.offering&view_type=list'],
    ['hinh-4-33-registration.png', '/web#action=314&model=univ.sms.registration&view_type=list'],
    ['hinh-4-34-elective-wish.png', '/web#action=315&model=univ.sms.elective.wish&view_type=list'],
    ['hinh-4-35-notification.png', '/web#action=304&model=univ.sms.notification&view_type=list'],
    ['hinh-4-36-feedback-backend.png', '/web#action=221&model=univ.sms.feedback&view_type=list'],
    ['hinh-4-37-health-insurance.png', '/web#action=222&model=univ.sms.health.insurance&view_type=list'],
    ['hinh-4-38-residence.png', '/web#action=223&model=univ.sms.residence.info&view_type=list'],
    ['hinh-4-39-military.png', '/web#action=224&model=univ.sms.military.service&view_type=list'],
    ['hinh-4-40-conduct-criteria.png', '/web#action=302&model=univ.sms.conduct.criteria&view_type=list'],
    ['hinh-4-41-conduct-score.png', '/web#action=303&model=univ.sms.conduct.score&view_type=list'],
    ['hinh-4-42-certificate-type.png', '/web#action=217&model=univ.sms.certificate.type&view_type=list'],
    ['hinh-4-43-certificate-request.png', '/web#action=218&model=univ.sms.certificate.request&view_type=list'],
    ['hinh-4-44-survey-type.png', '/web#action=329&model=univ.sms.survey.type&view_type=list'],
    ['hinh-4-45-survey-instance.png', '/web#action=330&model=univ.sms.survey.instance&view_type=list'],
    ['hinh-4-46-survey-response.png', '/web#action=331&model=univ.sms.survey.response&view_type=list'],
    ['hinh-4-57-dashboard-student.png', '/web#action=316&model=univ.sms.student&view_type=graph'],
    ['hinh-4-58-dashboard-attendance.png', '/web#action=317&model=univ.sms.attendance.sheet&view_type=graph'],
    ['hinh-4-59-dashboard-exam.png', '/web#action=318&model=univ.sms.exam.result&view_type=graph'],
    ['hinh-4-60-dashboard-fee.png', '/web#action=319&model=univ.sms.fee.invoice&view_type=graph'],
    ['hinh-4-61-dashboard-registration.png', '/web#action=320&model=univ.sms.registration&view_type=graph'],
    ['hinh-4-62-dashboard-conduct.png', '/web#action=321&model=univ.sms.conduct.score&view_type=graph'],
    ['hinh-4-63-report-transcript.png', '/web#action=309&model=univ.sms.transcript&view_type=list'],
    ['hinh-4-64-report-invoice.png', '/web#action=311&model=univ.sms.fee.invoice&view_type=list'],
    ['hinh-4-65-report-conduct.png', '/web#action=303&model=univ.sms.conduct.score&view_type=list'],
    ['hinh-4-66-report-certificate.png', '/web#action=218&model=univ.sms.certificate.request&view_type=list'],
    ['hinh-4-67-report-registration.png', '/web#action=314&model=univ.sms.registration&view_type=list'],
    ['hinh-4-68-report-attendance.png', '/web#action=301&model=univ.sms.attendance.sheet&view_type=list'],
    ['hinh-4-69-import.png', '/web#action=207&model=univ.sms.student&view_type=list'],
    ['hinh-4-70-export.png', '/web#action=207&model=univ.sms.student&view_type=list'],
  ];
  for (const item of backendPages) await capture(page, ...item);

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
