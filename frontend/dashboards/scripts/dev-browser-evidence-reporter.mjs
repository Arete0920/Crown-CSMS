import { lstatSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { EvidenceCollector, reject } from './browser-evidence-schema.mjs';

// Playwright swallows callback exceptions. Invalid callbacks leave no report;
// the separate parent process must validate a complete report before upload.
export default class DevBrowserEvidenceReporter {
  constructor() {
    this.collector = null;
    this.reportPath = null;
    try {
      const contextPath = process.env.CROWN_SAFE_EVIDENCE_CONTEXT;
      const projectDirectory = process.env.CROWN_SAFE_EVIDENCE_PROJECT;
      const reportPath = process.env.CROWN_SAFE_EVIDENCE_REPORT;
      if (![contextPath, projectDirectory, reportPath].every(value => typeof value === 'string' && path.isAbsolute(value))) reject();
      const info = lstatSync(contextPath);
      if (!info.isFile() || info.isSymbolicLink() || info.size > 1024 * 1024) reject();
      this.collector = new EvidenceCollector(JSON.parse(readFileSync(contextPath, 'utf8')), projectDirectory);
      this.reportPath = reportPath;
    } catch {
      // Never send exception messages, source snippets or paths to runner logs.
    }
  }

  // Returning false makes Playwright add a standard reporter with raw titles
  // and errors. This reporter intentionally owns, but does not print, stdio.
  printsToStdio() { return true; }
  onStdOut() {}
  onStdErr() {}
  onBegin(_config, suite) {
    this.collector?.guard(() => this.collector.begin(suite.allTests()));
  }
  onTestEnd(test, result) {
    this.collector?.guard(() => this.collector.endTest(test, result));
  }
  onError() { this.collector?.error(); }
  onEnd(result) {
    this.collector?.guard(() => {
      const report = this.collector.finish(result);
      writeFileSync(this.reportPath, `${JSON.stringify(report, null, 2)}\n`, { flag: 'wx', mode: 0o600 });
    });
    // Do not override the test runner's status or exit code.
  }
}
