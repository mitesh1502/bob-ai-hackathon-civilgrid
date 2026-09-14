import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { GridshieldService } from '../../services/gridshield.service';

const SAMPLES = [
  "Why is A-01 ranked above A-15?",
  "What should we do about asset A-03?",
  "Which asset is highest priority for our crew today?",
  "Compare A-02 and A-20",
  "Explain the risk for A-05",
];

@Component({
  selector: 'app-advisor',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div style="padding:28px 32px 48px;max-width:900px">
      <div class="page-title">&#129302; GridShield Advisor</div>
      <div class="page-caption">
        Ask questions grounded in the computed risk data. Every answer is built from real field values — no hallucination possible.
        Try: <em>"Why is A-01 ranked above A-20?"</em> or <em>"What should we do about A-03?"</em>
      </div>

      <div class="card">
        <label style="font-size:0.85rem;color:var(--muted);display:block;margin-bottom:6px">Your question:</label>
        <textarea [(ngModel)]="question" placeholder="e.g. Compare A-01 and A-15, or What is the risk for asset A-04?" rows="3"></textarea>
        <button class="ask-btn" (click)="ask()" [disabled]="asking || !question.trim()">
          {{ asking ? 'Generating answer…' : 'Ask' }}
        </button>
      </div>

      <div *ngIf="asking" style="text-align:center;padding:20px"><span class="spinner"></span></div>
      <div *ngIf="error" style="color:var(--critical);padding:8px">{{ error }}</div>

      <div *ngIf="answer" class="advisor-answer">{{ answer }}</div>

      <div style="margin-top:24px">
        <div style="font-size:0.88rem;font-weight:600;margin-bottom:10px">Sample questions:</div>
        <button *ngFor="let s of samples" class="sample-btn" (click)="askSample(s)">{{ s }}</button>
      </div>

      <footer style="border-top:1px solid var(--border);padding:16px 0;text-align:center;font-size:0.75rem;color:var(--muted);margin-top:32px">Made with IBM Bob</footer>
    </div>
  `,
})
export class AdvisorComponent {
  question = '';
  answer   = '';
  asking   = false;
  error    = '';
  samples  = SAMPLES;

  constructor(private svc: GridshieldService) {}

  ask() {
    if (!this.question.trim()) return;
    this.asking = true;
    this.answer = '';
    this.error  = '';
    this.svc.ask(this.question).subscribe({
      next: (r) => { this.answer = r.answer; this.asking = false; },
      error: (e) => { this.error = e.error?.error || e.message; this.asking = false; },
    });
  }

  askSample(q: string) {
    this.question = q;
    this.ask();
  }
}
