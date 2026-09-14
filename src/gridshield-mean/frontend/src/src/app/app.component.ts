import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { GridshieldService } from './services/gridshield.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, CommonModule],
  template: `
    <div style="display:flex;min-height:100vh">
      <!-- Sidebar -->
      <aside style="width:230px;min-width:230px;background:#1a202c;color:#e2e8f0;display:flex;flex-direction:column;position:sticky;top:0;height:100vh;overflow-y:auto">
        <div style="padding:20px 18px 12px;border-bottom:1px solid #2d3748">
          <div style="font-size:1.2rem;color:#fff;font-weight:700">&#9889; GridShield</div>
          <div style="font-size:0.75rem;color:#a0aec0;margin-top:3px">Civil-Engineering-Aware<br>Power Grid Advisor</div>
        </div>
        <nav style="padding:12px 0;flex:1">
          <a routerLink="/dashboard"  routerLinkActive="nav-active" class="nav-link">&#128202; Dashboard</a>
          <a routerLink="/risk-table" routerLinkActive="nav-active" class="nav-link">&#128203; Risk Table</a>
          <a routerLink="/asset/A-03" routerLinkActive="nav-active" class="nav-link">&#128269; Asset Detail</a>
          <a routerLink="/reactive"   routerLinkActive="nav-active" class="nav-link">&#128201; Reactive vs Preventive</a>
          <a routerLink="/advisor"    routerLinkActive="nav-active" class="nav-link">&#129302; Advisor Chat</a>
        </nav>
        <div style="padding:12px 18px;border-top:1px solid #2d3748">
          <div style="font-size:0.72rem;color:#718096;margin-bottom:8px;font-weight:600;text-transform:uppercase;letter-spacing:.05em">Risk Bands</div>
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;font-size:0.78rem;color:#a0aec0"><div style="width:10px;height:10px;border-radius:50%;background:#c0392b;flex-shrink:0"></div>Critical &ge;70</div>
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;font-size:0.78rem;color:#a0aec0"><div style="width:10px;height:10px;border-radius:50%;background:#e67e22;flex-shrink:0"></div>Elevated 45&ndash;69</div>
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;font-size:0.78rem;color:#a0aec0"><div style="width:10px;height:10px;border-radius:50%;background:#d4a017;flex-shrink:0"></div>Watch 20&ndash;44</div>
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;font-size:0.78rem;color:#a0aec0"><div style="width:10px;height:10px;border-radius:50%;background:#27ae60;flex-shrink:0"></div>Normal &lt;20</div>
        </div>
        <div style="padding:12px 18px;border-top:1px solid #2d3748">
          <button class="rerun-btn" (click)="rerunPipeline()" [disabled]="pipelineRunning">
            {{ pipelineRunning ? 'Running…' : '&#128260; Rerun Pipeline' }}
          </button>
          <div *ngIf="pipelineMsg" style="font-size:0.75rem;color:#68d391;margin-top:6px">{{ pipelineMsg }}</div>
          <div *ngIf="pipelineErr" style="font-size:0.75rem;color:#fc8181;margin-top:6px">{{ pipelineErr }}</div>
        </div>
        <div style="padding:12px 18px;border-top:1px solid #2d3748;font-size:0.72rem;color:#718096;line-height:1.5">
          All recommendations are advisory only. No field work authorised without engineer sign-off.
        </div>
      </aside>

      <!-- Page content -->
      <main style="flex:1;overflow-x:hidden">
        <router-outlet />
      </main>
    </div>
  `,
  styles: [`
    .nav-link {
      display:block; padding:9px 18px; color:#a0aec0; text-decoration:none;
      font-size:0.88rem; border-left:3px solid transparent;
      transition:background .15s,color .15s;
    }
    .nav-link:hover { background:#2d3748; color:#fff; border-left-color:#3b82d4; }
    :host ::ng-deep .nav-active { background:#2d3748 !important; color:#fff !important; border-left-color:#3b82d4 !important; }
    .rerun-btn { padding:7px 14px; border:none; border-radius:6px; background:#2d3748; color:#e2e8f0; font-size:0.82rem; width:100%; }
    .rerun-btn:hover:not(:disabled) { background:#3a4a60; }
    .rerun-btn:disabled { opacity:0.6; cursor:not-allowed; }
  `],
})
export class AppComponent {
  pipelineRunning = false;
  pipelineMsg = '';
  pipelineErr = '';

  constructor(private svc: GridshieldService) {}

  rerunPipeline() {
    this.pipelineRunning = true;
    this.pipelineMsg = '';
    this.pipelineErr = '';
    this.svc.runPipeline().subscribe({
      next: (r) => { this.pipelineRunning = false; this.pipelineMsg = r.message; },
      error: (e) => { this.pipelineRunning = false; this.pipelineErr = e.error?.error || 'Pipeline failed'; },
    });
  }
}
